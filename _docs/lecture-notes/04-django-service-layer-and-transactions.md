# Django Architectural Patterns: Service Layer, Selectors & Transactions

> ที่มา: CN331 สัปดาห์ที่ 10 — Part 2 (Django Architectural Patterns: Service Layer & Data Access) และ Part 4 กิจกรรมปฏิบัติการที่ 2
>
> *การขจัด Fat Views และ Fat Models ด้วย Service Layer, Selector Queries, ACID Transactions และ ADR*
>
> เนื้อหาที่เกี่ยวข้อง: Race Condition แบบ Read-Modify-Write และ F Expressions, `select_related`/`prefetch_related` → ดู [01-django-orm-queries-and-optimization.md](01-django-orm-queries-and-optimization.md) · ขอบเขต Django Apps → ดู [03-software-architecture-and-decomposition.md](03-software-architecture-and-decomposition.md)

---

## เลเยอร์สถาปัตยกรรมใน Web Application (Architectural Tiers)

การจัดโค้ดเป็น 4 ชั้นเชิงตรรกะช่วยแยกความรับผิดชอบอย่างเด็ดขาดและทำให้ระบบทดสอบได้ง่าย:

| ชั้นสถาปัตยกรรม (Layer) | หน้าที่และความรับผิดชอบหลัก | ไฟล์ใน Django | สิ่งที่ห้ามทำเด็ดขาด |
|---|---|---|---|
| **1. Presentation Layer** | รับ HTTP Request, แปลง JSON/HTML, จัดการ Headers, ส่ง Response | `views.py` | ✗ ห้ามคำนวณ Business Logic หรือเขียน SQL |
| **2. Validation Layer** | ตรวจสอบ Type, Format, ความยาวตัวอักษร, Field Rules | `forms.py` | ✗ ห้ามตัดสินใจกฎธุรกิจขั้นสูงข้ามโมเดล |
| **3. Business Logic Layer** | ประมวลผลกฎธุรกิจ, จัดการ Transaction, ประสานงานภายนอก | `services.py` | ✗ ห้ามยุ่งเกี่ยวกับ Request/Session objects |
| **4. Data Access Layer** | จัดการ Schema, ความสัมพันธ์ตาราง, สืบค้นข้อมูล ORM ประสิทธิภาพสูง | `selectors.py` | ✗ ห้ามส่งเมล หรือตัดเงินผ่าน API ภายนอก |

> 💡 **Takeaway** — **Strict Dependency Flow**: Presentation → Business Logic → Data Access ทิศทางการเรียกใช้ต้องลงล่างเท่านั้น ห้ามให้ Data Layer ย้อนกลับมาเรียก Presentation Layer

## หลุมพรางที่ 1: "Fat Views" (เมื่อ View แบกรับ Logic มากเกินไป)

**☠️ อาการของ Fat Views**

เมื่อโปรเจกต์เติบโตขึ้น นักศึกษามักยัดโค้ดทุกอย่างลงในฟังก์ชัน View:
- เช็กสิทธิ์ผู้ใช้ซ้อนกัน 4 ชั้น
- ดึงข้อมูลคิวรีที่ซับซ้อนหลายสิบแถว
- มีลูปคำนวณยอดเงินและส่วนลด
- เรียก API ภายนอกของ LINE Notify
- จัดการ `try-except` ยาวกว่า 100 บรรทัด

**🐞 ผลกระทบต่อคุณภาพซอฟต์แวร์**
- **Zero Reusability**: ไม่สามารถนำ Logic การลงทะเบียนนี้ไปใช้ซ้ำในจุดอื่นได้ (เช่น ใน Celery Background Task, Management Command, หรือ REST API)
- **Impossible to Unit Test**: หากต้องการทดสอบการคำนวณส่วนลด ต้องจำลอง HTTP Request ทั้งก้อนพร้อม Mock Authentication
- **Violation of SRP**: View แบกรับหน้าที่มากถึง 5 อย่างในเวลาเดียวกัน

