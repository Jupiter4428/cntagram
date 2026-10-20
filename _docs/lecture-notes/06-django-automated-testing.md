# Automated Testing in Django: Unit, Integration, Mocking & Coverage

> ที่มา: CN331 สัปดาห์ที่ 11 — Automated Testing in Django (Unit & Integration Testing) หน่วยที่ 1–4 และบทสรุป
>
> *จากการทดสอบด้วยมือสู่ชุดทดสอบอัตโนมัติ: Testing Pyramid, TDD, Django TestCase, Test Client, Mock และ Coverage.py*
>
> เนื้อหาที่เกี่ยวข้อง: `services.py`/`selectors.py` และ `@transaction.atomic` → ดู [04-django-service-layer-and-transactions.md](04-django-service-layer-and-transactions.md) · N+1 Queries → ดู [01-django-orm-queries-and-optimization.md](01-django-orm-queries-and-optimization.md) · Definition of Done → ดู [05-agile-scrum-sprints.md](05-agile-scrum-sprints.md)

---

## ทำไมวิศวกรซอฟต์แวร์ต้องเปลี่ยนจากการทดสอบด้วยมือสู่ Automated Testing?

**🐞 กับดักของการทดสอบด้วยมือ (Manual Trap)**
- **Manual Verification is Expensive**: การรันเซิร์ฟเวอร์แล้วคลิกฟอร์มทีละหน้า ใช้เวลามากขึ้นเรื่อยๆ ตามจำนวนฟีเจอร์
- **The Regression Nightmare**: แก้บั๊กจุดหนึ่งแต่ไปกระทบฟีเจอร์อื่น (Regression Bugs) เพราะมนุษย์เช็กซ้ำทุกกรณีไม่ได้ทุกวัน
- **Fear of Refactoring**: ทีมไม่กล้าจัดโครงสร้างโค้ด เพราะกลัวว่าแก้แล้วระบบที่เคยรันผ่านจะพังทลาย

**🛡️ พลังของ Automated Testing**
- **Repeatable & Instant Feedback**: สั่งรัน `manage.py test` ทดสอบหลายร้อยกรณีเสร็จในไม่กี่วินาที
- **Executable Specifications**: โค้ดทดสอบทำหน้าที่เป็นเอกสารความต้องการที่มีชีวิต ยืนยันพฤติกรรมจริงของระบบเสมอ
- **Safety Net for Sprint Delivery**: เป็นเกราะป้องกันที่ทำให้ทีมมั่นใจในการ Push โค้ดและทำ Code Review บน GitHub

> 💡 **Takeaway** — **Software Engineering Axiom**: *"Legacy code is simply code without automated tests."* — Michael Feathers โค้ดที่ไม่มีระบบทดสอบอัตโนมัติจะกลายเป็นหนี้ทางเทคนิคทันทีที่เขียนเสร็จ

---

# หน่วยที่ 1: QA Foundations — Testing Pyramid & TDD

## ต้นทุนของการพบจุดบกพร่องตามช่วงชีวิตการพัฒนา (Cost of Defect)

ตามหลักการวิศวกรรมซอฟต์แวร์ของ Boehm:

| ช่วงที่พบบั๊ก | ต้นทุนสัมพัทธ์ | เหตุผล |
|---|---|---|
| **Coding / Unit Stage** | 1× | ต้นทุนแก้บั๊กต่ำที่สุด เพราะโปรแกรมเมอร์ยังจำบริบทของโค้ดได้ทันที |
| **Integration / CI Stage** | 5×–10× | ต้องสืบค้นสาเหตุระหว่างโมดูลที่เชื่อมต่อกัน |
| **QA / Staging Stage** | 15×–25× | มีการเขียนรายงาน เปิด Ticket และส่งงานกลับไปแก้ |
| **Production Release** | 50×–100× | กระทบผู้ใช้งาน ข้อมูลเสียหาย เสียชื่อเสียงองค์กร |

> 💡 **Takeaway** — **Shift-Left Testing**: ผลักดันการทดสอบมาสู่ช่วงเริ่มต้นของการพัฒนาด้วยชุด Unit Tests ที่รันอัตโนมัติ เพื่อดักจับและกำจัดข้อผิดพลาดก่อนโค้ดจะหลุดออกจากเครื่องของนักพัฒนา

## พีระมิดการทดสอบ (The Testing Pyramid)

โมเดลของ Mike Cohn กำหนดสัดส่วนการทดสอบที่เหมาะสมสำหรับระบบที่มีสุขภาพดี (ยิ่งขึ้นยอดยิ่งช้าและต้นทุนสูง ยิ่งลงฐานยิ่งเร็วและระบุจุดพังได้แม่นยำ):

