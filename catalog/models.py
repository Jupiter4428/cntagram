# Create your models here.
from django.db import models


class Department(models.Model):
    """ภาควิชา เช่น CN, CE, ME, EE"""

    code = models.CharField("รหัสภาค", max_length=5, unique=True)
    name_th = models.CharField("ชื่อภาษาไทย", max_length=100)
    name_en = models.CharField("ชื่อภาษาอังกฤษ", max_length=100)
    is_active = models.BooleanField("เปิดใช้งาน", default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name_th}"


class Batch(models.Model):
    """รุ่นของภาควิชา (1 ภาค : N รุ่น)
    รหัสรุ่น เช่น CN21 ไม่เก็บใน DB ประกอบจาก department.code + number (3NF)
    """

    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name="batches"
    )
    number = models.PositiveSmallIntegerField("เลขรุ่น")  # 21, 22, ...

    class Meta:
        ordering = ["department__code", "number"]
        verbose_name_plural = "batches"
        constraints = [
            models.UniqueConstraint(
                fields=["department", "number"], name="uq_batch_department_number"
            ),
        ]

    @property
    def code(self):
        return f"{self.department.code}{self.number}"

    def __str__(self):
        return self.code


class Course(models.Model):
    """ข้อมูลวิชา (ไม่ผูกกับรุ่น) เช่น CN101, SC135"""

    code = models.CharField("รหัสวิชา", max_length=10, unique=True)
    name_th = models.CharField("ชื่อภาษาไทย", max_length=150, null=True, blank=True)
    name_en = models.CharField("ชื่อภาษาอังกฤษ", max_length=150)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} {self.name_en}"


class BatchCourse(models.Model):
    """วิชาที่เปิดในรุ่น (ตารางเชื่อม M:N ระหว่าง Batch กับ Course)"""

    batch = models.ForeignKey(
        Batch, on_delete=models.PROTECT, related_name="batch_courses"
    )
    course = models.ForeignKey(
        Course, on_delete=models.PROTECT, related_name="batch_courses"
    )

    class Meta:
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

    key = models.CharField(max_length=50, primary_key=True)
    value = models.CharField(max_length=100)

    @classmethod
    def get_int(cls, key, default=None):
        """อ่านค่าเป็นตัวเลข เช่น SystemSetting.get_int("legacy_batch_max", 23)"""
        try:
            return int(cls.objects.get(pk=key).value)
        except (cls.DoesNotExist, ValueError):
            return default

    def __str__(self):
        return f"{self.key} = {self.value}"