> 💡 **Takeaway** — **Golden Rule for Views**: หน้าที่เดียวของ View คือ *"รับ HTTP Request → เรียก Service ทำงาน → ส่ง HTTP Response กลับไป"* โค้ดใน View ควรมีความยาวไม่เกิน 15-20 บรรทัด!

## หลุมพรางที่ 2: "Fat Models" (เมื่อ Model กลายเป็น God Object)

**❓ สโลแกนดั้งเดิม: "Fat Models, Thin Views"**

ในอดีตมักสอนให้ย้าย Logic จาก View ไปใส่ใน Model:
- เพิ่ม Method ใน Model เพื่อจัดการการทำงาน
- ใช้ `model.save()` ทำหน้าที่หลายอย่าง

**❗ จุดแตกหักเมื่อโปรเจกต์ขยายตัว**
- **God Object**: โมเดลบวมเกิน 1,000 บรรทัด มี Method ปนกันมั่ว
- **Violating Boundaries**: โมเดลผูกกับ Third-party APIs ภายนอก

**✖ ตัวอย่าง Anti-Pattern ใน Model**

```python
class Enrollment(models.Model):
    student = models.ForeignKey(...)
    course = models.ForeignKey(...)

    def save(self, *args, **kwargs):
        # Hidden side-effects in save()
        if not self.pk:
            send_sms(self.student)
            charge_card(self.student, 5000)
        super().save(*args, **kwargs)
```

✗ **อันตราย**: ทุกครั้งที่รัน Fixture, Seeding หรือแก้ค่าใน Admin บัตรเครดิตจะถูกตัดเงินและ SMS จะถูกส่งทันที!

> 💡 **Takeaway** — **Model Responsibility**: โมเดลควรรับผิดชอบเฉพาะ **Data Integrity** (ชนิดข้อมูล, ฟิลด์, ความสัมพันธ์) และพฤติกรรมพื้นฐานเฉพาะตัว แต่ต้องไม่มี Side-effects ภายนอก

## QUICK CHECK: การจัดเลเยอร์สถาปัตยกรรมและ Separation of Concerns

*(สไลด์ไม่มีเนื้อหาคำถาม)*

## ทางออกระดับสากล: The Django Service Layer Pattern

**🛡️ สถาปัตยกรรม HackSoft Styleguide**

แบ่งโค้ดตรรกะในแต่ละ Django App ออกเป็น 2 ส่วนชัดเจน:

1. **`services.py` (Mutations & Actions)**:
   - ฟังก์ชันสร้าง แก้ไข หรือลบข้อมูล (CUD)
   - ควบคุม Database Transactions (`@transaction.atomic`)
   - ประสานงานกับ External Services (Email, Payment)
2. **`selectors.py` (Queries & Reads)**:
   - ฟังก์ชันสำหรับการสืบค้นข้อมูล (Pure Reads)
   - ปราศจาก Side-effects โดยเด็ดขาด
   - รวบรวมคิวรี ORM ซับซ้อน ป้องกัน N+1 Queries

**🏅 ประโยชน์ทางวิศวกรรมที่ได้รับทันที**
- **Skinny Views**: วิวเหลือเพียงการรับ Input, ส่งต่อให้ Service, และเรนเดอร์ Response
- **Extreme Testability**: เขียน Unit Test ทดสอบ Service/Selector ได้โดยตรง ไม่ต้องผ่าน Client
- **Single Source of Truth**: ให้บริการทั้ง Web UI และ REST API ผ่าน Service เดียวกัน ไม่เขียนโค้ดซ้ำ

> 💡 **Takeaway** — **Plain Python Functions**: Service Layer คือฟังก์ชันไพทอนธรรมดา (Pure Python Functions) ที่รับ Parameters ชัดเจน อ่านและบำรุงรักษาง่าย

