# บทที่ 3 วิธีดำเนินงาน

> แหล่งข้อมูล: [`CONTRIBUTING.md`](../../CONTRIBUTING.md) (Scrum, DoR/DoD, Workflow, Testing) · [`requirements.md`](../requirements.md) · [`database-design.md`](../database-design.md) · [ADR 0001](../adr/0001-modular-monolith-and-app-boundaries.md), [ADR 0002](../adr/0002-service-layer-and-selectors.md) · [`architecture/c4.md`](../architecture/c4.md) · โค้ดใน `catalog/`, `accounts/`, `materials/`
>
> บทนี้ยาวที่สุดและมีข้อมูลพร้อมแล้วมากที่สุด เวลาเรียบเรียงลงเล่มให้ใช้ตาราง/รูปจากเอกสารต้นทางโดยตรง แล้วเขียนคำอธิบายประกอบ

## 3.1 กระบวนการพัฒนาซอฟต์แวร์

### 3.1.1 ทีมและบทบาท Scrum

| บทบาท | ผู้รับผิดชอบ | หน้าที่ |
|---|---|---|
| Product Owner | อาจารย์ผู้สอน | จัดลำดับ Product Backlog และตรวจรับงานใน Sprint Review |
| Scrum Master | สมาชิกในทีม หมุนเวียนทุก Sprint | ดูแลกระบวนการ นำประชุม กำจัด blocker ดูแล Burndown |
| Developers | สมาชิกทั้ง 5 คน | ออกแบบและพัฒนาทุกชั้นร่วมกัน ไม่แบ่งงานแบบไซโล |

**[เติม: ชื่อ Scrum Master ของแต่ละ Sprint]**

### 3.1.2 วงรอบ Sprint (รูปที่ 3.x)

Sprint Planning (คำนวณ Velocity, ตั้ง Sprint Goal, ดึง story ที่ผ่าน DoR) → Daily Standup 15 นาที (เมื่อวาน/วันนี้/ติดอะไร) และอัปเดต Burndown → Sprint Review (Live demo ตาม AC และ DoD) → Sprint Retrospective (Start/Stop/Continue หรือ 4Ls แบบ Blameless, Action Items 1–2 ข้อ) → Sprint ถัดไป

### 3.1.3 เกณฑ์คุณภาพ (ตารางที่ 3.4)

- **Definition of Ready:** User Story ครบ 3 ส่วน, ผ่าน INVEST และไม่เกิน 8 แต้ม, AC 3–5 ข้อ, ประเมินแต้มร่วมกันแล้ว, มี mockup หรือรายการฟิลด์, dependency พร้อม
- **Definition of Done:** ผ่าน AC ครบ, มี automated test ผ่านทั้งหมด, PR ได้ approve ≥ 1 คน, merge เข้า `develop` ไม่พัง migration, view บาง/logic อยู่ใน service, ไม่มี N+1 query และ circular import, ผ่าน security พื้นฐาน, PEP 8 + docstring, รันบนเครื่องอื่นได้, อัปเดตเอกสารที่เกี่ยวข้อง
- งานที่เสร็จ 99% นับเป็น 0 Story Points

### 3.1.4 การจัดการ Source Code และ Workflow

