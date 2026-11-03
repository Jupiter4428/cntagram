# Project Presentation & Peer Evaluation: Live Demo, Engineering Defense, Agile Evidence & Capstone Deliverables

> ที่มา: CN331 สัปดาห์ที่ 14 — Project Presentation & Peer Evaluation หมวดที่ 1–4 และบทสรุป
>
> *จากกระดาษโน้ตแผ่นแรกสู่ระบบจริงบนอินเทอร์เน็ต: Time Budget, Live Demo, C4/ERD Defense, Service Layer, Test & CI Evidence, Velocity, Retrospective และ Peer Review*
>
> เนื้อหาที่เกี่ยวข้อง: Deploy บน Render, `DEBUG = False` และ Tag v1.0.0 → ดู [08-web-security-and-production-deployment.md](08-web-security-and-production-deployment.md) · C4 Model และ Modular Monolith → ดู [03-software-architecture-and-decomposition.md](03-software-architecture-and-decomposition.md) · Service Layer และ `@transaction.atomic` → ดู [04-django-service-layer-and-transactions.md](04-django-service-layer-and-transactions.md) · N+1 Queries → ดู [01-django-orm-queries-and-optimization.md](01-django-orm-queries-and-optimization.md) · Coverage → ดู [06-django-automated-testing.md](06-django-automated-testing.md) · GitHub Actions, Linters และ Branch Protection → ดู [07-ci-cd-and-static-analysis.md](07-ci-cd-and-static-analysis.md) · Velocity, Burndown และ Retrospective → ดู [05-agile-scrum-sprints.md](05-agile-scrum-sprints.md)

---

## ทำไมวิศวกรซอฟต์แวร์ต้องสื่อสารและสาธิตผลงานอย่างมืออาชีพ?

**🗣️ คุณค่าของการสื่อสารทางวิศวกรรม**
- **Software Needs Stakeholder Buy-in**: โค้ดที่ดีที่สุดจะไร้ความหมายหากไม่สามารถสาธิตให้ลูกค้าหรือผู้บริหารเห็นคุณค่าทางธุรกิจได้
- **Evidence Over Claims**: วิศวกรไม่พูดลอยๆ ว่า "ระบบเสถียร" แต่แสดงหลักฐานด้วย CI Pipeline Badge, Test Reports และ Production Metrics
- **Grace Under Pressure**: การสาธิตสด (Live Demo) ทดสอบความพร้อม ความมั่นใจ และการแก้ไขสถานการณ์เฉพาะหน้าของทีม

**🏆 เกณฑ์ประเมินกลุ่ม Agile Project (40%)**

| หมวด | สัดส่วน | สิ่งที่ประเมิน |
|---|---|---|
| **Working Product & Deployment** | 15% | ความสมบูรณ์ของระบบบน Cloud และ Security Hardening |
| **Software Architecture & Code** | 10% | Service Layer, Clean ORM Queries, Testing Coverage |
| **Agile Governance & CI/CD** | 10% | GitHub Actions, Velocity, PR Reviews, DoD |
| **Presentation & Peer Review** | 5% | ความชัดเจน การตอบคำถาม และการประเมินเพื่อน |

> 💡 **Takeaway** — **Capstone Goal**: วันนี้คือเวทีที่นักศึกษาจะได้แสดงผลผลิตจากการทำงานร่วมกันตลอด 14 สัปดาห์ จากกระดาษโน้ตแผ่นแรก สู่ระบบจริงที่เปิดใช้งานบนอินเทอร์เน็ต

## กำหนดการและลำดับการนำเสนอประจำวัน (Presentation Agenda)

แผนผังการดำเนินกิจกรรมตลอดช่วงเวลา 3 ชั่วโมงของการนำเสนอโครงงาน:

| ช่วง | หัวข้อ | เนื้อหา |
|---|---|---|
| ช่วงที่ 1 | กติกาและเกณฑ์ | Time Allocation, Rubrics, Live Demo Guidelines |
| ช่วงที่ 2 | การสาธิตระบบ | Live Demonstration, Core User Journeys, Edge Cases |
| ช่วงที่ 3 | ปกป้องสถาปัตยกรรม | C4 Diagrams, Testing Evidence, CI/CD, Q&A Defense |
| ช่วงที่ 4 | การประเมินเพื่อน | Peer Review Form, Scoring, Retrospective Wrap-up |

> 💡 **Takeaway** — **Time Allocation**: แต่ละกลุ่มจะได้รับเวลา **15 นาทีสำหรับการนำเสนอและสาธิต** ตามด้วย **5 นาทีสำหรับตอบข้อซักถามเชิงเทคนิค**

---