## โครงสร้างภายในของ `services.py` (Handling Mutations)

```python
# apps/enrollments/services.py
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.courses.models import Course
from apps.enrollments.models import Enrollment

@transaction.atomic
def enroll_student_in_course(*, student, course_id: int) -> Enrollment:
    course = Course.objects.select_for_update().get(id=course_id)
    if course.enrolled_count >= course.max_capacity:
        raise ValidationError(f"Quota reached ({course.max_capacity} seats)")
    if Enrollment.objects.filter(student=student, course=course).exists():
        raise ValidationError("Student already enrolled")
    enrollment = Enrollment.objects.create(student=student, course=course)
    course.enrolled_count += 1
    course.save(update_fields=['enrolled_count'])
    transaction.on_commit(lambda: send_confirmation(enrollment_id=enrollment.id))
    return enrollment
```

> 💡 **Takeaway** — **Key Insight**: การใช้ `@transaction.atomic` ร่วมกับ `select_for_update()` ช่วยแก้ปัญหา Race Condition เมื่อแย่งกันลงทะเบียนพร้อมกัน

## โครงสร้างภายในของ `selectors.py` (Pure Read Queries)

```python
# apps/courses/selectors.py
from django.db.models import QuerySet, Count, Avg, F
from apps.courses.models import Course

def get_available_courses_for_student(*, student) -> QuerySet:
    """Returns an optimized QuerySet of open courses. Prevents N+1 queries."""
    return (
        Course.objects
        .select_related('department').prefetch_related('prerequisites')
        .annotate(total_enrolled=Count('enrollments')).filter(is_active=True)
        .exclude(enrollments__student=student)
        .filter(max_capacity__gt=F('enrolled_count')).order_by('code')
    )

def get_department_course_statistics(*, department_id: int) -> dict:
    """Calculates summary statistics for a given department without mutating data."""
    return Course.objects.filter(department_id=department_id).aggregate(
        total_courses=Count('id'), avg_credits=Avg('credits')
    )
```

> 💡 **Takeaway** — **Read vs Write Isolation**: แยกตรรกะการดึงข้อมูล (`selectors.py`) ออกจากการเปลี่ยนแปลงข้อมูล (`services.py`) ทำให้โค้ดค้นหาข้อมูลสามารถนำไปใช้ซ้ำในหลายๆ หน้า View หรือ Export Reports ได้อย่างปลอดภัย

## เปรียบเทียบความสะอาดของโค้ด: Messy View vs Clean Service Layer

**✗ แบบเดิม: รวมทุกอย่างใน View (Messy View)**

```python
def enroll_view(request, course_id):
    if not request.user.is_authenticated:
        return redirect('login')
    course = get_object_or_404(Course, id=course_id)
    if course.enrolled_count >= course.max_capacity:
        messages.error(request, "Course is full")
        return redirect('course_list')
    e = Enrollment.objects.create(
        student=request.user, course=course
    )
    course.enrolled_count += 1
    course.save()
    send_mail("Confirmed", ..., [request.user.email])
    return redirect('dashboard')
```

**✓ แบบใหม่: View สื่อสารผ่าน Service (Clean View)**

```python
from apps.enrollments.services import enroll_student_in_course

@login_required
def enroll_view(request, course_id: int):
    try:
        enroll_student_in_course(
            student=request.user,
            course_id=course_id
        )
        messages.success(request, "Success")
    except ValidationError as err:
        messages.error(request, err.message)
    return redirect('dashboard')
```

✓ **Clean & Expressive**: View ทำหน้าที่คุยกับผู้ใช้ จัดการ Error และ Redirect เท่านั้น

> 💡 **Takeaway** — **Simplicity Wins**: โค้ด View ทางขวามือ (แบบใหม่) อ่านเข้าใจได้ในเวลา 5 วินาที ดูแลรักษาง่าย และป้องกันปัญหาบั๊กในระบบได้อย่างมั่นคง