| ชั้น | สัดส่วน | ลักษณะ |
|---|---|---|
| **Unit Tests** (ฐานพีระมิด) | ~70% | ทดสอบฟังก์ชัน/คลาสเดี่ยวๆ แบบแยกขาด · รันเร็วมากในหน่วย ms ชี้จุดพังได้แม่นยำ |
| **Integration Tests** (กลางพีระมิด) | ~20% | ทดสอบการทำงานร่วม: View + ORM + Template · ตรวจสอบความถูกต้องของ Business Flow |
| **End-to-End / UI Tests** (ยอดพีระมิด) | ~10% | รันผ่านเบราว์เซอร์จริง (Playwright) · ช้า มีความเปราะบาง (Flaky) ดูแลรักษายาก |

**⚠️ ข้อควรระวัง: Ice Cream Cone Anti-pattern** — หากทีมเน้นแต่ E2E หรือกด UI จะทำให้ CI Build ช้ามากและหาจุดบกพร่องได้ยาก

> 💡 **Takeaway** — **Pyramid Balance**: ลงทุนกับ Unit Tests เป็นฐานหลักเพื่อความรวดเร็ว เสริมด้วย Integration Tests เพื่อตรวจการเชื่อมโยงระบบ และจำกัด E2E ไว้เฉพาะ Critical User Journeys

## QUICK CHECK: Testing Pyramid Trade-offs

*(สไลด์ไม่มีเนื้อหาคำถาม)*

## แนวคิดการพัฒนาที่ขับเคลื่อนด้วยการทดสอบ (Test-Driven Development: TDD)

TDD กำหนดขั้นตอนการเขียนโค้ดผ่านวงจร **Red-Green-Refactor**:

1. **Red (เขียนเทสก่อน)** — *Write failing test*: เขียน Test Case ตาม Requirement และรันยืนยันว่าล้มเหลวตามคาด
2. **Green (โค้ดขั้นต่ำ)** — *Make test pass*: เขียนโค้ดเฉพาะเท่าที่จำเป็นเพื่อให้เทสผ่าน มุ่งผลลัพธ์ถูกต้องก่อน
3. **Refactor (ปรับโครงสร้าง)** — *Clean up design*: จัดระเบียบ ขจัดความซ้ำซ้อน ดึงเข้า Service โดยเทสยังผ่าน 100%

**ประโยชน์เชิงวิศวกรรมของ TDD**
- **Design for Testability**: โค้ดจะแยกส่วน (Decoupled) โดยธรรมชาติ
- **Clear Requirements**: ป้องกันการเขียนฟีเจอร์เกินจำเป็น (YAGNI)

> 💡 **Takeaway** — **TDD Discipline**: หัวใจของ TDD ไม่ใช่การตรวจจับบั๊ก แต่เป็น *"เทคนิคการออกแบบซอฟต์แวร์"* ที่ใช้การทดสอบช่วยนำทางสถาปัตยกรรมและการตัดสินใจ

## โครงสร้างมาตรฐานของ Test Case: รูปแบบ Arrange-Act-Assert (AAA)

ทุก Unit Test ที่มีคุณภาพสูงควรอ่านเข้าใจง่ายและแบ่งหน้าที่ชัดเจนตาม 3 ขั้นตอน:

- **Arrange (เตรียมสภาพแวดล้อม)**: สร้างอ็อบเจกต์ เตรียมข้อมูล Fixture จำลองสถานะเบื้องต้น
- **Act (เรียกใช้คำสั่งเป้าหมาย)**: เรียกใช้ฟังก์ชันหรือเมธอดที่ต้องการทดสอบเพียง 1 คำสั่ง
- **Assert (ตรวจสอบผลลัพธ์)**: เปรียบเทียบค่าที่ได้กับผลลัพธ์ที่คาดหวัง ยืนยันสถานะข้อมูล

```python
from django.test import TestCase
from courses.models import Course

class CourseModelTest(TestCase):
    def test_course_initial_seats(self):
        # 1. Arrange: course with capacity of 30
        course = Course.objects.create(
            code="CN331", title="SE", max_capacity=30
        )

        # 2. Act: get available seats
        available = course.available_seats()

        # 3. Assert: must equal 30 available seats
        self.assertEqual(available, 30)
```

**⚠️ ข้อควรระวัง: The Multi-Act Smell** — หลีกเลี่ยงการทำ Act หลายคำสั่งในเทสเดียว เพราะหากเกิดล้มเหลว จะระบุจุดพังได้ยาก