- Git branch strategy: `main` (production) / `develop` (integration, default branch) / feature branch แตกจาก `develop`
- Pull Request + Peer Code Review ทุกงาน ใช้ PR template และ Issue template (Feature Story, Bug Report, Tech Debt) ใน `.github/`
- Commit message ตาม Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:` ฯลฯ)
- GitHub Projects เป็น Scrum board พร้อม custom fields (Story Points, Sprint, Track)
- กติกาการใช้ AI ช่วยเขียนโค้ด: ผู้ commit รับผิดชอบ 100%, ต้องรันเทสต์และอธิบายโค้ดได้ทุกบรรทัด

**[ตรวจ: ถ้าส่วนนี้ยาวเกินสำหรับเล่ม ย้ายรายละเอียดไปภาคผนวก]**

## 3.2 การเก็บและวิเคราะห์ความต้องการ

### 3.2.1 จาก SRS สู่ Product Backlog

ในช่วงแรกทีมเขียน **SRS v1** แบบดั้งเดิมที่ล็อกความต้องการเป็นข้อ FR/NFR และกฎธุรกิจ (R-1 – R-6) ตั้งแต่ต้น ต่อมา (2026-10-12) ทีมเปลี่ยนเป็น **Product Backlog แบบ Agile** ด้วยเหตุผล:
- ความต้องการที่ล็อกล่วงหน้าขัดกับหลัก Negotiable ของ User Story และทำให้ปรับตาม Sprint Review ไม่ได้
- รายละเอียดควรถูกเขียน "เท่าที่จำเป็น เมื่อจำเป็น" (story ที่ใกล้เข้า Sprint จึงลงรายละเอียด)

การแปลง: FR → Epic/User Story, NFR → DoD / AC / Spike, กฎที่เคยล็อก → "ประเด็นที่ต้องคุย" ใต้ story, ประเด็นค้าง (O-1 – O-7) → story/spike

> ประเด็นนี้เป็น**จุดเด่นสำหรับอภิปรายในบทที่ 5** (บทเรียนเรื่อง requirement engineering ใน Agile) — **[เติม: ผลกระทบที่สังเกตได้จริงหลังเปลี่ยน]**

### 3.2.2 ผู้ใช้ระบบ (ตารางที่ 3.1)
ดู [`requirements.md` §3](../requirements.md#3-ผู้ใช้-roles): Guest, Student, Alumni, Moderator, Super Admin

### 3.2.3 Epic และ Product Backlog (ตารางที่ 3.2)

| Epic | คุณค่าที่ผู้ใช้ได้ | Story |
|---|---|---|
| E1 เข้าระบบอย่างปลอดภัย | เฉพาะคนในคณะเข้าได้ ศิษย์เก่าใช้ต่อได้ | US-1, US-2, US-11 – US-14 |
| E2 โครงสร้างคลัง | จัดตาม ภาค → รุ่น → วิชา ขยายภาคได้ | SP-0, US-3, US-4, US-15 – US-18 |
| E3 แบ่งปันเอกสาร | อัปโหลดเข้าที่ถูกต้องได้ง่าย | US-5, US-19 – US-22 |
| E4 คัดกรองคุณภาพ | ตรวจก่อนเผยแพร่ ข้อสอบคุมเข้มกว่า | US-6, US-9, US-10, US-23 – US-25 |
| E5 ค้นหาและอ่าน | พิมพ์รหัสวิชาแล้วเจอทุกรุ่นในหน้าเดียว | US-7, US-8, US-26, US-27 |
| E6 ชุมชน | ถาม-ตอบ แจ้งจุดผิด ให้คะแนน | US-28 – US-30 |
| E7 ลิขสิทธิ์และความไว้วางใจ | รายงาน/แจ้งลบได้ ตรวจย้อนหลังได้ | US-31 – US-33 |
| TD งานเทคนิค | ส่งมอบเร็วและมั่นคงขึ้น | TD-1 – TD-5 |

Sprint 1 commit 11 รายการ (SP-0, US-1 – US-10) เปิดเป็น GitHub issue #23 – #33
**[เติม: Story Points ของแต่ละรายการจาก issue]**

Spike ที่ต้องค้นคว้าก่อนตัดสินใจ: SP-1 สแกนไฟล์อันตราย/ไวรัส, SP-2 บริการส่งอีเมล/OTP, SP-3 preview PDF ไม่เปิด Direct URL, SP-4 สถานที่ deploy และการสำรองข้อมูล

### 3.2.4 ความต้องการด้านคุณภาพ (Non-Functional)

| ด้าน | เป้าตั้งต้น | กลไกที่ตรวจ |
|---|---|---|
| ความปลอดภัยพื้นฐาน (CSRF, XSS, SQLi, ตรวจสิทธิ์ฝั่ง server) | ทุก story | DoD |
| ไม่มี N+1 query | ทุกหน้าที่แสดงรายการ | DoD |
| ความเร็วหน้าค้นหา | ~2 วินาที | AC ของ US-7 |
| ใช้งานบนมือถือ | จอ ~360px, ภาษาไทย | AC ของ story ที่มีหน้าจอ |
| PDPA | ขอความยินยอม, ไม่แสดงอีเมล, ลบบัญชีได้ | AC ของ US-1, US-13 |
| Test coverage | > 80% | Sprint 2 Goal / TD-1 |
| ความพร้อมใช้งาน | ~99%/เดือน, สำรองวันละครั้ง | SP-4 |
| OWASP Top 10 | ตรวจรอบสุดท้าย | Sprint 3 |

## 3.3 การออกแบบสถาปัตยกรรมระบบ

### 3.3.1 System Context และ Container (รูปที่ 3.1, 3.2)
ดู [`architecture/c4.md`](../architecture/c4.md) — ผู้ใช้ 5 กลุ่มเข้าระบบผ่าน HTTPS, ระบบประกอบด้วย Django application (Modular Monolith), ฐานข้อมูล (SQLite ช่วงพัฒนา / PostgreSQL production), File Storage ที่ไม่เปิด Direct URL, และระบบภายนอกที่ยังรอ Spike (Email Service, Virus Scanner)

### 3.3.2 Modular Monolith และขอบเขต App (รูปที่ 3.3) — ADR 0001

| App | ความรับผิดชอบ | Model |
|---|---|---|
| `catalog` | โครงสร้างภาควิชา รุ่น รายวิชา และค่ากำหนดระบบ | Department, Batch, Course, BatchCourse, SystemSetting |
| `accounts` | ผู้ใช้ บทบาท และสิทธิ์ | User, Role, UserRole |
| `materials` | เอกสาร ไฟล์ และเวอร์ชัน | DocType, ExamPeriod, Document, ExamDetail, DocumentVersion |

ทิศทาง dependency ทางเดียว `catalog` ← `accounts` ← `materials`; FK ข้าม app อ้างด้วย string และ `settings.AUTH_USER_MODEL`
ทางเลือกที่ไม่เลือก: app เดียว (God App), 1 model ต่อ 1 app, Microservices — เหตุผลใน ADR 0001

### 3.3.3 การแยกชั้นภายใน App (รูปที่ 3.4) — ADR 0002

`views.py` / `forms.py` → `services.py` (เขียน, กฎธุรกิจ, transaction) / `selectors.py` (อ่านอย่างเดียว, ปรับ query) → `models.py` (schema, constraint, ความถูกต้องระดับแถว)

เหตุผล: ทดสอบกฎธุรกิจได้โดยไม่ผ่าน HTTP, ใช้ logic ซ้ำระหว่างหน้าเว็บกับ Bulk Import/management command ได้, ไม่มี side-effect ซ่อนใน `Model.save()`

## 3.4 การออกแบบฐานข้อมูล

ดูรายละเอียดเต็มใน [`database-design.md`](../database-design.md) (ใส่ data dictionary ฉบับเต็มในภาคผนวก)

### 3.4.1 ERD (รูปที่ 3.5)
ตาราง 20 ตารางใน 6 กลุ่ม: โครงสร้างภาควิชา, ผู้ใช้และสิทธิ์, เอกสารและไฟล์, ตั้งค่าและกฎ, การอนุมัติและตรวจสอบ, ชุมชน

### 3.4.2 กระบวนการ Normalization
UNF (ตารางเดียวจากตัวอย่างใน SRS v1) → 1NF (แยก `user_role`, `approval` ออกจากช่องหลายค่า) → 2NF (แยก `course`, `department`, `batch_course`) → 3NF (ไม่เก็บรหัสรุ่น `CN21` และปีเข้า เพราะคำนวณได้, ย้าย `vault` ไป `doc_type`, แยก `exam_detail` 1:1) → ตรวจ BCNF

### 3.4.3 การตัดสินใจออกแบบที่สำคัญ (ตารางที่ 3.3)
- เก็บกฎอนุมัติเป็นข้อมูล (`doc_type_required_role`) และค่ากำหนดใน `system_setting` (เช่น `legacy_batch_max` = 23, `max_upload_mb` = 50) — เปลี่ยนกฎได้โดยไม่แก้โค้ดหรือ deploy ใหม่
- แยก `document` กับ `document_version` — รองรับหลายเวอร์ชันโดยประวัติไม่หาย
- partial unique index 2 ชุดบน `user_role` แก้ปัญหา `NULL ≠ NULL` ใน UNIQUE
- ลบผู้ใช้ตาม PDPA ด้วยการ anonymize เพราะ FK เป็น `PROTECT`
- จุดที่ตั้งใจไม่ normalize: polymorphic reference ใน `audit_log`, enum `status`, `approval.approver_role_id`

### 3.4.4 การบังคับกฎใน 3 ชั้น
| ชั้น | ตัวอย่างกฎ |
|---|---|
| ฐานข้อมูล (PK/FK/UQ/CHECK) | รุ่นซ้ำในภาคเดียวกัน, ขนาดไฟล์ 0 < x ≤ 50 MB, ปี พ.ศ. 2500–2700, สถานะนอกค่าที่กำหนด |
| Model (`clean()`/`save()`) | อีเมล @student.tu.ac.th + รหัสคณะ `10`, moderator ต้องมีภาค, `exam_detail` เฉพาะเอกสารคลัง exam |
| Service | อัปโหลดได้เฉพาะภาคตัวเอง, ผู้อัปโหลดอนุมัติไฟล์ตัวเองไม่ได้, ข้อสอบต้องอนุมัติครบทุก role, Super Admin ≥ 2 คน, เขียน audit log ใน transaction เดียวกัน |

## 3.5 การออกแบบกระบวนการหลัก

**[เติม: วาด Activity Diagram หรือ Sequence Diagram เมื่อ story เสร็จ]** กระบวนการที่ควรมีรูป:
1. **สมัครสมาชิก (US-1):** ตรวจอีเมลซ้ำ → โดเมน → local part เป็นเลข 10 หลัก → หลัก 3–4 = `10` → บันทึก `student_id` และเวลายอมรับ PDPA
2. **อัปโหลดเอกสาร (US-5):** เลือกรายวิชาในรุ่น → ตรวจขนาด/ชนิดไฟล์ → คำนวณ sha256 → ล้างชื่อไฟล์ → `Document.add_version()` (ล็อกแถว) → สถานะ `pending`
3. **อนุมัติเอกสาร (US-6, US-9):** Moderator/Super Admin ตัดสิน → บันทึก `approval` → ตรวจว่าครบ `doc_type_required_role` → `published` (หรือ `rejected` พร้อมเหตุผล)
4. **ค้นหาและดาวน์โหลด (US-7, US-8):** ค้นด้วยรหัสวิชาข้ามทุกรุ่น → แสดงเฉพาะ `published` → ดาวน์โหลดผ่าน view ที่ตรวจสิทธิ์ → บันทึก `download_log`

## 3.6 เครื่องมือและเทคโนโลยี

| ประเภท | เครื่องมือ | เวอร์ชัน |
|---|---|---|
| ภาษา | Python | 3.12+ |
| Web framework | Django | 6.1.2 |
| UI | HTML + CSS ของทีม (`static/css/retro.css`) | - |
| ฐานข้อมูล | SQLite (dev), PostgreSQL (production) | **[เติม: เวอร์ชัน PostgreSQL]** |
| ไลบรารีอื่น | Pillow 12.3.0, python-decouple 3.8 | |
| Version control / PM | Git, GitHub (Issues, Projects, Pull Request, Actions) | |
| IDE | VS Code + Python, Git Graph | |
| Diagram | Mermaid | |
| Deploy | **[เติม: ผล SP-4]** | |

## 3.7 แผนการทดสอบและการประเมินผล

### 3.7.1 การทดสอบซอฟต์แวร์
- **Unit test** ของ service/selector โดยตรง (กฎธุรกิจและกฎสิทธิ์) และ model validation
- **View/Integration test** สำหรับ flow หลัก: view ที่ต้องล็อกอิน (redirect เมื่อไม่ล็อกอิน), สิทธิ์ความเป็นเจ้าของ, validation ของฟอร์ม
- **Query count test** ด้วย `assertNumQueries` สำหรับหน้ารายการ
- **CI** ด้วย GitHub Actions รัน `python manage.py test` ทุก PR (TD-1)
- **Coverage** ด้วย `coverage.py` เป้า > 80%
- **Acceptance test** ตาม AC ของแต่ละ story ใน Sprint Review (แนะนำเขียน AC แบบ Given-When-Then)
- **Security review** ตาม OWASP Top 10 ใน Sprint 3

### 3.7.2 ตัวชี้วัดการประเมินผล

| ตัวชี้วัด | วิธีวัด | เป้า |
|---|---|---|
| ความครบของฟังก์ชัน | สัดส่วน story ที่ผ่าน DoD เทียบกับที่ commit | **[เติม]** |
| Velocity / ความแม่นยำของการวางแผน | แต้มที่เสร็จ ÷ แต้มที่วางแผน ต่อ Sprint | — |
| คุณภาพโค้ด | เทสต์ผ่าน 100%, coverage | > 80% |
| ความเร็วหน้าค้นหา | เวลาตอบเฉลี่ย/เปอร์เซ็นไทล์ 95 กับข้อมูลทดสอบ **[เติม: ขนาดข้อมูล]** | ~2 วินาที |
| จำนวนคลิกถึงไฟล์ | นับจากผลค้นหา | ≤ 2 คลิก |
| ความพึงพอใจผู้ใช้ | แบบสอบถาม SUS 10 ข้อ หรือ Likert 5 ระดับ **[ตรวจ: เลือกเครื่องมือและจำนวนผู้ทดสอบ]** | **[เติม]** |
| ความครอบคลุมของคลัง | สัดส่วนรายวิชา CN21–CN25 ที่มีเอกสารเผยแพร่ | เพิ่มขึ้นทุก Sprint |
