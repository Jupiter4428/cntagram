"""Unit tests for webboard views and request handling."""

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from accounts.models import Role, UserRole
from catalog.models import Department
from webboard.models import BoardCategory, Post, Thread

User = get_user_model()


class WebboardViewsTests(TestCase):
    """Test HTTP views and permissions on the webboard."""

    @classmethod
    def setUpTestData(cls):
        """Prepare a student, moderator, category, and test thread."""
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
        cls.moderator = User.objects.create_user(
            email="6610000007@student.tu.ac.th",
            password="test-password-123",
            nickname="ViewModerator",
            department=dept,
            pdpa_consent_at=timezone.now(),
        )
        UserRole.objects.create(
            user=cls.moderator,
            role=Role.objects.get(code=Role.MODERATOR),
            department=dept,
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
        response = guest.get(reverse("webboard:board_index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_board_index_for_student(self):
        """Webboard index is accessible to authenticated student (status 200)."""
        response = self.client.get(reverse("webboard:board_index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "เว็บบอร์ดเด็กวิศวะ CNTAGRAM")
        self.assertContains(response, "เทคนิคการอ่านสอบไฟนอล")

    def test_category_threads_view_filters_by_slug(self):
        """Category view displays the selected category."""
        response = self.client.get(
            reverse("webboard:category_threads", kwargs={"slug": "academic"})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ห้องวิชาการ")

    def test_category_threads_view_returns_404_for_missing_slug(self):
        """Category view returns 404 for a missing category."""
        response = self.client.get(
            reverse("webboard:category_threads", kwargs={"slug": "not-found"})
        )

        self.assertEqual(response.status_code, 404)

    def test_thread_detail_view_and_view_counter(self):
        """Thread detail displays content and increments views count."""
        initial_views = self.thread.views_count
        response = self.client.get(
            reverse("webboard:thread_detail", kwargs={"pk": self.thread.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "เทคนิคการอ่านสอบไฟนอล")
        self.assertContains(response, f"ยอดอ่าน: {initial_views + 1}")
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.views_count, initial_views + 1)

    def test_thread_detail_renders_post_delete_button_for_author_and_moderator(self):
        """Delete button is shown for author and moderator, but not strangers."""
        post = Post.objects.create(
            thread=self.thread,
            author=self.student,
            content="ข้อความทดสอบปุ่มลบ",
        )
        # Logged in as post author (student)
        response = self.client.get(
            reverse("webboard:thread_detail", kwargs={"pk": self.thread.pk})
        )
        delete_url = reverse("webboard:post_delete", kwargs={"pk": post.pk})
        self.assertContains(response, delete_url)

        # Logged in as moderator
        self.client.force_login(self.moderator)
        response = self.client.get(
            reverse("webboard:thread_detail", kwargs={"pk": self.thread.pk})
        )
        self.assertContains(response, delete_url)

        # Logged in as stranger
        stranger = User.objects.create_user(
            email="6610000088@student.tu.ac.th",
            password="test-password-123",
            nickname="StrangerViewer",
            department=self.student.department,
            pdpa_consent_at=timezone.now(),
        )
        self.client.force_login(stranger)
        response = self.client.get(
            reverse("webboard:thread_detail", kwargs={"pk": self.thread.pk})
        )
        self.assertNotContains(response, delete_url)

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

    def test_moderator_can_pin_thread(self):
        """A user with the moderator role can pin a thread."""
        self.client.force_login(self.moderator)
        response = self.client.post(
            reverse("webboard:thread_pin_toggle", kwargs={"pk": self.thread.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.thread.refresh_from_db()
        self.assertTrue(self.thread.is_pinned)

    def test_moderator_can_lock_thread(self):
        """A user with the moderator role can lock a thread."""
        self.client.force_login(self.moderator)
        response = self.client.post(
            reverse("webboard:thread_lock_toggle", kwargs={"pk": self.thread.pk})
        )

        self.assertEqual(response.status_code, 302)
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

    def test_thread_reply_invalid_form_keeps_posts_unchanged(self):
        """An empty reply shows a specific error and creates no post."""
        response = self.client.post(
            reverse("webboard:thread_reply", kwargs={"pk": self.thread.pk}),
            data={"content": ""},
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Post.objects.filter(thread=self.thread).exists())
        self.assertIn(
            "กรุณากรอกข้อความตอบกลับให้ถูกต้อง",
            [str(message) for message in get_messages(response.wsgi_request)],
        )

    def test_thread_reply_locked_thread_keeps_posts_unchanged(self):
        """A locked thread shows a specific error and creates no post."""
        self.thread.is_locked = True
        self.thread.save(update_fields=["is_locked"])
        response = self.client.post(
            reverse("webboard:thread_reply", kwargs={"pk": self.thread.pk}),
            data={"content": "ตอบในกระทู้ล็อก"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Post.objects.filter(thread=self.thread).exists())
        self.assertIn(
            "['กระทู้นี้ถูกล็อกแล้ว ไม่อนุญาตให้ตอบข้อความเพิ่ม']",
            [str(message) for message in get_messages(response.wsgi_request)],
        )

    def test_thread_detail_returns_404_for_missing_thread(self):
        """Thread detail returns 404 for a missing thread."""
        response = self.client.get(
            reverse("webboard:thread_detail", kwargs={"pk": 99999})
        )

        self.assertEqual(response.status_code, 404)

    def test_thread_reply_returns_404_for_missing_thread(self):
        """Thread reply returns 404 for a missing thread."""
        response = self.client.post(
            reverse("webboard:thread_reply", kwargs={"pk": 99999}),
            data={"content": "ข้อความ"},
        )

        self.assertEqual(response.status_code, 404)

    def test_thread_pin_returns_404_for_missing_thread(self):
        """Pin toggle returns 404 for a missing thread."""
        response = self.client.post(
            reverse("webboard:thread_pin_toggle", kwargs={"pk": 99999})
        )

        self.assertEqual(response.status_code, 404)

    def test_student_cannot_pin_thread(self):
        """A student cannot pin a thread and sees the permission error."""
        response = self.client.post(
            reverse("webboard:thread_pin_toggle", kwargs={"pk": self.thread.pk})
        )

        self.thread.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.thread.is_pinned)
        self.assertIn(
            "เฉพาะผู้ดูแลระบบเท่านั้นที่สามารถปักหมุดกระทู้ได้",
            [str(message) for message in get_messages(response.wsgi_request)],
        )

    def test_thread_lock_returns_404_for_missing_thread(self):
        """Lock toggle returns 404 for a missing thread."""
        response = self.client.post(
            reverse("webboard:thread_lock_toggle", kwargs={"pk": 99999})
        )

        self.assertEqual(response.status_code, 404)

    def test_student_cannot_lock_thread(self):
        """A student cannot lock a thread and sees the permission error."""
        response = self.client.post(
            reverse("webboard:thread_lock_toggle", kwargs={"pk": self.thread.pk})
        )

        self.thread.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.thread.is_locked)
        self.assertIn(
            "เฉพาะผู้ดูแลระบบเท่านั้นที่สามารถล็อกกระทู้ได้",
            [str(message) for message in get_messages(response.wsgi_request)],
        )

    def test_stranger_cannot_delete_thread(self):
        """A stranger cannot delete a thread and sees the permission error."""
        other = User.objects.create_user(
            email="6610000099@student.tu.ac.th",
            password="test-password-123",
            nickname="Stranger",
            department=self.student.department,
            pdpa_consent_at=timezone.now(),
        )
        self.client.force_login(other)
        response = self.client.post(
            reverse("webboard:thread_delete", kwargs={"pk": self.thread.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Thread.objects.filter(pk=self.thread.pk).exists())
        self.assertIn(
            "คุณไม่มีสิทธิ์ในการลบกระทู้นี้",
            [str(message) for message in get_messages(response.wsgi_request)],
        )

    def test_thread_delete_returns_404_for_missing_thread(self):
        """Thread deletion returns 404 for a missing thread."""
        response = self.client.post(
            reverse("webboard:thread_delete", kwargs={"pk": 99999})
        )

        self.assertEqual(response.status_code, 404)

    def test_post_delete_by_author_succeeds(self):
        """Author can delete their post and gets redirected with message."""
        post = Post.objects.create(
            thread=self.thread,
            author=self.student,
            content="ข้อความที่ต้องการลบ",
        )
        response = self.client.post(
            reverse("webboard:post_delete", kwargs={"pk": post.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse("webboard:thread_detail", kwargs={"pk": self.thread.pk}),
        )
        self.assertFalse(Post.objects.filter(pk=post.pk).exists())
        messages = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertIn("ลบความคิดเห็นเรียบร้อยแล้ว", messages)

    def test_post_delete_by_moderator_succeeds(self):
        """Moderator can delete any post."""
        post = Post.objects.create(
            thread=self.thread,
            author=self.student,
            content="ข้อความที่ผู้ดูแลจะลบ",
        )
        self.client.force_login(self.moderator)
        response = self.client.post(
            reverse("webboard:post_delete", kwargs={"pk": post.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Post.objects.filter(pk=post.pk).exists())
        messages = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertIn("ลบความคิดเห็นเรียบร้อยแล้ว", messages)

    def test_post_delete_by_stranger_denied(self):
        """A stranger cannot delete another user's post."""
        other = User.objects.create_user(
            email="6610000099@student.tu.ac.th",
            password="test-password-123",
            nickname="StrangerPost",
            department=self.student.department,
            pdpa_consent_at=timezone.now(),
        )
        post = Post.objects.create(
            thread=self.thread,
            author=self.student,
            content="ข้อความของคนอื่น",
        )
        self.client.force_login(other)
        response = self.client.post(
            reverse("webboard:post_delete", kwargs={"pk": post.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Post.objects.filter(pk=post.pk).exists())
        messages = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertIn("คุณไม่มีสิทธิ์ในการลบความคิดเห็นนี้", messages)

    def test_post_delete_returns_404_for_missing_post(self):
        """Deleting non-existent post returns 404."""
        response = self.client.post(
            reverse("webboard:post_delete", kwargs={"pk": 99999})
        )
        self.assertEqual(response.status_code, 404)

    def test_post_delete_requires_post_method(self):
        """GET request to post_delete returns 405 Method Not Allowed."""
        post = Post.objects.create(
            thread=self.thread,
            author=self.student,
            content="ข้อความทดสอบ GET",
        )
        response = self.client.get(
            reverse("webboard:post_delete", kwargs={"pk": post.pk})
        )
        self.assertEqual(response.status_code, 405)

    def test_thread_edit_get_anonymous_redirects_login(self):
        """Anonymous user is redirected to login when visiting thread_edit."""
        anon_client = Client()
        response = anon_client.get(
            reverse("webboard:thread_edit", kwargs={"pk": self.thread.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_thread_edit_get_by_author_returns_200(self):
        """Author can view thread_edit form prefilled with data."""
        self.client.force_login(self.student)
        response = self.client.get(
            reverse("webboard:thread_edit", kwargs={"pk": self.thread.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "webboard/thread_edit.html")
        self.assertEqual(response.context["thread"].pk, self.thread.pk)
        self.assertEqual(response.context["form"]["title"].value(), self.thread.title)

    def test_thread_edit_get_by_non_author_returns_403(self):
        """Non-author gets 403 when trying to access thread_edit."""
        other = User.objects.create_user(
            email="6610000088@student.tu.ac.th",
            password="test-password-123",
            nickname="StrangerEdit",
            department=self.student.department,
            pdpa_consent_at=timezone.now(),
        )
        self.client.force_login(other)
        response = self.client.get(
            reverse("webboard:thread_edit", kwargs={"pk": self.thread.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_thread_edit_post_success_redirects_to_detail(self):
        """Author POST to thread_edit successfully updates thread and redirects."""
        self.client.force_login(self.student)
        response = self.client.post(
            reverse("webboard:thread_edit", kwargs={"pk": self.thread.pk}),
            {
                "category": self.category.pk,
                "title": "หัวข้อใหม่หลังการแก้ไข",
                "content": "เนื้อหาใหม่หลังการแก้ไข",
            },
        )
        self.assertRedirects(
            response,
            reverse("webboard:thread_detail", kwargs={"pk": self.thread.pk}),
        )
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.title, "หัวข้อใหม่หลังการแก้ไข")
        self.assertEqual(self.thread.content, "เนื้อหาใหม่หลังการแก้ไข")

    def test_thread_edit_post_on_locked_thread_denied(self):
        """Author cannot edit a locked thread and receives 403."""
        self.thread.is_locked = True
        self.thread.save(update_fields=["is_locked"])

        self.client.force_login(self.student)
        response = self.client.post(
            reverse("webboard:thread_edit", kwargs={"pk": self.thread.pk}),
            {
                "category": self.category.pk,
                "title": "พยายามแก้ไขกระทู้ล็อก",
                "content": "พยายามแก้ไขกระทู้ล็อก",
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_thread_edit_post_invalid_re_renders_form(self):
        """POST with empty title re-renders thread_edit form with error."""
        self.client.force_login(self.student)
        response = self.client.post(
            reverse("webboard:thread_edit", kwargs={"pk": self.thread.pk}),
            {
                "category": self.category.pk,
                "title": "",
                "content": "เนื้อหาปกติ",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "title", "กรุณาระบุหัวข้อกระทู้")

    def test_post_edit_get_by_author_returns_200(self):
        """Author can view post_edit form prefilled with current content."""
        post = Post.objects.create(
            thread=self.thread,
            author=self.student,
            content="ข้อความตอบกลับเดิม",
        )
        self.client.force_login(self.student)
        response = self.client.get(
            reverse("webboard:post_edit", kwargs={"pk": post.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "webboard/post_edit.html")
        self.assertEqual(response.context["post"].pk, post.pk)
        self.assertEqual(
            response.context["form"]["content"].value(), "ข้อความตอบกลับเดิม"
        )

    def test_post_edit_get_by_non_author_returns_403(self):
        """Non-author gets 403 when trying to access post_edit."""
        post = Post.objects.create(
            thread=self.thread,
            author=self.student,
            content="ข้อความของคนอื่น",
        )
        other = User.objects.create_user(
            email="6610000087@student.tu.ac.th",
            password="test-password-123",
            nickname="StrangerPostEdit",
            department=self.student.department,
            pdpa_consent_at=timezone.now(),
        )
        self.client.force_login(other)
        response = self.client.get(
            reverse("webboard:post_edit", kwargs={"pk": post.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_post_edit_post_success_redirects_to_detail(self):
        """Author POST to post_edit updates reply and redirects to thread_detail."""
        post = Post.objects.create(
            thread=self.thread,
            author=self.student,
            content="ข้อความก่อนแก้",
        )
        self.client.force_login(self.student)
        response = self.client.post(
            reverse("webboard:post_edit", kwargs={"pk": post.pk}),
            {"content": "ข้อความตอบกลับที่แก้ไขแล้ว"},
        )
        self.assertRedirects(
            response,
            reverse("webboard:thread_detail", kwargs={"pk": self.thread.pk}),
        )
        post.refresh_from_db()
        self.assertEqual(post.content, "ข้อความตอบกลับที่แก้ไขแล้ว")

    def test_post_edit_post_on_locked_thread_denied(self):
        """Author cannot edit reply when parent thread is locked and gets 403."""
        self.thread.is_locked = True
        self.thread.save(update_fields=["is_locked"])
        post = Post.objects.create(
            thread=self.thread,
            author=self.student,
            content="ข้อความในกระทู้ล็อก",
        )
        self.client.force_login(self.student)
        response = self.client.post(
            reverse("webboard:post_edit", kwargs={"pk": post.pk}),
            {"content": "พยายามแก้โพสต์ในกระทู้ล็อก"},
        )
        self.assertEqual(response.status_code, 403)

    def test_post_edit_post_invalid_re_renders_form(self):
        """POST to post_edit with empty content re-renders form with error."""
        post = Post.objects.create(
            thread=self.thread,
            author=self.student,
            content="ข้อความก่อนแก้",
        )
        self.client.force_login(self.student)
        response = self.client.post(
            reverse("webboard:post_edit", kwargs={"pk": post.pk}),
            {"content": "   "},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"], "content", "กรุณาระบุข้อความตอบกลับ"
        )

    def test_thread_detail_shows_edit_buttons_and_timestamp(self):
        """thread_detail renders edit buttons for author and displays update notice."""
        post = Post.objects.create(
            thread=self.thread,
            author=self.student,
            content="คอมเมนต์ที่จะถูกแก้",
        )
        # Simulate edited timestamps
        later = timezone.now() + timezone.timedelta(seconds=10)
        Thread.objects.filter(pk=self.thread.pk).update(updated_at=later)
        Post.objects.filter(pk=post.pk).update(updated_at=later)

        self.client.force_login(self.student)
        response = self.client.get(
            reverse("webboard:thread_detail", kwargs={"pk": self.thread.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, reverse("webboard:thread_edit", kwargs={"pk": self.thread.pk})
        )
        self.assertContains(
            response, reverse("webboard:post_edit", kwargs={"pk": post.pk})
        )
        self.assertContains(response, "แก้ไขล่าสุดเมื่อ")

    def test_board_index_pagination_15_threads_per_page(self):
        """board_index paginates threads at 15 items per page."""
        # Create 25 threads
        for i in range(25):
            Thread.objects.create(
                category=self.category,
                author=self.student,
                title=f"กระทู้ทดสอบ {i}",
                content="เนื้อหาทดสอบ",
            )

        # Page 1
        response = self.client.get(reverse("webboard:board_index"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["threads"]), 15)
        self.assertTrue(response.context["page_obj"].has_next())
        self.assertEqual(response.context["page_obj"].paginator.num_pages, 2)

        # Page 2
        response_page2 = self.client.get(reverse("webboard:board_index"), {"page": 2})
        self.assertEqual(response_page2.status_code, 200)
        # 25 new threads + 1 setUp thread = 26 threads total -> 15 on p1, 11 on p2
        self.assertEqual(len(response_page2.context["threads"]), 11)
        self.assertTrue(response_page2.context["page_obj"].has_previous())

    def test_category_threads_pagination(self):
        """category_threads paginates threads at 15 items per page."""
        for i in range(20):
            Thread.objects.create(
                category=self.category,
                author=self.student,
                title=f"กระทู้หมวดหมู่ {i}",
                content="เนื้อหาทดสอบ",
            )

        response = self.client.get(
            reverse(
                "webboard:category_threads",
                kwargs={"slug": self.category.slug},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["threads"]), 15)
        self.assertTrue(response.context["page_obj"].has_next())

        response_page2 = self.client.get(
            reverse(
                "webboard:category_threads",
                kwargs={"slug": self.category.slug},
            ),
            {"page": 2},
        )
        self.assertEqual(response_page2.status_code, 200)
        # 20 new threads + 1 setUp thread = 21 threads -> 15 on p1, 6 on p2
        self.assertEqual(len(response_page2.context["threads"]), 6)

    def test_thread_detail_post_pagination_20_posts_per_page(self):
        """thread_detail paginates replies at 20 posts per page."""
        for i in range(25):
            Post.objects.create(
                thread=self.thread,
                author=self.student,
                content=f"ความคิดเห็นที่ {i}",
            )

        # Page 1
        response = self.client.get(
            reverse("webboard:thread_detail", kwargs={"pk": self.thread.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["posts"]), 20)
        self.assertTrue(response.context["page_obj"].has_next())

        # Page 2
        response_page2 = self.client.get(
            reverse("webboard:thread_detail", kwargs={"pk": self.thread.pk}),
            {"page": 2},
        )
        self.assertEqual(response_page2.status_code, 200)
        self.assertEqual(len(response_page2.context["posts"]), 5)
        self.assertTrue(response_page2.context["page_obj"].has_previous())

    def test_thread_detail_view_counter_debounces_on_refresh(self):
        """Viewing thread multiple times in same session only increments view count."""
        detail_url = reverse("webboard:thread_detail", kwargs={"pk": self.thread.pk})
        self.thread.refresh_from_db()
        initial_views = self.thread.views_count

        # First visit: increments view count
        res1 = self.client.get(detail_url)
        self.assertEqual(res1.status_code, 200)
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.views_count, initial_views + 1)

        # Second visit (refresh in same session): does NOT increment
        res2 = self.client.get(detail_url)
        self.assertEqual(res2.status_code, 200)
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.views_count, initial_views + 1)

    def test_retro_pagination_ui_renders_links(self):
        """Retro pagination partial renders navigation controls on multiple pages."""
        for i in range(25):
            Thread.objects.create(
                category=self.category,
                author=self.student,
                title=f"กระทู้แบ่งหน้า {i}",
                content="เนื้อหา",
            )
        response = self.client.get(reverse("webboard:board_index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "webboard/_pagination.html")
        self.assertContains(response, "หน้าแรก")
        self.assertContains(response, "ถัดไป")
        self.assertContains(response, "[ 1 ]")
