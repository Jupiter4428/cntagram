"""Unit tests for webboard views and request handling."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from catalog.models import Department
from webboard.models import BoardCategory, Post, Thread

User = get_user_model()


class WebboardViewsTests(TestCase):
    """Test HTTP views and permissions on the webboard."""

    @classmethod
    def setUpTestData(cls):
        """Prepare student user, staff user, category, and test thread."""
        dept, _ = Department.objects.get_or_create(
            code="CN",
            defaults={
                "name_th": "วิศวกรรมคอมพิวเตอร์",
                "name_en": "Computer Engineering",
            },
        )
        cls.student = User.objects.create_user(
            email="6610000006@student.tu.ac.th",
            password="test-password-123",
            nickname="ViewStudent",
            department=dept,
            pdpa_consent_at=timezone.now(),
        )
        cls.staff = User.objects.create_user(
            email="6610000007@student.tu.ac.th",
            password="test-password-123",
            nickname="ViewStaff",
            department=dept,
            is_staff=True,
            pdpa_consent_at=timezone.now(),
        )
        cls.category = BoardCategory.objects.create(
            name="ห้องวิชาการ",
            slug="academic",
            order=1,
        )
        cls.thread = Thread.objects.create(
            category=cls.category,
            author=cls.student,
            title="เทคนิคการอ่านสอบไฟนอล",
            content="แชร์วิธีการเตรียมสอบวิชา CN101 ครับ :)",
        )

    def setUp(self):
        """Log in student by default for authenticated actions."""
        self.client.force_login(self.student)

    def test_guest_redirected_to_login(self):
        """Unauthenticated guests are redirected to the login page."""
        guest = Client()
        response = guest.get(reverse("webboard:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_board_index_for_student(self):
        """Webboard index is accessible to authenticated student (status 200)."""
        response = self.client.get(reverse("webboard:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "เว็บบอร์ดเด็กวิศวะ CNTAGRAM")
        self.assertContains(response, "เทคนิคการอ่านสอบไฟนอล")

    def test_category_threads_view(self):
        """Category view filters by slug, returns 404 if invalid."""
        response = self.client.get(
            reverse("webboard:category_threads", kwargs={"slug": "academic"})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ห้องวิชาการ")

        res_404 = self.client.get(
            reverse("webboard:category_threads", kwargs={"slug": "not-found"})
        )
        self.assertEqual(res_404.status_code, 404)

    def test_thread_detail_view_and_view_counter(self):
        """Thread detail displays content and increments views count."""
        initial_views = self.thread.views_count
        response = self.client.get(
            reverse("webboard:thread_detail", kwargs={"pk": self.thread.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "เทคนิคการอ่านสอบไฟนอล")
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.views_count, initial_views + 1)

    def test_thread_create_requires_login(self):
        """Unauthenticated user is redirected to login page."""
        anon = Client()
        response = anon.get(reverse("webboard:thread_create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_thread_create_post_success(self):
        """Authenticated student can compose and post a thread."""
        self.client.force_login(self.student)
        response = self.client.post(
            reverse("webboard:thread_create"),
            data={
                "category": self.category.id,
                "title": "กระทู้สร้างจากวิว",
                "content": "เนื้อหาผ่านฟอร์ม [img]https://example.com/a.gif[/img]",
            },
        )
        self.assertEqual(response.status_code, 302)
        created = Thread.objects.filter(title="กระทู้สร้างจากวิว").first()
        self.assertIsNotNone(created)
        self.assertEqual(created.author, self.student)

    def test_thread_reply_post(self):
        """Authenticated user can submit reply comment to thread."""
        self.client.force_login(self.student)
        response = self.client.post(
            reverse("webboard:thread_reply", kwargs={"pk": self.thread.pk}),
            data={"content": "ขอบคุณสำหรับคำแนะนำครับ :D"},
        )
        self.assertEqual(response.status_code, 302)
        post = Post.objects.filter(thread=self.thread).first()
        self.assertIsNotNone(post)
        self.assertEqual(post.content, "ขอบคุณสำหรับคำแนะนำครับ :D")

    def test_staff_pin_and_lock_toggle(self):
        """Staff can toggle pin and lock; non-staff receives error."""
        self.client.force_login(self.staff)

        res_pin = self.client.post(
            reverse("webboard:thread_pin_toggle", kwargs={"pk": self.thread.pk})
        )
        self.assertEqual(res_pin.status_code, 302)
        self.thread.refresh_from_db()
        self.assertTrue(self.thread.is_pinned)

        res_lock = self.client.post(
            reverse("webboard:thread_lock_toggle", kwargs={"pk": self.thread.pk})
        )
        self.assertEqual(res_lock.status_code, 302)
        self.thread.refresh_from_db()
        self.assertTrue(self.thread.is_locked)

    def test_thread_delete_by_author(self):
        """Author can delete their thread, redirecting to index."""
        self.client.force_login(self.student)
        response = self.client.post(
            reverse("webboard:thread_delete", kwargs={"pk": self.thread.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Thread.objects.filter(pk=self.thread.pk).exists())

    def test_thread_create_get_with_category_param(self):
        """Visiting thread create with category query pre-selects category."""
        self.client.force_login(self.student)
        response = self.client.get(
            f"{reverse('webboard:thread_create')}?category=academic"
        )
        self.assertEqual(response.status_code, 200)

    def test_thread_create_invalid_form(self):
        """Submitting invalid thread form redisplays page with errors."""
        self.client.force_login(self.student)
        response = self.client.post(
            reverse("webboard:thread_create"),
            data={"title": "", "content": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "title", "กรุณาระบุหัวข้อกระทู้")

    def test_thread_reply_invalid_form_and_locked(self):
        """Replying with empty content or on locked thread shows message."""
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("webboard:thread_reply", kwargs={"pk": self.thread.pk}),
            data={"content": ""},
        )
        self.assertEqual(response.status_code, 302)

        self.thread.is_locked = True
        self.thread.save(update_fields=["is_locked"])
        res_locked = self.client.post(
            reverse("webboard:thread_reply", kwargs={"pk": self.thread.pk}),
            data={"content": "ตอบในกระทู้ล็อก"},
        )
        self.assertEqual(res_locked.status_code, 302)

    def test_views_404_and_permission_denied_branches(self):
        """Views handle 404 on missing threads and permission checks."""
        self.client.force_login(self.student)

        self.assertEqual(
            self.client.get(
                reverse("webboard:thread_detail", kwargs={"pk": 99999})
            ).status_code,
            404,
        )

        self.assertEqual(
            self.client.post(
                reverse("webboard:thread_reply", kwargs={"pk": 99999}),
                data={"content": "ข้อความ"},
            ).status_code,
            404,
        )

        self.assertEqual(
            self.client.post(
                reverse("webboard:thread_pin_toggle", kwargs={"pk": 99999})
            ).status_code,
            404,
        )
        res_pin_denied = self.client.post(
            reverse("webboard:thread_pin_toggle", kwargs={"pk": self.thread.pk})
        )
        self.assertEqual(res_pin_denied.status_code, 302)

        self.assertEqual(
            self.client.post(
                reverse("webboard:thread_lock_toggle", kwargs={"pk": 99999})
            ).status_code,
            404,
        )
        res_lock_denied = self.client.post(
            reverse("webboard:thread_lock_toggle", kwargs={"pk": self.thread.pk})
        )
        self.assertEqual(res_lock_denied.status_code, 302)

        other = User.objects.create_user(
            email="6610000099@student.tu.ac.th",
            password="test-password-123",
            nickname="Stranger",
            department=self.student.department,
            pdpa_consent_at=timezone.now(),
        )
        self.client.force_login(other)
        res_del_denied = self.client.post(
            reverse("webboard:thread_delete", kwargs={"pk": self.thread.pk})
        )
        self.assertEqual(res_del_denied.status_code, 302)
        self.assertEqual(
            self.client.post(
                reverse("webboard:thread_delete", kwargs={"pk": 99999})
            ).status_code,
            404,
        )
