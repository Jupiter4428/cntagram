# เอกสารโปรเจค CNtagram (`_docs/`)

รวมเอกสารประกอบการพัฒนาทั้งหมด ไม่ว่าจะเป็น requirement, การออกแบบ, การตัดสินใจด้านสถาปัตยกรรม, สรุปเนื้อหารายวิชา และวัตถุดิบสำหรับเขียนเล่มรายงาน
ส่วนวิธีติดตั้งและรันโปรเจคดูที่ [README หลัก](../README.md) และวิธีทำงานร่วมกันดูที่ [CONTRIBUTING.md](../CONTRIBUTING.md)

## มีอะไรบ้าง

| ไฟล์ / โฟลเดอร์ | เนื้อหา | อ่านเมื่อ |
|---|---|---|
| [`requirements.md`](./requirements.md) | Product Backlog: User Story (US-x), Acceptance Criteria และลำดับความสำคัญ | อยากรู้ว่าระบบต้องทำอะไร หรือก่อนหยิบงานใน Sprint |
| [`database-design.md`](./database-design.md) | ออกแบบฐานข้อมูล (ERD 3NF) และเหตุผลของแต่ละตาราง | ก่อนแก้ `models.py` (ต้องอัปเดตไฟล์นี้ใน PR เดียวกัน) |
| [`architecture/c4.md`](./architecture/c4.md) | ไดอะแกรม C4 Model ระดับ 1–2 (System Context, Container) | อยากเห็นภาพรวมว่าระบบประกอบด้วยอะไร |
| [`adr/`](./adr/) | Architectural Decision Records: บันทึกว่าทำไมถึงเลือกสถาปัตยกรรมแบบนี้ | ก่อนเพิ่ม app ใหม่ หรือเปลี่ยนโครงสร้างโค้ด |
| [`lecture-notes/`](./lecture-notes/) | สรุปเนื้อหารายวิชา CN331 (Django ORM, CBV, Architecture, Service Layer, Scrum) | ต้องการทฤษฎีหรือแนวทางที่โปรเจคอ้างอิง |
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
