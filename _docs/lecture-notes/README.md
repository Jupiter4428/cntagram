# CN331 Software Engineering — Lecture Notes

วีรชัย (อ.แจ็ค) · Department of Electrical & Computer Engineering · Thammasat School of Engineering (TSE) · Semester 1/2569

เนื้อหาจากสไลด์สัปดาห์ที่ 7 (Advanced Django Queries & Sprint 1 Execution) และสัปดาห์ที่ 10 (Software Architecture & Sprint 2 Planning) จัดกลุ่มตามหัวข้อ:

| ไฟล์ | หัวข้อ | ที่มา |
|---|---|---|
| [01-django-orm-queries-and-optimization.md](01-django-orm-queries-and-optimization.md) | Advanced Django ORM, Q/F, aggregate/annotate, Lazy Evaluation, N+1, select_related/prefetch_related | Week 7 Part 1–2 |
| [02-django-class-based-views.md](02-django-class-based-views.md) | FBV vs CBV, Generic Views, Overriding, Mixins & MRO | Week 7 Part 3 |
| [03-software-architecture-and-decomposition.md](03-software-architecture-and-decomposition.md) | Architecture vs Design vs Code, Monolith/Microservices/Modular Monolith, C4 Model, Django Apps, Circular Dependencies | Week 10 Part 1, Lab 1 |
| [04-django-service-layer-and-transactions.md](04-django-service-layer-and-transactions.md) | Architectural Tiers, Fat Views/Models, services.py/selectors.py, ACID Transactions, select_for_update, ADR | Week 10 Part 2, Lab 2 |
| [05-agile-scrum-sprints.md](05-agile-scrum-sprints.md) | Sprint 1 Ceremonies (Standup, Burndown, Review, Retro), Sprint 2 Planning (Velocity, Tech Debt, Sprint Goal, DoR/DoD, Vertical Slicing, GitHub Projects) | Week 7 Part 4, Week 10 Part 3, Lab 3 |

---

## สัปดาห์ที่ 7: Advanced Django Queries & Sprint 1 Execution

### วัตถุประสงค์การเรียนรู้ประจำสัปดาห์ (Learning Outcomes)

เมื่อเรียนจบสัปดาห์นี้ นักศึกษาจะสามารถ:

1. **สร้างคิวรีขั้นสูงด้วย Django ORM**: ประยุกต์ใช้ Field Lookups, การสืบค้นข้ามความสัมพันธ์ (`__`), นิพจน์เชิงตรรกะ `Q` objects และการอัปเดตระดับฐานข้อมูลด้วย `F` expressions
2. **ประมวลผลข้อมูลเชิงสถิติในระดับฐานข้อมูล**: จำแนกและประยุกต์ใช้ `aggregate()` สำหรับค่าสรุปทั้งตาราง และ `annotate()` สำหรับการจัดกลุ่มและเพิ่มแอตทริบิวต์รายแถว
3. **วิเคราะห์และเพิ่มประสิทธิภาพการเข้าถึงฐานข้อมูล**: วินิจฉัยปัญหา N+1 Queries ตรวจสอบการทำงานของ Lazy Evaluation และใช้ `select_related()` กับ `prefetch_related()` ได้ถูกต้อง
4. **พัฒนาสถาปัตยกรรมวิวด้วย Class-Based Views (CBVs)**: แปลงวิวแบบฟังก์ชัน (FBV) สู่ Generic Views (`ListView`, `DetailView`, `CreateView`, `UpdateView`, `DeleteView`)
5. **ปรับแต่งการทำงานและควบคุมสิทธิ์ใน CBVs**: โอเวอร์ไรด์เมธอด `get_queryset()`, `get_context_data()`, `form_valid()` และจัดการความปลอดภัยด้วย Mixins ตามกฎ MRO
6. **ดำเนินพิธีกรรม Sprint 1 Review & Retrospective**: จัดการประชุม Daily Standup, ตรวจสอบความคืบหน้าด้วย Burndown Chart, สาธิต Increment ตาม Definition of Done (DoD) และปรับปรุงกระบวนการทำงาน
7. **สังเคราะห์องค์ความรู้เพื่อเตรียมสอบกลางภาค**: เชื่อมโยง Software Engineering Theory, Django MVT, Models, Views, Forms, Auth และ Agile Frameworks เพื่อแก้โจทย์บูรณาการ

### ทำไมวิศวกรซอฟต์แวร์ต้องเชี่ยวชาญ Advanced ORM, CBVs & Sprint Execution?

