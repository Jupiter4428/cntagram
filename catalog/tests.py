from django.test import TestCase

# Create your tests here.
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, UserRole
from catalog.models import Batch, BatchCourse, Course, Department

User = get_user_model()


class CatalogTestCase(TestCase):
    """setUp ร่วม: ภาค CN, นักศึกษาทั่วไป และ Super Admin"""

    def setUp(self):
        self.client = Client()
        self.now = timezone.now()

        # สร้าง Role พื้นฐานโดยใช้ Role constants
        self.role_student, _ = Role.objects.get_or_create(code=Role.STUDENT, defaults={"name_th": "นักศึกษา"})
        self.role_super_admin, _ = Role.objects.get_or_create(code=Role.SUPER_ADMIN, defaults={"name_th": "ผู้ดูแลระบบ"})

        # สร้างภาควิชาตั้งต้น
        self.dept_cn = Department.objects.create(
            code="CN",
            name_th="วิศวกรรมคอมพิวเตอร์",
            name_en="Computer Engineering",
        )

        # นักศึกษาทั่วไป
        self.student = User.objects.create_user(
            email="6810610001@student.tu.ac.th",
            password="password123",
            nickname="student_test",
            department=self.dept_cn,
            pdpa_consent_at=self.now,
        )
        UserRole.objects.create(user=self.student, role=self.role_student)

        # Super Admin
        self.admin = User.objects.create_user(
            email="6810610002@student.tu.ac.th",
            password="password123",
            nickname="admin_test",
            department=self.dept_cn,
            is_superuser=True,
            pdpa_consent_at=self.now,
        )
        UserRole.objects.create(user=self.admin, role=self.role_super_admin)


class DepartmentTests(CatalogTestCase):
    def test_anonymous_user_redirect_to_login(self):
        """ผู้ใช้ที่ไม่ได้ล็อกอิน เข้าหน้านี้ต้อง redirect ไปยังหน้า login"""
        response = self.client.get(reverse("catalog:department_list"))
        login_url = reverse("accounts:login")
        expected_url = f"{login_url}?next={reverse('catalog:department_list')}"
        self.assertRedirects(response, expected_url)

    def test_permission_denied_for_non_super_admin(self):
        """User ทั่วไปที่ล็อกอินแล้ว เข้าหน้านี้ต้องได้ 403 Forbidden"""
        self.client.force_login(self.student)
        response = self.client.get(reverse("catalog:department_list"))
        self.assertEqual(response.status_code, 403)

    def test_duplicate_department_code(self):
        """เพิ่มรหัสภาควิชาซ้ำไม่ได้ โดย normalize เป็นตัวพิมพ์ใหญ่แล้วแจ้งเตือน"""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("catalog:department_create"),
            {
                "code": "cn",
                "name_th": "คอมพิวเตอร์ 2",
                "name_en": "Computer 2",
                "is_active": True,
            },
        )
        self.assertEqual(Department.objects.filter(code="CN").count(), 1)
        self.assertFormError(response.context["form"], "code", "รหัสภาควิชานี้มีอยู่ในระบบแล้ว")

    def test_update_department_keep_same_code(self):
        """แก้ไขภาคโดยใช้ code เดิมต้องผ่านและ redirect ได้ปกติ"""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("catalog:department_update", args=[self.dept_cn.pk]),
            {
                "code": "CN",
                "name_th": "วิศวกรรมคอมพิวเตอร์ (แก้ไข)",
                "name_en": "Computer Engineering",
                "is_active": True,
            },
        )
        self.assertRedirects(response, reverse("catalog:department_list"))
        self.dept_cn.refresh_from_db()
        self.assertEqual(self.dept_cn.name_th, "วิศวกรรมคอมพิวเตอร์ (แก้ไข)")

    def test_cannot_delete_department_with_batches(self):
        """ลบภาควิชาที่มีรุ่นผูกอยู่ไม่ได้ พร้อมแจ้งเตือนว่ายังมีรุ่น/วิชาอยู่ในภาค"""
        self.client.force_login(self.admin)
        Batch.objects.create(department=self.dept_cn, number=21)

        response = self.client.post(
            reverse("catalog:department_delete", args=[self.dept_cn.pk]),
            follow=True,
        )
        self.assertTrue(Department.objects.filter(code="CN").exists())
        self.assertContains(response, "ลบไม่ได้ เพราะยังมีรุ่น/วิชาอยู่ในภาคนี้")

    def test_cannot_delete_department_with_users(self):
        """ลบภาควิชาที่มี user ผูกอยู่ (แต่ไม่มีรุ่น) ไม่ได้ พร้อมแจ้งเตือนว่ายังมีผู้ใช้สังกัดอยู่"""
        dept_ce = Department.objects.create(code="CE", name_th="วิศวกรรมโยธา", name_en="Civil Engineering")
        User.objects.create_user(
            email="6810610003@student.tu.ac.th",
            password="password123",
            nickname="ce_user",
            department=dept_ce,
            pdpa_consent_at=self.now,
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("catalog:department_delete", args=[dept_ce.pk]),
            follow=True,
        )
        self.assertTrue(Department.objects.filter(code="CE").exists())
        self.assertContains(response, "ลบไม่ได้ เพราะยังมีผู้ใช้สังกัดภาคนี้อยู่")

    def test_seed_commands_idempotent(self):
        """คำสั่ง seed_roles และ seed_catalog ต้องรันซ้ำได้โดยไม่สร้างข้อมูลซ้ำซ้อน"""
        call_command("seed_roles")
        call_command("seed_roles")
        call_command("seed_catalog")
        call_command("seed_catalog")

        self.assertEqual(Role.objects.count(), 4)
        self.assertEqual(Department.objects.count(), 4)
        # รุ่นตัวอย่าง CN21-CN25 ใช้วิชาชุดเดียวกัน 4 วิชา (ไม่สร้างวิชาซ้ำต่อรุ่น)
        self.assertEqual(
            [b.code for b in Batch.objects.all()], ["CN21", "CN22", "CN23", "CN24", "CN25"]
        )
        self.assertEqual(Course.objects.count(), 4)
        self.assertEqual(BatchCourse.objects.count(), 5 * 4)