> 💡 **Takeaway** — **AAA Pattern**: จัดระเบียบการทดสอบเป็น 3 บล็อกชัดเจนเสมอ เพื่อให้เพื่อนร่วมทีมที่เข้ามาอ่านหรือดู CI Logs เข้าใจเจตนาของเทสได้ในทันที

## QUICK CHECK: TDD Cycle & Test Case Isolation

*(สไลด์ไม่มีเนื้อหาคำถาม)*

---

# หน่วยที่ 2: Django TestCase — Database Isolation & Model Testing

## สถาปัตยกรรมของ Django TestCase: Database Isolation

เมื่อเราสั่ง `python manage.py test` Django มีกลไกการทำงานเบื้องหลังที่สำคัญ:

- **Isolated Test Database**: สร้าง Database ชั่วคราวแยกต่างหาก (เช่น `test_default`) ดึง Schema จาก Migrations โดยไม่แตะต้อง Production DB
- **Atomic Transaction Wrapper**: ครอบแต่ละ Test Method ไว้ใน Database Transaction เมื่อทดสอบจะทำการ **Rollback** ทันที
- **Zero Side-Effects**: ข้อมูลที่สร้างในแต่ละเทสจะถูกล้างทิ้ง ทำให้ทุกเทสเริ่มต้นด้วย Database ที่สะอาดเสมอ

```
Test Runner Starts      → สร้าง Database: test_db จาก Migrations
Test Method Execution   → BEGIN Transaction
                          setUp() → รันโค้ดเทส → tearDown()
                          ROLLBACK Transaction
Runner Finished         → ลบ test_db ทิ้งอัตโนมัติ
```

> 💡 **Takeaway** — **Isolation Guarantee**: ความเป็นอิสระของการทดสอบ (Independence) เป็นคุณสมบัติสำคัญที่สุด เทสที่ดีต้องสามารถรันสลับลำดับใดๆ ได้โดยให้ผลลัพธ์ผ่านเท่ากันเสมอ

## คำสั่ง Terminal สำหรับการรันการทดสอบ (Running Tests via CLI)

**1. โครงสร้างโฟลเดอร์ทดสอบ (Test Discovery)**
- Django ค้นหาไฟล์ที่ขึ้นต้นด้วย `test_*.py`
- แนะนำแยกไฟล์ตามบทบาทของ Architecture Layers:

```
courses/
  tests/
    __init__.py
    test_models.py     # Model methods & clean()
    test_services.py   # Service workflows
    test_views.py      # Views & client tests
```

**2. ระดับการเจาะจง**: ทั้งโปรเจกต์ → App → File → Method

**3. คำสั่ง Terminal และ Flags ที่จำเป็น**

```bash
# 1. Run all tests in project
python manage.py test

# 2. Target specific app, file, or method
python manage.py test courses
python manage.py test courses.tests.test_models
python manage.py test courses.tests.test_models.CourseModelLogicTests.test_is_full

# 3. Essential flags for developers
python manage.py test --keepdb     # Reuse DB; skip setup (5x faster)
python manage.py test -v 2         # Verbose: show each test name
python manage.py test --failfast   # Exit immediately on 1st error
```

> 💡 **Takeaway** — **Developer Workflow**: ในการพัฒนา Local ประจำวัน ให้ใช้คำสั่ง `python manage.py test --keepdb -v 2` ร่วมกับการระบุชื่อ Class หรือ Method เพื่อรอบการ Feedback ที่เร็วที่สุดในระดับวินาที

## การเพิ่มความเร็วการทดสอบ: เปรียบเทียบ `setUp()` กับ `setUpTestData()`

ปัญหาการทดสอบช้ามักเกิดจากการสร้างข้อมูลซ้ำซ้อนในฐานข้อมูล:

| | `setUp(self)` | `setUpTestData(cls)` |
|---|---|---|
| **รันเมื่อใด** | รันใหม่**ก่อนทุกๆ Test Method** (มี 10 เทส เขียน DB 10 รอบ) | รันเพียง**ครั้งเดียวต่อ Test Class** |
| **เหมาะกับ** | ข้อมูลที่เทสต้องแก้ไขค่า (Mutate) | สร้าง Fixtures ระดับคลาสในโหมด Read-only |
| **ผลต่อความเร็ว** | — | ลดเวลาการรันเทสลงได้ถึง 50%–80% |

```python
from courses.models import Course, Department

class CourseQueryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dept = Department.objects.create(name="CPE")
        cls.c1 = Course.objects.create(code="CN331", title="SE", dept=cls.dept)

    def test_course_str(self):
        self.assertEqual(str(self.c1), "CN331: SE")

    def test_dept_relation(self):
        self.assertEqual(self.c1.dept.name, "CPE")
```

