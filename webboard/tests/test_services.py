"""Unit tests for webboard business logic services."""

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone
from catalog.models import Department
from webboard import services
from webboard.models import BoardCategory, Post, Thread

User = get_user_model()


class WebboardServicesTests(TestCase):
    """Test webboard services mutations, validations, and permission checks."""

    @classmethod
    def setUpTestData(cls):
        """Prepare author, student, staff, and category."""
        dept, _ = Department.objects.get_or_create(
            code="CN",
            defaults={
                "name_th": "วิศวกรรมคอมพิวเตอร์",
                "name_en": "Computer Engineering",
            },
        )
        cls.author = User.objects.create_user(
            email="6610000003@student.tu.ac.th",
            password="test-password-123",
            nickname="AuthorUser",
            department=dept,
            pdpa_consent_at=timezone.now(),
        )
        cls.other_user = User.objects.create_user(
            email="6610000004@student.tu.ac.th",
            password="test-password-123",
            nickname="OtherUser",
            department=dept,
            pdpa_consent_at=timezone.now(),
        )
        cls.staff_user = User.objects.create_user(
            email="6610000005@student.tu.ac.th",
            password="test-password-123",
            nickname="StaffUser",
            department=dept,
            is_staff=True,
            pdpa_consent_at=timezone.now(),
        )
        cls.category = BoardCategory.objects.create(
            name="ห้องสนทนาทั่วไป",
            slug="general-talk",
        )

    def test_create_thread_success_and_validation(self):
        """Creating thread validates non-empty title and content."""
        thread = services.create_thread(
            author=self.author,
            category=self.category,
            title="ยินดีต้อนรับสู่เว็บบอร์ด",
            content="ขอเชิญทุกคนมาคุยกัน :)",
        )
        self.assertEqual(thread.title, "ยินดีต้อนรับสู่เว็บบอร์ด")
        self.assertEqual(thread.content, "ขอเชิญทุกคนมาคุยกัน :)")

        with self.assertRaises(ValidationError):
            services.create_thread(
                author=self.author,
                category=self.category,
                title="   ",
                content="เนื้อหา",
            )

        with self.assertRaises(ValidationError):
            services.create_thread(
                author=self.author,
                category=self.category,
                title="หัวข้อ",
                content="   ",
            )

    def test_create_post_success_and_locked_thread_rejection(self):
        """Replying to thread succeeds when unlocked, rejects when locked."""
        thread = services.create_thread(
            author=self.author,
            category=self.category,
            title="กระทู้ถามคำถาม",
            content="วิชานี้ยากไหมครับ",
        )
        post = services.create_post(
            thread=thread,
            author=self.other_user,
            content="ไม่ยากเลยถ้าตั้งใจอ่านชีท!",
        )
        self.assertEqual(post.content, "ไม่ยากเลยถ้าตั้งใจอ่านชีท!")

        thread.is_locked = True
        thread.save(update_fields=["is_locked"])

        with self.assertRaises(ValidationError) as ctx:
            services.create_post(
                thread=thread,
                author=self.other_user,
                content="ตอบไม่ได้แล้ว",
            )
        self.assertIn("ถูกล็อกแล้ว", str(ctx.exception))

    def test_increment_thread_views(self):
        """Thread views counter increments atomically."""
        thread = services.create_thread(
            author=self.author,
            category=self.category,
            title="ทดสอบยอดวิว",
            content="รายละเอียด",
        )
        self.assertEqual(thread.views_count, 0)
        services.increment_thread_views(thread_id=thread.id)
        thread.refresh_from_db()
        self.assertEqual(thread.views_count, 1)

    def test_toggle_pin_and_lock_permissions(self):
        """Only staff can toggle pin or lock status."""
        thread = services.create_thread(
            author=self.author,
            category=self.category,
            title="ทดสอบสิทธิ์",
            content="เนื้อหา",
        )

        with self.assertRaises(PermissionDenied):
            services.toggle_thread_pin(thread=thread, actor=self.author)

        with self.assertRaises(PermissionDenied):
            services.toggle_thread_lock(thread=thread, actor=self.author)

        new_pin = services.toggle_thread_pin(thread=thread, actor=self.staff_user)
        self.assertTrue(new_pin)

        new_lock = services.toggle_thread_lock(thread=thread, actor=self.staff_user)
        self.assertTrue(new_lock)

    def test_delete_thread_permissions(self):
        """Author and staff can delete, stranger cannot."""
        thread = services.create_thread(
            author=self.author,
            category=self.category,
            title="กระทู้จะถูกลบ",
            content="เนื้อหา",
        )

        with self.assertRaises(PermissionDenied):
            services.delete_thread(thread=thread, actor=self.other_user)

        services.delete_thread(thread=thread, actor=self.author)
        self.assertFalse(Thread.objects.filter(pk=thread.pk).exists())

    def test_delete_post_permissions(self):
        """Author and staff can delete post, stranger cannot."""
        thread = services.create_thread(
            author=self.author,
            category=self.category,
            title="กระทู้สำหรับโพสต์",
            content="เนื้อหา",
        )
        post = services.create_post(
            thread=thread,
            author=self.author,
            content="คอมเมนต์จะถูกลบ",
        )

        with self.assertRaises(PermissionDenied):
            services.delete_post(post=post, actor=self.other_user)

        services.delete_post(post=post, actor=self.author)
        self.assertFalse(Post.objects.filter(pk=post.pk).exists())
