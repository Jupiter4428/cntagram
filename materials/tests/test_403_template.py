from django.template import loader
from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse


class ForbiddenTemplateTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_renders_default_message_when_exception_is_empty(self):
        """กรณีไม่มีข้อความ exception จะแสดงข้อความเริ่มต้นของระบบ"""
        request = self.factory.get("/some-forbidden-url/")
        template = loader.get_template("403.html")
        rendered = template.render({"exception": ""}, request=request)

        self.assertIn("เนื้อหานี้สงวนสิทธิ์เฉพาะผู้ดูแลระบบ", rendered)
        self.assertIn(reverse("accounts:home"), rendered)
        self.assertIn(reverse("materials:vault"), rendered)

    def test_renders_custom_exception_message(self):
        """กรณีส่งข้อความ exception กำหนดเอง จะนำมาแสดงผลในหน้าเว็บ"""
        request = self.factory.get("/materials/approvals/")
        template = loader.get_template("403.html")
        rendered = template.render({"exception": "เฉพาะผู้ดูแลเท่านั้นที่สามารถเข้าถึงได้"}, request=request)

        self.assertIn("เฉพาะผู้ดูแลเท่านั้นที่สามารถเข้าถึงได้", rendered)

    def test_escapes_html_in_exception_to_prevent_xss(self):
        """ข้อความ exception ต้องถูก escape HTML เสมอเพื่อป้องกัน XSS"""
        request = self.factory.get("/some-url/")
        template = loader.get_template("403.html")
        malicious_input = "<script>alert('xss')</script>"
        rendered = template.render({"exception": malicious_input}, request=request)

        self.assertNotIn(malicious_input, rendered)
        self.assertIn("&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;", rendered)