## QUICK CHECK: สถาปัตยกรรม Django Service Layer กับ Fat Models

*(สไลด์ไม่มีเนื้อหาคำถาม)*

## ความปลอดภัยของฐานข้อมูลใน Service Layer: ACID Transactions

**🗄️ กฎความปลอดภัยทางธุรกรรม (ACID)**

การทำงานของระบบลงทะเบียนประกอบด้วยหลายขั้นตอน:
1. ตัดโควตาที่นั่งในตาราง `Course`
2. สร้างเรคคอร์ดในตาราง `Enrollment`
3. สร้างใบเสร็จค่าธรรมเนียมในตาราง `Invoice`

**ความเสี่ยง**: หากระบบล่มระหว่างขั้นตอนที่ 2 และ 3 ที่นั่งจะหายไปแต่ไม่มีใบเสร็จ และข้อมูลจะขัดแย้ง (Inconsistency)

**✅ การรับประกันด้วย Transaction Decorator**
- **`@transaction.atomic`**: ครอบทั้งกระบวนการใน Service หากเกิด Exception ที่บรรทัดใด ระบบจะ **Rollback** การเปลี่ยนแปลงทั้งหมดทันที
- **`transaction.on_commit()`**: สั่งให้ทำงาน (เช่น ส่งอีเมล) เฉพาะเมื่อฐานข้อมูล Commit สำเร็จ 100% เท่านั้น ป้องกันการส่งเมลหลอก

> 💡 **Takeaway** — **Transaction Boundary**: Service Layer คือขอบเขตที่เหมาะสมที่สุดในการกำหนดขอบเขตของ Database Transaction เพราะเป็นจุดที่รู้ภาพรวมของขั้นตอนการทำงานทั้งหมด

## การรับมือ Concurrency และ Race Conditions ใน Service Layer

**⚠️ ปัญหาแย่งชิงทรัพยากร (Race Condition)**

เมื่อผู้ใช้ 2 คนกดลงทะเบียนวิชาที่เหลือ **1 ที่นั่งสุดท้าย** พร้อมกัน:
1. Request A อ่านที่นั่งเหลือ 1
2. Request B อ่านที่นั่งเหลือ 1
3. Request A สร้าง Enrollment และเซฟ (เหลือ 0)
4. Request B สร้าง Enrollment และเซฟ (-1 เกินโควตา!)

✗ การใช้แค่ `if capacity > 0` ไม่สามารถป้องกันบั๊กนี้ได้เมื่อมี Concurrency!

**🔒 Row-Level Locking ด้วย `select_for_update`**

```python
@transaction.atomic
def enroll_student(*, student, course_id):
    course = Course.objects.select_for_update().get(id=course_id)
    if course.enrolled_count >= course.max_capacity:
        raise ValidationError("Course is full")
    Enrollment.objects.create(student=student, course=course)
    course.enrolled_count += 1
    course.save(update_fields=['enrolled_count'])
```

✓ `select_for_update()` สั่ง SQL ล็อกแถวนั้นไว้ ทำให้ Request B ต้องรอจนกว่า Request A จะ Commit เสร็จ

> 💡 **Takeaway** — **Data Consistency at Scale**: การผสาน `@transaction.atomic` เข้ากับ Pessimistic Locking คือมาตรฐานของระบบธุรกรรมระดับโปรดักชัน

## QUICK CHECK: ความปลอดภัยทางธุรกรรมและการรับมือ Race Conditions

*(สไลด์ไม่มีเนื้อหาคำถาม)*

## การบันทึกการตัดสินใจสถาปัตยกรรม: Architectural Decision Records (ADR)

**📄 ADR คืออะไร?**

