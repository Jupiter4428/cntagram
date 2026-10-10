#..\accounts\models.py
# Create your models here.
import re

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models, transaction
from django.utils import timezone

STUDENT_EMAIL_DOMAIN = "student.tu.ac.th"

# ตัวที่ 1-2 = ปีเข้า, ตัวที่ 3-4 = คณะ (ต้องเป็น 10), รวม 10 หลัก
# ใช้ [0-9] แทน \d (\d รับเลขไทย/เลขยูนิโค้ดอื่นด้วย) และใช้ \Z แทน $ ($ ยอมให้มี \n ต่อท้าย)
student_id_validator = RegexValidator(
    regex=r"^[0-9]{2}10[0-9]{6}\Z",
    message="Student ID must be 10 ASCII digits, and characters 3-4 must be 10.",
)

# ชื่อเล่นที่ห้ามใช้ เพื่อกันการสวมรอยเป็นผู้ดูแล เทียบหลังตัดช่องว่าง/ขีด/จุด และทำ casefold
# คำภาษาไทยตั้งใจเก็บไว้ เพราะเป็นข้อมูลที่ใช้กันการสวมรอยด้วยภาษาไทย
# ("แอดมิน" = admin, "ผู้ดูแล" = moderator, "ผู้ดูแลระบบ" = system administrator)
RESERVED_NICKNAMES = {
    "admin",
    "administrator",
    "moderator",
    "mod",
    "superadmin",
    "root",
    "system",
    "แอดมิน",
    "ผู้ดูแล",
    "ผู้ดูแลระบบ",
}


def validate_nickname(value):
    normalized = re.sub(r"[\s_\-.]+", "", value).casefold()
    if normalized in RESERVED_NICKNAMES:
        raise ValidationError("This nickname is reserved. Please choose another one.")


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        # createsuperuser อาจส่ง department มาเป็น instance หรือเป็น pk ก็ได้
        dept = extra_fields.pop("department", None)
        if dept is not None:
            extra_fields["department" if hasattr(dept, "pk") else "department_id"] = dept
        email = self.normalize_email(email.strip()).lower()
        # รหัสนักศึกษาดึงจากหน้า @ ของอีเมลเสมอ (superuser ข้ามได้)
        if not extra_fields.get("is_superuser") and not extra_fields.get("student_id"):
            _, extra_fields["student_id"] = self.model.validate_student_email(
                email, check_duplicate=False
            )
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        # ห้ามเติมเวลายินยอม PDPA ให้เอง: ต้องเป็นเวลาที่ผู้ใช้กดยอมรับจริง
        if extra_fields.get("pdpa_consent_at") is None:
            raise ValueError(
                "pdpa_consent_at is required (the time the user accepted PDPA consent)"
            )
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("email_verified_at", timezone.now())
        # superuser สร้างผ่าน CLI โดยเจ้าของระบบ จึงอนุโลมให้ตั้งเวลายินยอมให้อัตโนมัติ
        extra_fields.setdefault("pdpa_consent_at", timezone.now())
        # ไม่ถาม student_id: ถ้าอีเมลเป็นอีเมลนักศึกษาที่ถูกต้อง ดึงจากหน้า @
        # ไม่งั้น (superuser ใช้อีเมลอื่นได้) ให้รหัสสำรองหลังรู้ pk (กัน UNIQUE ชนกัน)
        if not extra_fields.get("student_id"):
            try:
                _, extra_fields["student_id"] = self.model.validate_student_email(
                    email, check_duplicate=False
                )
            except ValidationError:
                pass
        user = self._create_user(email, password, **extra_fields)
        if not user.student_id:
            user.student_id = f"a{user.pk:09d}"  # 10 ตัวอักษร ไม่ชนกับรหัสจริง
            user.save(update_fields=["student_id"])
        return user


