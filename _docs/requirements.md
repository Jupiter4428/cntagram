# Product Backlog & Requirements — CNtagram

เว็บบอร์ดรวมชีทสรุปและข้อสอบเก่าของคณะวิศวกรรมศาสตร์ (Multi-Department Batch Vault)

> เอกสารนี้**แทน SRS v1** ([`archive/requirements-srs-v1.pdf`](./archive/requirements-srs-v1.pdf)) ซึ่งล็อกสเปกละเอียดเป็นข้อ FR/NFR ตั้งแต่ต้น
> ฉบับนี้เขียนแบบ Agile Requirements ตามหลักใน [`lecture-notes/05-agile-scrum-sprints.md`](./lecture-notes/05-agile-scrum-sprints.md):
> requirement คือ **User Story ที่คุยกันต่อได้ (Negotiable)** จัดลำดับโดย Product Owner และปรับทุกครั้งหลัง Sprint Review (*Inspect & Adapt*)

---

## 1. วิธีอ่านและใช้เอกสารนี้

| หลักการ | ในทางปฏิบัติ |
|---|---|
| **Backlog มีชีวิต ไม่ใช่สัญญา** | PO (อาจารย์ผู้สอน) จัดลำดับใหม่ได้ทุกเมื่อ สมาชิกทุกคนเสนอ story ใหม่ได้โดยเปิด issue ด้วย template |
| **ละเอียดเท่าที่จำเป็น เมื่อจำเป็น** | Story ที่จะเข้า Sprint ถัดไปต้องผ่าน [Definition of Ready](../CONTRIBUTING.md#definition-of-ready-dor) (มี AC ครบ ประเมินแต้มแล้ว) ส่วน story ที่ไกลออกไปเป็นแค่ประโยคเดียวหรือ Epic แล้วค่อยลงรายละเอียดตอน Sprint Planning |
| **GitHub Project คือแหล่งความจริงเดียว** | AC, Story Points, ผู้รับผิดชอบ และสถานะของ story ที่เปิดเป็น issue แล้ว ให้ดูที่ issue บน GitHub เท่านั้น เอกสารนี้เก็บเฉพาะภาพรวม (Vision, Epic, ผู้ใช้, ข้อจำกัด) และ story ที่ยังไม่ได้เปิด issue |
| **ตัวเลขคือเป้าตั้งต้น** | ค่าอย่าง 2 วินาที, 50 MB, 72 ชั่วโมง เป็น**เป้าหมายเริ่มต้น**ที่ทีมกับ PO ตกลงกันและวัดผลจริงใน Sprint Review ไม่ใช่สเปกตายตัว |
| **ไม่ระบุวิธี implement** | การออกแบบ (ตาราง, index, โครงสร้างโค้ด) อยู่ใน [`database-design.md`](./database-design.md) และ [ADR](./adr/) ส่วนเกณฑ์คุณภาพที่ทุก story ต้องผ่านอยู่ใน [Definition of Done](../CONTRIBUTING.md#definition-of-done-dod) |
| **กฎธุรกิจคือสมมติฐานที่ทดสอบได้** | กฎที่ SRS v1 เคยล็อกไว้ (สิทธิ์ การอนุมัติ รุ่นจุดตัด) ถูกย้ายมาเป็น "สิ่งที่ต้องคุยกัน" ใต้ story ที่เกี่ยวข้อง และกลายเป็น Acceptance Criteria เมื่อ story นั้นเข้า Sprint |

---

## 2. Product Vision

นักศึกษาวิศวะทุกภาควิชา**หาชีทสรุปและข้อสอบเก่าของวิชาที่ต้องการเจอได้ในที่เดียว** แทนการไล่ถามในกลุ่มแชทและไดรฟ์ส่วนตัวที่กระจัดกระจาย
เอกสารผ่านการคัดกรองก่อนเผยแพร่ เข้าถึงได้เฉพาะคนในคณะ และเคารพลิขสิทธิ์ของอาจารย์ เพื่อให้ความรู้ส่งต่อจากรุ่นพี่ถึงรุ่นน้องได้ต่อเนื่องทุกปี

**ขอบเขตเริ่มต้น:** ภาควิชา CN (ข้อมูลรุ่น CN21–CN25) แล้วขยายไปภาควิชาอื่นในคณะ

### สัญญาณว่าผลิตภัณฑ์กำลังสำเร็จ (วัดและทบทวนทุก Sprint Review)

| เป้าหมาย | วัดจาก | เป้าตั้งต้น |
|---|---|---|
| ค้นหาเจอเร็ว | เวลาตอบของหน้าค้นหา / จำนวนคลิกจากผลค้นหาถึงไฟล์ | ~2 วินาที, ≤ 2 คลิก |
| คลังมีของจริง | สัดส่วนรายวิชาของ CN21–CN25 ที่มีเอกสารเผยแพร่แล้ว | เพิ่มขึ้นทุก Sprint |
| คัดกรองทันใจ | เวลาเฉลี่ยตั้งแต่อัปโหลดถึงมีผลอนุมัติ/ปฏิเสธ | ภายใน ~7 วัน |
| ตอบเรื่องร้องเรียนทัน | เวลาเฉลี่ยตั้งแต่ได้รับรายงานถึงมีคำตัดสิน | ภายใน ~72 ชั่วโมง |
| คนใช้จริง | ผู้ใช้ต่อเดือน, สัดส่วนผู้ที่อัปโหลด | ติดตามแนวโน้ม ไม่ตั้งเป้า |

---

## 3. ผู้ใช้ (Roles)

| บทบาท | เป็นใคร | สิ่งที่เขาต้องการจากระบบ |
|---|---|---|
| **Guest** | คนที่ยังไม่ล็อกอิน | รู้ว่าระบบนี้คืออะไร สมัคร/ล็อกอินได้ และส่งคำร้องแจ้งลบเอกสารละเมิดลิขสิทธิ์ผ่านแบบฟอร์มสาธารณะได้ (เห็นเอกสารในคลังไม่ได้) |
| **Student / Alumni** | นักศึกษาและศิษย์เก่าคณะวิศวะที่สมัครด้วยอีเมล `@student.tu.ac.th` | หาชีท/ข้อสอบเก่าของวิชาที่เรียน แบ่งปันชีทของตัวเอง รายงานเอกสารที่มีปัญหา และพูดคุยในเว็บบอร์ด |
| **Moderator** | ตัวแทนนักศึกษาประจำภาควิชา (เช่น ประธานรุ่น) ที่ Super Admin แต่งตั้ง | คัดกรองเอกสารของภาคตัวเอง ซ่อนเอกสารที่มีปัญหา ดูรายการรายงานของภาค และดูแลเว็บบอร์ด |
| **Super Admin** | ผู้ดูแลระบบส่วนกลางของคณะ (มีอย่างน้อย 2 คนเพื่อส่งต่องานได้) | ดูแลโครงสร้างข้อมูล นำเข้าเอกสารจำนวนมาก จัดการสิทธิ์ ข้อสอบรุ่นเก่า และตัดสินเรื่องร้องเรียน/ลิขสิทธิ์ |

> ตารางสิทธิ์ละเอียดรายบทบาท **ไม่ล็อกไว้ล่วงหน้า** สิทธิ์แต่ละข้อเกิดขึ้นจาก AC ของ story ที่ทำเสร็จแล้ว (ดูสถานะจริงได้จาก issue ที่ Done)

---

## 4. ข้อจำกัดที่เปลี่ยนไม่ได้ (Constraints)

ส่วนนี้เป็นส่วนเดียวที่ "ล็อก" เพราะมาจากภายนอกทีม:

- **รายวิชา CN331:** พัฒนาด้วย Python 3.12+ / Django บนฐานข้อมูลเชิงสัมพันธ์ จัดการงานบน GitHub (Issues, Projects, Pull Request) และ Demo สุดท้ายสัปดาห์ที่ 14
- **ผู้ใช้ต้องเป็นคนในคณะ:** ยืนยันตัวตนด้วยอีเมล `@student.tu.ac.th` (หลัก 3–4 ของรหัสนักศึกษา = `10` คือคณะวิศวะ)
- **PDPA:** ขอความยินยอมก่อนเก็บข้อมูล ไม่แสดงอีเมลต่อผู้ใช้อื่น และลบ/ปิดบังข้อมูลส่วนบุคคลได้เมื่อผู้ใช้ขอ
- **ลิขสิทธิ์:** ต้องมีช่องทางให้เจ้าของลิขสิทธิ์แจ้งลบเนื้อหา และนำเนื้อหาลงได้

---

## 5. Epics

Epic คือกลุ่มคุณค่าใหญ่ที่แตกเป็นหลาย story ได้ ทุก story ต้องตัดแบบ **Vertical Slice** (UI + View + Service + DB ในชิ้นเดียว ใช้งานได้จริงเมื่อ Done)

| Epic | คุณค่าที่ผู้ใช้ได้ |
|---|---|
| **E1 เข้าระบบอย่างปลอดภัย** | เฉพาะคนในคณะเข้าคลังได้ และศิษย์เก่ายังใช้งานต่อได้ |
| **E2 โครงสร้างคลัง** | เอกสารจัดเป็นระเบียบตาม ภาควิชา → รุ่น → รายวิชา และขยายไปภาคอื่นได้ |
| **E3 แบ่งปันเอกสาร** | นักศึกษาอัปโหลดชีท/ข้อสอบเก่าเข้าที่ที่ถูกต้องได้ง่าย |
| **E4 คัดกรองคุณภาพ** | ทุกไฟล์ผ่านการตรวจก่อนเผยแพร่ ข้อสอบคุมเข้มกว่าชีททั่วไป |
| **E5 ค้นหาและอ่าน** | พิมพ์รหัสวิชาแล้วเจอเอกสารจากทุกรุ่นในหน้าเดียว |
| **E6 ชุมชนและปฏิสัมพันธ์เว็บบอร์ด** | บรรยากาศเว็บบอร์ดยุค 2000s, พูดคุยทักทาย, โพลสำรวจ, เพลงประกอบ, และการแลกเปลี่ยนในชุมชน |
| **E7 ลิขสิทธิ์และความไว้วางใจ** | รายงานปัญหาได้ นำเนื้อหาลงได้อย่างตรวจสอบย้อนหลังได้ |
| **TD งานเทคนิค / หนี้ทางเทคนิค** | ทีมส่งมอบได้เร็วและมั่นคงขึ้นใน Sprint ถัดไป (ใช้โควตา ≥ 20% ของแต้มต่อ Sprint ตั้งแต่ Sprint 2) |

---

## 6. Product Backlog

### 6.1 Story ที่เปิดเป็น issue แล้ว (Sprint 1)

รายละเอียด AC และแต้มอยู่ที่ issue ลำดับในตารางคือลำดับความสำคัญปัจจุบัน

| ID | Story | Epic | MoSCoW | Issue |
|---|---|---|---|---|
| SP-0 | ออกแบบ ERD (3NF) | E2 | Must | [#23](https://github.com/Jupiter4428/cntagram/issues/23) |
| US-1 | สมัครสมาชิกด้วยอีเมลคณะ | E1 | Must | [#28](https://github.com/Jupiter4428/cntagram/issues/28) |
| US-2 | เข้าสู่ระบบ/ออกจากระบบ และบล็อก Guest | E1 | Must | [#24](https://github.com/Jupiter4428/cntagram/issues/24) |
| US-3 | Super Admin เพิ่มภาควิชา | E2 | Must | [#25](https://github.com/Jupiter4428/cntagram/issues/25) |
| US-4 | Super Admin เพิ่มรุ่นและรายวิชาในรุ่น | E2 | Must | [#26](https://github.com/Jupiter4428/cntagram/issues/26) |
| US-5 | อัปโหลดชีท PDF | E3 | Must | [#29](https://github.com/Jupiter4428/cntagram/issues/29) |
| US-6 | Moderator อนุมัติชีทสรุป/สไลด์ | E4 | Must | [#30](https://github.com/Jupiter4428/cntagram/issues/30) |
| US-7 | ค้นหาชีทตามรหัสวิชาและเปิดอ่าน | E5 | Must | [#31](https://github.com/Jupiter4428/cntagram/issues/31) |
| US-8 | ดาวน์โหลดแบบป้องกัน + นับสถิติ | E5 | Should | [#32](https://github.com/Jupiter4428/cntagram/issues/32) |
| US-9 | ข้อสอบเก่าต้องอนุมัติทั้ง Moderator และ Admin | E4 | Should | [#33](https://github.com/Jupiter4428/cntagram/issues/33) |
| US-10 | แต่งตั้ง/ถอด Moderator | E4 | Should | [#27](https://github.com/Jupiter4428/cntagram/issues/27) |

#### ขอบเขต Sprint 1 ตามหัวข้อของวิชา

ทุกหัวข้อตัดเป็น Vertical Slice อยู่ใน story ด้านบน ไม่แยกเป็น story "ทำ Model ทั้งหมด" หรือ "ทำ Form ทั้งหมด" ([lecture 05: Vertical Slicing](./lecture-notes/05-agile-scrum-sprints.md#เทคนิคการซอยงาน-backlog-vertical-slicing-vs-horizontal-slicing))

| หัวข้อ | อยู่ใน |
|---|---|
| **Authentication** | US-1 สมัคร (อีเมลคณะ + PDPA consent), US-2 login/logout/rate limit/บล็อก Guest, US-3 `super_admin_required` + seed `role` + Super Admin คนแรก, US-10 Moderator ตามภาค, US-13 ลบบัญชีแบบ Anonymize |
| **Forms** (Django Form/ModelForm, validation ฝั่ง server เรียกกฎใน model ตัวเดียว) | US-1 `RegisterForm`, US-2 `LoginForm`, US-3 `DepartmentForm`, US-4 `BatchForm`/`CourseForm`/`BatchCourseForm`, US-5 `UploadForm`, US-6 `ReviewForm`, US-7 `SearchForm`, US-17 `BulkImportForm`, US-25 `HideDocumentForm`, US-32 `ReportDocumentForm`, US-33 `TakedownRequestForm`, US-35 `ResolveReportForm` |
| **Core Models** | SP-0 ERD; model ที่มีในระบบ: `accounts` (`User`, `Role`, `UserRole`, `UserCounter`, `PollVote`, `ShoutboxMessage`), `catalog` (`Department`, `Batch`, `Course`, `BatchCourse`, `SystemSetting`), `materials` (`DocType`, `ExamPeriod`, `Document`, `ExamDetail`, `DocumentVersion`, `Approval`, `DocTypeRequiredRole`, `DownloadLog`, `Report`, `TakedownRequest`), และ `webboard` (`BoardCategory`, `Thread`, `Post`); ข้อมูลตั้งต้น: `role` ใน US-3, รุ่น/วิชาตัวอย่าง (`seed_catalog`) ใน US-4, `doc_type`/`exam_period`/`system_setting` ใน US-5, หมวดหมู่เว็บบอร์ดใน `webboard` migration `0002_seed_categories` |
| **Dashboard** | US-2 หน้าแรก Guest + navbar, US-3 Dashboard หน้าแรก (เมนู Admin), US-6 Approval Queue ใน dashboard, US-34 (รวม US-22) แสดงรายการ "ไฟล์ของฉัน + สถานะและเหตุผลที่ถูกปฏิเสธ" และแจ้งเตือนจำนวนไฟล์รออนุมัติของ Moderator บนหน้าแรก |

> **ปรับ 2026-10-13 ตามหลักใน lecture 05:** งานที่ค้นพบระหว่าง Sprint ไม่เพิ่มเป็น story ใหม่กลาง Sprint 1 (กัน Scope Creep และงานที่ยังไม่ผ่าน DoR) งานที่เป็น Blocker ของ story ใน Sprint (seed ข้อมูลตั้งต้น) ใส่เป็นงานย่อยของ story นั้นแทน ส่วนงานใหม่รอ Sprint Planning ถัดไปตาม Velocity จริง

### 6.2 Story ที่พัฒนาใน Sprint 2 – Sprint 3 (เปิดใช้งานในระบบปัจจุบัน)

#### E1 เข้าระบบอย่างปลอดภัย

| ID | Story | MoSCoW | Issue / PR |
|---|---|---|---|
| US-13 | **As a** ผู้ใช้ **I want** ขอลบบัญชีของตัวเอง **so that** ข้อมูลส่วนบุคคลของฉันถูกลบตาม PDPA (`User.anonymize()`) | Should | [#144](https://github.com/Jupiter4428/cntagram/issues/144) |

#### E2 โครงสร้างคลัง

| ID | Story | MoSCoW | Issue / PR |
|---|---|---|---|
| US-17 | **As a** Super Admin **I want** นำเข้าไฟล์เดิมจำนวนมากด้วย CSV + ZIP พร้อมโหมดทดลองรัน (dry run) **so that** ย้ายข้อมูล CN21–CN25 เข้าระบบได้ครบโดยไม่ต้องอัปโหลดทีละไฟล์ | Must | [#215](https://github.com/Jupiter4428/cntagram/issues/215) · PR [#223](https://github.com/Jupiter4428/cntagram/pull/223) |

#### E3 แบ่งปันเอกสาร

| ID | Story | MoSCoW | Issue / PR |
|---|---|---|---|
| US-12 | **As a** ผู้ใช้ **I want** ระบบปฏิเสธไฟล์ที่ซ้ำกับไฟล์ในคลังด้วย SHA-256 **so that** คลังไม่มีไฟล์ขยะซ้ำกันหลายฉบับ | Should | [#143](https://github.com/Jupiter4428/cntagram/issues/143) |
| US-21 | **As a** ผู้อัปโหลด **I want** ส่งไฟล์เวอร์ชันใหม่ แก้คำอธิบาย หรือลบไฟล์ของตัวเอง **so that** ชีทของฉันถูกต้องและทันสมัย | Should | [#217](https://github.com/Jupiter4428/cntagram/issues/217) · PR [#234](https://github.com/Jupiter4428/cntagram/pull/234) |
| US-34 | **As a** ผู้อัปโหลดและ Moderator **I want** เห็นรายการ "ไฟล์ของฉัน" พร้อมสถานะและเหตุผลที่ไม่ผ่านอนุมัติ รวมถึงจำนวนไฟล์รออนุมัติบนหน้าแรก **so that** ติดตามสถานะเอกสารและคิวตรวจได้ทันที (รวม US-22) | Should | [#34](https://github.com/Jupiter4428/cntagram/issues/34) |

#### E4 คัดกรองคุณภาพ

| ID | Story | MoSCoW | Issue / PR |
|---|---|---|---|
| US-25 | **As a** Moderator / Super Admin **I want** ปฏิเสธไฟล์พร้อมเหตุผล และซ่อนไฟล์ที่เผยแพร่แล้วแต่มีปัญหา (`status = hidden`) **so that** คลังมีแต่เอกสารที่ถูกต้อง | Must | [#216](https://github.com/Jupiter4428/cntagram/issues/216) · PR [#227](https://github.com/Jupiter4428/cntagram/pull/227) |

#### E5 ค้นหาและอ่าน

| ID | Story | MoSCoW | Issue / PR |
|---|---|---|---|
| US-11 | **As a** นักศึกษา **I want** กรองผลค้นหาตาม ประเภทเอกสาร ปีการศึกษา ช่วงสอบ **so that** เจอข้อสอบเก่าที่ตรงกับที่จะสอบ | Should | [#142](https://github.com/Jupiter4428/cntagram/issues/142) |

#### E6 ชุมชนและปฏิสัมพันธ์เว็บบอร์ด

| ID | Story | MoSCoW | Issue / PR |
|---|---|---|---|
| US-36 | **As an** นักศึกษาที่เข้าสู่ระบบ **I want** พิมพ์ส่งข้อความทักทายสดใน Shoutbox โดยไม่รีเฟรชหน้าเว็บ **so that** มีปฏิสัมพันธ์ ส่งกำลังใจ และพูดคุยกับเพื่อนๆ ในชุมชนได้ทันที | Should | [#89](https://github.com/Jupiter4428/cntagram/issues/89) · PR [#180](https://github.com/Jupiter4428/cntagram/pull/180) |
| US-37 | **As a** ผู้ใช้งานเว็บบอร์ด **I want** โหวตโพลประจำสัปดาห์และเห็นกราฟผลคะแนนทันทีโดยไม่รีเฟรชหน้าเว็บ **so that** ร่วมแสดงความคิดเห็นในประเด็นการเรียนของชาววิศวะได้สะดวก | Should | [#89](https://github.com/Jupiter4428/cntagram/issues/89) · PR [#180](https://github.com/Jupiter4428/cntagram/pull/180) |
| US-38 | **As a** ผู้ใช้งานเว็บบอร์ด **I want** เห็นยอดผู้เข้าชมเว็บไซต์สะสมที่นับเพิ่มจริงในรูปแบบ LCD 6 หลัก **so that** ทราบสถิติความเคลื่อนไหวและความนิยมของเว็บบอร์ดในสไตล์เรโทร | Could | [#89](https://github.com/Jupiter4428/cntagram/issues/89) · PR [#180](https://github.com/Jupiter4428/cntagram/pull/180) |
| US-39 | **As an** นักศึกษา **I want** เปิดฟังเพลงประกอบ BGM Player ยุค 2000s พร้อมเลือกเพลงและปรับระดับเสียงได้ **so that** สร้างบรรยากาศ Nostalgia และผ่อนคลายขณะอ่านชีทเตรียมสอบ | Could | [#161](https://github.com/Jupiter4428/cntagram/issues/161) · PR [#180](https://github.com/Jupiter4428/cntagram/pull/180) |
| E6-WB | **As a** นักศึกษาและ Moderator **I want** ตั้งกระทู้ถาม-ตอบแยกหมวดหมู่และผูกรายวิชา ตอบกลับ แก้ไข/ลบข้อความ ปักหมุด/ล็อกกระทู้ และใช้อีโมติคอน MSN / ฝังภาพ GIF **so that** แลกเปลี่ยนความรู้ในบรรยากาศเว็บบอร์ดยุค 2000s | Should | PR [#202](https://github.com/Jupiter4428/cntagram/pull/202), [#222](https://github.com/Jupiter4428/cntagram/pull/222), [#226](https://github.com/Jupiter4428/cntagram/pull/226), [#232](https://github.com/Jupiter4428/cntagram/pull/232), [#233](https://github.com/Jupiter4428/cntagram/pull/233) |

##### รายละเอียด Acceptance Criteria ของฟังก์ชันชุมชนและเรโทรวิดเจ็ต (US-36 – US-39)

###### US-36: Shoutbox ทักทายสดชุมชนเด็กวิศวะ (Community Shoutbox with AJAX)
- **AC 1 (Authentication & Guest Mode):** เฉพาะผู้ใช้ที่ล็อกอินแล้วเท่านั้นที่แสดงกล่องพิมพ์ข้อความและส่งข้อความได้ หากเป็นผู้เข้าชมทั่วไป (Guest) จะแสดงปุ่ม "เข้าสู่ระบบเพื่อพิมพ์ทักทาย" ที่ลิงก์ตรงไปยังหน้า Login
- **AC 2 (Author Attribution):** ข้อความที่ส่งจะระบุสังกัดและชื่อเล่นอัตโนมัติในรูปแบบ `[<รหัสภาควิชา>] <ชื่อเล่น>` (เช่น `[CN] บอย`) ตามโปรไฟล์ของนักศึกษา
- **AC 3 (Persistent Storage & Rolling Window):** จัดเก็บข้อความในตาราง `ShoutboxMessage` และดึงข้อความล่าสุดมาแสดงผลเรียงตามเวลาในกล่องสนทนาพร้อม scrollbar
- **AC 4 (Seamless Non-refresh Submission):** ส่งข้อความด้วย AJAX (Fetch API) และอัปเดตกล่องแชททันทีโดยไม่ต้องโหลดหรือรีเฟรชหน้าเว็บทั้งหน้า พร้อมเลื่อนกล่องข้อความลงล่างสุดอัตโนมัติ
- **AC 5 (Validation & Security):** จำกัดความยาวข้อความไม่เกิน 150 ตัวอักษร, ป้องกันข้อความว่างเปล่า, ป้องกัน XSS ผ่าน Django template auto-escaping และมี CSRF Protection

###### US-37: โพลสำรวจความคิดเห็นประจำสัปดาห์ (Weekly Community Poll with AJAX)
- **AC 1 (Seamless Non-refresh Voting):** ผู้ใช้เลือกตัวเลือกและกด "โหวต" ส่งข้อมูลผ่าน AJAX และสลับหน้าจอไปแสดงผลลัพธ์ทันทีโดยไม่รีเฟรชหน้าเว็บ
- **AC 2 (Live Percentage & Bar Graph):** คำนวณเปอร์เซ็นต์คะแนนสดของแต่ละตัวเลือก (`คะแนน / คะแนนรวม * 100`) และแสดงหลอดกราฟแท่งความกว้างตามสัดส่วนร้อยละ
- **AC 3 (Per-User Vote Persistence):** จัดเก็บผลโหวตในตาราง `PollVote` (1 บัญชีโหวตได้ 1 เสียงและเปลี่ยนตัวเลือกได้) พร้อมอัปเดตป้ายสถานะเป็น "โหวตแล้ว" ทันทีหลังโหวตสำเร็จ
- **AC 4 (Interactive View Toggle):** มีปุ่ม "ดูตัวเลือก / โหวตใหม่" และ "กลับไปดูผลโหวต" เพื่อให้ผู้ใช้สลับดูตัวเลือกหรือผลคะแนนได้สะดวก
- **AC 5 (Graceful Degradation):** รองรับ fallback เป็นการส่งฟอร์มแบบดั้งเดิม (POST + 302 redirect) หากเบราว์เซอร์ไม่รองรับ JavaScript

###### US-38: ตัวนับสถิติผู้เข้าชมเว็บไซต์แบบเรียลไทม์ (Real-time Retro Visitor Counter)
- **AC 1 (Atomic Counting):** ทุกครั้งที่มีการเปิดหน้าแรก (Home) ของเว็บไซต์ ระบบจะเพิ่มค่ายอดผู้เข้าชมสะสมทีละ 1 แบบ atomic
- **AC 2 (6-Digit LCD Presentation):** แสดงผลเป็นตัวเลข 6 หลักแบบเติมศูนย์ด้านหน้า (เช่น `000039`) ในกรอบ LCD สไตล์เรโทร
- **AC 3 (Accessibility):** ใช้องค์ประกอบ semantic `<output>` พร้อมระบุ `aria-label` ตามยอดตัวเลขจริงสำหรับ screen reader
- **AC 4 (Collapsible Window):** ฝังเป็นวิดเจ็ตใน sidebar ที่สามารถย่อ-ขยายได้ด้วย `<details>` / `<summary>`
- **AC 5 (Real Statistics Label):** กำกับข้อความใต้ตัวเลขชัดเจนว่าเป็น "สถิติยอดผู้เข้าชมสะสมแบบเรียลไทม์"

###### US-39: เครื่องเล่นเพลงประกอบเว็บบอร์ด BGM Player ยุค 2000s (Interactive Retro BGM Player)
- **AC 1 (Playback Engine):** ควบคุมการเล่น/หยุดชั่วคราว (Play/Pause), เพลงก่อนหน้า (Prev), และเพลงถัดไป (Next) ได้อย่างแม่นยำ
- **AC 2 (Seekbar & Time Elapsed):** แสดงแถบความคืบหน้า (Seekbar) ที่ลากเลื่อนตำแหน่งการเล่นเพลงได้ พร้อมแสดงเวลา `mm:ss / mm:ss`
- **AC 3 (Curated Playlist):** บรรจุเพลย์ลิสต์เพลงย้อนยุคและเพลงชิปจูนประจำคณะ สามารถเปิด-ปิดดูรายชื่อเพลงและกดเลือกเพลงที่ต้องการได้
- **AC 4 (Volume & Mute Control):** มีแถบเลื่อนปรับระดับเสียง และปุ่มปิด/เปิดเสียง (Mute/Unmute)
- **AC 5 (Y2K / Winamp Aesthetic):** มีแอนิเมชันแผ่นดิสก์หมุนขณะเล่นเพลง และสไตล์กรอบตามธีม Windows Classic / Y2K

#### E7 ลิขสิทธิ์และความไว้วางใจ

| ID | Story | MoSCoW | Issue / PR |
|---|---|---|---|
| US-32 | **As a** ผู้ใช้ **I want** รายงานเอกสารที่มีปัญหา (ละเมิดลิขสิทธิ์, ข้อสอบที่ห้ามเผยแพร่, เนื้อหาผิด) **so that** ผู้ดูแลรู้และจัดการได้ (`Report`) | Should | [#218](https://github.com/Jupiter4428/cntagram/issues/218) · PR [#229](https://github.com/Jupiter4428/cntagram/pull/229) |
| US-33 | **As a** อาจารย์/เจ้าของลิขสิทธิ์ที่ไม่มีบัญชี **I want** แจ้งลบเนื้อหาผ่านแบบฟอร์มสาธารณะ (`/materials/takedown/`) **so that** งานของฉันถูกนำลงจากระบบ (`TakedownRequest`) | Should | [#219](https://github.com/Jupiter4428/cntagram/issues/219) · PR [#230](https://github.com/Jupiter4428/cntagram/pull/230) |
| US-35 | **As a** Super Admin **I want** ตรวจเรื่องร้องเรียนแล้วตัดสิน (`remove`, `dismiss`, `request_changes`) พร้อมบันทึกเหตุผลและซ่อนเอกสารอัตโนมัติ **so that** ข้อพิพาทลิขสิทธิ์จบได้อย่างโปร่งใส | Should | [#220](https://github.com/Jupiter4428/cntagram/issues/220) · PR [#231](https://github.com/Jupiter4428/cntagram/pull/231) |

#### TD งานเทคนิค / หนี้ทางเทคนิค (Track = Tech Debt)

เขียนตาม **Technical Story Format** (Title / Value / Points / AC) ดู [CONTRIBUTING](../CONTRIBUTING.md#technical-story-งาน-refactoring-และ-tech-debt)

| ID | Title | Value |
|---|---|---|
| TD-1 | Chore: ตั้ง CI ด้วย GitHub Actions รัน `python manage.py test` ทุก PR ([#107](https://github.com/Jupiter4428/cntagram/issues/107)) — ทำใน **Sprint 3** | กันโค้ดที่เทสต์ไม่ผ่านเข้า `main` และเป็นฐานของ coverage > 80% |
| TD-9 | Chore: ตั้ง coverage.py (`.coveragerc` + requirements) ตาม DoD ของ Sprint 2 ([#108](https://github.com/Jupiter4428/cntagram/issues/108)) | ทุกคนวัด coverage บนเครื่องได้ตัวเลขเดียวกัน และแนบผลใน PR ได้ |
| TD-8 | Chore: เพิ่มด่าน Static Analysis ใน CI (`black --check`, `flake8` + `.flake8`, `bandit`) ตาม [lecture 07](./lecture-notes/07-ci-cd-and-static-analysis.md) — ทำใน **Sprint 3** | โค้ดใน `main` มีรูปแบบเดียวกัน ไม่มี import/ตัวแปรที่ไม่ใช้ และไม่มี hardcoded secret ก่อน deploy ขึ้น Cloud |
| TD-4 | Docs: C4 Context/Container Diagram ให้ตรงกับระบบที่ deploy จริง | ทีมและผู้ประเมินเห็นสถาปัตยกรรมตรงกัน |
| TD-5 | Refactor: ย้าย business logic ที่สะสมใน view ระหว่าง Sprint 1 เข้า `services.py` / `selectors.py` | View สั้น ทดสอบ logic ได้ตรงโดยไม่ผ่าน HTTP |
| TD-7 | Refactor: แยก partial ข้อมูลเอกสารที่ซ้ำใน `vault.html` / `document_detail.html` ([#40](https://github.com/Jupiter4428/cntagram/issues/40)) | แก้ฟิลด์ที่แสดงของเอกสารที่เดียว มีผลทั้งหน้าค้นหาและหน้าเอกสาร |
| TD-2 | Chore: Seed ข้อมูลตั้งต้น (`role`, `doc_type`, `exam_period`, `system_setting`, `seed_catalog`, `seed_materials`) ([#35](https://github.com/Jupiter4428/cntagram/issues/35)) | เตรียมข้อมูลพื้นฐานให้พร้อมใช้งานทันทีหลังติดตั้ง |
| TD-3 | Chore: ตั้งค่า Django Admin ครบทุกแอปพร้อมป้องกันการละเมิดกฎธุรกิจ ([#36](https://github.com/Jupiter4428/cntagram/issues/36)) | ผู้ดูแลตรวจสอบข้อมูลหลังบ้านได้อย่างปลอดภัย |

### 6.3 Spike (ค้นคว้าก่อนตัดสินใจ)

| ID | คำถาม | ผลลัพธ์ที่ได้ในระบบ |
|---|---|---|
| SP-0 | ออกแบบฐานข้อมูลอย่างไรให้เป็น 3NF และรองรับกฎอนุมัติหลายบทบาท | [`database-design.md`](./database-design.md) + [ADR 0001](./adr/0001-modular-monolith-and-app-boundaries.md), [ADR 0004](./adr/0004-approval-tables-in-materials.md) |
| SP-3 | Preview PDF บนเว็บโดยไม่เปิด Direct URL (ทุกคำขอผ่านการตรวจสิทธิ์) | `materials:document_preview` + [ADR 0003](./adr/0003-document-storage-and-protected-preview.md) |
| SP-4 | Deploy ที่ไหน สำรองและกู้คืนข้อมูลอย่างไร | Render (Singapore) + Managed PostgreSQL + [ADR 0005](./adr/0005-production-deployment-and-backup.md) + [`backup-operations.md`](./backup-operations.md) |

---

## 7. คุณภาพของระบบ (Non-Functional) — อยู่ตรงไหนใน Agile

แทนที่จะเป็นรายการ NFR ที่ล็อกไว้ คุณภาพแต่ละด้านถูกใส่ไว้ในที่ที่ตรวจได้จริง:

| ด้าน | เป้าตั้งต้น | อยู่ที่ |
|---|---|---|
| ความปลอดภัยพื้นฐาน (CSRF, XSS, SQL Injection, ตรวจสิทธิ์ฝั่ง server) | ต้องผ่านทุก story | **DoD** |
| กฎสิทธิ์และกฎการอนุมัติมี automated test | ต้องผ่านทุก story ที่แตะสิทธิ์ | **DoD** |
| ไม่มี N+1 query | ต้องผ่านทุก story ที่แสดงรายการ | **DoD** |
| ความเร็วหน้าค้นหา | ~2 วินาที กับข้อมูลปกติ | **AC** ของ US-7 |
| ลิงก์ดาวน์โหลด/preview ต้องตรวจสิทธิ์ทุกครั้ง | ไม่มี Direct URL | **AC** ของ US-8, SP-3 |
| ใช้งานบนมือถือ | จอกว้างตั้งแต่ ~360px, ภาษาไทย | **AC** ของ story ที่มีหน้าจอ |
| PDPA | ขอความยินยอม, ไม่แสดงอีเมล, ลบบัญชีได้ | **AC** ของ US-1, US-13 |
| Coverage | > 80% (Sprint 2) | **DoD** ของ Sprint 2 / TD-9 (วัดบนเครื่อง) · TD-1 (ด่านใน CI, Sprint 3) |
| ความพร้อมใช้งานและการสำรองข้อมูล | ~99%/เดือน, สำรองวันละครั้ง | **SP-4** แล้วกลายเป็น story ของ Sprint 3 |
| OWASP Top 10 | ตรวจรอบสุดท้าย | **Sprint 3** |

---

## 8. Roadmap และสรุปผลลัพธ์จริง (Agile Velocity)

| Sprint | Sprint Goal | Epic หลัก | Planned | Done (DoD) | Actual Velocity | สัดส่วน Tech Debt |
|---|---|---|---|---|---|---|
| **Sprint 1** | นักศึกษา CN สมัคร ล็อกอิน อัปโหลดชีท และค้นหาชีทที่ Moderator อนุมัติแล้วได้ | E1, E2, E3, E4, E5 (US-1 – US-7) | 28 pts | 21 pts | **21** | ~14% (TD-2 seed data) |
| **Sprint 2** | Must story ทั้ง 7 ของ Sprint 1 ใช้งานได้ครบทั้งหน้าเว็บและหลังบ้าน: Super Admin ตั้งค่าภาค รุ่น และวิชาผ่านหน้าเว็บได้ Moderator เปิดดู PDF ก่อนอนุมัติหรือปฏิเสธพร้อมเหตุผล และทุก story ผ่าน DoD ของ Sprint 2 (มี unit test, coverage รวม ≥ 80%) | US-2, US-3, US-4, US-6 (ยกมาจาก Sprint 1) + TD (#93, #67, TD-9) | 21 pts | 21 pts | **21** | 24% (TD 5 pts: #93, #67, TD-9) |
| **Sprint 3** | คลังพร้อมใช้งานจริงบน Cloud: ปลอดภัยตาม OWASP ครบถ้วน CI/CD และเจ้าของลิขสิทธิ์แจ้งลบเนื้อหาได้ | E1, E3, E7, SP-4, TD-1 (CI), TD-8 (Static Analysis) | 21 pts | 24 pts | **24** | ~21% (TD-1, TD-8, SP-4) |
| **Final (สัปดาห์ 14)** | Live Demo + Production Readiness & Agile Metrics (Average Velocity = 22 pts/Sprint, Coverage 96%, 660+ Automated Tests) | E1–E7 ครบสมบูรณ์พร้อม Production Release v1.0.0 | — | — | **เฉลี่ย 22** | **≥ 20% ทุก Sprint** |

> **หมายเหตุการคำนวณ Velocity:**
> Velocity คำนวณจากผลรวมของ Story Points เฉพาะชิ้นงานที่เสร็จสมบูรณ์ 100% ตามเกณฑ์ Definition of Done (DoD) และ merge เข้าสู่ branch หลักแล้วเท่านั้น งานที่ไม่ผ่าน DoD หรือยังไม่เสร็จสมบูรณ์จะไม่ถูกนับแต้มในรอบนั้นๆ ตามหลักการ Empirical Process Control ของ Agile Scrum

---

## 9. ประวัติการเปลี่ยนแปลง

| วันที่ | การเปลี่ยนแปลง |
|---|---|
| 2026-10-12 | แทน SRS v1 ด้วย Product Backlog แบบ Agile: แปลง FR เป็น Epic/User Story, แปลง NFR เป็น DoD/AC/Spike, ย้ายกฎที่ล็อกไว้ (R-1 – R-6, FR-2.4, FR-2.5) มาเป็นประเด็นที่ต้องคุยใต้ story, ย้ายประเด็นค้าง (O-1 – O-7) เป็น story/spike |
| 2026-10-13 | ตรวจขอบเขต Sprint 1 (Authentication, Forms, Core Models, Dashboard) แล้วปรับตาม lecture 05 (ไม่เพิ่ม story ใหม่กลาง Sprint): US-34 Dashboard (#34, รวม US-22) และ TD-3 Django admin (#36) เข้า Product Backlog รอ Sprint 2, TD-2 seed (#35 ปิด) ย้ายเป็นงานย่อยของ US-3/US-5; DoD ในทุก issue เพิ่มข้อ View บาง / ไม่มี N+1 และ circular import / อัปเดตเอกสาร ตาม DoD ใน lecture; แก้ issue ให้ตรงกับ model จริง — US-1 เพิ่ม AC PDPA consent/ชื่อเล่น/ภาควิชา, US-5 ใช้ Document/ExamDetail/DocumentVersion แทน SheetFile, US-10 ใช้ `user_role` แทนตาราง M:N ใหม่, US-8 นับจาก `download_log`, US-4/US-7 index ตาม database-design §5; ระบุ Form ของแต่ละ story; DoD ใน issue เปลี่ยนเป็น merge เข้า `develop` |
| 2026-10-16 | US-7 (#31): ต้นแบบ SP-3 (preview ผ่าน view ที่ตรวจสิทธิ์ ไม่มี `MEDIA_URL`) บันทึกเป็น ADR 0003 (Proposed); `SearchForm` ปฏิเสธรุ่นที่ไม่อยู่ในภาคที่เลือก; การเช็ก `scan_status` และชนิดไฟล์ก่อน preview ย้ายไปเป็นงานของ US-24; เพิ่ม TD-7 (#40) แยก partial ข้อมูลเอกสารจาก code review |
| 2026-10-26 | เพิ่ม TD-8 (Static Analysis ใน CI: Black, Flake8, Bandit) ตาม lecture 07 สัปดาห์ที่ 12 กำหนดทำใน Sprint 3; TD-1 คงขอบเขตเดิม (เทสต์ + coverage ใน Sprint 2) |
| 2026-10-27 | Sprint 2 Planning: Velocity Sprint 1 = 21 (นับ story ใน §6.1 ที่ story และ sub-issue ปิดครบ); ตั้ง Sprint 2 Goal ใหม่ใน §8; Sprint 2 ทำเนื้อหาถึงสัปดาห์ที่ 11 จึงย้าย TD-1 (CI, #107) ไป Sprint 3 และเพิ่ม TD-9 (coverage.py, #108); คง `LANGUAGE_CODE = 'en-us'` แล้วแปล error ในฟอร์มเอง (#97) |
| 2026-10-28 | DoD ของ Sprint 2 (coverage): issue ที่เข้า Sprint 2 ขึ้นไปโดยไม่ได้ยกมาจาก Sprint 1 และยังไม่มี PR เปิดอยู่ (#42, #107, #111, #115) เพิ่มข้อ "แนบผล `coverage report -m --fail-under=80` ใน PR, coverage รวมไม่ต่ำกว่า 80%" ตาม lecture 06 (#108 มีข้อนี้อยู่แล้ว); ตั้ง coverage.py ด้วย `.coveragerc` และ `coverage==7.17.0` ใน requirements (TD-9, #108) วัดบน `develop` (`14b4da1`) ได้ 264 tests ผ่าน, coverage รวม 94% |
| 2026-11-03 | Sprint 3 (ส่งงาน 2026-11-09 ต้องเสร็จ 2026-11-08): ดึง story ที่ผูกกับฟีเจอร์หลักและเล็กพอทำทันเข้า Sprint 3 แล้วเลื่อนเลข story ให้ต่อจาก US-10 ไม่ชนกัน (US-22 และ US-34 คงเลขเดิมเพราะมี issue แล้ว) — เข้า Sprint 3: เดิม US-26 → **US-11** ([#142](https://github.com/Jupiter4428/cntagram/issues/142)), US-21 ส่วนไฟล์ซ้ำ → **US-12** ([#143](https://github.com/Jupiter4428/cntagram/issues/143)), US-13 คงเดิม ([#144](https://github.com/Jupiter4428/cntagram/issues/144)); ที่เหลือเลื่อน: 11→14, 12→15, 14→16, 15→17, 16→18, 17→19, 18→20, 19→21, 20→23, US-21 ส่วนสแกนไวรัส → 24, 23→25, 24→26, 25→27, 27→28, 28→29, 29→30, 30→31, 31→32, 32→33, 33→35; เลขในตารางและประวัติข้างบนใช้เลขใหม่แล้ว |
| 2026-11-08 | เพิ่ม User Story ของฟังก์ชันชุมชนและเรโทรวิดเจ็ตหน้าแรกใน E6 ตามการพัฒนาจริงใน PR #180 (Refs #89, #161): **US-36** (Shoutbox ทักทายสดแบบ AJAX), **US-37** (โพลประจำสัปดาห์แบบ AJAX), **US-38** (ตัวนับสถิติผู้เข้าชมเว็บไซต์แบบเรียลไทม์), และ **US-39** (เครื่องเล่นเพลงประกอบเว็บบอร์ด BGM Player ยุค 2000s) พร้อมระบุ Acceptance Criteria ละเอียดครบถ้วน |
| 2026-11-09 | เพิ่มแอป `webboard` (กระดานสนทนาชุมชนเรโทรยุค 2000s พร้อม MSN emoticons, GIF embeds และการแก้ไข/ลบกระทู้และข้อความ), ระบบนำเข้าไฟล์จำนวนมาก (US-17), การซ่อนเอกสารที่เผยแพร่แล้ว (US-25), ระบบรายงานปัญหาและแจ้งลบเนื้อหาละเมิดลิขสิทธิ์ (US-32, US-33, US-35) และอัปเดต §6 และ §10 ให้แสดงเฉพาะฟีเจอร์ที่มีอยู่จริงในระบบปัจจุบัน |

---

## 10. สรุปฟังก์ชันที่มีในระบบปัจจุบัน (`main`)

ตารางนี้สรุปฟังก์ชันทั้งหมดที่เปิดใช้งานแล้วบน `main` อ้างอิงจาก URL routes ใน `accounts/urls.py`, `catalog/urls.py`, `materials/urls.py`, `webboard/urls.py` และชั้น `services.py` / `selectors.py`

**Production URL:** [https://cntagram-h195.onrender.com/](https://cntagram-h195.onrender.com/) (Render — Singapore Region)

| หมวด | ฟังก์ชันที่มีในโค้ด | Story / Issue | หลักฐานในโค้ด |
|---|---|---|---|
| **บัญชีและความปลอดภัย** | สมัครสมาชิกด้วยอีเมลคณะ (`@student.tu.ac.th` รหัสคณะ `10`), เข้าสู่ระบบ/ออกจากระบบ, จำกัดอัตราการเดารหัสผ่านแบบ Two-bucket (ตามบัญชีและ IP), ลบบัญชีตนเองตาม PDPA ที่ `/account/delete/` (Anonymize), แสดงรายการ "ไฟล์ของฉัน + เหตุผลที่ถูกปฏิเสธ" และแจ้งเตือนคิวตรวจบนหน้าแรก | US-1, US-2, US-13, US-34 (#34, #172) | `accounts/urls.py`, `accounts/services.py`, `accounts/models.py`, `materials/templatetags/materials_stats.py` |
| **สิทธิ์และบทบาท** | แต่งตั้ง/ถอดถอน Moderator ประจำภาควิชา, แดชบอร์ดผู้ดูแลระบบส่วนกลาง และ Django Admin ครบทุกแอป | US-3, US-10, TD-3 | `accounts/urls.py`, `portal/permissions.py`, `*/admin.py` |
| **โครงสร้างหลักสูตร** | จัดการภาควิชา (ดู/เพิ่ม/แก้/ลบ), รุ่น (ดู/เพิ่ม/ลบ), ผูก/ถอดรายวิชาในรุ่น (`BatchCourse`), รายวิชา (ดู/เพิ่ม), ค่ากำหนดระบบ (`SystemSetting`) | US-3, US-4 | `catalog/urls.py`, `catalog/services.py`, `catalog/selectors.py` |
| **คลังเอกสารและการค้นหา** | อัปโหลด PDF พร้อมช่องค้นหารายวิชาแบบ Combobox และตรวจ SHA-256 ป้องกันไฟล์ซ้ำ, ผู้อัปโหลดแก้ไขชื่อ/คำอธิบาย อัปโหลดเวอร์ชันใหม่ หรือลบเอกสารของตนเองได้ (`document_edit`, `document_new_version`, `document_delete`), นำเข้าเอกสารจำนวนมากด้วย CSV + ZIP ทั้งทาง CLI (`import_documents`) และหน้าเว็บ (`/materials/bulk-import/` พร้อมโหมดทดลองรัน), คลังเอกสารแยก Lecture / Exam Vault, ค้นหาด้วยรหัสวิชาพร้อมกรองภาควิชา/รุ่น/ประเภทเอกสาร/ช่วงสอบ/ปี พ.ศ., เปิดอ่านตัวอย่าง PDF แบบ Inline (`<iframe>`) และดาวน์โหลดแบบตรวจสิทธิ์พร้อมบันทึก `DownloadLog` | US-5, US-7, US-8, US-11, US-12, US-17, US-21 (#215, #217, #224) | `materials/urls.py`, `materials/services.py`, `materials/selectors.py`, `materials/downloads.py`, `materials/management/commands/import_documents.py` |
| **การคัดกรองและอนุมัติ** | คิวรออนุมัติแยกตามสิทธิ์, รีวิว/อนุมัติ/ปฏิเสธพร้อมเหตุผลตามกฎ `DocTypeRequiredRole` (ชีททั่วไปใช้ 1 ฝ่าย / ข้อสอบเก่าต้องครบทั้ง Moderator และ Super Admin / ข้อสอบรุ่น ≤ `legacy_batch_max` ใช้ Super Admin), พรีวิวและดาวน์โหลดไฟล์ระหว่างรอพิจารณา, ซ่อนเอกสารที่เผยแพร่แล้วพร้อมเหตุผล (`document_hide`) | US-6, US-9, US-25 (#205, #216) | `materials/urls.py`, `materials/views.py`, `materials/services.py` |
| **ลิขสิทธิ์และการร้องเรียน** | ผู้ใช้รายงานเอกสารที่มีปัญหา (`Report`), แบบฟอร์มสาธารณะให้อาจารย์/เจ้าของลิขสิทธิ์แจ้งลบเนื้อหาที่ `/materials/takedown/` (`TakedownRequest`), หน้าดูรายงานที่เปิดอยู่สำหรับ Moderator (`/materials/reports/`) และหน้าพิจารณาตัดสินชี้ขาดของ Super Admin (`/materials/reports/review/`) | US-32, US-33, US-35 (#218, #219, #220) | `materials/urls.py`, `materials/models.py`, `materials/services.py`, `materials/selectors.py` |
| **ชุมชนหน้าแรก** | กล่องทักทายสด Shoutbox แบบ AJAX (`ShoutboxMessage`), โพลสำรวจประจำสัปดาห์แบบ AJAX 1 เสียงต่อบัญชี (`PollVote`), ตัวนับสถิติผู้เข้าชม LCD 6 หลัก, เครื่องเล่นเพลงประกอบ BGM Player ยุค 2000s | US-36 – US-39 (#89, #161) | `accounts/urls.py`, `accounts/services.py`, `static/js/home_widgets.js`, `static/js/bgm_player.js` |
| **กระดานสนทนาเว็บบอร์ด** | หมวดหมู่เว็บบอร์ด (`BoardCategory`), ตั้งกระทู้ถาม-ตอบ (`Thread`) ผูกรายวิชาได้, ตอบกลับ (`Post`), แบ่งหน้า Pagination และกันปั๊มยอดวิวด้วย Session, แก้ไขกระทู้/ข้อความพร้อมป้ายกำกับแก้ไขแล้ว (`is_edited`), แปลงรหัสอีโมติคอน MSN (เช่น `:D`, `(L)`) และฝังภาพ `[img]...[/img]` หรือลิงก์ GIF ปลอดภัย, ปักหมุด/ล็อกกระทู้, ลบกระทู้และข้อความตอบกลับตามสิทธิ์ | E6 (#202, #209, #210, #211, #212, #213) | `webboard/urls.py`, `webboard/services.py`, `webboard/selectors.py`, `webboard/emoticons.py` |
| **Production & CI/CD** | CI Pipeline (`black`, `flake8`, `bandit`, `manage.py check`, `makemigrations --check`, `coverage ≥ 80%`), Deploy บน Render ด้วย Gunicorn + WhiteNoise + Managed PostgreSQL, สคริปต์สำรองข้อมูลและตรวจความพร้อม Production | TD-1, TD-8, TD-9, SP-4 (#107, #108, #139, #141, #169, #192) | `.github/workflows/ci.yml`, `portal/settings.py`, `build.sh`, `scripts/backup_restore.sh`, `scripts/check_production_readiness.py` |
