"""Unit tests for webboard selectors."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from catalog.models import Course, Department
from webboard import selectors
from webboard.models import BoardCategory, Post, Thread

User = get_user_model()


class WebboardSelectorsTests(TestCase):
    """Test read-only selector queries."""

    @classmethod
    def setUpTestData(cls):
        """Prepare sample category, course, user, threads, and posts."""
        dept, _ = Department.objects.get_or_create(
            code="CN",
            defaults={
                "name_th": "วิศวกรรมคอมพิวเตอร์",
                "name_en": "Computer Engineering",
            },
        )
        cls.user = User.objects.create_user(
            email="6610000002@student.tu.ac.th",
            password="test-password-123",
            nickname="SelectorTester",
            department=dept,
            pdpa_consent_at=timezone.now(),
        )
        cls.category_a = BoardCategory.objects.create(
            name="หมวด ก",
            slug="cat-a",
            order=1,
        )
        cls.category_b = BoardCategory.objects.create(
            name="หมวด ข",
            slug="cat-b",
            order=2,
        )
        cls.course = Course.objects.create(
            code="CN101",
            name_th="การเขียนโปรแกรมคอมพิวเตอร์",
            name_en="Computer Programming",
        )

        cls.thread_1 = Thread.objects.create(
            category=cls.category_a,
            author=cls.user,
            title="กระทู้ที่หนึ่ง หมวด ก",
            content="เนื้อหาเกี่ยวกับวิชา",
            course=cls.course,
            is_pinned=True,
        )
        cls.thread_2 = Thread.objects.create(
            category=cls.category_b,
            author=cls.user,
            title="กระทู้ที่สอง หมวด ข",
            content="เนื้อหาทั่วไปเรื่องอื่น",
        )
        cls.post_1 = Post.objects.create(
            thread=cls.thread_1,
            author=cls.user,
            content="ตอบกระทู้ 1",
        )

    def test_list_board_categories_annotates_thread_count(self):
        """Categories query annotates correct thread counts."""
        categories = list(selectors.list_board_categories())
        self.assertGreaterEqual(len(categories), 2)
        cat_map = {c.slug: c.threads_count for c in categories}
        self.assertEqual(cat_map.get("cat-a"), 1)
        self.assertEqual(cat_map.get("cat-b"), 1)

    def test_get_category_by_slug_returns_category(self):
        """Retrieve a category by its valid slug."""
        cat = selectors.get_category_by_slug("cat-a")

        self.assertIsNotNone(cat)
        self.assertEqual(cat.name, "หมวด ก")

    def test_get_category_by_slug_returns_none_for_missing_slug(self):
        """A missing category slug returns None."""
        self.assertIsNone(selectors.get_category_by_slug("non-existent"))

    def test_list_threads_orders_pinned_threads_first(self):
        """Pinned threads appear before unpinned threads."""
        threads = list(selectors.list_threads())

        self.assertEqual(threads[0].id, self.thread_1.id)

    def test_list_threads_filters_by_category(self):
        """Category filtering returns only threads in that category."""
        cat_b_threads = list(selectors.list_threads(category_slug="cat-b"))

        self.assertEqual(len(cat_b_threads), 1)
        self.assertEqual(cat_b_threads[0].id, self.thread_2.id)

    def test_list_threads_filters_by_course(self):
        """Course filtering returns only threads for that course."""
        course_threads = list(selectors.list_threads(course_code="CN101"))

        self.assertEqual(len(course_threads), 1)
        self.assertEqual(course_threads[0].id, self.thread_1.id)

    def test_list_threads_filters_by_search_query(self):
        """Search filtering matches thread content."""
        searched = list(selectors.list_threads(search_query="เรื่องอื่น"))

        self.assertEqual(len(searched), 1)
        self.assertEqual(searched[0].id, self.thread_2.id)

    def test_get_thread_by_id_returns_thread(self):
        """Retrieve a thread by its primary key."""
        thread = selectors.get_thread_by_id(self.thread_1.id)

        self.assertIsNotNone(thread)
        self.assertEqual(thread.title, "กระทู้ที่หนึ่ง หมวด ก")

    def test_get_thread_by_id_returns_none_when_missing(self):
        """A missing thread ID returns None."""
        self.assertIsNone(selectors.get_thread_by_id(999999))

    def test_list_posts_for_thread_returns_posts_in_order(self):
        """List posts returns replies for a specific thread in order."""
        posts = list(selectors.list_posts_for_thread(self.thread_1.id))

        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].content, "ตอบกระทู้ 1")

    def test_list_posts_for_thread_returns_empty_queryset(self):
        """List posts returns no replies for a thread without replies."""
        empty_posts = list(selectors.list_posts_for_thread(self.thread_2.id))

        self.assertEqual(len(empty_posts), 0)