# หมวดที่ 1: กติกา กำหนดเวลา และรูปแบบการนำเสนอ

*การจัดสรรเวลาอย่างมืออาชีพ การสาธิตระบบสดแบบ Live Demo และการหลีกเลี่ยงข้อผิดพลาดทั่วไป*

## การบริหารเวลา 15 นาทีอย่างมีประสิทธิภาพ (Time Budget Breakdown)

การตรงต่อเวลาคือเครื่องหมายของวิศวกรมืออาชีพ จัดสรรเวลาตามโครงสร้างแนะนำ:

| นาทีที่ | ช่วง | เนื้อหา |
|---|---|---|
| 0–2 (2m) | **Problem & Value Proposition** | ปัญหาคืออะไร? ใครคือผู้ใช้? คุณค่าหลักของระบบคืออะไร? |
| 2–8 (6m) | **Live Software Demonstration** | สาธิตระบบจริงบน Cloud (Render URL) ตาม Core User Journey |
| 8–12 (4m) | **Engineering & Architecture Defense** | แสดง C4 Model, ERD, Clean Code (Service Layer), Test Suite (> 80%) |
| 12–15 (3m) | **Agile Governance & Retrospective** | แสดง GitHub Board, Burndown, Velocity Sprints 1–3 และข้อคิดที่ได้ |
| 15–20 | **Technical Q&A** | ตอบคำถามเชิงลึกจากอาจารย์และเพื่อนร่วมชั้น |

**⏱️ สัญญาณเตือนเวลา** — ให้สัญญาณเมื่อเหลือ 3 นาที และจะตัดการนำเสนอทันทีเมื่อครบ 15 นาที

> 💡 **Takeaway** — **Rehearse Rehearse Rehearse**: ทุกกลุ่มต้องซ้อมจับเวลาร่วมกันล่วงหน้าอย่างน้อย 2 รอบเพื่อความกระชับและลื่นไหล

## กฎเหล็กของการสาธิตระบบสด (Live Demo Best Practices)

**✅ สิ่งที่ต้องทำ (Best Practices)**
- **Live on Cloud Only**: สาธิตบน Production URL จริง (Render) เท่านั้น
- **Prepare Realistic Seed Data**: เตรียมข้อมูลจำลองที่สมจริงอ่านง่ายไว้ล่วงหน้า
- **Show Happy Path & Boundary**: แสดงทั้งกรณีผ่าน และกรณีแจ้งเตือนเมื่อกรอกผิด
- **Multiple Roles Login**: แสดงการสลับบทบาท เช่น อาจารย์ กับ นักศึกษา

**❌ ข้อห้ามและจุดบกพร่องที่พบบ่อย**
- **No Pre-recorded Video**: ห้ามเปิดวิดีโอที่อัดไว้แทนการสาธิตสด
- **Don't Type Long Text Live**: เตรียมข้อความไว้ใน Clipboard เพื่อ Paste
- **Never Demo with `DEBUG=True`**: หากขึ้นหน้าจอ Error สีเหลืองจะถูกหักคะแนนความปลอดภัยทันที

> 💡 **Takeaway** — **Plan for Contingency**: มีแผนสำรองเสมอ เปิดแท็บเบราว์เซอร์เตรียมไว้ทุกหน้าที่จำเป็นก่อนเริ่มจับเวลา

---

# หมวดที่ 2: การปกป้องการตัดสินใจทางวิศวกรรม

*การแสดง C4 Architecture Diagrams, โครงสร้างฐานข้อมูล ERD, ประสิทธิภาพ ORM Queries และหลักฐาน Test Coverage*

## การนำเสนอสถาปัตยกรรมระบบ (Architecture Defense with C4 Model)

เชื่อมโยงความรู้จากสัปดาห์ที่ 10: แสดงภาพรวมความเข้าใจเชิงระบบ ไม่ใช่แค่โค้ด:

- **C4 Context Diagram**: ระบบตั้งอยู่ตรงไหน ใครเป็นผู้ใช้หลัก และมีระบบภายนอกใดเกี่ยวข้อง
- **C4 Container Diagram**: Browser → Cloud PaaS (Render) → Gunicorn → Django Apps → PostgreSQL
- **Modular Monolith Structure**: ชี้แจงการแบ่งขอบเขต Apps (เช่น `courses`, `accounts`) ว่ามี Separation of Concerns อย่างไร และปราศจาก Circular Imports

```
Student / Faculty Users
        ↓
Django Web System (Render Cloud)
        ↓
PostgreSQL Database
```

**❓ ข้อสอบถามสำคัญ** — ต้องพร้อมตอบคำถาม: *"ทำไมถึงเลือก Modular Monolith แทน Microservices?"*

