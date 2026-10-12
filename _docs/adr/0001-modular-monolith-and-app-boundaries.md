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
  - `accounts`: ผู้ใช้ บทบาท และสิทธิ์
  - `materials`: เอกสาร ไฟล์ และเวอร์ชัน
- **ทิศทาง Dependency ทางเดียว:** `catalog` ← `accounts` ← `materials` (ลูกศรชี้ไปที่ app ที่ถูกพึ่ง)
  - `catalog` ไม่ import app ใดเลย
  - `accounts` พึ่ง `catalog` ได้
  - `materials` พึ่งได้ทั้งสอง
- FK ข้าม app อ้างด้วย string (`"catalog.BatchCourse"`) และอ้างผู้ใช้ด้วย `settings.AUTH_USER_MODEL`
- การทำงานที่ต้องประสานหลาย app (เช่น อนุมัติเอกสารแล้วบันทึก Audit Log) เขียนใน `services.py` ของ app ที่อยู่ปลายทาง dependency ไม่ให้ app ต้นทางเรียกย้อนกลับ
- ตารางของ Sprint 2 (`approval`, `download_log`, `audit_log`, `report`, `doc_type_required_role`) จะอยู่ app ไหน ให้ตกลงใน Sprint 2 Planning แล้วเขียน ADR ใหม่

## Alternatives considered
- **App เดียว (`core`)**: เริ่มเร็วแต่กลายเป็น God App และทุกคนชนไฟล์เดียวกัน
- **1 model ต่อ 1 app**: import ข้ามกันวุ่นวายเกินขนาดโปรเจค
- **Microservices**: overhead ด้าน network และ distributed transaction ไม่คุ้มกับทีมและระยะเวลา

## Consequences
- แบ่งงานใน Sprint ตาม app ได้ ลด merge conflict
- ต้องคอยระวัง circular import ถ้าเกิดขึ้นถือเป็นสัญญาณว่าขอบเขต app ปนกัน ต้อง refactor (ย้าย logic ไป service หรือย้าย model)
- ข้อมูลอยู่ฐานเดียว จึงใช้ `@transaction.atomic` ข้าม app ได้ตามปกติ
