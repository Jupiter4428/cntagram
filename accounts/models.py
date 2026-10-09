# Create your models here.
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

# ตัวที่ 1-2 = ปีเข้า, ตัวที่ 3-4 = คณะ (ต้องเป็น 10), รวม 10 หลัก
student_id_validator = RegexValidator(
    regex=r"^\d{2}10\d{6}$",
    message="รหัสนักศึกษาต้องมี 10 หลัก และตัวที่ 3-4 ต้องเป็น 10",
)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("ต้องระบุอีเมล")
        # createsuperuser อาจส่ง department มาเป็น instance หรือเป็น pk ก็ได้
        dept = extra_fields.pop("department", None)
        if dept is not None:
            extra_fields["department" if hasattr(dept, "pk") else "department_id"] = dept
        extra_fields.setdefault("pdpa_consent_at", timezone.now())
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("email_verified_at", timezone.now())
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User (ตาราง app_user ใน ERD)
    - password_hash ใน ERD = field `password` ของ AbstractBaseUser (เก็บเป็น hash อยู่แล้ว)
    - ปีเข้า/คณะ ไม่เก็บ ดึงจาก student_id ตอนใช้ (3NF)
    """

    student_id = models.CharField(
        "รหัสนักศึกษา", max_length=10, unique=True, validators=[student_id_validator]
    )
    email = models.EmailField("อีเมลนักศึกษา", max_length=255, unique=True)
    personal_email = models.EmailField(
        "อีเมลส่วนตัว (Alumni)", max_length=255, unique=True, null=True, blank=True
    )
    nickname = models.CharField("ชื่อเล่น (แสดงแทนอีเมล)", max_length=50)
    department = models.ForeignKey(
        "catalog.Department", on_delete=models.PROTECT, related_name="users"
    )
    email_verified_at = models.DateTimeField(null=True, blank=True)
    pdpa_consent_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # สำหรับเข้า Django admin
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["student_id", "nickname", "department"]

    @property
    def entry_year(self):
        """ปีเข้า 2 หลักแรกของรหัสนักศึกษา (คำนวณ ไม่เก็บ)"""
        return int(self.student_id[:2])

    def __str__(self):
        return f"{self.nickname} ({self.student_id})"


class Role(models.Model):
    """student, alumni, moderator, super_admin (Guest ไม่ใช่ผู้ใช้ จึงไม่มีแถว)"""

    id = models.SmallAutoField(primary_key=True)
    code = models.CharField(max_length=30, unique=True)
    name_th = models.CharField(max_length=50)

    def __str__(self):
        return self.code


class UserRole(models.Model):
    """M:N ผู้ใช้ - role (department ใช้เฉพาะ moderator = ภาคที่ดูแล, role อื่น = NULL)"""

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

    class Meta:
        indexes = [
            models.Index(fields=["role", "department"], name="idx_userrole_role_dept"),
        ]
        constraints = [
            # SQL ถือว่า NULL != NULL จึงต้องแยก UQ เป็น 2 เงื่อนไข
            # ไม่งั้น (user, student, NULL) ซ้ำกันได้
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

    def __str__(self):
        scope = f" @{self.department.code}" if self.department_id else ""
        return f"{self.user_id}:{self.role.code}{scope}"