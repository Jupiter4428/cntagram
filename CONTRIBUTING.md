# Project Django (CN331)

คู่มือสำหรับสมาชิกทีม: ขั้นตอนทำงานแบบ Agile/Scrum, มาตรฐานโค้ด Django และเกณฑ์ส่งงาน (Definition of Done)
สรุปจากเนื้อหาวิชา CN331 สัปดาห์ที่ 1–6 อ่านให้จบก่อนเปิด Pull Request ครั้งแรก

> การตั้งค่าเครื่อง (Setup), Tech Stack, วิธี Sync โค้ด, โครงสร้างโปรเจค และ Branch Strategy ย้ายไปอยู่ที่ [README.md](./README.md)

## สารบัญ
1. [Agile Workflow](#agile-workflow-ก่อนจะส่งโค้ด)
2. [Scrum ของทีมเรา](#scrum-ของทีมเรา)
3. [Git ที่ต้องรู้](#git-ที่ต้องรู้)
4. [มาตรฐานโค้ด Django](#มาตรฐานโค้ด-django)
5. [Testing และการใช้ AI](#testing-และการใช้-ai-ช่วยเขียนโค้ด)
6. [Commit Message Convention](#-commit-message-convention)
7. [Pull Request และ Code Review](#pull-request-และ-code-review)
8. [Checklist ก่อนส่งโค้ด](#-checklist-ก่อนส่งโค้ด-ก่อนเปิด-pr)
9. [Database และ Models](#database-และ-models)

> Setup, Sync, Project Structure และ Branch Strategy: ดูที่ [README.md](./README.md)

---

## Agile Workflow (ก่อนจะส่งโค้ด)

ทีมใช้ Sprint-based development บน Agile/Scrum และติดตามงานด้วย **GitHub Projects (Kanban board)** + **Issues** + **Milestones (Sprint 1–3)**

### กระดาน Kanban

| คอลัมน์ | ความหมาย | ย้ายเข้าเมื่อ |
|---|---|---|
| **Backlog** | งานทั้งหมดที่ยังไม่เริ่ม | สร้าง issue ใหม่ |
| **Ready** | ผ่าน [Definition of Ready](#definition-of-ready-dor-พร้อมเริ่มทำ) และถูกเลือกเข้า Sprint | วางแผน Sprint เสร็จ |
| **In progress** | กำลังทำ (เปิด branch แล้ว) | เริ่มเขียนโค้ด |
| **In review** | เปิด PR รอเพื่อนตรวจ | เปิด PR |
| **Done** | ผ่าน [Definition of Done](#definition-of-done-dod-เสร็จจริง) และ merge แล้ว | merge PR |

- จำกัดงานที่ทำพร้อมกัน (WIP): แต่ละคนไม่ควรมีการ์ดใน **In progress** เกิน 1–2 ใบ
- ใน Backlog ตั้งชื่อ issue เป็น `US-XX: <ชื่อ story>` และผูกกับ Milestone ของ Sprint ที่จะทำ

### 1. หยิบงานจาก Backlog / Board
- เลือกงานจากคอลัมน์ **Ready** ตามลำดับความสำคัญ
- Assign ตัวเองเป็นผู้รับผิดชอบ แล้วย้ายการ์ดเป็น **In progress**

### 2. สร้าง Branch ใหม่จาก `develop`

**กฎสำคัญ: ทุกคนต้องสร้าง branch ของตัวเองใหม่ทุกครั้งที่เริ่มงาน ห้ามทำงานตรงบน `develop` หรือ `main` เด็ดขาด และห้ามใช้ branch ร่วมกับคนอื่น**

ตั้งชื่อ branch ตาม convention (ใส่เลข issue เพื่อให้สืบย้อนกลับได้):
```
feature/issue-<เลข>-<ชื่อ-feature>   เช่น feature/issue-12-course-form
bugfix/issue-<เลข>-<ชื่อ-bug>        เช่น bugfix/issue-31-null-email
hotfix/<ชื่อ-hotfix>                  เช่น hotfix/prod-crash
```
```bash
git switch develop
git pull origin develop
git switch -c feature/issue-12-course-form
```

### 3. พัฒนาและ Commit
- Commit บ่อยๆ เป็นก้อนเล็กๆ ที่มีความหมาย (1 commit = 1 เรื่อง)
- เขียน commit message ตาม [Commit Message Convention](#-commit-message-convention) เช่น
  ```
  feat: add login form validation
  fix: correct date format in invoice
  ```
- ก่อน commit ให้ดู `git diff --staged` ทุกครั้ง และรันเทสต์ (ดู [Testing](#testing-และการใช้-ai-ช่วยเขียนโค้ด))
  ```bash
  python manage.py test
  ```

### 4. Push และเปิด Pull Request (PR)

เมื่อทำงานใน branch ของตัวเองเสร็จแล้ว ให้ push ขึ้น branch ของตัวเองก่อน (ไม่ push ตรงเข้า `develop`/`main`/`master` เด็ดขาด):
```bash
git push -u origin feature/issue-12-course-form
```
- จากนั้นเปิด PR จาก branch ของตัวเองเข้า `develop` (**base = develop, compare = branch ของเรา**) และย้ายการ์ดเป็น **In review**
- กรอกตาม [PR Template](#pull-request-และ-code-review) ด้านล่าง: ทำอะไร, task/issue ไหน, วิธีทดสอบ, screenshot ถ้าแก้ UI

### 5. Code Review
- ต้องมีอย่างน้อย **1 คนรีวิวและ approve** ก่อน merge (วิชาแนะนำ 1–2 คน)
- แก้ตาม comment ที่ reviewer ให้มา
- ห้าม self-merge โดยไม่มีคน approve

### 6. Merge เข้า `develop`
- ใช้ **Squash and Merge** หรือ **Merge commit** ตามที่ทีมตกลงกัน
- ลบ branch ทิ้งหลัง merge เสร็จ แล้วทุกคนรัน [Sync](./README.md#ทุกครั้งที่-pull-โค้ดใหม่-sync-ก่อนเริ่มงาน)

> ⚠️ **ข้อควรรู้เรื่อง `Closes #N`:** GitHub ปิด issue อัตโนมัติจากคำว่า `Closes #N` ก็ต่อเมื่อ PR ถูก merge เข้า **default branch** ซึ่งตอนนี้คือ `main` แต่ PR ของทีมเรา merge เข้า `develop` ดังนั้นหลัง merge ให้ตรวจว่า issue ถูกปิดและการ์ดอยู่ **Done** แล้วจริง ถ้ายัง ให้ปิด/ย้ายเอง (หรือให้ทีมตกลงเปลี่ยน default branch เป็น `develop`)

### 7. อัปเดตสถานะ Task
- ย้ายการ์ดบน board เป็น **Done** (เมื่อผ่าน DoD เท่านั้น)
- งานมีแค่สองสถานะคือ "Done" กับ "Not Done" ไม่มี "เกือบเสร็จ"

### 8. Sprint Review / Retrospective
- นำงานที่เสร็จ (ซอฟต์แวร์ที่รันได้จริง) ไป demo ใน Sprint Review
- ร่วมพูดคุยใน Retrospective ว่าอะไรควรปรับปรุงในสปรินท์ถัดไป

---

## Scrum ของทีมเรา

### ทีมและบทบาท
| บทบาท | ใคร | หน้าที่ |
|---|---|---|
| **Product Owner (PO)** | อาจารย์ผู้สอน | จัดลำดับ Product Backlog, ตรวจรับงานทุก Sprint |
| **Scrum Master (SM)** | สมาชิกในทีม **หมุนเวียนทุก Sprint** | ดูแลกระบวนการ Scrum, ช่วยกำจัด blocker, ประสานการประชุม |
| **Developers** | ทุกคน (ทีมละ 5 คน) | ออกแบบ เขียน Model/View/Template/Test ร่วมกัน ไม่แบ่งงานแบบไซโล (ไม่มี "คน DB" หรือ "คน HTML" คนเดียว) |

### กิจกรรมประจำ Sprint (1–2 สัปดาห์)
| กิจกรรม | ทำอะไร | ผลลัพธ์ |
|---|---|---|
| **Sprint Planning** | เลือก User Stories จาก Backlog แตกเป็น Task ประเมิน Story Points | Sprint Goal + Sprint Backlog |
| **Daily Standup** (15 นาที) | ตอบ 3 ข้อ: เมื่อวานทำอะไร / วันนี้จะทำอะไร / ติดอะไรไหม | แผนวันนี้ + blocker |
| **Sprint Review** | demo ซอฟต์แวร์ที่รันได้จริงให้ PO ตรวจและให้ feedback | Backlog ที่ปรับแล้ว |
| **Sprint Retrospective** | อะไรดี / อะไรไม่ดี / ข้อตกลง 1–2 ข้อที่จะเปลี่ยนจริงในรอบหน้า | Action Items |

กฎของ Daily Standup: ห้ามถกปัญหาเทคนิคยาวๆ (ถ้าเจอ blocker ให้นัดคุยแยกหลังจบ), ห้ามมาสาย, ห้ามปกปิดปัญหา
กฎของ Retrospective: **Blameless** มองหากระบวนการที่ต้องแก้ ไม่ใช่จับผิดคน

### แผน 3 Sprint
| Sprint | เนื้อหาหลัก | สิ่งที่ส่งมอบ |
|---|---|---|
| **Sprint 1** | Authentication, Forms, Core Models, Dashboard | โครงสร้าง Models, ระบบสิทธิ์, หน้าจอ CRUD แรก, Backlog บน GitHub |
| **Sprint 2** | Business Logic, Unit Testing, CI/CD Pipeline | ฟีเจอร์หลัก, Unit Tests (**coverage > 80%**), CI/CD |
| **Sprint 3** | Security (OWASP), Cloud Deploy, Demo | ระบบสมบูรณ์ที่ปลอดภัยและ deploy บน Cloud Server |
| **Final** | Demo สัปดาห์ที่ 14 | Live Demo, Agile Metrics, ประเมินเพื่อนร่วมกลุ่ม |

คะแนนประเมินจากงานที่ส่งมอบจริงบน GitHub ในแต่ละ Sprint

### เขียน User Story
```
As a <บทบาท>,
I want <สิ่งที่ต้องการทำ>,
So that <ประโยชน์/คุณค่าที่ได้>
```
ตรวจคุณภาพด้วย **INVEST**: Independent, Negotiable, Valuable, Estimable, Small (จบใน 1 Sprint), Testable

**Acceptance Criteria (AC)** เขียนได้ 2 แบบ
```
# แบบ Checklist
- [ ] ระบบต้องตรวจว่าที่นั่งเหลือ > 0
- [ ] เมื่อสำเร็จ แสดงข้อความ "ลงทะเบียนสำเร็จ"

# แบบ Given-When-Then (แปลงเป็น automated test ได้ตรงๆ)
Given นักศึกษาล็อกอินแล้ว และรายวิชามีที่นั่งว่าง
When  กดปุ่ม "ยืนยันการลงทะเบียน"
Then  ระบบบันทึกข้อมูลและแสดงข้อความ "ลงทะเบียนสำเร็จ"
```

**ซอย story แบบ Vertical Slice** (ผู้ใช้ได้ฟีเจอร์ที่ใช้งานได้จริงทุก Sprint: UI + View + DB ในชิ้นเดียว) อย่าซอยตาม layer ("Sprint นี้ทำ HTML ทั้งหมด")

### Issue Template (`US-XX`)
```markdown
**Title:** US-04: Student Course Enrollment

## User Story
As a student, I want to enroll in a course via a form,
so that I secure my seat.

## Acceptance Criteria
- [ ] ...
- [ ] ... (อย่างน้อย 3–5 ข้อ)

## Priority (MoSCoW): Must / Should / Could / Won't
## Story Points: 5
## Tasks
- [ ] Model
- [ ] Form
- [ ] View (@login_required)
- [ ] Template
- [ ] Unit Test
```
ตั้ง Label (เช่น `enhancement`) และ Milestone (`Sprint N`) ทุกครั้ง

### จัดลำดับความสำคัญ (MoSCoW)
- **Must** ขาดไม่ได้ (เช่น Auth, ฟอร์มหลัก) / **Should** ควรมี / **Could** มีก็ดี เลื่อนได้ / **Won't** ไม่ทำรอบนี้
- Sprint 1 เน้น **Must Have ประมาณ 60–70%** ของขอบเขต เพื่อให้ได้ซอฟต์แวร์ที่เสร็จจริง

### ประเมินขนาดงานด้วย Story Points
- ใช้ลำดับ Fibonacci: `1, 2, 3, 5, 8, 13, 20, 40, 100` (Story Points คือขนาดสัมพัทธ์ ไม่ใช่ชั่วโมง และเทียบข้ามทีมไม่ได้)
- Story ที่ได้ **13 แต้มขึ้นไป ใหญ่เกินไป** ต้องแตกเป็น story เล็กก่อนเข้า Sprint
- ตกลง Reference Stories ร่วมกัน เช่น 1 แต้ม = เพิ่ม checkbox บนฟอร์มเดิม, 3 แต้ม = Form + View + Template พื้นฐาน, 5 แต้ม = logic ข้ามหลายส่วน (เช่น Register + Auth)
- **Planning Poker:** PO อธิบาย story → ทีมซักถาม → ทุกคนเปิดการ์ดพร้อมกัน → คนที่ให้สูง/ต่ำสุดอธิบายเหตุผล → โหวตซ้ำจนได้ข้อสรุป
- **Sprint 1 ยังไม่มีข้อมูล velocity อย่ารับงานเกินตัว** (ตัวอย่างในสไลด์: ประมาณ 15–20 แต้มรวมทั้งทีม)

### Definition of Ready (DoR): พร้อมเริ่มทำ
Story จะถูกดึงเข้า Sprint ได้ต่อเมื่อ
- [ ] เขียนเป็น User Story ครบ (Role, Action, Benefit)
- [ ] ผ่านเกณฑ์ INVEST (มีคุณค่าและเล็กพอ)
- [ ] มี Acceptance Criteria ชัดเจนอย่างน้อย 3–5 ข้อ
- [ ] มี Mockup UI หรือโครงสร้างฟิลด์ Data Model คร่าวๆ
- [ ] ไม่มี dependency ภายนอกที่ยังไม่เสร็จ
- [ ] ทีมประเมิน Story Points ร่วมกันแล้ว

### Definition of Done (DoD): เสร็จจริง
การ์ดจะย้ายเป็น **Done** ได้ต่อเมื่อครบทุกข้อ ("It works on my machine" ไม่นับว่าเสร็จ)
- [ ] โค้ดตามมาตรฐาน PEP 8 สะอาด มี docstring และไม่มี linter warning หรือ bug ร้ายแรง
- [ ] มี Automated Unit Tests และรันผ่านทั้งหมด
- [ ] ผ่าน Acceptance Criteria ครบทุกข้อของ story
- [ ] เปิด PR และผ่าน Peer Code Review อย่างน้อย 1 คน
- [ ] Merge เข้า `develop` ได้โดยไม่มี merge conflict

### แตก Story เป็น Task
ทุก story แตกเป็นงานเทคนิคตามลำดับนี้ แล้วติ๊กใน Issue
```
Model → Form → View (@login_required) → Template → Unit Test
```

### ข้อผิดพลาดที่ต้องเลี่ยงใน Sprint
1. **Overcommit:** รับงานมากเกินกำลังทีม
2. **Story ก้อนใหญ่:** ทำไม่เสร็จในรอบเดียว ไม่มีของส่งมอบ
3. **ต่างคนต่างทำ:** ไม่ push ไม่คุยใน Standup แล้วมารวมโค้ดตอนท้าย จนเกิด conflict มหาศาล
4. **ข้ามการเขียนเทสต์:** ระบบจะพังตอนเริ่มรวมระบบใน Sprint ถัดไป

---

## Git ที่ต้องรู้

### ก่อน commit
```bash
git status
git diff                 # แก้อะไรไปบ้าง (Working Dir vs Staging)
git diff --staged        # สิ่งที่กำลังจะถูก commit จริง
```
ดู diff ก่อนเสมอ เพื่อไม่เผลอ commit ไฟล์ส่วนเกิน, รหัสผ่าน หรือ secret key

### ยกเลิกสิ่งที่ทำผิด
```bash
git restore --staged app.py        # ถอนไฟล์ออกจาก Staging (เนื้อหาไฟล์ยังอยู่ ปลอดภัย)
git restore app.py                 # ⚠️ ทิ้งการแก้ไขที่ยังไม่ commit ทั้งหมด กู้คืนไม่ได้!
git commit --amend -m "feat: ..." # แก้ message / เพิ่มไฟล์ที่ลืมใน commit ล่าสุด
```
**ห้ามใช้ `--amend` กับ commit ที่ push ขึ้น remote แล้ว** เพราะ hash จะเปลี่ยนและ history ของเพื่อนในทีมจะไม่ตรงกัน

### `git add` เก็บ snapshot ณ ตอนที่พิมพ์
ถ้าแก้ไฟล์เพิ่มหลัง `git add` ไฟล์นั้นจะอยู่ทั้งใน Staging (เวอร์ชันเก่า) และ Modified (เวอร์ชันใหม่) ต้อง `git add` ซ้ำก่อน commit ไม่งั้นส่วนที่แก้ทีหลังจะไม่ถูกรวม

### `fetch` vs `pull`
- `git fetch` ดึงประวัติล่าสุดมาไว้ที่ `origin/develop` โดยไม่แตะไฟล์ของเรา (ใช้ `git diff develop origin/develop` ดูก่อน merge ได้)
- `git pull` = `fetch` + `merge`

### แก้ Merge Conflict
Conflict เกิดเมื่อสองคนแก้บรรทัดเดียวกัน เป็นเรื่องปกติของงานทีม ไม่ต้องตกใจ
```
<<<<<<< HEAD
    return amount * 0.07        ← โค้ดบน branch ที่เรายืนอยู่
=======
    return amount * 0.10        ← โค้ดจาก branch ที่กำลังนำมารวม
>>>>>>> feature/issue-12-course-form
```
1. เปิดไฟล์ใน VS Code เลือกโค้ดที่ถูก แล้วลบ `<<<<<<<`, `=======`, `>>>>>>>` ออกให้หมด
2. `git add <ไฟล์>`
3. `git commit -m "fix: resolve merge conflict in <ไฟล์>"`

ถ้าไม่แน่ใจว่าโค้ดฝั่งไหนถูก ให้คุยกับเจ้าของโค้ดอีกฝั่งก่อน อย่าเลือกมั่ว

---

## มาตรฐานโค้ด Django

หลักใหญ่: **Never trust user input**, แยกหน้าที่ให้ชัด (Model เก็บข้อมูล, View ตัดสินใจ, Template แสดงผล) และไม่เขียนซ้ำ (DRY)

### Models
- สืบทอด `models.Model` และ **เขียน `__str__()` ทุก Model** (Admin และ dropdown จะอ่านรู้เรื่อง)
- ใช้ `class Meta` กำหนด `ordering`, `verbose_name`, `verbose_name_plural` (ชื่อไทยต้องกำหนดพหูพจน์เอง ไม่งั้น Admin เติม "s" ให้)
- ฟิลด์ข้อความ **ไม่ใช้ `null=True`** ให้ใช้ `blank=True, default=""` (กัน NULL กับ "" ปนกัน) ข้อยกเว้นเดียวคือฟิลด์ที่ต้อง `unique=True` และเว้นว่างได้ เช่น `User.personal_email` ต้องเป็น `null=True` เพราะ `""` สองแถวจะชน unique กันเอง
  - `null=True` = ระดับฐานข้อมูล, `blank=True` = ระดับ validation ของ Form
- เงิน/เกรด/ค่าที่ต้องแม่นยำ ใช้ `DecimalField(max_digits=.., decimal_places=..)` **ห้ามใช้ `FloatField`**
- ตัวเลือกคงที่ใช้ `models.TextChoices`
- `ForeignKey` ต้องระบุ `on_delete` และ `related_name` เป็นพหูพจน์เสมอ
  - `CASCADE` เฉพาะข้อมูลลูกที่ผูกชีวิตกับแม่จริงๆ, `PROTECT` สำหรับข้อมูลโครงสร้าง/การเงิน, `SET_NULL` ต้องคู่กับ `null=True`
- M:N ที่ต้องเก็บข้อมูลเพิ่มของความสัมพันธ์ (วันที่, เกรด) ให้สร้างโมเดลกลางและใช้ `through=` พร้อม `unique_together` เพื่อกันลงทะเบียนซ้ำ
- สร้าง `indexes` เฉพาะฟิลด์ที่ค้นหา/กรองบ่อย (เพิ่มความเร็ว SELECT แต่ INSERT/UPDATE ช้าลงเล็กน้อย)
- ถ้าใช้ Custom User ให้อ้างอิงผ่าน `settings.AUTH_USER_MODEL` หรือ `get_user_model()` ไม่ import `User` ตรงๆ

```python
class Course(models.Model):
    code = models.CharField(max_length=10, unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    department = models.ForeignKey(
        "Department", on_delete=models.PROTECT, related_name="courses"
    )

    class Meta:
        ordering = ["code"]
        verbose_name = "รายวิชา"
        verbose_name_plural = "รายวิชาทั้งหมด"

    def __str__(self):
        return f"{self.code} - {self.title}"
```

> โค้ดตัวอย่างด้านบนใช้อธิบายสไตล์เท่านั้น ไม่ใช่ model จริงของโปรเจค (ของจริงอยู่ใน `catalog/models.py`)

**ลำดับแปลง ERD เป็นโค้ด:** (1) Model ที่ไม่มี FK ก่อน → (2) Model ที่มี FK + `on_delete` → (3) Junction Model → (4) Constraints/Indexes

### Migrations
```bash
python manage.py makemigrations   # สร้างไฟล์ migration จากการแก้ models.py
python manage.py migrate          # รันลงฐานข้อมูลจริง
python manage.py showmigrations   # [X] = รันแล้ว, [ ] = ยังไม่รัน
python manage.py sqlmigrate <app> 0001   # ดู SQL ที่จะรัน
```
- แก้ตารางผ่าน `models.py` เท่านั้น **ไม่แก้ฐานข้อมูลด้วย SQL เอง**
- **commit ไฟล์ใน `migrations/` ขึ้น Git ทุกครั้ง** (เป็นส่วนหนึ่งของโค้ด)
- **ห้ามลบโฟลเดอร์ `migrations/` หรือลบไฟล์ฐานข้อมูลเพื่อหนีปัญหา** เพราะเพื่อนร่วมทีมจะซิงก์ประวัติต่อไม่ได้
- เพิ่มฟิลด์ใหม่ให้ตารางที่มีข้อมูลอยู่ ต้องมี `default=...` (ฟิลด์บังคับ) หรือ `null=True, blank=True` (ฟิลด์ไม่บังคับ) ไม่งั้น `makemigrations` จะหยุดถาม
- สองคนสร้าง migration เลขเดียวกันคนละ branch (เช่น `0002_add_phone` กับ `0002_add_email`) จะขึ้น *Conflicting migrations* ให้แก้ด้วย
  ```bash
  python manage.py makemigrations --merge
  python manage.py migrate
  ```
- บน server จริงรันแค่ `migrate` ไม่รัน `makemigrations`

### URLs
- ทุก app มี `urls.py` ของตัวเอง ใช้ `include()` ใน root URLconf
- ประกาศ `app_name = '<app>'` และตั้ง `name=` ให้ทุก path
- **ห้าม hardcode URL** ใช้ `reverse('courses:course_detail', args=[pk])` ใน `.py` และ `{% url 'courses:course_detail' course.id %}` ใน template
- ชื่อใน converter ต้องตรงกับชื่อ argument ของ view ทุกตัวอักษร

```python
# courses/urls.py
app_name = "courses"
urlpatterns = [
    path("", views.course_list, name="course_list"),
    path("<int:pk>/", views.course_detail, name="course_detail"),   # view รับ (request, pk)
]
```

### Views (Function-Based)
- รับ `request` เป็นพารามิเตอร์แรก และ **ต้อง return `HttpResponse`** (หรือ `render`/`redirect`/`JsonResponse`) ห้าม return `None` หรือสตริงเปล่า
- ค้นหา object ด้วย `get_object_or_404()` แทน `try/except DoesNotExist`
- อ่าน query string ด้วย `request.GET.get('key', default)` ไม่ใช้ `request.GET['key']` (จะเกิด 500 เมื่อไม่มีคีย์)
- หน้าที่ต้องล็อกอินใช้ `@login_required` (ตั้ง `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL` ใน settings)
- **ตรวจความเป็นเจ้าของข้อมูล (กัน IDOR):** ผู้ใช้ A ต้องแก้ URL เป็นของ B แล้วทำอะไรไม่ได้
  ```python
  @login_required
  def cancel_enrollment(request, pk):
      enrollment = get_object_or_404(Enrollment, pk=pk)
      if enrollment.student != request.user and not request.user.is_staff:
          raise PermissionDenied
      ...
  ```
- Logout ต้องเป็น **POST** (`@require_POST`) พร้อมปุ่มฟอร์มและ `{% csrf_token %}`
- แจ้งผลให้ผู้ใช้ด้วย `django.contrib.messages` (`messages.success(request, "...")`)
- รหัสผ่านใช้ `set_password()` / `authenticate()` ไม่เก็บหรือเทียบ plaintext เอง

### Forms
- **ไม่อ่าน `request.POST` ดิบๆ** ให้ใช้ `forms.Form` หรือ `forms.ModelForm` เสมอ (ได้ validation, type coercion, error message และกัน XSS ในตัว)
- รูปแบบมาตรฐานของ view ที่รับฟอร์ม + **Post/Redirect/Get** (สำเร็จแล้ว `redirect()` เสมอ กัน refresh แล้วส่งซ้ำ):
  ```python
  def course_create(request):
      if request.method == "POST":
          form = CourseModelForm(request.POST)
          if form.is_valid():
              course = form.save()
              return redirect("courses:course_detail", pk=course.pk)
      else:
          form = CourseModelForm()
      return render(request, "courses/course_form.html", {"form": form})
  ```
- `ModelForm` ต้องระบุ `fields = [...]` ชัดเจน **ห้ามใช้ `fields = '__all__'`** กับฟอร์มสาธารณะ (กัน Mass Assignment)
- ต้องใส่ข้อมูลเพิ่ม (เช่น `created_by`) ใช้ `form.save(commit=False)` แล้วตั้งค่า, `obj.save()`, และ `form.save_m2m()` ถ้ามีฟิลด์ M:N
- แก้ข้อมูลเดิมส่ง `instance=obj` ทั้งตอน POST และ GET
- `clean_<field>()` ต้อง **`return` ค่ากลับเสมอ**, ตรวจข้ามฟิลด์ใช้ `clean()` + `super().clean()` + `self.add_error(...)`

### Templates
- ใช้ **Template Inheritance:** `base.html` เจาะช่อง `{% block %}`, หน้าลูกขึ้นต้นด้วย `{% extends 'base.html' %}` เป็น **บรรทัดแรกสุดของไฟล์**
- ชิ้นส่วนที่ใช้ซ้ำแยกเป็น partial ชื่อขึ้นต้นด้วย `_` เช่น `_navbar.html`, `_course_card.html` แล้ว `{% include %}`
- **ทุกฟอร์ม `method="post"` ต้องมี `{% csrf_token %}`** (ขาดจะได้ 403)
- Template ใช้แสดงผลเท่านั้น ไม่ใส่ logic/การ query ซับซ้อน; เรียก method ได้เฉพาะที่ไม่มีพารามิเตอร์ และห้ามใส่ `()`
- **ห้ามใช้ `|safe` กับข้อมูลที่มาจากผู้ใช้** (คอมเมนต์, ชื่อ, ค่าจากฟอร์ม) เพราะปิดระบบกัน XSS
- ไฟล์ static ใช้ `{% load static %}` + `{% static 'css/app.css' %}` ไม่ hardcode path
- ใช้ `{% for %}...{% empty %}...{% endfor %}` แทนการครอบ `{% if %}` เอง
- UI ใช้ **Bootstrap 5** (Grid 12 คอลัมน์: `col-12 col-md-6 col-lg-4`), ใส่ class ให้ widget ของฟอร์มผ่าน `attrs` หรือ `django-crispy-forms`

### ความปลอดภัย (สรุป)
| ภัย | วิธีป้องกันในโปรเจคเรา |
|---|---|
| SQL Injection | ใช้ Django ORM เสมอ ห้ามต่อสตริงสร้าง SQL เอง |
| XSS | Auto-escaping ของ DTL, ไม่ใช้ `\|safe` กับ user input |
| CSRF | `{% csrf_token %}` ทุกฟอร์ม POST |
| Broken Access Control / IDOR | `@login_required` + ตรวจความเป็นเจ้าของใน view |
| Secret รั่ว | เก็บใน `.env` ไม่ commit |

ใน Sprint 3 ทีมต้องตรวจรอบสุดท้ายตาม **OWASP Top 10**

---

## Testing และการใช้ AI ช่วยเขียนโค้ด

### Testing
```bash
python manage.py test                 # รันทั้งหมด
python manage.py test courses         # รันเฉพาะ app
```
- ทุกฟีเจอร์ต้องมี Unit Test (เป็นส่วนหนึ่งของ DoD) และต้องผ่าน **100%** ก่อนเปิด PR
- ควรเทสต์อย่างน้อย: validation ของ Form, view ที่ต้องล็อกอิน (ไม่ล็อกอินต้อง redirect), สิทธิ์ของเจ้าของข้อมูล, และ logic ใน Model
- เป้าหมาย Sprint 2: **coverage > 80%**
  ```bash
  pip install coverage
  coverage run manage.py test && coverage report
  ```
- แนวทาง TDD: เขียนเทสต์ก่อน แล้วค่อยเขียนฟังก์ชันจริง (ไม่บังคับ แต่แนะนำ)
- commit เทสต์ด้วย type `test:`

### การใช้ AI (Copilot, Cursor ฯลฯ)
AI เขียนโค้ดเร็วขึ้นมาก แต่ **คอขวดย้ายไปที่การตรวจสอบ** AI อาจสร้างข้อมูลมั่ว (hallucination) และช่องโหว่ความปลอดภัยโดยไม่รู้ตัว กฎของทีม:
1. **คุณรับผิดชอบโค้ดที่เพิ่มเข้ามา 100%** ข้อผิดพลาดของ AI คือข้อผิดพลาดของคุณ
2. **ห้ามนำโค้ดจาก AI ไปใช้โดยไม่รันชุดทดสอบ**
3. สมาชิกทุกคนต้อง **อธิบายโค้ดทุกส่วนที่ push ขึ้น GitHub ได้** แม้ AI จะเป็นคนเขียน (Peer Review จะถาม)
4. ใช้เวลากับขั้น Requirements/Design (สเปกที่ชัดเจนสั่ง AI ได้แม่นกว่า) และขั้น Test/Review ให้มากขึ้น
5. ตั้ง `.cursorrules` (หรือไฟล์กฎของเครื่องมือที่ใช้) ในโปรเจค เพื่อให้ AI ทำตามมาตรฐานเดียวกับทีม ตัวอย่าง:
   ```
   - Python 3.12, Django 5.x, Function-Based Views, Bootstrap 5
   - ทุก Model ต้องมี __str__ และ class Meta
   - ห้าม raw SQL, ห้าม fields='__all__', ห้าม |safe กับ user input
   - ใช้ get_object_or_404, reverse()/{% url 'ns:name' %}, ไม่ hardcode URL
   - ทุกฟอร์ม POST ต้องมี {% csrf_token %}; view ที่ต้องล็อกอินใช้ @login_required
   - เขียน unit test ประกอบทุกฟีเจอร์ commit ตาม Conventional Commits
   ```

---

## 📝 Commit Message Convention

ทีมใช้รูปแบบ [Conventional Commits](https://www.conventionalcommits.org/) เพื่อให้ประวัติ commit อ่านง่ายและตรวจสอบย้อนหลังได้

### รูปแบบ
```
<type>: <คำอธิบายสั้นๆ>

[รายละเอียดเพิ่มเติม (ถ้าจำเป็น)]
```

### Type ที่ใช้
| Type | ใช้เมื่อ | ตัวอย่าง |
|---|---|---|
| `feat` | เพิ่มฟีเจอร์ใหม่ | `feat: add user login page` |
| `fix` | แก้บั๊ก | `fix: correct date format in invoice` |
| `docs` | แก้ไขเอกสารเท่านั้น (README, CONTRIBUTING ฯลฯ) | `docs: update setup instructions` |
| `style` | ปรับ format/โค้ดสไตล์ที่ไม่กระทบการทำงาน (เว้นวรรค, semicolon, CSS ล้วนๆ) | `style: format views.py with black` |
| `refactor` | ปรับโครงสร้างโค้ดโดยไม่เพิ่มฟีเจอร์และไม่แก้บั๊ก | `refactor: extract order logic into service` |
| `perf` | ปรับปรุงประสิทธิภาพ | `perf: add index to product table` |
| `test` | เพิ่มหรือแก้ไข test | `test: add unit tests for login form` |
| `chore` | งานจุกจิกที่ไม่เกี่ยวกับโค้ดหลัก (อัปเดต dependency, แก้ config) | `chore: update requirements.txt` |
| `build` | เปลี่ยนแปลงระบบ build หรือ dependency ภายนอก | `build: upgrade Django to 5.0` |
| `ci` | แก้ไข CI/CD pipeline | `ci: add GitHub Actions test workflow` |
| `revert` | ย้อน commit ก่อนหน้า | `revert: revert "feat: add user login page"` |

### กฎการเขียน
- ใช้ **type เป็นตัวพิมพ์เล็กทั้งหมด** ตามด้วย `:` และเว้นวรรค 1 ครั้ง
- คำอธิบายขึ้นต้นด้วย **คำกริยา** (add, fix, update, remove ...) และไม่ต้องลงท้ายด้วยจุด
- ความยาวบรรทัดแรกไม่ควรเกิน **72 ตัวอักษร**
- **1 commit = 1 เรื่อง** อย่ารวมหลายงานไว้ใน commit เดียว
- ถ้าต้องการระบุขอบเขต สามารถใส่ scope ในวงเล็บได้ เช่น `feat(auth): add password reset`
- ถ้าเกี่ยวข้องกับ task ให้อ้างอิงใน body หรือท้าย message เช่น `Refs #12`

### ตัวอย่างที่ดี ✅
```
feat: add login form validation
fix(auth): prevent null email on signup
docs: add commit message convention
refactor: split views into separate modules
chore: remove unused imports
```

### ตัวอย่างที่ไม่ดี ❌
```
update                    # ไม่มี type และไม่บอกว่าแก้อะไร
fixed errors              # ไม่มี type ไม่ชัดเจน
Fix bug.                  # type ตัวพิมพ์ใหญ่, ไม่ชัดเจน, มีจุดท้ายประโยค
feat:add stuff and fix x  # ไม่เว้นวรรค และรวมหลายเรื่องใน commit เดียว
```

---

## Pull Request และ Code Review

### PR Template
```markdown
## Summary of Changes
- ทำอะไรไป (เช่น เพิ่ม CourseModelForm พร้อม Bootstrap 5)
- validation/logic สำคัญที่เพิ่ม

## วิธีทดสอบ
1. ...
2. รัน `python manage.py test`

## Screenshot (ถ้าแก้ UI)

Closes #12
```

### หน้าที่ของผู้เปิด PR (Author)
- อธิบายเจตนาของ PR และสิ่งที่แก้ให้ชัดเจน
- แนบ screenshot ถ้ามีการปรับ UI/Frontend
- ตรวจว่า automated tests ผ่านทั้งหมด **ก่อน** ขอ review
- merge/rebase `develop` ล่าสุดเข้า branch ตัวเองก่อนเปิด PR

### หน้าที่ของผู้ตรวจ (Reviewer)
- **อ่านและเข้าใจตรรกะของโค้ด** ไม่ใช่แค่กด Approve
- ตรวจความถูกต้อง สไตล์โค้ด เคสที่อาจเกิดบั๊ก ความปลอดภัย (input validation, สิทธิ์, CSRF)
- ให้คำแนะนำอย่างสร้างสรรค์และสุภาพ (Constructive Feedback)

### ขั้นตอนใน GitHub
**Author:** push branch → เข้าหน้า repo กดแถบเหลือง **"Compare & pull request"** → ตั้ง base เป็น `develop` → กรอก Title/Description → **Create pull request**
**Reviewer:** แท็บ **Files changed** อ่าน diff → **Submit review** → เลือก **Approve** (หรือ **Request changes**)
เมื่อ approve ครบ กด **Merge pull request**

---

## ✅ Checklist ก่อนส่งโค้ด (ก่อนเปิด PR)

- [ ] Pull โค้ดล่าสุดจาก `develop` และ merge/rebase เข้า branch ตัวเองแล้ว
- [ ] รันโค้ดแล้วไม่มี error
- [ ] เขียน unit test ประกอบฟีเจอร์ และรัน test ผ่านทั้งหมด
- [ ] ผ่าน Acceptance Criteria ครบทุกข้อของ story
- [ ] ไม่มีไฟล์ `.env`, `db.sqlite3`, หรือไฟล์ credential หลุดไปใน commit (เช็ค `git diff --staged`)
- [ ] Commit message สื่อความหมายชัดเจน และตรงตาม Commit Message Convention
- [ ] ถ้าแก้ Model: มีไฟล์ migration ที่ commit แล้ว และไม่ได้ลบ/แก้ migration เก่าที่คนอื่นรันไปแล้ว
- [ ] อัปเดต `requirements.txt` ถ้ามีการติดตั้ง package ใหม่
- [ ] โค้ดตาม PEP 8 มี docstring และลบ debug code / print ที่ไม่จำเป็นออก
- [ ] ทุกฟอร์ม POST มี `{% csrf_token %}` และหน้าที่ต้องล็อกอินมี `@login_required`
- [ ] ย้ายสถานะ task บน board ให้ตรงกับความคืบหน้าจริง (PR → **In review**)

---

## Database และ Models

โครงสร้างตารางอ้างอิงจาก `database-design.md` (ERD 3NF, SP-0) ถ้าจะเพิ่ม/แก้ตาราง ให้แก้ไฟล์นี้กับ `models.py` **ใน PR เดียวกัน** ไม่ให้เอกสารกับโค้ดเพี้ยนกัน

### แบ่ง app (Sprint 1)
| App | Models | Story |
|---|---|---|
| `accounts` | `User`, `Role`, `UserRole` | US-1, US-2 |
| `catalog` | `Department`, `Batch`, `Course`, `BatchCourse`, `SystemSetting` | US-3, US-4 |
| `documents` | `DocType`, `ExamPeriod`, `Document`, `ExamDetail`, `DocumentVersion` | US-5 |

- ตาราง Sprint 2 (`approval`, `download_log`, `audit_log`, `report`, `doc_type_required_role`) ยังไม่มีใน `models.py` ให้ตกลง app ปลายทางตอน Sprint 2 Planning
- ลำดับพึ่งพา: `catalog` ไม่พึ่ง app ใดเลย → `accounts` พึ่ง `catalog` → `documents` พึ่งทั้งสอง
- อ้างข้าม app ด้วย **string** เช่น `"catalog.Department"` และอ้างผู้ใช้ด้วย `settings.AUTH_USER_MODEL` ห้าม import model ข้าม app ที่หัวไฟล์ `models.py` (กัน circular import)

### ข้อตกลงที่ห้ามฝ่าฝืน
- **User:** login ด้วย `email` (`USERNAME_FIELD`), ฟิลด์ `password` ของ Django คือ `password_hash` ใน ERD (เก็บเป็น hash อยู่แล้ว), `is_staff` เพิ่มเพื่อเข้า Django admin สร้างผู้ใช้ด้วย `User.objects.create_user(email, password, student_id=..., nickname=..., department=...)` เท่านั้น
- **ค่าที่คำนวณได้ห้ามเก็บเป็น column (3NF):** รหัสรุ่น `CN21` ใช้ `Batch.code`, ปีเข้าใช้ `User.entry_year`, เวอร์ชันล่าสุดใช้ `Document.current_version` ส่วนจำนวนดาวน์โหลดจะนับจาก `download_log` (Sprint 2)
- **FK ทุกเส้นเป็น `on_delete=PROTECT`:** ลบข้อมูลที่ถูกอ้างอยู่จะเกิด `ProtectedError` ต้องดักใน view แล้วแสดงข้อความภาษาไทย (ตรงกับ AC ของ US-3/US-4)
- **`UserRole.department`:** ใช้เฉพาะ role `moderator` (ภาคที่ดูแล) role อื่นเป็น `NULL` SQL ถือว่า `NULL ≠ NULL` จึงแยก UNIQUE เป็น 2 constraint (`uq_userrole_with_dept` / `uq_userrole_without_dept`) อย่ารวมกลับเป็นอันเดียว
- **ฟิลด์ตัวเลือก** (`vault`, `status`, `scan_status`) ใช้ `TextChoices` คู่กับ `CheckConstraint` ถ้าเพิ่มค่าใหม่ต้องแก้ **ทั้งสองที่** แล้วสร้าง migration
- `Role`, `DocType`, `ExamPeriod` ใช้ `SmallAutoField` ส่วน `ExamDetail` ใช้ `document` เป็น PK (OneToOne)

### DB บังคับให้ vs. ต้องเขียนเอง
| DB บังคับให้แล้ว (อย่าเขียนซ้ำ) | ต้องเขียนใน form/view/service |
|---|---|
| รุ่นซ้ำในภาคเดียวกัน, วิชาซ้ำในรุ่นเดียวกัน, เวอร์ชันซ้ำของเอกสาร | อีเมลต้องเป็น `@student.tu.ac.th` และดึง `student_id` จาก local part ของอีเมล (US-1) |
| `size_bytes` ≤ 50 MB, `status`/`vault`/`scan_status` นอกค่าที่กำหนด | ผู้ใช้อัปโหลดได้เฉพาะภาควิชาของตัวเอง ฝั่ง server ต้องเช็กด้วย (US-5) |
| ลบ Department/Batch/Course ที่ยังถูกอ้างอยู่ไม่ได้ | รุ่น ≤ `legacy_batch_max` ให้ Super Admin เท่านั้น |
| รูปแบบ `student_id` (10 หลัก, ตัวที่ 3–4 = `10`) เมื่อเรียก `full_clean()`/ผ่าน ModelForm (ไม่ใช่ระดับ DB) | role `moderator` ต้องมี `department`, Super Admin ต้องมีอย่างน้อย 2 คน |

### `SystemSetting` (ค่ากำหนดปรับได้โดยไม่ deploy ใหม่)
| key | ค่าเริ่มต้น | ใช้ทำอะไร |
|---|---|---|
| `legacy_batch_max` | `23` | รุ่นที่ ≤ ค่านี้ ให้ Super Admin จัดการเท่านั้น |
| `max_upload_mb` | `50` | ขนาดไฟล์สูงสุดตอนอัปโหลด |

```python
from catalog.models import SystemSetting

legacy_max = SystemSetting.get_int("legacy_batch_max", 23)   # คืนค่า default ถ้ายังไม่มีแถวนี้
```
ข้อควรระวัง: `DocumentVersion` มี CHECK ขนาดไฟล์ 50 MB แบบ**ตายตัว** (`MAX_UPLOAD_BYTES` ใน `documents/models.py`) การแก้ `max_upload_mb` ใน DB ไม่เปลี่ยน CHECK นี้ ถ้าจะลดให้เช็กใน form ด้วย `get_int` ถ้าจะเพิ่มเกิน 50 MB ต้องแก้ค่าคงที่และสร้าง migration

### ข้อมูลตั้งต้น (seed) ที่ระบบต้องมี
| ตาราง | ข้อมูล |
|---|---|
| `Department` | CN, CE, ME, EE (ตาม AC ของ US-3) |
| `Role` | `student`, `alumni`, `moderator`, `super_admin` |
| `DocType` | `summary`, `cheatsheet`, `slide` (vault = `lecture`) และ `exam` (vault = `exam`) |
| `ExamPeriod` | `midterm`, `final` |
| `SystemSetting` | `legacy_batch_max`, `max_upload_mb` ตามตารางด้านบน |

ตอนนี้ยังไม่มี script seed อัตโนมัติ ให้ใส่ผ่าน Django admin หรือ `manage.py shell` ถ้าจะทำเป็น data migration หรือ management command ให้เปิด issue ก่อน

### Migration รอบแรก (`0001`)
- ให้ **ผู้ดูแล ERD คนเดียว** สร้างและ push `0001_initial` ของ `accounts`, `catalog`, `documents` ใน PR แรก คนอื่นรอ PR นั้น merge แล้ว `pull` + `migrate` เท่านั้น **ห้ามรัน `makemigrations` เองก่อนหน้านั้น** ไม่งั้นจะได้ 0001 คนละชุดและชนกัน
  ```bash
  python manage.py makemigrations accounts catalog documents
  python manage.py migrate
  ```
- ถ้าเครื่องคุณเคย `migrate` ก่อนมี `AUTH_USER_MODEL` จะเจอ `InconsistentMigrationHistory` กรณีนี้เท่านั้นที่ให้ลบ `db.sqlite3` (ไฟล์ในเครื่องคุณ ไม่อยู่ใน Git) แล้ว `migrate` ใหม่ได้ (ต้อง seed ใหม่ด้วย) ส่วนโฟลเดอร์ `migrations/` **ยังห้ามลบ** ตามกฎด้านบน