class BatchTests(CatalogTestCase):
    def test_create_batch_builds_code_from_department(self):
        """เลือกภาค CN แล้วใส่เลข 21 → ได้รุ่น CN21 แสดงในหน้ารายการรุ่น"""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("catalog:batch_create"),
            {"department": self.dept_cn.pk, "number": 21},
            follow=True,
        )
        self.assertRedirects(response, reverse("catalog:batch_list"))
        self.assertContains(response, "CN21")
        self.assertTrue(Batch.objects.filter(department=self.dept_cn, number=21).exists())

    def test_duplicate_batch_rejected(self):
        """ใส่เลข 21 ซ้ำในภาคเดิม → แจ้งว่ารุ่นนี้มีแล้ว และไม่สร้างซ้ำ"""
        Batch.objects.create(department=self.dept_cn, number=21)
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("catalog:batch_create"),
            {"department": self.dept_cn.pk, "number": 21},
        )
        self.assertEqual(Batch.objects.filter(department=self.dept_cn, number=21).count(), 1)
        self.assertFormError(response.context["form"], None, "รุ่นนี้มีอยู่แล้ว")
        self.assertContains(response, "รุ่นนี้มีอยู่แล้ว")

    def test_batch_list_groups_batches_under_their_department(self):
        """หน้ารายการรุ่นแยกตามภาควิชา: รุ่นของแต่ละภาคอยู่ใต้ชื่อภาคนั้น"""
        dept_ee = Department.objects.create(code="EE", name_th="วิศวกรรมไฟฟ้า", name_en="Electrical Engineering")
        Batch.objects.create(department=dept_ee, number=24)
        Batch.objects.create(department=self.dept_cn, number=21)
        self.client.force_login(self.admin)

        response = self.client.get(reverse("catalog:batch_list"))

        html = response.content.decode()
        positions = [html.index(text) for text in ["วิศวกรรมคอมพิวเตอร์", "CN21", "วิศวกรรมไฟฟ้า", "EE24"]]
        self.assertEqual(positions, sorted(positions))

    def test_delete_empty_batch(self):
        """ลบรุ่นที่ยังไม่มีวิชาได้"""
        batch = Batch.objects.create(department=self.dept_cn, number=21)
        self.client.force_login(self.admin)
        response = self.client.post(reverse("catalog:batch_delete", args=[batch.pk]), follow=True)
        self.assertRedirects(response, reverse("catalog:batch_list"))
        self.assertFalse(Batch.objects.filter(pk=batch.pk).exists())

    def test_cannot_delete_batch_with_courses(self):
        """ลบ CN21 ที่ยังมีวิชาอยู่ไม่ได้ พร้อมแจ้งเหตุผล"""
        batch = Batch.objects.create(department=self.dept_cn, number=21)
        course = Course.objects.create(code="CN200", name_en="Discrete Mathematics")
        BatchCourse.objects.create(batch=batch, course=course)
        self.client.force_login(self.admin)
        response = self.client.post(reverse("catalog:batch_delete", args=[batch.pk]), follow=True)
        self.assertTrue(Batch.objects.filter(pk=batch.pk).exists())
        self.assertContains(response, "ลบรุ่น CN21 ไม่ได้ เพราะยังมีรายวิชาอยู่ในรุ่นนี้")