> 💡 **Takeaway** — **Performance Optimization**: ใช้ `setUpTestData` สำหรับข้อมูลอ้างอิงที่ไม่ถูกแก้ไข (Fixtures ใน DB) เพื่อเร่งความเร็วของ Test Suite ทั้งโครงการ

## การทดสอบ Django Models: Business Logic & Model Methods

ตามหลัก **DDD (Domain-Driven Design)**: ควรสร้าง **Rich Model** ที่มี Business Logic อยู่ในเมธอดของตัวเอง (ไม่ใช่แค่ตารางเก็บข้อมูล):
- ตรวจสอบค่าเริ่มต้น (Default Values)
- ตรวจสอบพฤติกรรม Custom Methods เช่น `is_full()`
- ตรวจสอบการแสดงผลข้อความ `__str__()`

**ตัวอย่าง Business Rule ใน Model**: `course.is_full()` คืนค่า `True` เมื่อจำนวน `Enrollment` ถึงขีดจำกัด `max_capacity`

```python
class CourseModelLogicTests(TestCase):
    def setUp(self):
        self.course = Course.objects.create(code="CN331", max_capacity=1)
        self.student = Student.objects.create(name="Alice")

    def test_is_full_false_when_open(self):
        self.assertFalse(self.course.is_full())

    def test_is_full_true_when_capped(self):
        Enrollment.objects.create(
            course=self.course, student=self.student
        )
        self.assertTrue(self.course.is_full())
```

> 💡 **Takeaway** — **DDD & Model Behavior**: ตามหลัก Domain-Driven Design ให้เน้นทดสอบ "พฤติกรรมและกฎธุรกิจ" (Rich Model) ในเมธอดของโมเดล ไม่ต้องทดสอบสิ่งที่ Django รับประกันอยู่แล้ว เช่น ฟิลด์ `id`

## กับดักสำคัญ: Model `save()` ไม่ได้เรียก `clean()` อัตโนมัติ!

**⚠️ ข้อควรระวังใน Django ORM** — คำสั่ง `create()` หรือ `save()` **จะไม่รัน `clean()` อัตโนมัติ!** การตรวจสอบจะรันเฉพาะเมื่อบันทึกผ่าน **Django Form** หรือ **Admin Interface**

**วิธีทดสอบ Validation ใน Unit Test**:
- ต้องเรียก `instance.full_clean()` เองอย่างชัดเจน
- ใช้ `assertRaises(ValidationError)`
- ตรวจสอบฟิลด์ใน `exception.message_dict`

```python
from django.core.exceptions import ValidationError
from django.test import TestCase
from courses.models import Course

class CourseValidationTests(TestCase):
    def test_negative_capacity_error(self):
        # Arrange: invalid negative capacity
        course = Course(
            code="CN331", title="SE", max_capacity=-5
        )
        # Act & Assert: full_clean must raise
        with self.assertRaises(ValidationError) as ctx:
            course.full_clean()
        self.assertIn("max_capacity", ctx.exception.message_dict)
```

> 💡 **Takeaway** — **Validation Rigor**: ในการเขียน Model Test ต้องใช้ `full_clean()` เสมอเพื่อตรวจสอบกฎทางธุรกิจที่กำหนดไว้ในฟังก์ชัน `clean()`

## QUICK CHECK: Django TestCase DB Isolation & full_clean

*(สไลด์ไม่มีเนื้อหาคำถาม)*

## QUICK CHECK: setUp vs setUpTestData Optimization

*(สไลด์ไม่มีเนื้อหาคำถาม)*

---

# หน่วยที่ 3: Views, Forms & Architecture Services

## การทดสอบ Django Forms (Unit Testing Form Validation)

Form ทำหน้าที่ตรวจสอบข้อมูลนำเข้า การทดสอบฟอร์มทำได้รวดเร็วมากเพราะไม่ต้องเชื่อมต่อ Database:
- **Happy Path**: ส่งข้อมูลถูกต้อง `form.is_valid()` คืนค่า `True`
- **Required Fields**: ละเว้นข้อมูลจำเป็น ตรวจสอบว่าฟิลด์ปรากฏใน `form.errors`
- **Custom Validation**: ตรวจสอบข้อความแจ้งเตือนเมื่อข้อมูลผิดเงื่อนไขเฉพาะ