**มิติวิศวกรรมข้อมูล & ประสิทธิภาพระบบ**
- **Database Bottlenecks**: คอขวดของ Web Applications มากกว่า 90% มักเกิดจากการดึงข้อมูลจาก Database ที่ไม่มีประสิทธิภาพ
- **Race Conditions**: การคำนวณในหน่วยความจำของ Python นำไปสู่ปัญหาข้อมูลไม่สอดคล้องกัน (Inconsistency) เมื่อมีคำขอทำงานพร้อมกัน
- **Maintainable Architecture**: CBVs ช่วยลดความซ้ำซ้อนของโค้ดตามหลัก OOP และ DRY (Don't Repeat Yourself)

**มิติการส่งมอบงาน Agile & การวัดผล**
- **Sprint 1 Delivery**: พิสูจน์ว่าทีมสามารถเปลี่ยน User Stories ให้เป็นระบบที่รันได้จริงตามเกณฑ์ DoD
- **Empirical Process Control**: ใช้ Daily Standup และ Burndown Chart ในการตรวจจับความเสี่ยงได้ตั้งแต่เนิ่นๆ
- **Continuous Improvement**: Retrospective คือหัวใจสำคัญของ Agile ในการพัฒนาและยกระดับประสิทธิภาพทีมอย่างต่อเนื่อง

> 💡 **Takeaway** — **From Basic Prototype to Scalable Engineering**: สัปดาห์นี้เรายกระดับจากการเขียนโค้ดเว็บระดับพื้นฐาน สู่การปรับแต่งคิวรีประสิทธิภาพสูง การจัดโครงสร้าง View ระดับมืออาชีพ และการปิดรอบ Sprint 1 ก่อนสอบกลางภาค

### แผนผังการเรียนรู้ประจำสัปดาห์ที่ 7 (Session Roadmap)

เนื้อหาในสัปดาห์นี้ถูกออกแบบเป็น 4 ส่วนหลักที่เชื่อมโยงเทคนิค Backend เข้ากับกระบวนการทำงานแบบมืออาชีพ:

| Part | หัวข้อ | เนื้อหา |
|---|---|---|
| Part 1 | Advanced Django ORM Queries & Aggregations | Field Lookups, Spanning Relationships (`__`), Q Objects, F Expressions, `aggregate()` vs `annotate()` |
| Part 2 | Database Performance & Optimization | Lazy Evaluation, QuerySet Caching, ปัญหา N+1 Queries, `select_related()` vs `prefetch_related()`, Profiling |
| Part 3 | Class-Based Views (CBVs) & Generic Views | FBV vs CBV, Base `View`, CRUD Views (`ListView`, `DetailView`, `CreateView` ฯลฯ), Overriding & Mixins (MRO) |
| Part 4 | Sprint 1 Ceremonies & Midterm Preparation | Daily Scrum, Burndown Charts, Sprint Review (Demo to DoD), Retrospective (4Ls/Start-Stop), Midterm Knowledge Blueprint |

**Case Studies**: ระบบบริการการศึกษา (University Course Portal) & ระบบบริหารงาน Agile (Sprint Task Tracker)

### วิวัฒนาการของการพัฒนาระบบ: จากระดับเริ่มต้นสู่ระดับมืออาชีพ

**✗ วิธีการระดับเริ่มต้น (Weeks 3–6)**
- ใช้ `.filter()` และ `.all()` ดึงข้อมูลทั้งหมดมาไว้ใน Python Memory แล้วใช้ลูป `for` คำนวณสรุป
- เข้าถึงความสัมพันธ์ข้ามตารางในเทมเพลต เช่น `{{ course.department.name }}` จนเกิด SQL queries ซ้ำซาก
- เขียน Function-Based Views ซ้ำๆ ในการแสดงรายการ รายละเอียด และการจัดการฟอร์ม
- ติดตามงานแบบไม่เห็นตัวเลขความคืบหน้าที่แท้จริง

**✓ วิธีการทางวิศวกรรมระดับมืออาชีพ (Week 7)**
- มอบหน้าที่การประมวลผล กรอง และคำนวณทางสถิติให้ **Database Engine** ทำงานผ่าน ORM
- ควบคุมการ Join และโหลดข้อมูลล่วงหน้าด้วย `select_related` และ `prefetch_related`
- ใช้ **Generic CBVs** เพื่อลด Boilerplate Code เพิ่มการนำกลับมาใช้ใหม่ และโครงสร้างแบบ OOP
- ขับเคลื่อนทีมด้วย **Sprint Review & Retro** และตัวชี้วัด Burndown Velocity

> 💡 **Takeaway** — วิศวกรซอฟต์แวร์ไม่เพียงเขียนระบบให้ "ทำงานได้" (Make it work) แต่ต้องทำให้ระบบ "ถูกต้อง ดูแลรักษาง่าย และมีประสิทธิภาพ" (Make it right, make it maintainable, make it fast)

### QUICK CHECK: การสังเคราะห์ความรู้สถาปัตยกรรมระบบเว็บ (Midterm Synthesis)

พิจารณาสถาปัตยกรรม Django MVT หากต้องการสร้างรายงานสรุปผลการลงทะเบียนโดย *"ต้องคำนวณจำนวนวิชาและเกรดเฉลี่ยรวม พร้อมแสดงวิชาที่มีเกรดเฉลี่ยสูงสุด 5 อันดับแรก"* ตามหลัก Separation of Concerns โค้ดส่วนคำนวณขั้นสูงนี้ควรวางไว้ที่ใด?

- A. เขียนลูปคำนวณและตัดเกรดใน HTML Template ด้วย `{% for %}`
- B. เขียนคำสั่งผ่าน ORM (`annotate`, `aggregate`) ใน `get_queryset()` หรือ Manager
- C. ดึงข้อมูลดิบทั้งหมดมาให้ JavaScript บนเบราว์เซอร์คำนวณผ่าน `reduce()`
- D. เขียนฟังก์ชันคำนวณใน `urls.py` ก่อนส่งต่อให้ View

**คำตอบที่ถูกต้อง: B** — เหตุผล: ตามหลัก Separation of Concerns การคำนวณและกรองข้อมูลควรทำในระดับ Backend ผ่าน Model Manager หรือ `get_queryset()` ของ View เพื่อให้ Database ประมวลผลอย่างรวดเร็ว ส่วน Template มีหน้าที่แสดงผลเท่านั้น และการส่งข้อมูลดิบไปคำนวณบนเบราว์เซอร์สิ้นเปลืองแบนด์วิดท์มหาศาล

### สรุปภาพรวมเนื้อหาประจำสัปดาห์ที่ 7 (Lecture Synthesis)

> ✍️ หมายเหตุลายมือบนสไลด์: "สอบอาทิตย์หลังมิดเทอม"

**เทคนิคทางวิศวกรรมฝั่ง Backend**
- **Advanced Lookups & Q**: เพิ่มความยืดหยุ่นในการสืบค้นด้วยตรรกะ OR และ NOT
- **F Expressions**: การคำนวณระดับ RDBMS ป้องกัน Race Conditions
- **Aggregate vs Annotate**: สรุปผลทั้งตาราง (Dictionary) vs สรุปผลรายแถว (QuerySet)
- **Query Optimization**: กำจัด N+1 Queries ด้วย `select_related` และ `prefetch_related`
- **Generic CBVs**: สถาปัตยกรรมวิว OOP ที่ลด Boilerplate Code

**กระบวนการส่งมอบงานแบบ Agile**
- **Daily Standup**: การซิงค์งาน 15 นาทีเพื่อตรวจจับและขจัด Blockers
- **Burndown Velocity**: ตัวชี้วัดความสามารถที่แท้จริงของทีมในการเผางาน
- **Sprint Review**: การสาธิต Working Software ร่วมกับผู้มีส่วนได้ส่วนเสีย
- **Sprint Retrospective**: การเรียนรู้ข้อบกพร่องและตั้ง Action Items สู่รอบถัดไป
- **Midterm Readiness**: สังเคราะห์ความรู้สัปดาห์ 1–7 สู่การสอบกลางภาค

### แหล่งข้อมูลอ้างอิง (Week 7)

- **Django Official Documentation (v5.0)**:
  - *Making Queries & QuerySet API Reference*: https://docs.djangoproject.com/en/5.0/topics/db/queries/
  - *Aggregation and Annotation*: https://docs.djangoproject.com/en/5.0/topics/db/aggregation/
  - *Class-Based Views Overview & Built-in Display/Editing Views*: https://docs.djangoproject.com/en/5.0/topics/class-based-views/
  - *Database access optimization guidelines*: https://docs.djangoproject.com/en/5.0/topics/db/optimization/
- **Database & Software Architecture Literature**:
  - Martin Fowler (2002). *Patterns of Enterprise Application Architecture*. Addison-Wesley. (Active Record vs Data Mapper, Query Objects)
  - Daniel Roy Greenfeld & Audrey Roy Greenfeld (2020). *Two Scoops of Django 3.x: Best Practices for Python and Django*.
- **Agile & Scrum Process References**:
  - Ken Schwaber & Jeff Sutherland (2020). *The Scrum Guide: The Definitive Guide to Scrum*. https://scrumguides.org/
  - Esther Derby & Diana Larsen (2006). *Agile Retrospectives: Making Good Teams Great*. Pragmatic Bookshelf.

---

## สัปดาห์ที่ 10: Software Architecture & Sprint 2 Planning

### วัตถุประสงค์การเรียนรู้ประจำสัปดาห์ (Learning Outcomes)

เมื่อเรียนจบสัปดาห์นี้ นักศึกษาจะสามารถ:

1. **วิเคราะห์และออกแบบสถาปัตยกรรมระบบ (System Architecture)**: จำแนกโครงสร้าง Monolithic vs Modular Monolith และถ่ายทอดแบบจำลองระบบผ่าน C4 Model (Context & Container Diagrams)
2. **จัดระเบียบโมดูลและแบ่งขอบเขตของ Django Apps**: วางผังความรับผิดชอบ (Separation of Concerns) กำหนดทิศทาง Dependency ทางเดียว และขจัดปัญหา Circular Imports
3. **ประยุกต์ใช้ Service Layer & Selector Pattern**: แก้ปัญหารหัสโปรแกรมแบบ Fat Views และ Fat Models โดยแยก Business Logic เข้าสู่ `services.py` และ Query Logic สู่ `selectors.py`
4. **รับประกันความปลอดภัยของข้อมูลและบันทึกการตัดสินใจ**: ควบคุม Database Transactions (`@transaction.atomic`, `select_for_update`) และจัดทำ Architectural Decision Records (ADR)
5. **วางแผนและปรับเทียบความเร็วใน Sprint 2 Planning**: คำนวณ Actual Velocity จาก Sprint 1, จัดการหนี้ทางเทคนิค (Technical Debt) ผ่าน Refactoring Stories และกำหนด Sprint 2 Goal
6. **บริหารจัดการรอบการทำงานด้วยเกณฑ์คุณภาพและ GitHub**: ซอยย่อยงานด้วย Vertical Slicing, บังคับใช้เกณฑ์ DoR/DoD และบริหารจัดการงานบน GitHub Projects & Issues

### ทำไมวิศวกรซอฟต์แวร์ต้องเชี่ยวชาญ Architecture & Sprint 2 Planning?

**มิติวิศวกรรมสถาปัตยกรรม & คุณภาพโค้ด**
- **Feature Accumulation & Code Rot**: เมื่อฟีเจอร์เริ่มสะสมและขยายตัวมากขึ้น โค้ดที่ขาดโครงสร้างที่ดีจะเสื่อมสภาพกลายเป็น "Spaghetti Code" ที่ View ฟังก์ชันเดียวยาวกว่า 200 บรรทัด
- **The God Object Trap**: การยัด Logic ทุกอย่างลง Model (*Fat Model*) ทำให้เกิดการผูกมัดแน่น (Tight Coupling) และทดสอบแบบ Unit Test ได้ยากมาก
- **Explicit Boundaries & Maintainability**: การกำหนดขอบเขตและเลเยอร์ที่ชัดเจนช่วยให้ทีมพัฒนาฟีเจอร์ใหม่ได้รวดเร็วโดยไม่ทำลายส่วนเดิม

**มิติการบริหารโครงการ Agile & การอยู่รอดของทีม**
- **Sprint 1 Reality Check**: มากกว่า 70% ของทีมประเมินความเร็ว (Velocity) สูงเกินจริง และเกิดงานคั่งค้างสะสมจากรอบแรก
- **Managing Technical Debt**: หากไม่จัดสรร Story Points เพื่อทำ Refactoring ใน Sprint 2 ระบบจะพังทลายเมื่อถึงช่วงส่งมอบงานไฟนอล
- **Clear Sprint 2 Goal**: รวมพลังทีมสู่คุณค่าชิ้นสำคัญชิ้นถัดไป แทนที่จะต่างคนต่างทำงานแบบไร้ทิศทาง

> 💡 **Takeaway** — **Transition to Professional Engineering**: สัปดาห์ที่ 10 คือจุดเปลี่ยนสำคัญจากการเขียนเว็บแบบนักศึกษามือสมัครเล่น (Prototype) สู่การเป็นวิศวกรซอฟต์แวร์ที่ออกแบบระบบให้ขยายตัวได้ ดูแลรักษาง่าย และบริหารกระบวนการส่งมอบงานอย่างมีวินัย

### แผนผังการเรียนรู้ประจำสัปดาห์ที่ 10 (Session Roadmap)

เนื้อหาสัปดาห์นี้ครอบคลุม 4 เสาหลักที่เชื่อมโยงการตัดสินใจระดับระบบ สู่ระดับโค้ด และกระบวนการทีม:

| Part | หัวข้อ | เนื้อหา |
|---|---|---|
| Part 1 | Software Architecture & System Decomposition | Architecture vs Design, C4 Model, Multi-App Boundaries, Dependency Rules, Circular Dependencies |
| Part 2 | Django System Architecture: Service Layer & Selectors | Architectural Tiers, Fat Views/Models Anti-patterns, `services.py`, `selectors.py`, ACID Transactions, ADRs |
| Part 3 | Agile Sprint 2 Planning & Governance | Velocity Recalibration, Technical Debt Metaphor, Refactoring User Stories, Sprint 2 Goal, DoR/DoD, GitHub Projects |
| Part 4 | Lab Practice, Synthesis & Architecture Matrix | Lab: C4 Diagramming, Code Refactoring Challenge, Sprint 2 Kickoff, High-Yield Synthesis Matrix, References & Bridge to Testing |

**Case Study โครงการศึกษา**: ระบบบริการการศึกษาและทะเบียนออนไลน์ (**University Course Portal & Learning Hub**)

### สะพานเชื่อมสู่สัปดาห์ที่ 11 (Bridge to Automated Testing)

**ความสำเร็จในสัปดาห์นี้ (Week 10 Milestones)**
- เข้าใจสถาปัตยกรรม C4 Model และแยกขอบเขตของ Django Apps อย่างเป็นระบบ
- รู้จักแก้ปัญหา Fat Views/Models ด้วยแนวคิด Service Layer และ Selectors
- ป้องกัน Concurrency Race Conditions ด้วย Database Transactions
- ปรับเทียบ Velocity และเปิดตัว Sprint 2 บน GitHub Projects เรียบร้อย

**สัปดาห์หน้า: Week 11 Automated Testing**
- **ทำไมต้องทดสอบอัตโนมัติ?**: การทดสอบด้วยมือ (Manual Click) ช้าและไม่ยั่งยืน
- **Django TestCase Framework**: เขียน Unit Tests และ Integration Tests ด้วยไพทอน
- **Coverage.py**: การวัดความครอบคลุมของการทดสอบให้เกิน 80%
- **Mocking & FactoryBoy**: จำลองข้อมูลทดสอบโดยไม่ยุ่งกับฐานข้อมูลจริง

> **"Clean Architecture makes code testable; automated tests keep it alive."**

### แหล่งข้อมูลอ้างอิง (Week 10)

- **Software Architecture Literature**:
  - Martin Fowler (2002). *Patterns of Enterprise Application Architecture*. Addison-Wesley. (Layered Architecture, Service Layer, Active Record)
  - Simon Brown (2018). *The C4 model for visualising software architecture*. https://c4model.com/
  - Robert C. Martin (2017). *Clean Architecture: A Craftsman's Guide to Software Structure and Design*. Prentice Hall.
- **Django Architecture Best Practices**:
  - HackSoft (2023). *Django Styleguide: Services & Selectors Architecture Pattern*. https://github.com/HackSoftware/Django-Styleguide
  - Daniel Roy Greenfeld & Audrey Roy Greenfeld (2020). *Two Scoops of Django 3.x: Best Practices for Python and Django*.
  - Django Official Documentation (v5.0): *Database Transactions, Concurrency, and Models*. https://docs.djangoproject.com/
- **Agile & Software Craftsmanship**:
  - Robert C. Martin (2008). *Clean Code: A Handbook of Agile Software Craftsmanship*. Prentice Hall.
  - Ken Schwaber & Jeff Sutherland (2020). *The Scrum Guide*. https://scrumguides.org/
  - Ward Cunningham (1992). *The WyCash Portfolio Management System (Technical Debt Metaphor)*. OOPSLA '92.