class CatalogPermissionTests(CatalogTestCase):
    def test_non_super_admin_gets_403_on_batch_and_course_pages(self):
        """นักศึกษาทั่วไปเข้าหน้าจัดการรุ่น/วิชาไม่ได้ (เช็กสิทธิ์ฝั่ง server)"""
        batch = Batch.objects.create(department=self.dept_cn, number=21)
        course = Course.objects.create(code="CN200", name_en="Discrete Mathematics")
        batch_course = BatchCourse.objects.create(batch=batch, course=course)
        self.client.force_login(self.student)

        for url in [
            reverse("catalog:batch_list"),
            reverse("catalog:batch_create"),
            reverse("catalog:batch_delete", args=[batch.pk]),
            reverse("catalog:batch_course_manage", args=[batch.pk]),
            reverse("catalog:batch_course_remove", args=[batch.pk, batch_course.pk]),
            reverse("catalog:course_list"),
            reverse("catalog:course_create"),
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url).status_code, 403)
        self.assertTrue(BatchCourse.objects.filter(pk=batch_course.pk).exists())


class CourseTests(CatalogTestCase):
    def test_create_course(self):
        """สร้างวิชาใหม่ด้วยรหัส ชื่อไทย ชื่ออังกฤษ แล้วแสดงในหน้ารายการวิชา"""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("catalog:course_create"),
            {"code": "cn200", "name_th": "คณิตศาสตร์ดิสครีต", "name_en": "Discrete Mathematics"},
            follow=True,
        )
        self.assertRedirects(response, reverse("catalog:course_list"))
        self.assertContains(response, "CN200")

    def test_duplicate_course_code_rejected(self):
        """รหัสวิชาซ้ำ (ต่างแค่ตัวพิมพ์) สร้างไม่ได้"""
        Course.objects.create(code="CN200", name_en="Discrete Mathematics")
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("catalog:course_create"),
            {"code": "cn200", "name_th": "", "name_en": "Discrete Math 2"},
        )
        self.assertEqual(Course.objects.filter(code="CN200").count(), 1)
        self.assertFormError(response.context["form"], "code", "รหัสวิชานี้มีอยู่ในระบบแล้ว")
        self.assertContains(response, "รหัสวิชานี้มีอยู่ในระบบแล้ว")

    def test_course_form_points_to_batch_pages_for_existing_courses(self):
        """ฟอร์มเพิ่มวิชาบอกว่าวิชาที่มีอยู่แล้วให้ไปผูกในหน้าจัดการรุ่น ไม่ต้องสร้างซ้ำ"""
        self.client.force_login(self.admin)

        response = self.client.get(reverse("catalog:course_create"))

        self.assertContains(response, "ผูกวิชาเดิมเข้ารุ่น")

    def test_course_list_shows_thai_and_english_names(self):
        """หน้ารายการวิชาแสดงทั้งชื่อไทยและชื่ออังกฤษ"""
        Course.objects.create(code="CN200", name_th="คณิตศาสตร์ดิสครีต", name_en="Discrete Mathematics")
        self.client.force_login(self.admin)

        response = self.client.get(reverse("catalog:course_list"))

        self.assertContains(response, "คณิตศาสตร์ดิสครีต")
        self.assertContains(response, "Discrete Mathematics")


