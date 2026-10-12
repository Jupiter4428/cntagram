# ส่วนนำของเล่ม (Front Matter)

## ปก

| รายการ | ข้อมูล |
|---|---|
| ชื่อโครงงาน (ไทย) | ระบบเว็บบอร์ดคลังชีทสรุปและข้อสอบเก่าสำหรับนักศึกษาคณะวิศวกรรมศาสตร์ |
| ชื่อโครงงาน (อังกฤษ) | CNtagram: A Multi-Department Study Material and Past Exam Repository for Engineering Students |
| ชื่อระบบ | CNtagram |
| ผู้จัดทำ | **[เติม: ชื่อ–นามสกุล และรหัสนักศึกษา สมาชิก 5 คน]** |
| อาจารย์ผู้สอน / ที่ปรึกษา | **[ตรวจ: อาจารย์ผู้สอนรายวิชา CN331 (บทบาท Product Owner)]** |
| รายวิชา | CN331 Software Engineering |
| หน่วยงาน | ภาควิชาวิศวกรรมไฟฟ้าและคอมพิวเตอร์ คณะวิศวกรรมศาสตร์ มหาวิทยาลัยธรรมศาสตร์ |
| ภาคการศึกษา | ภาคเรียนที่ 1 ปีการศึกษา 2569 |

**[ตรวจ: ชื่อโครงงานภาษาอังกฤษ และชื่อภาควิชาที่ถูกต้องตามรูปแบบของคณะ]**

---

## บทคัดย่อ (ร่าง)

> ร่างนี้เขียนจากขอบเขตและการออกแบบ ประโยคที่มี **[เติม]** ต้องแทนด้วยผลจริงจากบทที่ 4 ก่อนส่งเล่ม

ปัจจุบันชีทสรุปและข้อสอบเก่าของนักศึกษาคณะวิศวกรรมศาสตร์กระจัดกระจายอยู่ตามกลุ่มแชทและไดรฟ์ส่วนตัว ทำให้ค้นหาได้ยาก ไม่มีการคัดกรองคุณภาพ และความรู้ไม่ถูกส่งต่อระหว่างรุ่นอย่างต่อเนื่อง โครงงานนี้จึงพัฒนาระบบ CNtagram ซึ่งเป็นเว็บแอปพลิเคชันคลังเอกสารกลางที่จัดเอกสารตามภาควิชา รุ่น และรายวิชา แยกคลังชีทสรุปซึ่งผูกกับรุ่นออกจากคลังข้อสอบเก่าซึ่งรวมศูนย์ตามรายวิชา จำกัดการเข้าถึงเฉพาะนักศึกษาคณะด้วยการตรวจอีเมลมหาวิทยาลัยและรหัสคณะในรหัสนักศึกษา และกำหนดให้เอกสารทุกชิ้นผ่านการอนุมัติจากผู้ดูแลก่อนเผยแพร่ โดยข้อสอบเก่าต้องได้รับการอนุมัติทั้งจากผู้ดูแลประจำภาควิชาและผู้ดูแลระบบส่วนกลาง

ระบบพัฒนาด้วย Python และ Django ตามกระบวนการ Scrum จำนวน 3 Sprint ใช้สถาปัตยกรรมแบบโมโนลิทเชิงโมดูล (Modular Monolith) แบ่งเป็น 3 แอปตามโดเมนที่มีทิศทางการพึ่งพาทางเดียว และแยกชั้นตรรกะทางธุรกิจ (Service Layer) ออกจากชั้นนำเสนอ ฐานข้อมูลออกแบบตามบรรทัดฐานที่ 3 (3NF) โดยเก็บกฎการอนุมัติและค่ากำหนดเป็นข้อมูลเพื่อปรับได้โดยไม่ต้องแก้โค้ด และออกแบบให้สอดคล้องกับพระราชบัญญัติคุ้มครองข้อมูลส่วนบุคคล พ.ศ. 2562

ผลการดำเนินงานพบว่า **[เติม: ทีมส่งมอบ User Story ได้ X จาก Y เรื่อง รวม Z Story Points, Velocity เฉลี่ย …, ชุดทดสอบอัตโนมัติ N กรณีผ่านทั้งหมด coverage …%, หน้าค้นหาตอบสนองเฉลี่ย … วินาที, ผลประเมินความพึงพอใจ/SUS …]**

**คำสำคัญ:** คลังเอกสารการเรียน, ข้อสอบเก่า, Django, สกรัม, โมโนลิทเชิงโมดูล, การออกแบบฐานข้อมูลเชิงสัมพันธ์

---

## Abstract (Draft)

Lecture summaries and past examination papers for engineering students are currently scattered across chat groups and personal cloud drives, making them hard to find, unvetted, and poorly passed on between cohorts. This project develops CNtagram, a web-based central repository that organizes materials by department, cohort (batch) and course. It separates a cohort-specific lecture vault from a course-centric past-exam vault, restricts access to faculty members by validating university e-mail addresses and the faculty code embedded in student IDs, and requires every document to be approved before publication, with past exams requiring approval from both a department moderator and a central administrator.

The system is built with Python and Django over three Scrum sprints. It follows a modular monolith architecture of three domain-based Django apps with a one-way dependency direction and a service layer that separates business logic from presentation. The relational schema is normalized to third normal form (3NF), stores approval rules and system settings as data so they can change without code modification, and is designed to comply with Thailand's Personal Data Protection Act B.E. 2562 (2019).

**[Fill in: delivered stories and story points, average velocity, number of automated tests and coverage, search response time, user satisfaction/SUS score.]**

**Keywords:** study material repository, past examinations, Django, Scrum, modular monolith, relational database design

---

## กิตติกรรมประกาศ

**[เติม: ขอบคุณอาจารย์ผู้สอน ผู้ทดลองใช้ระบบ รุ่นพี่ที่ให้ข้อมูลเอกสาร CN21–CN25 ฯลฯ]**

---

## สารบัญ (โครง)

1. บทที่ 1 บทนำ
   1.1 ที่มาและความสำคัญ · 1.2 วัตถุประสงค์ · 1.3 ขอบเขต · 1.4 ประโยชน์ที่คาดว่าจะได้รับ · 1.5 นิยามศัพท์ · 1.6 แผนการดำเนินงาน
2. บทที่ 2 ทฤษฎีและงานที่เกี่ยวข้อง
   2.1 การพัฒนาซอฟต์แวร์แบบ Agile/Scrum · 2.2 Django และสถาปัตยกรรม MVT · 2.3 สถาปัตยกรรมซอฟต์แวร์ · 2.4 Service Layer และ Transaction · 2.5 การออกแบบฐานข้อมูลและ Normalization · 2.6 ประสิทธิภาพ ORM · 2.7 ความปลอดภัยของเว็บแอปพลิเคชัน · 2.8 กฎหมายที่เกี่ยวข้อง · 2.9 งานและระบบที่เกี่ยวข้อง
3. บทที่ 3 วิธีดำเนินงาน
   3.1 กระบวนการพัฒนา · 3.2 การเก็บและวิเคราะห์ความต้องการ · 3.3 การออกแบบสถาปัตยกรรม · 3.4 การออกแบบฐานข้อมูล · 3.5 การออกแบบกฎทางธุรกิจและสิทธิ์ · 3.6 เครื่องมือ · 3.7 แผนการทดสอบและการประเมินผล
4. บทที่ 4 ผลการดำเนินงาน
5. บทที่ 5 สรุป อภิปรายผล และข้อเสนอแนะ
- บรรณานุกรม
- ภาคผนวก
