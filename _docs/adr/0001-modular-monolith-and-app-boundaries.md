# ADR 0001: Modular Monolith และขอบเขต Django Apps

- **Status:** Accepted
- **Date:** 2026-10-12
- **Issue:** #23 (SP-0)

## Context
ทีม 5 คนพัฒนาใน Sprint สั้น ต้องทำงานขนานกันโดยไม่ชนไฟล์กัน และต้อง deploy ง่าย
ข้อมูลแบ่งเป็นโดเมนชัดเจน: โครงสร้างภาควิชา/รุ่น/วิชา, ผู้ใช้และสิทธิ์, เอกสารและไฟล์
หลักจาก [`lecture-notes/03`](../lecture-notes/03-software-architecture-and-decomposition.md): *Monolith First* และแบ่ง App ตาม Bounded Context

## Decision
- ใช้ **Django project เดียว (Modular Monolith)** config อยู่ที่ `portal/` และฐานข้อมูลเดียว
- แบ่ง app ตามโดเมน แต่ละ app อธิบายได้ในประโยคเดียว:
  - `catalog`: โครงสร้างภาควิชา รุ่น รายวิชา และค่ากำหนดระบบ
  - `accounts`: ผู้ใช้ บทบาท สิทธิ์ และวิดเจ็ตชุมชนหน้าแรก (Shoutbox, Poll, Counter)
  - `materials`: เอกสาร ไฟล์ เวอร์ชัน การอนุมัติ บันทึกการดาวน์โหลด และการร้องเรียน/แจ้งลบ (`Report`, `TakedownRequest`)
  - `webboard` (เพิ่มใน Sprint 3, PR #202): กระดานสนทนาชุมชน หมวดหมู่ กระทู้ถาม-ตอบ (ผูกรายวิชาได้) ข้อความตอบกลับ แก้ไข/ลบ/ปักหมุด/ล็อก อีโมติคอน MSN และฝังภาพ GIF
- **ทิศทาง Dependency ทางเดียว:** `catalog` ← `accounts` ← (`materials`, `webboard`) (ลูกศรชี้ไปที่ app ที่ถูกพึ่ง)
  - `catalog` ไม่ import app ใดเลย
  - `accounts` พึ่ง `catalog` ได้
  - `materials` และ `webboard` พึ่งได้ทั้ง `catalog` และ `accounts` (โดย `materials` กับ `webboard` ไม่ import กันเอง)
- FK ข้าม app อ้างด้วย string (`"catalog.BatchCourse"`) และอ้างผู้ใช้ด้วย `settings.AUTH_USER_MODEL`
- **ข้อยกเว้นสำหรับการอ่านข้อมูล (เพิ่ม 2026-10-26, #65):** app ต้นทางใช้ข้อมูลของ app ปลายทางได้ 2 ทาง โดยโค้ด Python ของ app ต้นทางไม่ต้อง import app ปลายทาง
  - template ของ app ต้นทาง `{% load %}` template tag ของ app ปลายทางได้ (เช่น `accounts/index_admin.html` และ `accounts/index.html` ใช้ `materials_stats`) tag ต้องเรียก selector และอ่านอย่างเดียว
  - selector ของ app ต้นทางนับหรือกรองผ่าน reverse relation ได้ (เช่น `Count("documents")` ใน `accounts/selectors.py`)
- การทำงานที่ต้องประสานหลาย app เขียนใน `services.py` ของ app ที่อยู่ปลายทาง dependency ไม่ให้ app ต้นทางเรียกย้อนกลับ
- ตารางการอนุมัติ การดาวน์โหลด และการร้องเรียน (`approval`, `doc_type_required_role`, `download_log`, `report`, `takedown_request`) อยู่ใน `materials` ตาม [ADR 0004](./0004-approval-tables-in-materials.md)

## Alternatives considered
- **App เดียว (`core`)**: เริ่มเร็วแต่กลายเป็น God App และทุกคนชนไฟล์เดียวกัน
- **1 model ต่อ 1 app**: import ข้ามกันวุ่นวายเกินขนาดโปรเจค
- **Microservices**: overhead ด้าน network และ distributed transaction ไม่คุ้มกับทีมและระยะเวลา

## Consequences
- แบ่งงานใน Sprint ตาม app ได้ ลด merge conflict
- ต้องคอยระวัง circular import ถ้าเกิดขึ้นถือเป็นสัญญาณว่าขอบเขต app ปนกัน ต้อง refactor (ย้าย logic ไป service หรือย้าย model)
- ข้อมูลอยู่ฐานเดียว จึงใช้ `@transaction.atomic` ข้าม app ได้ตามปกติ
- query ของ template tag ข้าม app เกิดตอน render จึงไม่อยู่ใน `assertNumQueries` ของ selector ฝั่งต้นทาง ต้องเทสต์ที่ selector ของ app ปลายทางเอง และเปลี่ยนชื่อ `related_name` ฝั่งปลายทางแล้วต้องแก้ selector ของ app ต้นทางตาม