เอกสารข้อความขนาดสั้น (Markdown) บันทึกไว้ใน Git Repository เพื่ออธิบายว่า:
- เหตุใดทีมจึงตัดสินใจเลือกสถาปัตยกรรมนี้?
- มีทางเลือกอื่นใดที่ถูกปฏิเสธไปบ้าง?
- ผลกระทบและข้อแลกเปลี่ยน (Trade-offs) คืออะไร?

**ประโยชน์**: สมาชิกใหม่เข้าใจเหตุผลเบื้องหลัง และป้องกันการถกเถียงเรื่องเดิมซ้ำๆ

**🔢 โครงสร้างมาตรฐานของเอกสาร ADR**
1. **Title**: เช่น *ADR 003: Adoption of Service Layer Pattern*
2. **Status**: Proposed, Accepted, Deprecated, Superseded
3. **Context**: ปัญหา View และ Model บวมจนทดสอบไม่ได้
4. **Decision**: แยก Logic เข้า `services.py` และ Query เข้า `selectors.py`
5. **Consequences**: ต้องเขียนไฟล์เพิ่มขึ้น แต่มี Testability สูงขึ้น

> 💡 **Takeaway** — **Documentation as Code**: เก็บไฟล์ ADR ไว้ในโฟลเดอร์ `docs/adr/` ของโปรเจกต์ เพื่อให้ประวัติการตัดสินใจทางสถาปัตยกรรมได้รับการตรวจสอบผ่าน Pull Request เช่นเดียวกับโค้ด

## ตารางสรุปการจัดวางโค้ด: Where Should Code Live?

หลักเกณฑ์การตัดสินใจสำหรับทีม เพื่อขจัดข้อสงสัยว่าควรเขียนโค้ดบรรทัดนี้ไว้ที่ไฟล์ใด:

| ตำแหน่งไฟล์ | สิ่งที่ควรอยู่ตรงนี้ (What belongs here) | สิ่งที่ไม่ควรอยู่ตรงนี้ (What does NOT belong) | ผลลัพธ์ที่ได้ |
|---|---|---|---|
| **`views.py`** | จัดการ HTTP Request/Response, อ่านคุกกี้, เรียก Service, สั่ง Redirect | Business Logic, การคำนวณเงิน, การเขียน Query ยาวๆ | Views สั้น สะอาด สื่อสารชัดเจน |
| **`forms.py`** | ตรวจสอบ Type, Format, ความยาวตัวอักษร, Field validation | การบันทึกข้อมูลข้ามตาราง, การตัดบัตรเครดิต | ปลอดภัยต่อข้อมูลป้อนเข้า |
| **`services.py`** | การเปลี่ยนแปลงข้อมูล (Mutations), กฎธุรกิจ, Transactions, เรียก API นอก | จัดการ HTTP, การจัดฟอร์แมต HTML, Pure Read queries | นำกลับมาใช้ซ้ำได้ ทดสอบง่าย |
| **`selectors.py`** | การดึงข้อมูล (Queries), `select_related`, การคำนวณสถิติ `aggregate` | การแก้ไข/ลบข้อมูล, การส่งอีเมลแจ้งเตือน | ปลอดภัย ไร้ Side-effects |
| **`models.py`** | โครงสร้างฐานข้อมูล, Schema, Fields, Relationships, Simple properties | Business workflows ที่ผูกกับระบบภายนอก | Model ไม่บวม โค้ดเสถียร |

> 💡 **Takeaway** — **Architectural Discipline**: การรักษาวินัยในการแยกตำแหน่งของโค้ดให้ถูกต้องตั้งแต่เริ่มต้น จะช่วยประหยัดเวลาในการแก้ปัญหาของทีมได้หลายสิบชั่วโมงในระหว่าง Sprint 2 และ 3

## สรุปใจความสำคัญของ Part 2 (Django Architecture Takeaways)

