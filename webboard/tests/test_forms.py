"""Unit tests for webboard forms."""

from django.test import TestCase
from webboard.forms import PostForm, ThreadForm
from webboard.models import BoardCategory


class WebboardFormsTests(TestCase):
    """Test validation logic of thread and post forms."""

    @classmethod
    def setUpTestData(cls):
        """Prepare sample board category."""
        cls.category = BoardCategory.objects.create(
            name="หมวดพูดคุย",
            slug="talk",
        )

    def test_thread_form_valid(self):
        """ThreadForm validates with required category, title, and content."""
        form = ThreadForm(
            data={
                "category": self.category.id,
                "title": "หัวข้อทดสอบฟอร์ม",
                "content": "เนื้อหาของกระทู้ทดสอบ",
            }
        )
        self.assertTrue(form.is_valid())

    def test_thread_form_invalid_empty_fields(self):
        """ThreadForm rejects blank or whitespace-only inputs."""
        form = ThreadForm(
            data={
                "category": self.category.id,
                "title": "   ",
                "content": "   ",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)
        self.assertIn("content", form.errors)

    def test_post_form_valid(self):
        """PostForm validates non-empty reply text."""
        form = PostForm(data={"content": "ข้อความตอบกลับฟอร์ม"})
        self.assertTrue(form.is_valid())

    def test_post_form_invalid_empty_content(self):
        """PostForm rejects blank or whitespace-only content."""
        form = PostForm(data={"content": "   "})
        self.assertFalse(form.is_valid())
        self.assertIn("content", form.errors)
