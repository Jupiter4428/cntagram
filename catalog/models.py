#..\catalog\models.py
# Create your models here.
from django.db import models


class Department(models.Model):
    """ภาควิชา เช่น CN, CE, ME, EE"""

    code = models.CharField("Department code", max_length=5, unique=True)
    name_th = models.CharField("Thai name", max_length=100)
    name_en = models.CharField("English name", max_length=100)
    is_active = models.BooleanField("Active", default=True)

    class Meta:
        db_table = "department"
        ordering = ["code"]

    def _normalize(self):
        # เก็บเป็นตัวพิมพ์ใหญ่เสมอ กัน "cn" กับ "CN" กลายเป็นคนละภาค
        if self.code:
            self.code = self.code.strip().upper()

    def clean(self):
        super().clean()
        self._normalize()  # ต้องทำก่อน validate_unique()

    def save(self, *args, **kwargs):
        self._normalize()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name_th}"


class BatchManager(models.Manager):
    def get_queryset(self):
        # Batch.code / __str__ ต้องใช้ department.code จึง join มาให้เลย กัน N+1
        return super().get_queryset().select_related("department")


class Batch(models.Model):
    """รุ่นของภาควิชา (1 ภาค : N รุ่น)

    รหัสรุ่น เช่น CN21 ไม่เก็บใน DB ประกอบจาก department.code + number (3NF)
    """

    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name="batches"
    )
    number = models.PositiveSmallIntegerField("Batch number")  # 21, 22, ...

    objects = BatchManager()

    class Meta:
        db_table = "batch"
        ordering = ["department__code", "number"]
        verbose_name_plural = "batches"
        constraints = [
            models.UniqueConstraint(
                fields=["department", "number"], name="uq_batch_department_number"
            ),
            models.CheckConstraint(
                condition=models.Q(number__gte=1),
                name="ck_batch_number_positive",
            ),
        ]

    @property
    def code(self):
        return f"{self.department.code}{self.number}"

    def __str__(self):
        return self.code


class Course(models.Model):
    """ข้อมูลวิชา (ไม่ผูกกับรุ่น) เช่น CN101, SC135"""

    code = models.CharField("Course code", max_length=10, unique=True)
    name_th = models.CharField("Thai name", max_length=150, null=True, blank=True)
    name_en = models.CharField("English name", max_length=150)

    class Meta:
        db_table = "course"
        ordering = ["code"]

    def _normalize(self):
        if self.code:
            self.code = self.code.strip().upper()
        # ชื่อไทยที่ว่างต้องเป็น NULL ไม่ใช่ ""
        self.name_th = (self.name_th or "").strip() or None

    def clean(self):
        super().clean()
        self._normalize()

    def save(self, *args, **kwargs):
        self._normalize()
        super().save(*args, **kwargs)

    @property
    def display_name(self):
        """ชื่อที่ใช้แสดง: ไทยก่อน ถ้าไม่มีใช้อังกฤษ"""
        return self.name_th or self.name_en

    def __str__(self):
        return f"{self.code} {self.name_en}"


class BatchCourseManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("batch__department", "course")


class BatchCourse(models.Model):
    """วิชาที่เปิดในรุ่น (ตารางเชื่อม M:N ระหว่าง Batch กับ Course)"""

    batch = models.ForeignKey(
        Batch, on_delete=models.PROTECT, related_name="batch_courses"
    )
    course = models.ForeignKey(
        Course, on_delete=models.PROTECT, related_name="batch_courses"
    )

    objects = BatchCourseManager()

    class Meta:
        db_table = "batch_course"
        constraints = [
            models.UniqueConstraint(
                fields=["batch", "course"], name="uq_batchcourse_batch_course"
            ),
        ]

    def __str__(self):
        return f"{self.batch} / {self.course.code}"


class SystemSetting(models.Model):
    """ค่ากำหนดที่ปรับได้โดยไม่ต้อง deploy ใหม่

    เช่น legacy_batch_max = 23, max_upload_mb = 50
    """

    LEGACY_BATCH_MAX = "legacy_batch_max"
    MAX_UPLOAD_MB = "max_upload_mb"

    key = models.CharField(max_length=50, primary_key=True)
    value = models.CharField(max_length=100)

    class Meta:
        db_table = "system_setting"

    @classmethod
    def get_int(cls, key, default=None):
        """อ่านค่าเป็นตัวเลข เช่น SystemSetting.get_int("legacy_batch_max", 23)"""
        try:
            return int(cls.objects.get(pk=key).value)
        except (cls.DoesNotExist, ValueError, TypeError):
            return default

    def __str__(self):
        return f"{self.key} = {self.value}"