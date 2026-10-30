# บทที่ 2 ทฤษฎีและงานที่เกี่ยวข้อง

> แหล่งข้อมูล: [`lecture-notes/`](../lecture-notes/) (01–05) · [ADR](../adr/) · [`database-design.md`](../database-design.md) §4 · รหัสอ้างอิงอยู่ใน [references.md](./references.md)
>
> **หลักการเขียนบทนี้:** อธิบายทฤษฎีเท่าที่ระบบใช้จริง และจบทุกหัวข้อด้วย "การนำมาใช้ในโครงงาน" เพื่อเชื่อมไปบทที่ 3 อ้างอิงแหล่งต้นฉบับ (หนังสือ/เอกสารทางการ) แทนการอ้าง lecture notes อย่างเดียว

## 2.1 การพัฒนาซอฟต์แวร์แบบ Agile และ Scrum

**สาระสำคัญ**
- Agile Manifesto ให้คุณค่ากับซอฟต์แวร์ที่ใช้งานได้และการตอบรับการเปลี่ยนแปลง มากกว่าเอกสารครบถ้วนและการทำตามแผนตายตัว [อ้างอิง: AGILE2001]
- Scrum เป็นกรอบการทำงานเชิงประจักษ์ (Empirical Process Control) บนเสา 3 ต้น: ความโปร่งใส การตรวจสอบ และการปรับตัว [อ้างอิง: SCRUM2020]
  - **บทบาท:** Product Owner, Scrum Master, Developers
  - **กิจกรรม:** Sprint Planning, Daily Scrum, Sprint Review, Sprint Retrospective
  - **สิ่งประดิษฐ์:** Product Backlog, Sprint Backlog, Increment