```python
from django.test import SimpleTestCase
from courses.forms import CourseForm

class CourseFormTests(SimpleTestCase):
    def test_valid_form(self):
        data = {"code": "CN331", "title": "SE", "max_capacity": 40}
        form = CourseForm(data=data)
        self.assertTrue(form.is_valid())

    def test_blank_code_invalid(self):
        data = {"code": "", "title": "SE", "max_capacity": 40}
        form = CourseForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("code", form.errors)
```

> 💡 **Takeaway** — **SimpleTestCase Efficiency**: หากแบบทดสอบใดไม่จำเป็นต้องเชื่อมต่อ Database (เช่น ฟอร์ม หรือยูทิลิตีทางคณิตศาสตร์) ให้สืบทอดจาก `SimpleTestCase` เพื่อความเร็วสูงสุด

## การทดสอบ Service Layer จากสัปดาห์ที่ 10 (Testing Business Workflows)

การแยก Business Logic ออกจาก Views มาไว้ใน `services.py` ทำให้เรา**ทดสอบ Core Logic ได้โดยตรงโดยไม่ต้องจำลอง HTTP Request**:
- ตรวจสอบสถานะข้อมูลหลังรัน Service
- ตรวจสอบการ Rollback ของ `@transaction.atomic`
- ตรวจจับ Business Exceptions ที่คาดหวัง

```python
class EnrollmentServiceTests(TestCase):
    def setUp(self):
        self.c = Course.objects.create(code="CN331", max_capacity=1)
        self.s1 = Student.objects.create(name="Somchai")
        self.s2 = Student.objects.create(name="Somsri")

    def test_enroll_service(self):
        # 1. Happy path: enrollment succeeds
        enroll_student_service(self.s1, self.c)
        self.assertEqual(self.c.enrollments.count(), 1)
        # 2. Capacity reached: raises Domain Error
        with self.assertRaises(CourseFullError):
            enroll_student_service(self.s2, self.c)
```

> 💡 **Takeaway** — **Service Layer Testability**: สถาปัตยกรรมที่สะอาดย่อมนำมาซึ่งการทดสอบที่ง่ายและทรงพลัง การแยก Service ออกจาก View ทำให้การทำ Unit Test ตรงประเด็นและกระชับ

## การจำลองผู้ใช้ด้วย Django Test Client (View Testing)

Django มีเครื่องมือ `self.client` เป็นเสมือนเบราว์เซอร์จำลองในระดับโปรแกรม:

- **No Real HTTP Server Needed**: ส่งคำเข้าสู่ WSGI/ASGI Handler โดยตรง ทำงานเร็วมาก
- **Lifecycle Inspection**:
  - **Status Code**: 200 (OK), 302 (Redirect), 403, 404
  - **Template Used**: `assertTemplateUsed(res, 'tpl.html')`
  - **Context Data**: ตรวจสอบตัวแปรใน `res.context`
- **URL Decoupling with `reverse()`**: สร้าง URL จากชื่อ route เสมอ หลีกเลี่ยง hardcoded paths

```
Django Test Client      self.client.get(reverse('list'))
        ↓
URLconf & View Processing   Middlewares → View → Context
        ↓
Response Object         status_code, context['courses']
```

> 💡 **Takeaway** — **Comprehensive View Checks**: ตรวจสอบทั้งรหัสสถานะ เทมเพลตที่ใช้ และเนื้อหาบริบท เพื่อป้องกันหน้าเว็บที่แสดงผลรหัส 200 แต่ไม่มีข้อมูลหรือแสดงผลผิดพลาด

## ตัวอย่างการทดสอบ View: สิทธิ์การเข้าถึง และการแสดงผลข้อมูล

ตรวจสอบว่าผู้ใช้ที่ไม่ล็อกอินต้องถูก Redirect (302) ส่วนผู้ใช้ที่ล็อกอินแล้วเข้าถึงได้ (200):

```python
from django.urls import reverse
from django.contrib.auth import get_user_model

class CourseViewAuthTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user("student1", "pass123")
        self.url = reverse("course_list")

    def test_anonymous_redirected(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp.url)

    def test_authenticated_can_access(self):
        self.client.force_login(self.user)
        resp = self.client.get(self.url)

        # Status code, template & context
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "courses/course_list.html")
        self.assertIn("courses", resp.context)
```

> 💡 **Takeaway** — **Client Login**: ใช้ `self.client.force_login(user)` ในการทดสอบสิทธิ์ เพราะข้ามกระบวนการแฮชรหัสผ่านของระบบ Authentication ช่วยให้เทสรันได้เร็วยิ่งขึ้น

## การทดสอบคำสั่ง POST: ปฏิบัติตามแบบแผน Post/Redirect/Get (PRG)