> 💡 **Takeaway** — **Architectural Maturity**: แสดงให้เห็นว่าการออกแบบระบบมีเหตุผลและผ่านการไตร่ตรองตามหลักการ Modular Monolith

## หลักฐานความสะอาดของโค้ด: Service Layer & Clean ORM Queries

แสดงตัวอย่างซอร์สโค้ดที่ดีที่สุด 1–2 ฟังก์ชันของกลุ่ม:

- **Service Layer Demonstration**: แสดงไฟล์ `services.py` ที่แยก Business Logic ออกจาก Views และครอบด้วย `@transaction.atomic`
- **Query Optimization**: แสดงว่าทีมป้องกันปัญหา N+1 Query ด้วย `select_related()` และ `prefetch_related()`
- **Type Hints & Docstrings**: โค้ดมีความเป็นระเบียบ อ่านง่าย และตรงตาม PEP 8

```python
# Service Layer demonstration
@transaction.atomic
def enroll_student_service(
    *, student: Student, course: Course
) -> Enrollment:
    """Enrolls student with business validation."""
    if course.is_full():
        raise CourseFullError("Capacity reached.")

    enrollment, _ = Enrollment.objects.get_or_create(
        student=student, course=course
    )
    return enrollment
```

> 💡 **Takeaway** — **Showcase Your Best Code**: เลือกส่วนของโปรแกรมที่แสดงถึงความเข้าใจเชิงลึกด้านวิศวกรรมมานำเสนอ อย่าเปิดไล่ดูทุกไฟล์

## หลักฐานการทดสอบและ CI Pipeline (Quality Evidence)

**🧪 รายงานผลการทดสอบ (Test Evidence)**
- **Total Test Cases**: แสดงจำนวน Test Cases ทั้งหมด (เช่น 45 tests) และเวลาที่ใช้รัน
- **Coverage Report**: แสดงภาพ `coverage report` ยืนยันอัตราความครอบคลุม ≥ 80%
- **Test Types**: ชี้แจงสัดส่วนของ Model, Form, View Client และ Mocking

**✔️ สถานะ GitHub Actions Pipeline**
- **Green Build Badge**: แสดงหน้าจอ Actions ที่มีสถานะผ่านทั้งหมด (Green Checkmarks)
- **Branch Protection Proof**: แสดงการตั้งค่าไม่อนุญาตให้ Merge หากเทสไม่ผ่าน
- **Linters Clean**: แสดงว่า Flake8, Black และ Bandit ไม่พบข้อผิดพลาด

> 💡 **Takeaway** — **Hard Evidence**: ตัวเลข Coverage และไปป์ไลน์ CI สีเขียวคือหลักฐานที่หนักแน่นที่สุดว่าซอฟต์แวร์ของกลุ่มมีคุณภาพระดับวิศวกรรม

---

# หมวดที่ 3: การนำเสนอกระบวนการ Agile และสถิติทีม

*การวิเคราะห์ Velocity, Burndown Charts, ประสบการณ์จาก Sprint Retrospectives และบทเรียนที่ได้รับ*

## การวิเคราะห์ความเร็วของทีม (Velocity & Burndown Analysis)

แสดงพัฒนาการของทีมผ่านข้อมูลตัวเลขจริงจาก GitHub Projects:

- **Sprint 1 Velocity**: มักเกิดการประเมินสูงเกินจริง (Over-commitment) และเหลืองานค้าง
- **Sprint 2 Velocity**: ทีมเริ่มปรับเทียบความเร็วได้แม่นยำขึ้น จัดสรรแต้มเพื่อ Refactoring และ Tests
- **Sprint 3 Velocity**: การส่งมอบงานมีเสถียรภาพ มุ่งเน้นการ Hardening และขึ้นระบบ Cloud
- **Burndown Chart Reflection**: แสดงกราฟการเบิร์นงาน ชี้จุดสะดุดและวิธีที่ทีมช่วยกันแก้ไขอุปสรรค (Impediments)

ตัวอย่างกราฟ Velocity บนสไลด์ (Story Points ต่อ Sprint):

| Sprint | Story Points |
|---|---|
| S1 | 18 |
| S2 | 24 |
| S3 | 22 |

**สรุปข้อคิดสำคัญ** — ความเร็วที่แท้จริงไม่ใช่การมีแต้มเยอะที่สุด แต่คือ **ความสม่ำเสมอและความแม่นยำ** ในการคาดการณ์ (Predictability)

> 💡 **Takeaway** — **Data-Driven Agile**: ใช้วิทยาศาสตร์ของข้อมูลตัวเลขจาก GitHub Projects บ่งบอกถึงสุขภาพและวุฒิภาวะของทีม

