# เอกสารโปรเจค CNtagram (`_docs/`)

รวมเอกสารประกอบการพัฒนาทั้งหมด ไม่ว่าจะเป็น requirement, การออกแบบ, การตัดสินใจด้านสถาปัตยกรรม, สรุปเนื้อหารายวิชา และวัตถุดิบสำหรับเขียนเล่มรายงาน
ส่วนวิธีติดตั้งและรันโปรเจคดูที่ [README หลัก](../README.md) และวิธีทำงานร่วมกันดูที่ [CONTRIBUTING.md](../CONTRIBUTING.md)

## มีอะไรบ้าง

| ไฟล์ / โฟลเดอร์ | เนื้อหา | อ่านเมื่อ |
|---|---|---|
| [`requirements.md`](./requirements.md) | Product Backlog: User Story (US-x), Acceptance Criteria และลำดับความสำคัญ | อยากรู้ว่าระบบต้องทำอะไร หรือก่อนหยิบงานใน Sprint |
| [`known-limitations.md`](./known-limitations.md) | ข้อจำกัดของระบบรุ่นที่ส่ง (ย้ายจาก README ตาม lecture สัปดาห์ 13) | อยากรู้ว่ายังไม่ทำอะไร / ตอนปิด story ที่ตัดขอบเขต |
| [`database-design.md`](./database-design.md) | ออกแบบฐานข้อมูล (ERD 3NF) และเหตุผลของแต่ละตาราง | ก่อนแก้ `models.py` (ต้องอัปเดตไฟล์นี้ใน PR เดียวกัน) |
| [`architecture/c4.md`](./architecture/c4.md) | ไดอะแกรม C4 Model ระดับ 1–2 (System Context, Container) | อยากเห็นภาพรวมว่าระบบประกอบด้วยอะไร |
| [`adr/`](./adr/) | Architectural Decision Records (ADR 0001–0005): บันทึกว่าทำไมถึงเลือกสถาปัตยกรรมแบบนี้ | ก่อนเพิ่ม app ใหม่ หรือเปลี่ยนโครงสร้างโค้ด |
| [`backup-operations.md`](./backup-operations.md) | ขั้นตอนสำรองและกู้คืนข้อมูล Production (PostgreSQL & Offsite S3 Backup) | ก่อนรันสคริปต์สำรอง/กู้คืนฐานข้อมูลจริง |
| [`deployment-prep-checklist.md`](./deployment-prep-checklist.md) | เช็กลิสต์เตรียมก่อน Deploy (security, packages, WhiteNoise, PostgreSQL, Render, Release) ตาม lecture สัปดาห์ 13 | ก่อนขึ้น Cloud / ทำ SP-4 |
| [`production-demo-readiness.md`](./production-demo-readiness.md) | รายงานตรวจสอบความพร้อมของระบบ Production สำหรับการสาธิต | ตรวจสอบสถานะความพร้อมของสภาพแวดล้อมจริง |
| [`lecture-notes/`](./lecture-notes/) | สรุปเนื้อหารายวิชา CN331 (Django ORM, CBV, Architecture, Service Layer, Scrum, Automated Testing, CI/CD & Static Analysis, Web Security & Deployment) | ต้องการทฤษฎีหรือแนวทางที่โปรเจคอ้างอิง |
| [`research/`](./research/) | ร่างเล่มรายงานโครงงาน แยกตามบท 1–5 พร้อมบรรณานุกรมและภาคผนวก | เขียนหรือแก้เล่มรายงาน |
| [`archive/`](./archive/) | เอกสารเก่าที่เลิกใช้แล้ว เช่น SRS v1 (`.pdf`, `.docx`) | อยากดูที่มาของ requirement เดิมเท่านั้น |

## ลำดับการอ่านสำหรับคนใหม่

1. [`requirements.md`](./requirements.md): ระบบนี้ทำอะไร ให้ใคร
2. [`architecture/c4.md`](./architecture/c4.md): ภาพรวมของระบบ
3. [`adr/`](./adr/): โค้ดแบ่ง app และแบ่งชั้นอย่างไร
4. [`database-design.md`](./database-design.md): โครงสร้างข้อมูล

## แหล่งความจริง (Source of Truth)

- สเปกยึดตาม `requirements.md`, `database-design.md`, `adr/` และ `architecture/c4.md`
- ถ้า `research/` หรือ `archive/` ขัดกับไฟล์ข้างบน ให้ยึดไฟล์ข้างบนเป็นหลัก
- เปลี่ยนโค้ดส่วนไหน ให้แก้เอกสารที่เกี่ยวข้องใน PR เดียวกันด้วย

## สถานะปัจจุบัน (พฤศจิกายน 2026)

- **เว็บไซต์ Production:** [https://cntagram-h195.onrender.com/](https://cntagram-h195.onrender.com/) (Render — Singapore)
- สรุปฟังก์ชันที่มีจริงในโค้ดปัจจุบัน (`catalog`, `accounts`, `materials`, `webboard`) และรายการ Product Backlog ดูที่ [`requirements.md`](./requirements.md) และ [`architecture/c4.md`](./architecture/c4.md)
- แผนการสำรองและซ้อมกู้คืนฐานข้อมูล Production ดูที่ [`backup-operations.md`](./backup-operations.md)