เมื่อผู้ใช้ส่งฟอร์มสำเร็จ ระบบที่ดีจะต้องตอบกลับด้วย HTTP 302 Redirect เพื่อป้องกันการ Refresh ซ้ำ:
- ตรวจสอบว่าส่ง POST แล้วได้รหัส 302
- ตรวจสอบ URL ปลายทางของการ Redirect
- ยืนยันว่าข้อมูลใหม่ถูกบันทึกลงใน DB จริง

```python
class CourseCreateViewTests(TestCase):
    def test_create_course_success_redirects(self):
        url = reverse("course_create")
        data = {"code": "CN331", "title": "SE", "max_capacity": 50}
        resp = self.client.post(url, data)

        # Verify HTTP 302 & redirect
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("course_list"))
        # Verify record persisted in DB
        self.assertTrue(Course.objects.filter(code="CN331").exists())
```

> 💡 **Takeaway** — **Verify Database Impact**: นอกจากการเช็กรหัสสถานะ 302 แล้ว ต้องยืนยันผลลัพธ์ในฐานข้อมูลเสมอว่าข้อมูลใหม่ถูกสร้างหรือแก้ไขอย่างถูกต้อง

## QUICK CHECK: Form Testing Assertions

*(สไลด์ไม่มีเนื้อหาคำถาม)*

## QUICK CHECK: View Test Redirection Verification

*(สไลด์ไม่มีเนื้อหาคำถาม)*

---

# หน่วยที่ 4: Mocking, Test Doubles & Coverage

## ทำไมและเมื่อไหร่ที่ต้องจำลองระบบด้วย Mock (Test Doubles)?

ระบบในชีวิตจริงจำเป็นต้องติดต่อกับบริการภายนอก:
- ส่งอีเมลแจ้งเตือน (SMTP Server)
- ตัดเงินผ่าน Payment Gateway (Stripe/Omise)
- เรียก 3rd-party REST API หรือเวลาเครื่อง

**💣 ผลกระทบหากไม่ใช้ Mock**
- ชุดทดสอบรันช้ามากเพราะรอ Network I/O
- เกิด Flaky Tests เมื่อเน็ตหลุดหรือ API ล่ม
- เสี่ยงตัดเงินจริงหรือส่งสแปมจริงขณะรันเทส!

```
Tuition Service: checkout_tuition()
   ├─✗ ห้ามต่อจริง → Real Stripe API      (Network delay, Real charge!)
   └─@patch ──────→ MagicMock Object     (Instant response, Deterministic!)
```

**นิยามของ Mock**: **Mock** คือวัตถุจำลองที่ถูกสร้างแทนที่ Component จริง กำหนด `return_value` ได้ และบันทึกประวัติการถูกเรียกใช้

> 💡 **Takeaway** — **Boundary Testing**: Mock เฉพาะระบบที่อยู่นอกเหนือขอบเขตการควบคุมของระบบเรา (External Boundaries) อย่า Mock ระบบภายในของตัวเองจนไม่ได้ทดสอบอะไรจริง

## การใช้งาน `unittest.mock.patch` ใน Service Layer

จำลองการตัดเงินค่าธรรมเนียมผ่าน Payment Gateway:
- ใช้ Decorator `@patch("module.path.target")`
- กำหนดค่าคืนกลับด้วย `mock_obj.return_value`
- ตรวจสอบพารามิเตอร์ด้วย `assert_called_once_with()`

```python
from unittest.mock import patch

class PaymentServiceMockTests(TestCase):
    @patch("billing.services.stripe_client.charge")
    def test_payment_success(self, mock_charge):
        # 1. Arrange: define mock return value
        mock_charge.return_value = {"id": "ch_1", "status": "paid"}
        # 2. Act: invoke service under test
        result = process_payment_service(student_id=1, amount=5000)
        # 3. Assert: verify result & call args
        self.assertTrue(result["success"])
        mock_charge.assert_called_once_with(amount=5000, currency="thb")
```

> 💡 **Takeaway** — **Where to Patch**: กฎเหล็กของ mock คือ *"Patch where an object is LOOKED UP, not where it is defined"* ให้ patch ตรงจุดที่โมดูลนั้นถูก import มาใช้งาน

## การทดสอบ Error Handling: จำลองระบบภายนอกล่มด้วย `side_effect`

Mock ช่วยให้เราจำลองข้อผิดพลาดที่เกิดขึ้นจริงได้ยาก:
- เซิร์ฟเวอร์ภายนอกเกิด Network Timeout
- บัตรเครดิตยอดเงินไม่พอ หรือระบบล่ม