## บทเรียนจาก Sprint Retrospectives (Team Growth & Reflection)

**💡 สิ่งที่ทำได้ดี (What Went Well)**
- การตกลง Branching และ PR Template ทำให้รีวิวโค้ดได้รวดเร็ว
- Automated Tests ช่วยตรวจพบบั๊กใน Service Layer ได้อย่างทันท่วงที
- การแบ่งหน้าที่ตามความถนัดอย่างโปร่งใสบน GitHub Board

**🔧 บทเรียนและการปรับปรุง (Key Lessons)**
- **Don't Delay Integration**: การเก็บโค้ดไว้นานเกินไปทำให้เกิด Merge Conflict
- **Mock Early**: สร้าง Mock สำหรับ API ภายนอกตั้งแต่แรกเพื่อไม่ให้งานสะดุด
- **Communication is Key**: การคุยกันสั้นๆ สม่ำเสมอสำคัญกว่าการแก้ปัญหาคนเดียว

> 💡 **Takeaway** — **Continuous Improvement**: ความผิดพลาดในการทำโครงงานไม่ใช่เรื่องน่าอับอาย แต่การเรียนรู้และนำไปปรับปรุงให้ดีขึ้นคือหัวใจของ Agile

---

# หมวดที่ 4: ระบบการประเมินเพื่อน เกณฑ์การให้คะแนน และสรุปผล

*แบบฟอร์ม Peer Review จริยธรรมการประเมิน เกณฑ์ Rubrics 4 ด้าน และก้าวต่อไปสู่การสอบปลายภาค*

## ระบบการประเมินเพื่อนร่วมชั้น (Constructive Peer Evaluation)

นักศึกษาทุกคนต้องทำหน้าที่เป็นผู้ประเมินโครงงานของกลุ่มเพื่อน:

- **Online Evaluation Form**: สแกน QR Code เข้าสู่ระบบประเมินประจำวันในระหว่างที่แต่ละกลุ่มนำเสนอ
- **Constructive Feedback (คำวิจารณ์เชิงสร้างสรรค์)**: ให้ความเห็นที่มีประโยชน์ เช่น *"ประทับใจการจัดการ Service Layer แต่อยากเสนอแนะให้ปรับ UI บนมือถือ"*
- **Ethics & Objectivity**: ประเมินตามเกณฑ์ผลงานจริง ปราศจากอคติหรือการสมยอมคะแนน

**สัดส่วนเกณฑ์การประเมินเพื่อน (Peer Form)**

| เกณฑ์ | ความหมาย | สัดส่วน |
|---|---|---|
| **1. Functional Completeness** | ระบบทำงานได้จริง ไหลลื่น ปราศจากบั๊กค้างคา | 30% |
| **2. Architectural Quality** | โครงสร้างโค้ดและการออกแบบฐานข้อมูล | 25% |
| **3. Testing & Security** | การมีเทสและระบบความปลอดภัย | 25% |
| **4. Presentation Quality** | ความชัดเจนและการตอบคำถาม | 20% |

> 💡 **Takeaway** — **Professional Integrity**: ความสามารถในการให้ฟีดแบ็กที่มีคุณค่าแก่เพื่อนร่วมงานเป็นหนึ่งในทักษะจำเป็นสูงสุดของวิศวกรซอฟต์แวร์

---

# สรุปบทเรียน: ตารางสังเคราะห์เกณฑ์การส่งมอบ

## ตารางสังเคราะห์องค์ประกอบส่งมอบโครงงาน (Capstone Deliverables)

สรุปสิ่งที่แต่ละกลุ่มต้องส่งมอบผ่าน GitHub ภายในสิ้นสุดสัปดาห์ที่ 14:

| รายการส่งมอบ | ตำแหน่ง / รูปแบบ | เกณฑ์การตรวจสอบทางวิศวกรรม | สัดส่วน |
|---|---|---|---|
| **Live Cloud App** | URL บน Render / PaaS | `DEBUG=False`, HTTPS, ใช้งานได้จริง | 15% |
| **Clean Architecture** | Service Layer & Models | แยก Business Logic, ไม่มี N+1 Queries | 10% |
| **Automated Quality** | GitHub Actions CI | Tests Pass, Coverage ≥ 80%, Linters Clean | 10% |
| **Documentation** | `README.md` & Release Tag | Setup Guide, C4 Diagrams, Tag `v1.0.0` | 5% |

> 💡 **Takeaway** — **Submission Gate**: ทุกกลุ่มต้องยืนยันว่าได้ส่งลิงก์ GitHub Repo และ Live Production URL ในระบบส่งงานของรายวิชาก่อน 23:59 น. ของวันนี้
