"""Unit tests for webboard business logic services."""

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone
from accounts.models import Role, UserRole
from catalog.models import Department
from webboard import services
from webboard.models import BoardCategory, Post, Thread

User = get_user_model()


class WebboardServicesTests(TestCase):
    """Test webboard services mutations, validations, and permission checks."""

    @classmethod
    def setUpTestData(cls):
        """Prepare authors, a moderator, and a category."""
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
        cls.moderator_user = User.objects.create_user(
            email="6610000005@student.tu.ac.th",
            password="test-password-123",
            nickname="ModeratorUser",
            department=dept,
            pdpa_consent_at=timezone.now(),
        )
        UserRole.objects.create(
            user=cls.moderator_user,
            role=Role.objects.get(code=Role.MODERATOR),
            department=dept,
        )
        cls.category = BoardCategory.objects.create(
            name="ห้องสนทนาทั่วไป",
            slug="general-talk",
        )

    def test_create_thread_strips_and_saves_content(self):
        """Creating a thread strips and saves its title and content."""
        thread = services.create_thread(
            author=self.author,
            category=self.category,
            title="  ยินดีต้อนรับสู่เว็บบอร์ด  ",
            content="  ขอเชิญทุกคนมาคุยกัน :)  ",
        )

        self.assertEqual(thread.title, "ยินดีต้อนรับสู่เว็บบอร์ด")
        self.assertEqual(thread.content, "ขอเชิญทุกคนมาคุยกัน :)")

    def test_create_thread_rejects_blank_title(self):
        """Creating a thread rejects a blank title."""
        with self.assertRaises(ValidationError):
            services.create_thread(
                author=self.author,
                category=self.category,
                title="   ",
                content="เนื้อหา",
            )

    def test_create_thread_rejects_blank_content(self):
        """Creating a thread rejects blank content."""
        with self.assertRaises(ValidationError):
            services.create_thread(
                author=self.author,
                category=self.category,
                title="หัวข้อ",
                content="   ",
            )

    def test_create_post_saves_reply_on_unlocked_thread(self):
        """Replying to an unlocked thread saves the reply."""
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

    def test_create_post_rejects_locked_thread(self):
        """Replying to a locked thread raises a validation error."""
        thread = services.create_thread(
            author=self.author,
            category=self.category,
            title="กระทู้ที่ถูกล็อก",
            content="เนื้อหา",
        )
        Thread.objects.filter(pk=thread.pk).update(is_locked=True)
        with self.assertRaises(ValidationError) as ctx:
            services.create_post(
                thread=thread,
                author=self.other_user,
                content="ตอบไม่ได้แล้ว",
            )
        self.assertIn("ถูกล็อกแล้ว", str(ctx.exception))

    def test_create_post_rejects_blank_content(self):
        """Replying with blank content raises a validation error."""
        thread = services.create_thread(
            author=self.author,
            category=self.category,
            title="กระทู้สำหรับทดสอบข้อความว่าง",
            content="เนื้อหา",
        )

        with self.assertRaisesMessage(ValidationError, "กรุณาระบุข้อความตอบกลับ"):
            services.create_post(
                thread=thread,
                author=self.other_user,
                content="   ",
            )

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

    def test_create_post_rechecks_locked_thread_in_transaction(self):
        """Reply creation rejects a thread locked after the caller read it."""
        thread = services.create_thread(
            author=self.author,
            category=self.category,
            title="กระทู้ที่กำลังถูกล็อก",
            content="เนื้อหา",
        )
        Thread.objects.filter(pk=thread.pk).update(is_locked=True)

        with self.assertRaisesMessage(ValidationError, "กระทู้นี้ถูกล็อกแล้ว"):
            services.create_post(
                thread=thread,
                author=self.other_user,
                content="ข้อความที่ไม่ควรถูกสร้าง",
            )

        self.assertFalse(Post.objects.filter(thread=thread).exists())

    def test_student_cannot_pin_thread(self):
        """A student without a moderator role cannot pin a thread."""
        thread = services.create_thread(
            author=self.author,
            category=self.category,
            title="ทดสอบสิทธิ์",
            content="เนื้อหา",
        )

        with self.assertRaises(PermissionDenied):
            services.toggle_thread_pin(thread=thread, actor=self.author)

    def test_student_cannot_lock_thread(self):
        """A student without a moderator role cannot lock a thread."""
        thread = services.create_thread(
            author=self.author,
            category=self.category,
            title="ทดสอบสิทธิ์ล็อก",
            content="เนื้อหา",
        )

        with self.assertRaises(PermissionDenied):
            services.toggle_thread_lock(thread=thread, actor=self.author)

    def test_moderator_can_pin_thread(self):
        """A moderator can pin a thread."""
        thread = services.create_thread(
            author=self.author,
            category=self.category,
            title="ทดสอบปักหมุด",
            content="เนื้อหา",
        )

        new_state = services.toggle_thread_pin(
            thread=thread,
            actor=self.moderator_user,
        )

        self.assertTrue(new_state)

    def test_moderator_can_lock_thread(self):
        """A moderator can lock a thread."""
        thread = services.create_thread(
            author=self.author,
            category=self.category,
            title="ทดสอบล็อก",
            content="เนื้อหา",
        )

        new_state = services.toggle_thread_lock(
            thread=thread,
            actor=self.moderator_user,
        )

        self.assertTrue(new_state)

    def test_stranger_cannot_delete_thread(self):
        """A stranger cannot delete another user's thread."""
        thread = services.create_thread(
            author=self.author,
            category=self.category,
            title="กระทู้จะถูกลบ",
            content="เนื้อหา",
        )

        with self.assertRaises(PermissionDenied):
            services.delete_thread(thread=thread, actor=self.other_user)

        self.assertTrue(Thread.objects.filter(pk=thread.pk).exists())

    def test_author_can_delete_thread(self):
        """A thread author can delete their thread."""
        thread = services.create_thread(
            author=self.author,
            category=self.category,
            title="กระทู้ของเจ้าของ",
            content="เนื้อหา",
        )

        services.delete_thread(thread=thread, actor=self.author)

        self.assertFalse(Thread.objects.filter(pk=thread.pk).exists())

    def test_moderator_can_delete_thread(self):
        """A moderator can delete another user's thread."""
        thread = services.create_thread(
            author=self.author,
            category=self.category,
            title="กระทู้สำหรับผู้ดูแลลบ",
            content="เนื้อหา",
        )

        services.delete_thread(thread=thread, actor=self.moderator_user)

        self.assertFalse(Thread.objects.filter(pk=thread.pk).exists())

    def test_stranger_cannot_delete_post(self):
        """A stranger cannot delete another user's reply."""
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

        self.assertTrue(Post.objects.filter(pk=post.pk).exists())

    def test_author_can_delete_post(self):
        """A reply author can delete their reply."""
        thread = services.create_thread(
            author=self.author,
            category=self.category,
            title="กระทู้สำหรับลบความคิดเห็น",
            content="เนื้อหา",
        )
        post = services.create_post(
            thread=thread,
            author=self.author,
            content="ความคิดเห็นของเจ้าของ",
        )

        services.delete_post(post=post, actor=self.author)

        self.assertFalse(Post.objects.filter(pk=post.pk).exists())

    def test_moderator_can_delete_post(self):
        """A moderator can delete another user's reply."""
        thread = services.create_thread(
            author=self.author,
            category=self.category,
            title="กระทู้สำหรับผู้ดูแลลบความคิดเห็น",
            content="เนื้อหา",
        )
        post = services.create_post(
            thread=thread,
            author=self.author,
            content="ความคิดเห็นที่จะถูกผู้ดูแลลบ",
        )

        services.delete_post(post=post, actor=self.moderator_user)

        self.assertFalse(Post.objects.filter(pk=post.pk).exists())