กำหนดคุณสมบัติ `mock.side_effect` เพื่อทดสอบว่าระบบจัดการ Error และ Rollback ฐานข้อมูลอย่างสมบูรณ์

```python
class PaymentFailureTests(TestCase):
    @patch("billing.services.stripe_client.charge")
    def test_timeout_rollback(self, mock_charge):
        # Arrange: simulate network timeout
        mock_charge.side_effect = GatewayTimeoutError("Timeout")
        # Act & Assert: must raise PaymentFailedError
        with self.assertRaises(PaymentFailedError):
            process_payment_service(student_id=1, amount=5000)
        # Verify atomic rollback succeeded
        self.assertEqual(PaymentTransaction.objects.count(), 0)
```

> 💡 **Takeaway** — **Resilience Verification**: ใช้ `side_effect` ทดสอบกิ่งการทำงานที่ผิดปกติ (Unhappy Paths) เพื่อการันตีว่าระบบจะไม่เกิดปัญหาข้อมูลค้างคาหรือเงินสูญหาย

## การวัดความครอบคลุมของชุดทดสอบด้วย Coverage.py

**Workflow คำสั่ง Terminal สำหรับวัด Coverage**:

```bash
# 1. ติดตั้งและรันเทสพร้อมวัดผล
pip install coverage
coverage run --source='.' manage.py test --keepdb

# 2. สรุปผลบน Terminal พร้อมเช็กเกณฑ์ขั้นต่ำ
coverage report -m --fail-under=80

# 3. สร้างรายงาน HTML เจาะลึกรายบรรทัด
coverage html && open htmlcov/index.html
```

**ตัวอย่างตารางผลลัพธ์ `coverage report`**

| Name | Stmts | Miss | Cover | Missing |
|---|---|---|---|---|
| `courses/models.py` | 35 | 0 | 100% | |
| `courses/services.py` | 42 | 4 | 90% | 51-54 |
| `courses/views.py` | 60 | 12 | 80% | 88-102 |
| **TOTAL** | **137** | **16** | **88%** | |

**พารามิเตอร์ CLI สำคัญ**
- `--source='.'`: วัดเฉพาะโค้ดโปรเจกต์ (ตัด 3rd-party libs)
- `-m` (Missing): ชี้เลขบรรทัดที่ยังขาดเทสไปครอบคลุม
- `--fail-under=80`: ส่ง Exit code ล้มเหลวหากไม่ถึง 80% (ใช้ใน CI)

> 💡 **Takeaway** — **Automated Quality Gate**: การสั่ง `coverage report --fail-under=80` ช่วยสร้าง Gatekeeper ตรวจสอบคุณภาพ หากครอบคลุมไม่ถึง 80% คำสั่งจะ Fail ทันที เพื่อป้องกันการ Merge โค้ดที่ขาดเทส

## Line Coverage กับ Branch Coverage: ระวังกับดัก Vanity Metrics

- **Line (Statement) Coverage**: นับว่าบรรทัดคำสั่งถูกรันผ่านหรือไม่
  - อาจหลอกตาได้ เพราะการรันผ่านไม่ได้แปลว่าครอบคลุมทุกเงื่อนไข
- **Branch Coverage**: ตรวจสอบว่าเงื่อนไขในคำสั่ง `if` / `else` ถูกทดสอบ**ครบทุกทางแยก**หรือไม่
  - เปิดใช้งานในไฟล์ `.coveragerc`:

```ini
[run]
branch = True
source = .
omit = */migrations/*, */tests/*, manage.py
```

```python
def calculate_discount(student, is_early):
    discount = 0
    if student.is_scholarship:  # Branch 1
        discount += 50
    if is_early:                # Branch 2
        discount += 10
    return discount
```

**⚠️ ข้อคิดวิศวกรรม: 100% Coverage ≠ Zero Bugs** — แม้จะทำได้ 100% Coverage แต่ถ้าเขียน Assertion ไม่ครอบคลุม หรือไม่ทดสอบ Boundary Values ระบบก็ยังมีบั๊กเกิดได้

> 💡 **Takeaway** — **Meaningful Assertions**: ตัวเลขเปอร์เซ็นต์ Coverage เป็นเพียงเครื่องมือเตือนว่าโค้ดส่วนใดยังไม่ได้ทดสอบ แต่คุณภาพที่แท้จริงอยู่ที่ความถูกต้องและความลึกซึ้งของคำสั่ง Assert

## QUICK CHECK: Mocking Strategy & Return Values

*(สไลด์ไม่มีเนื้อหาคำถาม)*