- **User Story** รูปแบบ "As a … I want … so that …" และเกณฑ์ INVEST (Independent, Negotiable, Valuable, Estimable, Small, Testable) [อ้างอิง: COHN2004]
- **Story Points / Planning Poker / Velocity** สำหรับประมาณขนาดงานเชิงสัมพัทธ์และวางแผน Sprint [อ้างอิง: COHN2005]
- **Burndown Chart** ติดตามงานคงเหลือรายวัน และการวิเคราะห์รูปแบบกราฟ (เช่น เส้นแบนแล้วดิ่งตอนท้าย = งานใหญ่เกินไปหรือรวมงานตอนท้าย)
- **Definition of Ready / Definition of Done** และ **Vertical Slicing** (ตัด story ให้ครอบคลุม UI + logic + DB ในชิ้นเดียว)
- **MoSCoW** (Must / Should / Could / Won't) สำหรับจัดลำดับความสำคัญ
- **หนี้ทางเทคนิค (Technical Debt)** อุปมาของ Ward Cunningham: ทางลัดวันนี้คือดอกเบี้ยที่ต้องจ่ายในอนาคต [อ้างอิง: CUNNINGHAM1992]

**การนำมาใช้ในโครงงาน:** ทีม 5 คนทำงาน 3 Sprint โดยอาจารย์ผู้สอนเป็น Product Owner Scrum Master หมุนเวียนทุก Sprint เปลี่ยนเอกสาร SRS แบบล็อกสเปกเป็น Product Backlog แบบ User Story ใช้ GitHub Projects เป็น Scrum board และกำหนดโควตา Tech Debt ≥ 20% ของแต้มตั้งแต่ Sprint 2 (บทที่ 3 หัวข้อ 3.1)

## 2.2 Django Framework และสถาปัตยกรรม MVT

**สาระสำคัญ**
- Django เป็น web framework ภาษา Python แบบ "batteries-included" ใช้รูปแบบ **Model–View–Template (MVT)** [อ้างอิง: DJANGODOCS]
  - Model: นิยามโครงสร้างข้อมูลและเข้าถึงฐานข้อมูลผ่าน ORM
  - View: รับ HTTP request ประมวลผล และคืน response
  - Template: แสดงผล HTML
- **Function-Based Views (FBV) vs Class-Based Views (CBV)** และ Generic Views (`ListView`, `DetailView`, `CreateView` ฯลฯ), การ override เมธอด และ Mixins ตามลำดับ MRO
- **Custom User Model** (`AbstractBaseUser` + `PermissionsMixin`) ต้องตั้ง `AUTH_USER_MODEL` ก่อน migrate ครั้งแรก
- Migrations สำหรับจัดการการเปลี่ยนแปลง schema แบบมีเวอร์ชัน

**การนำมาใช้ในโครงงาน:** Django 6.1, ใช้ FBV เป็นหลัก, custom User ที่ล็อกอินด้วยอีเมลแทน username และดึงรหัสนักศึกษาจากอีเมลอัตโนมัติ, UI ด้วย Bootstrap 5

## 2.3 สถาปัตยกรรมซอฟต์แวร์

### 2.3.1 Architecture vs Design vs Code
สถาปัตยกรรมคือการตัดสินใจที่ "เปลี่ยนยาก" และกำหนดโครงสร้างหลักของระบบ ต่างจากการออกแบบระดับคลาสและโค้ด [อ้างอิง: BASS2021]

### 2.3.2 Monolith, Microservices และ Modular Monolith
| แบบ | ข้อดี | ข้อเสีย |
|---|---|---|
| Monolith | deploy ง่าย transaction ง่าย | โตแล้วกลายเป็น "Big Ball of Mud" |
| Microservices | scale/deploy แยกส่วนได้ | overhead ด้านเครือข่าย distributed transaction และการปฏิบัติการ |
| Modular Monolith | deploy เป็นชิ้นเดียว แต่แบ่งโมดูลตามโดเมนมีขอบเขตชัด | ต้องมีวินัยรักษาขอบเขตโมดูล |

หลัก **Monolith First** — เริ่มจาก monolith แล้วค่อยแยกเมื่อขอบเขตโดเมนชัด [อ้างอิง: FOWLER2015] และการแบ่งโมดูลตาม **Bounded Context** จาก Domain-Driven Design [อ้างอิง: EVANS2003]

### 2.3.3 C4 Model
แบบจำลองถ่ายทอดสถาปัตยกรรม 4 ระดับ: Context → Container → Component → Code [อ้างอิง: BROWN-C4]

### 2.3.4 Circular Dependencies
การ import วนระหว่างโมดูลเป็นสัญญาณว่าขอบเขตปนกัน แก้โดยกำหนดทิศทาง dependency ทางเดียว อ้าง FK ด้วย string และย้าย logic ข้ามโมดูลไปไว้ในชั้น service

### 2.3.5 Architectural Decision Records (ADR)
บันทึกสั้นที่ระบุ Context / Decision / Alternatives / Consequences ของการตัดสินใจเชิงสถาปัตยกรรม [อ้างอิง: NYGARD2011]

**การนำมาใช้ในโครงงาน:** Modular Monolith 3 app (`catalog` ← `accounts` ← `materials`), C4 Level 1–2, ADR 0001–0002 (บทที่ 3 หัวข้อ 3.3)

## 2.4 Service Layer, Selectors และ Database Transaction

**สาระสำคัญ**
- ปัญหา **Fat Views** (logic ปนกับ HTTP ทดสอบยาก ใช้ซ้ำไม่ได้) และ **Fat Models** (model กลายเป็น God Object และมี side-effect ซ่อนใน `save()`)
- **Service Layer Pattern** [อ้างอิง: FOWLER2002] และแนวทางของ HackSoft Django Styleguide: `services.py` สำหรับการเขียนข้อมูลและกฎธุรกิจ, `selectors.py` สำหรับการอ่านข้อมูล [อ้างอิง: HACKSOFT]
- **ACID Transactions** และ `@transaction.atomic`, การกัน race condition ด้วย row lock (`select_for_update()`) และ `F()` expressions, งานหลัง commit ด้วย `transaction.on_commit`

**การนำมาใช้ในโครงงาน:** ADR 0002 กำหนดให้ view บาง (~20 บรรทัด), service รับ keyword-only argument และไม่รับ `request`; `Document.add_version()` ล็อกแถวเอกสารก่อนออกเลขเวอร์ชันเพื่อกันเลขชนเมื่ออัปโหลดพร้อมกัน

## 2.5 การออกแบบฐานข้อมูลเชิงสัมพันธ์และ Normalization

**สาระสำคัญ**
- แบบจำลองเชิงสัมพันธ์ [อ้างอิง: CODD1970] และ ER Diagram [อ้างอิง: CHEN1976]
- Functional dependency และรูปแบบบรรทัดฐาน [อ้างอิง: CODD1972; ELMASRI2016]
  - **1NF** ค่าในทุกช่องเป็นค่าเดี่ยว ไม่มีกลุ่มซ้ำ
  - **2NF** ไม่มี partial dependency ต่อ composite key
  - **3NF** ไม่มี transitive dependency
  - **BCNF** ทุก determinant เป็น candidate key
- Integrity constraints: PK, FK (`ON DELETE RESTRICT/PROTECT`), UNIQUE, CHECK, partial unique index
- การ denormalize อย่างมีเหตุผล (เช่น enum ในตาราง, polymorphic reference ใน audit log)

**การนำมาใช้ในโครงงาน:** ออกแบบ ERD 3NF ตั้งแต่ตารางตั้งต้น (UNF) ไล่ถึง BCNF พร้อมระบุจุดที่ตั้งใจไม่ normalize (บทที่ 3 หัวข้อ 3.4)

## 2.6 ประสิทธิภาพการเข้าถึงข้อมูลผ่าน ORM

**สาระสำคัญ**
- QuerySet เป็น **lazy** — ประเมินผลเมื่อวนลูป, slice, `len()`, `list()` ฯลฯ และมี QuerySet caching
- ปัญหา **N+1 Queries** และวิธีแก้: `select_related()` (JOIN สำหรับ FK/1:1) และ `prefetch_related()` (query แยกสำหรับความสัมพันธ์แบบ many)
- `Q` objects สำหรับ OR/NOT, `F` expressions สำหรับคำนวณในฐานข้อมูล, `aggregate()` vs `annotate()`
- เครื่องมือวัด: Django Debug Toolbar, `assertNumQueries` และการทำ index

**การนำมาใช้ในโครงงาน:** DoD กำหนดว่าห้ามมี N+1 query, รวม `select_related`/`prefetch_related` ไว้ใน `selectors.py`, ออกแบบ index เพื่อรองรับเป้าเวลาตอบหน้าค้นหาประมาณ 2 วินาที, นับยอดดาวน์โหลดด้วย aggregate จาก `download_log` แทนการเก็บตัวนับซ้ำ

## 2.7 ความปลอดภัยของเว็บแอปพลิเคชัน

**สาระสำคัญ**
- **OWASP Top 10** ความเสี่ยงสำคัญของเว็บแอปพลิเคชัน เช่น Broken Access Control, Injection, Security Misconfiguration [อ้างอิง: OWASP2021]
- กลไกของ Django: CSRF token, auto-escaping ใน template, ORM ป้องกัน SQL injection, password hashing
- การป้องกันไฟล์: ไม่เปิด Direct URL ให้ไฟล์ (ทุกคำขอตรวจสิทธิ์), ตรวจชนิดไฟล์/ไวรัส, ป้องกัน path traversal

**การนำมาใช้ในโครงงาน:** ตรวจสิทธิ์ฝั่ง server ทุก request (DoD), `storage_path` รับเฉพาะ path สัมพัทธ์ ห้าม `..` และ `\`, ล้างชื่อไฟล์ก่อนบันทึก, เก็บ `sha256` ตรวจไฟล์ซ้ำ, Spike SP-1 (สแกนไวรัส) และ SP-3 (preview แบบไม่เปิด Direct URL — ADR 0003), ตรวจ OWASP Top 10 ใน Sprint 3

## 2.8 กฎหมายที่เกี่ยวข้อง

- **พระราชบัญญัติคุ้มครองข้อมูลส่วนบุคคล พ.ศ. 2562 (PDPA)** — ความยินยอม, หลักการใช้ข้อมูลเท่าที่จำเป็น, สิทธิขอลบ/ทำให้ไม่สามารถระบุตัวตนได้ [อ้างอิง: PDPA2562]
- **พระราชบัญญัติลิขสิทธิ์ พ.ศ. 2537** และฉบับแก้ไข (รวมถึงมาตรการแจ้งเตือนและนำออก (notice and takedown) ของผู้ให้บริการ) [อ้างอิง: COPYRIGHT2537]

**การนำมาใช้ในโครงงาน:** เก็บเวลายอมรับ PDPA (`pdpa_consent_at`), แสดงชื่อเล่นแทนอีเมล, ลบผู้ใช้ด้วย `anonymize()` (ล้างข้อมูลระบุตัวตนแทนการลบแถวเพื่อรักษา FK), Epic E7 ระบบรายงานและแจ้งลบเนื้อหาพร้อม Audit Log

**[ตรวจ: ยืนยันมาตราที่เกี่ยวข้องกับ notice-and-takedown ใน พ.ร.บ.ลิขสิทธิ์ ฉบับแก้ไข (ฉบับที่ 2 พ.ศ. 2558 / ฉบับที่ 4 พ.ศ. 2561) ก่อนอ้าง]**

## 2.9 งานและระบบที่เกี่ยวข้อง

**[เติม: ค้นคว้าและเปรียบเทียบระบบที่มีอยู่ อย่างน้อย 3–5 ระบบ]** ตัวเลือกที่ควรศึกษา:

| ระบบ | ประเด็นที่ควรเปรียบเทียบ |
|---|---|
| กลุ่มแชท/ไดรฟ์ที่นักศึกษาใช้อยู่ (LINE, Facebook Group, Google Drive) | สภาพปัจจุบันที่เป็นต้นเหตุของปัญหา |
| แพลตฟอร์มแบ่งปันเอกสารการเรียน (เช่น Studocu, Course Hero) | โมเดลการแบ่งปัน การคัดกรอง ลิขสิทธิ์ การเข้าถึงสาธารณะ |
| ระบบจัดการการเรียนรู้ของมหาวิทยาลัย (LMS เช่น Moodle / Google Classroom ที่คณะใช้) | เอกสารผูกกับรายวิชาและภาคเรียน ไม่ส่งต่อข้ามรุ่น |
| คลังข้อสอบเก่าของมหาวิทยาลัยอื่นหรือของสโมสรนักศึกษา | การควบคุมข้อสอบและสิทธิ์การเข้าถึง |
| งานวิจัย/โครงงานนักศึกษาที่คล้ายกัน (ค้นใน ThaiLIS, คลังปริญญานิพนธ์) | แนวทางและผลการประเมิน |

ตารางเปรียบเทียบที่แนะนำ (ตารางที่ 2.x): คอลัมน์ = ระบบ, แถว = จัดตามภาค/รุ่น/วิชา · คลังข้อสอบแยก · จำกัดเฉพาะคนในคณะ · คัดกรองก่อนเผยแพร่ · รองรับศิษย์เก่า · แจ้งลบเนื้อหา · ภาษาไทย/ค่าใช้จ่าย

ย่อหน้าปิดบท: สรุปช่องว่าง (gap) ที่ระบบเดิมยังไม่ตอบ → จุดเด่นของ CNtagram คือการผสาน **โครงสร้างภาค–รุ่น–วิชา + คลังข้อสอบรวมศูนย์ + การอนุมัติหลายระดับ + การจำกัดเฉพาะคนในคณะ + กลไก PDPA/ลิขสิทธิ์** ในระบบเดียว
