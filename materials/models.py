#..\materials\models.py
# Create your models here.
import unicodedata

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models, transaction
from django.db.models import Max

from catalog.models import SystemSetting

# เพดานสูงสุดที่ DB บังคับ (CHECK) ส่วนค่าที่ปรับได้จริงคือ system_setting.max_upload_mb
# ซึ่งเช็กใน DocumentVersion.clean() และต้องไม่เกินค่านี้
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB (ตาม CHECK ใน ERD)

sha256_validator = RegexValidator(
    regex=r"^[0-9a-f]{64}\Z",
    message="sha256 must be 64 lowercase hex characters.",
)


def validate_storage_path(value):
    """อนุญาตเฉพาะ path สัมพัทธ์ภายใน storage

    ปฏิเสธ "/" นำหน้า, "..", "//", backslash และอักขระควบคุม
    """
    parts = value.split("/")
    if (
        "\\" in value
        or any(part in ("", ".", "..") for part in parts)
        or any(unicodedata.category(ch)[0] == "C" for ch in value)
    ):
        raise ValidationError("Unsafe storage_path.")


def sanitize_filename(name):
    """ตัด path, อักขระควบคุม (กัน header injection ใน Content-Disposition)
    และจุด/ช่องว่างท้ายชื่อไฟล์ออก"""
    name = (name or "").replace("\\", "/").split("/")[-1]
    name = "".join(ch for ch in name if unicodedata.category(ch)[0] != "C")
    name = name.strip().strip(".").strip()
    return name[:255] or "file"


class DocType(models.Model):
    """summary, exam, cheatsheet, slide"""

    class Vault(models.TextChoices):
        LECTURE = "lecture", "Lecture vault (per batch)"
        EXAM = "exam", "Exam vault (shared across batches)"

    id = models.SmallAutoField(primary_key=True)
    code = models.CharField(max_length=20, unique=True)
    name_th = models.CharField(max_length=50)
    vault = models.CharField(max_length=10, choices=Vault.choices)

    class Meta:
        db_table = "doc_type"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(vault__in=["lecture", "exam"]),
                name="ck_doctype_vault",
            ),
        ]

    def __str__(self):
        return self.code


class ExamPeriod(models.Model):
    """midterm, final"""

    id = models.SmallAutoField(primary_key=True)
    code = models.CharField(max_length=20, unique=True)
    name_th = models.CharField(max_length=50)

    class Meta:
        db_table = "exam_period"

    def __str__(self):
        return self.code


class Document(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending approval"
        PUBLISHED = "published", "Published"
        REJECTED = "rejected", "Rejected"
        HIDDEN = "hidden", "Hidden"

    batch_course = models.ForeignKey(
        "catalog.BatchCourse", on_delete=models.PROTECT, related_name="documents"
    )
    doc_type = models.ForeignKey(
        DocType, on_delete=models.PROTECT, related_name="documents"
    )
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="documents"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "document"
        indexes = [
            models.Index(fields=["batch_course", "status"], name="idx_doc_bc_status"),
            models.Index(fields=["doc_type", "status"], name="idx_doc_type_status"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    status__in=["pending", "published", "rejected", "hidden"]
                ),
                name="ck_document_status",
            ),
        ]

    @property
    def current_version(self):
        """เวอร์ชันปัจจุบัน = version_no สูงสุด

        ถ้า prefetch_related("versions") มาแล้ว จะไม่ยิง query เพิ่ม (กัน N+1)
        """
        prefetched = getattr(self, "_prefetched_objects_cache", {}).get("versions")
        if prefetched is not None:
            return max(prefetched, key=lambda v: v.version_no, default=None)
        return self.versions.order_by("-version_no").first()

    @transaction.atomic
    def add_version(self, *, storage_path, original_name, size_bytes, sha256):
        """เพิ่มเวอร์ชันใหม่อย่างปลอดภัยเมื่อมีการอัปโหลดพร้อมกัน

        ล็อกแถว document ก่อนคำนวณ version_no ถัดไป ไม่งั้นสองคนอาจได้เลขเดียวกัน
        แล้วชน unique constraint
        """
        Document.objects.select_for_update().get(pk=self.pk)
        last = self.versions.aggregate(m=Max("version_no"))["m"] or 0
        return DocumentVersion.objects.create(
            document=self,
            version_no=last + 1,
            storage_path=storage_path,
            original_name=original_name,
            size_bytes=size_bytes,
            sha256=sha256,
        )

    def __str__(self):
        return self.title