**✔ เสาหลักด้านการจัดโครงสร้างโค้ด**
- **No More Fat Views**: วิวเป็นเพียงด่านหน้า รับข้อมูล ส่งต่อ ตอบกลับ สั้นกระชับ
- **No More Fat Models**: หยุดการใส่ Side-effects ภายนอกลงในเมธอด `save()` ของ Model
- **Service/Selector Architecture**: แยกหน้าที่ชัดเจนระหว่างการดึงข้อมูล (`selectors.py`) และการแก้ไขข้อมูล (`services.py`)

**✔ เสาหลักด้านความปลอดภัยธุรกรรม**
- **ACID Safety**: ครอบคลุม Business Workflows ด้วย `@transaction.atomic`
- **Pessimistic Locking**: ใช้ `select_for_update()` ป้องกัน Race Condition
- **ADR Documentation**: บันทึกเหตุผลการออกแบบทางสถาปัตยกรรมไว้ใน Git Repo เสมอ

**ลำดับถัดไป**: เชื่อมโยงโครงสร้างสถาปัตยกรรมและโค้ด สู่การวางแผนส่งมอบงานใน **Sprint 2 Planning** → ดู [05-agile-scrum-sprints.md](05-agile-scrum-sprints.md)

---

## กิจกรรมปฏิบัติการที่ 2: ความท้าทายในการทำ Code Refactoring

**</> ภารกิจปรับปรุงโครงสร้างโค้ด (Refactoring Challenge)**

ให้ทุกกลุ่มสำรวจโค้ดของตนเองจาก Sprint 1 และเลือกทำภารกิจ Refactoring อย่างน้อย 1 จุด:
- **Mission A**: แยกฟังก์ชัน View ที่ยาวเกิน 50 บรรทัด ออกเป็น `services.py` และ `selectors.py`
- **Mission B**: นำ Side-effects ออกจากเมธอด `save()` ของ Model และคลุมการทำงานด้วย `@transaction.atomic`
- **Mission C**: ป้องกัน Race Condition ด้วย `select_for_update()` และบันทึกเหตุผลในเอกสาร ADR

**🔀 การส่งมอบงาน Refactoring ผ่าน Git**
- **Branch**: สร้างกิ่งแยกชื่อ `refactor/service-layer-cleanup`
- **Pull Request**: ส่งงานในรูปแบบ PR บน GitHub
- **Diff**: แสดงการเปรียบเทียบโค้ดก่อนทำและหลังทำ (Before/After)
- **Peer Review**: ได้รับการ Approve จากสมาชิกในกลุ่มก่อน Merge

> 💡 **Takeaway** — **Zero Regressions**: หัวใจของการทำ Refactoring คือฟังก์ชันการทำงานภายนอกต้องทำงานได้ถูกต้องสมบูรณ์เหมือนเดิมทุกประการ ห้ามทำฟังก์ชันเดิมพังเด็ดขาด

---

## ตารางสังเคราะห์องค์ความรู้: Service Layer (ตอนที่ 2 — ส่วนสถาปัตยกรรม)

| มโนทัศน์หลัก | เป้าหมายทางวิศวกรรม | การประยุกต์ใช้จริงใน Django | ข้อควรระวังสำคัญ |
|---|---|---|---|
| **Service Layer** | รวมศูนย์การเปลี่ยนแปลงข้อมูลและธุรกรรม | ฟังก์ชันใน `services.py` คลุมด้วย `@transaction.atomic` | ห้ามส่ง Request เข้าไป |
| **Selectors** | แยกคิวรีอ่านข้อมูล ป้องกัน N+1 queries | ฟังก์ชันใน `selectors.py` ใช้ `select_related` | ห้ามมี Side-effects ใดๆ |
| **Row Locking** | ป้องกัน Race Condition เมื่อแย่งทรัพยากร | `select_for_update()` ภายใน Transaction | ล็อกเฉพาะแถวที่จำเป็น |

*(แถว Velocity Calibration ของตารางนี้อยู่ใน [05-agile-scrum-sprints.md](05-agile-scrum-sprints.md))*