## QUICK CHECK: Code Coverage Interpretation

*(สไลด์ไม่มีเนื้อหาคำถาม)*

---

# สรุปบทเรียน: ตารางสังเคราะห์องค์ความรู้ & Sprint 2 DoD

## ตารางสังเคราะห์องค์ความรู้ (ตอนที่ 1): ลำดับชั้นการทดสอบใน Django

| คลาสทดสอบ | ขอบเขตการใช้งาน | คุณลักษณะเด่น / กลไก | ความเร็ว |
|---|---|---|---|
| `SimpleTestCase` | ยูทิลิตี, Math, Forms, Templates | ไม่สร้าง Test DB, ห้ามมีคำสั่งคิวรี | สูงสุด (< 5ms) |
| `TestCase` | Models, ORM, Views, Services | สร้าง Isolated DB และ Rollback transaction | ปานกลาง (~50ms) |
| `TransactionTestCase` | Multi-threading, Signals | ทำงานจริงโดยไม่ใช้ Rollback (ช้ากว่ามาก) | ช้า (~500ms) |
| `LiveServerTestCase` | End-to-End, Playwright/Selenium | เปิด HTTP Server จริงเพื่อรับ Browser | ช้ามาก (> 2s) |

> 💡 **Takeaway** — **Design Rule**: เริ่มต้นด้วย `TestCase` เป็นมาตรฐานหลัก และใช้ `SimpleTestCase` ทุกครั้งที่สามารถทดสอบได้โดยไม่ต้องต่อฐานข้อมูล

## ตารางสังเคราะห์องค์ความรู้ (ตอนที่ 2): Assertion Methods สำคัญใน Django

| Assertion Method | เป้าหมายการทดสอบ | ตัวอย่างการใช้งานจริง |
|---|---|---|
| `assertEqual(a, b)` | ยืนยันความเท่ากันของค่า | ตรวจสอบผลลัพธ์ของฟังก์ชัน หรือ Status code |
| `assertRaises(Exc)` | ยืนยันว่าเกิด Exception ตามคาด | ตรวจสอบ `ValidationError` เมื่อข้อมูลผิดกฎ |
| `assertRedirects(res, url)` | ตรวจสอบการส่งต่อหน้าเว็บ | ตรวจสอบ Post/Redirect/Get flow หลังส่งฟอร์ม |
| `assertTemplateUsed(res, t)` | ตรวจสอบการเรนเดอร์ Template | ยืนยันว่า View เรียกใช้ไฟล์ HTML ที่ถูกต้อง |
| `assertNumQueries(n)` | ป้องกันปัญหา N+1 queries | ยืนยันประสิทธิภาพของ Selectors ว่าใช้คำสั่ง SQL คงที่ |

> 💡 **Takeaway** — **Query Optimization**: เมธอด `assertNumQueries` เป็นอาวุธลับของวิศวกรซอฟต์แวร์ในการันตีว่า ORM จะไม่เกิดคิวรีบานปลายใน Production

## หมุดหมายใน Sprint 2: ยกระดับ Definition of Done ด้วยการทดสอบ

**📋 Definition of Done (DoD) ของ Sprint 2** — ก่อนที่ทีมจะสามารถย้าย User Story จาก **"In Review"** สู่ **"Done"** บน GitHub Projects จะต้องผ่านเกณฑ์วิศวกรรม:

1. โค้ดฟังก์ชันใหม่ทุกชิ้นต้องมี Unit Test กำกับ
2. ชุดทดสอบทั้งหมดต้องรันผ่าน 100% ปราศจากข้อผิดพลาด
3. อัตราความครอบคลุมรวม (Coverage) ต้องไม่ต่ำกว่า **80%**
4. ไม่มี N+1 Query regressions ใน Core Services

**🔀 วินัยในการเปิด Pull Request (PR)**
- **Attach Test Evidence**: แนบภาพ Terminal จากคำสั่ง `coverage report -m --fail-under=80` ลงใน PR Description
- **Peer Review Check**: ผู้ทำ Code Review ต้องตรวจสอบความถูกต้องของ Test Cases ก่อนกด Approve
- **No Tests, No Merge**: ปฏิเสธการ Merge โค้ดที่ไม่มีการเขียนเทสกำกับอย่างเด็ดขาด

> 💡 **Takeaway** — **Agile Excellence**: การมี Automated Tests ช่วยให้การส่งมอบงานใน Sprint 2 รวดเร็วและปราศจากความหวาดระแวง เพราะทีมมีตาข่ายนิรภัยคุ้มครองระบบอยู่ตลอดเวลา