class ExamDetail(models.Model):
    """1:1 กับ Document ที่เป็นข้อสอบ"""

    document = models.OneToOneField(
        Document,
        on_delete=models.PROTECT,
        primary_key=True,
        related_name="exam_detail",
    )
    exam_period = models.ForeignKey(
        ExamPeriod, on_delete=models.PROTECT, related_name="exam_details"
    )
    exam_year_be = models.PositiveSmallIntegerField(
        "Exam year (B.E.)",
        validators=[MinValueValidator(2500), MaxValueValidator(2700)],
    )

    class Meta:
        db_table = "exam_detail"
        indexes = [
            models.Index(
                fields=["exam_period", "exam_year_be"], name="idx_exam_period_year"
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(exam_year_be__gte=2500, exam_year_be__lte=2700),
                name="ck_exam_year_be_range",
            ),
        ]

    def clean(self):
        super().clean()
        # exam_detail ผูกได้เฉพาะเอกสารที่ประเภทอยู่ในคลังข้อสอบ
        if self.document_id is not None:
            if self.document.doc_type.vault != DocType.Vault.EXAM:
                raise ValidationError(
                    {"document": "exam_detail is only allowed for exam documents"}
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.document_id} {self.exam_period.code} {self.exam_year_be}"


class DocumentVersion(models.Model):
    class ScanStatus(models.TextChoices):
        PENDING = "pending", "Pending scan"
        CLEAN = "clean", "Clean"
        INFECTED = "infected", "Malware found"

    document = models.ForeignKey(
        Document, on_delete=models.PROTECT, related_name="versions"
    )
    version_no = models.PositiveSmallIntegerField()
    storage_path = models.CharField(
        max_length=500, unique=True, validators=[validate_storage_path]
    )
    original_name = models.CharField(max_length=255)
    size_bytes = models.PositiveBigIntegerField()
    sha256 = models.CharField(max_length=64, db_index=True, validators=[sha256_validator])
    scan_status = models.CharField(
        max_length=10, choices=ScanStatus.choices, default=ScanStatus.PENDING
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "document_version"
        constraints = [
            models.UniqueConstraint(
                fields=["document", "version_no"], name="uq_docversion_doc_no"
            ),
            models.CheckConstraint(
                condition=models.Q(size_bytes__gt=0),
                name="ck_docversion_size_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(size_bytes__lte=MAX_UPLOAD_BYTES),
                name="ck_docversion_size_max",
            ),
            models.CheckConstraint(
                condition=models.Q(scan_status__in=["pending", "clean", "infected"]),
                name="ck_docversion_scan_status",
            ),
        ]

    def clean(self):
        super().clean()
        # save() เรียกแค่ clean() (ไม่เรียก validators ของ field) จึงเช็กซ้ำตรงนี้
        # เพื่อให้ path/hash ที่ไม่ปลอดภัยเข้า DB ไม่ได้ แม้ข้อมูลไม่ได้มาจากฟอร์ม
        for field, validator in (
            ("storage_path", validate_storage_path),
            ("sha256", sha256_validator),
        ):
            value = getattr(self, field)
            if value:
                try:
                    validator(value)
                except ValidationError as exc:
                    raise ValidationError({field: exc.messages})
        if self.size_bytes is not None:
            limit_mb = SystemSetting.get_int(SystemSetting.MAX_UPLOAD_MB, 50)
            if limit_mb <= 0:  # ค่าตั้งผิด ให้ถอยกลับเป็นค่าเริ่มต้น
                limit_mb = 50
            limit = min(limit_mb * 1024 * 1024, MAX_UPLOAD_BYTES)
            if self.size_bytes > limit:
                raise ValidationError(
                    {"size_bytes": f"File is larger than {limit_mb} MB"}
                )

    def save(self, *args, **kwargs):
        self.original_name = sanitize_filename(self.original_name)
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.document_id} v{self.version_no}"


class Approval(models.Model):
    class Decision(models.TextChoices):
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    document = models.ForeignKey(
        Document, on_delete=models.PROTECT, related_name="approvals"
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="approvals"
    )
    approver_role = models.ForeignKey(
        "accounts.Role", on_delete=models.PROTECT, related_name="approvals"
    )
    decision = models.CharField(
        max_length=10, choices=Decision.choices
    )
    reason = models.TextField(blank=True, null=True)
    decided_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "approval"
        constraints = [
            models.UniqueConstraint(
                fields=["document", "approver"], name="uq_approval_document_approver"
            ),
            models.CheckConstraint(
                condition=models.Q(decision__in=["approved", "rejected"]),
                name="ck_approval_decision",
            ),
        ]

    def clean(self):
        super().clean()
        if self.decision == self.Decision.REJECTED and not (self.reason and self.reason.strip()):
            raise ValidationError({"reason": "Reason is required when rejecting a document."})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.document_id} - {self.approver_id} ({self.decision})"
