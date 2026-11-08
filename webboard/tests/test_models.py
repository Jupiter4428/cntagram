"""Unit tests for webboard models."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from catalog.models import Department
from webboard.models import BoardCategory, Post, Thread

User = get_user_model()


class WebboardModelsTests(TestCase):
    """Test model creation, string representation, and ordering."""

    @classmethod
    def setUpTestData(cls):
        """Set up test user, department, and category."""
        dept, _ = Department.objects.get_or_create(
            code="CN",
            defaults={
                "name_th": "วิศวกรรมคอมพิวเตอร์",
                "name_en": "Computer Engineering",
            },
        )
        cls.user = User.objects.create_user(
            email="6610000001@student.tu.ac.th",
            password="test-password-123",
            nickname="ModelTester",
            department=dept,
            pdpa_consent_at=timezone.now(),
        )
        cls.category = BoardCategory.objects.create(
            name="ห้องทดสอบ",
            slug="test-room",
            icon="🧪",
            order=10,
        )

    def test_board_category_str(self):
        """Category string representation includes its icon and name."""
        self.assertEqual(str(self.category), "🧪 ห้องทดสอบ")

    def test_thread_str_and_default_ordering(self):
        """Thread string representation includes category prefix."""
        thread = Thread.objects.create(
            category=self.category,
            author=self.user,
            title="กระทู้ทดสอบโมเดล",
            content="เนื้อหาทดสอบ",
        )
        self.assertEqual(str(thread), "[ห้องทดสอบ] กระทู้ทดสอบโมเดล")
        self.assertFalse(thread.is_pinned)
        self.assertFalse(thread.is_locked)
        self.assertEqual(thread.views_count, 0)

    def test_post_str(self):
        """Post string representation includes post ID and thread title."""
        thread = Thread.objects.create(
            category=self.category,
            author=self.user,
            title="หัวข้อกระทู้หลัก",
            content="เนื้อหากระทู้หลัก",
        )
        post = Post.objects.create(
            thread=thread,
            author=self.user,
            content="ข้อความตอบกลับแรก",
        )
        self.assertEqual(str(post), f"Reply #{post.id} on หัวข้อกระทู้หลัก")