class BatchCourseTests(CatalogTestCase):
    def setUp(self):
        super().setUp()
        self.cn21 = Batch.objects.create(department=self.dept_cn, number=21)
        self.cn22 = Batch.objects.create(department=self.dept_cn, number=22)
        self.cn200 = Course.objects.create(code="CN200", name_en="Discrete Mathematics")
        self.client.force_login(self.admin)

    def add(self, batch, course):
        return self.client.post(
            reverse("catalog:batch_course_manage", args=[batch.pk]),
            {"course": course.pk},
            follow=True,
        )

    def test_same_course_shared_by_many_batches(self):
        """เพิ่ม CN200 ให้ CN21 และ CN22 → ทั้งสองรุ่นชี้ไปที่วิชา CN200 ตัวเดียวกัน"""
        self.add(self.cn21, self.cn200)
        response = self.add(self.cn22, self.cn200)

        self.assertContains(response, "CN200")
        self.assertEqual(Course.objects.filter(code="CN200").count(), 1)
        self.assertEqual(
            set(BatchCourse.objects.values_list("batch_id", "course_id")),
            {(self.cn21.pk, self.cn200.pk), (self.cn22.pk, self.cn200.pk)},
        )

    def test_course_already_in_batch_rejected(self):
        """เพิ่มวิชาเดิมเข้ารุ่นเดิมซ้ำไม่ได้"""
        self.add(self.cn21, self.cn200)
        response = self.add(self.cn21, self.cn200)

        self.assertEqual(BatchCourse.objects.filter(batch=self.cn21).count(), 1)
        self.assertFormError(response.context["form"], "course", "วิชานี้อยู่ในรุ่นนี้แล้ว")
        self.assertContains(response, "วิชานี้อยู่ในรุ่นนี้แล้ว")

    def test_remove_course_from_batch_keeps_course(self):
        """ถอด CN200 ออกจาก CN21 → CN22 ยังมี CN200 และข้อมูลวิชายังอยู่"""
        self.add(self.cn21, self.cn200)
        self.add(self.cn22, self.cn200)
        batch_course = BatchCourse.objects.get(batch=self.cn21, course=self.cn200)

        response = self.client.post(
            reverse("catalog:batch_course_remove", args=[self.cn21.pk, batch_course.pk]),
            follow=True,
        )

        self.assertRedirects(response, reverse("catalog:batch_course_manage", args=[self.cn21.pk]))
        self.assertFalse(BatchCourse.objects.filter(batch=self.cn21).exists())
        self.assertTrue(BatchCourse.objects.filter(batch=self.cn22, course=self.cn200).exists())
        self.assertTrue(Course.objects.filter(pk=self.cn200.pk).exists())

    def test_list_pages_have_no_n_plus_one(self):
        """จำนวน query คงที่ไม่ว่าจะมีกี่รุ่น/กี่วิชา (session, user, เช็กสิทธิ์ + query ของหน้า)"""
        for i, number in enumerate([23, 24, 25]):
            batch = Batch.objects.create(department=self.dept_cn, number=number)
            course = Course.objects.create(code=f"CN10{i}", name_en=f"Course {i}")
            BatchCourse.objects.create(batch=self.cn21, course=course)
            BatchCourse.objects.create(batch=batch, course=course)

        with self.assertNumQueries(4):
            self.client.get(reverse("catalog:batch_list"))
        with self.assertNumQueries(6):  # + รุ่น, วิชาในรุ่น, ตัวเลือกวิชาในฟอร์ม
            self.client.get(reverse("catalog:batch_course_manage", args=[self.cn21.pk]))
