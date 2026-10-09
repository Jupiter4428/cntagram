# Create your models here.
from django.conf import settings
from django.db import models

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB (ตาม CHECK ใน ERD)


class DocType(models.Model):
    """summary, exam, cheatsheet, slide"""

    class Vault(models.TextChoices):
        LECTURE = "lecture", "คลังชีท (แยกตามรุ่น)"
        EXAM = "exam", "คลังข้อสอบ (รวมข้ามรุ่น)"

    id = models.SmallAutoField(primary_key=True)
    code = models.CharField(max_length=20, unique=True)
    name_th = models.CharField(max_length=50)
    vault = models.CharField(max_length=10, choices=Vault.choices)

    class Meta:
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

    def __str__(self):
        return self.code


class Document(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "รออนุมัติ"
        PUBLISHED = "published", "เผยแพร่"
        REJECTED = "rejected", "ไม่อนุมัติ"
        HIDDEN = "hidden", "ซ่อน"

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
        """เวอร์ชันปัจจุบัน = version_no สูงสุด"""
        return self.versions.order_by("-version_no").first()

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
    exam_year_be = models.PositiveSmallIntegerField("ปีที่สอบ (พ.ศ.)")

    class Meta:
        indexes = [
            models.Index(
                fields=["exam_period", "exam_year_be"], name="idx_exam_period_year"
            ),
        ]

    def __str__(self):
        return f"{self.document_id} {self.exam_period.code} {self.exam_year_be}"


class DocumentVersion(models.Model):
    class ScanStatus(models.TextChoices):
        PENDING = "pending", "รอสแกน"
        CLEAN = "clean", "ปลอดภัย"
        INFECTED = "infected", "พบมัลแวร์"

    document = models.ForeignKey(
        Document, on_delete=models.PROTECT, related_name="versions"
    )
    version_no = models.PositiveSmallIntegerField()
    storage_path = models.CharField(max_length=500)
    original_name = models.CharField(max_length=255)
    size_bytes = models.PositiveBigIntegerField()
    sha256 = models.CharField(max_length=64)
    scan_status = models.CharField(
        max_length=10, choices=ScanStatus.choices, default=ScanStatus.PENDING
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["document", "version_no"], name="uq_docversion_doc_no"
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

    def __str__(self):
        return f"{self.document_id} v{self.version_no}"