class DepartmentCodeField(models.ForeignKey):
    """FK ไป Department (เก็บเป็น pk ตัวเลขเหมือนเดิม) แต่รับตัวย่อภาคตอนกรอกได้

    createsuperuser ส่งสิ่งที่พิมพ์มาผ่าน field.clean() -> to_python()
    จึงแปลงตัวย่อ ("cn" / "CN") เป็น pk ที่นี่ ถ้าไม่พบก็แจ้งว่าไม่มีภาควิชานี้
    """

    def to_python(self, value):
        if isinstance(value, str):
            value = value.strip()
            if not value.isdigit():
                pk = (
                    self.remote_field.model._default_manager.filter(
                        code=value.upper(), is_active=True
                    )
                    .values_list("pk", flat=True)
                    .first()
                )
                if pk is None:
                    raise ValidationError(
                        "ไม่พบภาควิชานี้ในระบบ (admin ต้องสร้างภาควิชาก่อน)"
                    )
                return pk
        return super().to_python(value)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User (ตาราง app_user ใน ERD)

    - password_hash ใน ERD = field `password` ของ AbstractBaseUser (เก็บเป็น hash อยู่แล้ว)
    - ปีเข้า/คณะ ไม่เก็บ ดึงจาก student_id ตอนใช้ (3NF)
    - email / personal_email เก็บเป็นตัวพิมพ์เล็กเสมอ กัน Alice@x กับ alice@x
      กลายเป็นคนละบัญชี
    - __str__ คืนเฉพาะ nickname (PDPA: ห้ามโผล่ student_id/อีเมลในหน้าที่คนอื่นเห็น)
    """

    # ไม่ต้องกรอก: clean()/create_user() ดึงจากหน้า @ ของ email ให้เอง
    # (superuser ที่สร้างผ่าน CLI ยังกรอกเองได้)
    student_id = models.CharField(
        "Student ID",
        max_length=10,
        unique=True,
        blank=True,
        editable=False,
        validators=[student_id_validator],
    )
    email = models.EmailField("Student email", max_length=255, unique=True)
    personal_email = models.EmailField(
        "Personal email (alumni)", max_length=255, unique=True, null=True, blank=True
    )
    nickname = models.CharField(
        "Nickname (shown instead of email)",
        max_length=50,
        validators=[validate_nickname],
    )
    # เก็บเป็น pk ตัวเลข แต่ createsuperuser กรอกเป็นตัวย่อภาคได้ (CN, CHE)
    department = DepartmentCodeField(
        "catalog.Department",
        verbose_name="Department code, e.g. CN, CHE",
        on_delete=models.PROTECT,
        related_name="users",
    )
    email_verified_at = models.DateTimeField(null=True, blank=True)
    pdpa_consent_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # สำหรับเข้า Django admin
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nickname", "department"]  # student_id ระบบใส่ให้เอง

    class Meta:
        db_table = "app_user"

    @property
    def entry_year(self):
        """ปีเข้า = 2 หลักแรกของรหัสนักศึกษา (คำนวณ ไม่เก็บ)"""
        return int(self.student_id[:2])

    @property
    def is_email_verified(self):
        return self.email_verified_at is not None

    def _normalize(self):
        if self.student_id:
            self.student_id = self.student_id.strip()
        if self.email:
            self.email = self.email.strip().lower()
        # "" ต้องเก็บเป็น NULL ไม่งั้น UNIQUE ของ personal_email จะชนกันเอง
        # ระหว่างคนที่ไม่กรอก
        self.personal_email = (self.personal_email or "").strip().lower() or None
        if self.nickname:
            self.nickname = self.nickname.strip()

    @classmethod
    def validate_student_email(cls, email, *, check_duplicate=True):
        """กฎทั้งหมดของ student email อยู่ที่นี่ที่เดียว คืน (email, student_id)

        ลำดับ: เมลซ้ำ → โดเมน → หน้า @ เป็นรหัสนักศึกษา 10 หลัก → หลักที่ 3-4 = 10
        """
        email = (email or "").strip().lower()

        # 1) เมลซ้ำไหม
        if check_duplicate and cls.objects.filter(email=email).exists():
            raise ValidationError("อีเมลนี้ถูกใช้สมัครแล้ว")

        # 2) โดเมนต้องเป็น @student.tu.ac.th
        local, _, domain = email.partition("@")
        if domain != STUDENT_EMAIL_DOMAIN:
            raise ValidationError(f"ต้องใช้อีเมลนักศึกษา @{STUDENT_EMAIL_DOMAIN} เท่านั้น")

        # 3) หน้า @ ต้องเป็นรหัสนักศึกษา 10 หลัก (ใช้ [0-9] กันเลขไทย/ยูนิโค้ด)
        if not re.fullmatch(r"[0-9]{10}", local):
            raise ValidationError(
                "ส่วนหน้า @ ต้องเป็นรหัสนักศึกษา 10 หลัก (ตัวเลขอารบิกเท่านั้น)"
            )

        # 4) หลักที่ 3-4 ต้องเป็น 10 (คณะวิศวะ)
        if local[2:4] != "10":
            raise ValidationError("คุณไม่ได้อยู่คณะวิศวกรรมศาสตร์ จึงสมัครไม่ได้")

        # 5) ผ่านแล้ว ส่งรหัสนักศึกษากลับไปบันทึกลง DB
        if check_duplicate and cls.objects.filter(student_id=local).exists():
            raise ValidationError("รหัสนักศึกษานี้ถูกใช้สมัครแล้ว")
        return email, local

    def clean(self):
        super().clean()
        # normalize ก่อน validate_unique() ซึ่ง Django เรียกหลัง clean()
        self._normalize()
        if self.is_superuser or not self.email:
            return
        # เช็กซ้ำที่ validate_unique() อยู่แล้ว จึงไม่เช็กซ้ำตรงนี้
        try:
            _, self.student_id = self.validate_student_email(
                self.email, check_duplicate=False
            )
        except ValidationError as exc:
            raise ValidationError({"email": exc.messages})

    def save(self, *args, **kwargs):
        self._normalize()
        super().save(*args, **kwargs)

    @transaction.atomic
    def anonymize(self):
        """ลบข้อมูลส่วนบุคคลตามสิทธิ์ PDPA โดยไม่ลบแถว

        เก็บแถวไว้เพราะ FK เป็น PROTECT จึงลบจริงไม่ได้เมื่อผู้ใช้มีเอกสารผูกอยู่
        """
        if self.pk is None:
            raise ValueError("Save the user before anonymizing")
        self.email = f"deleted-{self.pk}@deleted.invalid"
        self.student_id = f"x{self.pk:09d}"  # 10 ตัวอักษร ไม่ชนกับรหัสจริง
        self.personal_email = None
        self.nickname = "Deleted user"
        self.is_active = False
        self.set_unusable_password()
        self.save()

    def __str__(self):
        return self.nickname


class Role(models.Model):
    """student, alumni, moderator, super_admin

    Guest ไม่ใช่ผู้ใช้ จึงไม่มีแถว
    """

    STUDENT = "student"
    ALUMNI = "alumni"
    MODERATOR = "moderator"
    SUPER_ADMIN = "super_admin"

    id = models.SmallAutoField(primary_key=True)
    code = models.CharField(max_length=30, unique=True)
    name_th = models.CharField(max_length=50)

    class Meta:
        db_table = "role"

    def __str__(self):
        return self.code


class UserRoleManager(models.Manager):
    def get_queryset(self):
        # กัน N+1 ตอนเรียก __str__ / admin
        return super().get_queryset().select_related("role", "department")


class UserRole(models.Model):
    """M:N ผู้ใช้ - role

    department ใช้เฉพาะ moderator (ภาคที่ดูแล) role อื่นเป็น NULL
    """

    user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="user_roles"
    )
    role = models.ForeignKey(
        Role, on_delete=models.PROTECT, related_name="user_roles"
    )
    department = models.ForeignKey(
        "catalog.Department",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="user_roles",
    )
    granted_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="granted_roles",
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    objects = UserRoleManager()

    class Meta:
        db_table = "user_role"
        indexes = [
            models.Index(fields=["role", "department"], name="idx_userrole_role_dept"),
        ]
        constraints = [
            # SQL ถือว่า NULL != NULL จึงต้องแยก UQ เป็น 2 เงื่อนไข
            # ไม่งั้น (user, student, NULL) ซ้ำกันได้
            # หมายเหตุ: partial UQ ใช้ได้บน PostgreSQL/SQLite เท่านั้น
            # MySQL จะข้าม constraint นี้ (models.W036) จึงเช็กซ้ำใน clean() ด้านล่างด้วย
            models.UniqueConstraint(
                fields=["user", "role", "department"],
                condition=models.Q(department__isnull=False),
                name="uq_userrole_with_dept",
            ),
            models.UniqueConstraint(
                fields=["user", "role"],
                condition=models.Q(department__isnull=True),
                name="uq_userrole_without_dept",
            ),
        ]

    def clean(self):
        super().clean()
        if self.role_id is None:
            return
        is_moderator = self.role.code == Role.MODERATOR
        if is_moderator and self.department_id is None:
            raise ValidationError(
                {"department": "A moderator must have a department to manage"}
            )
        if not is_moderator and self.department_id is not None:
            raise ValidationError(
                {"department": "Only the moderator role can have a department"}
            )
        if self.user_id is not None:
            duplicated = (
                UserRole.objects.filter(
                    user_id=self.user_id,
                    role_id=self.role_id,
                    department_id=self.department_id,  # ถ้าเป็น None จะกลายเป็น IS NULL
                )
                .exclude(pk=self.pk)
                .exists()
            )
            if duplicated:
                raise ValidationError(
                    "This user already has this role (for this department)"
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        scope = f" @{self.department.code}" if self.department_id else ""
        return f"{self.user_id}:{self.role.code}{scope}"