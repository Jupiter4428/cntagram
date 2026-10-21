# Architectural Decision Records (ADR)

บันทึกสั้นๆ ว่า**ทำไม**ทีมเลือกสถาปัตยกรรมแบบนี้ มีทางเลือกอะไรที่ไม่เลือก และต้องแลกกับอะไร
ตามหลักใน [`lecture-notes/04-django-service-layer-and-transactions.md`](../lecture-notes/04-django-service-layer-and-transactions.md#การบันทึกการตัดสินใจสถาปัตยกรรม-architectural-decision-records-adr)

| ADR | เรื่อง | Status |
|---|---|---|
| [0001](./0001-modular-monolith-and-app-boundaries.md) | Modular Monolith และขอบเขต Django Apps | Accepted |
| [0002](./0002-service-layer-and-selectors.md) | Service Layer และ Selectors | Accepted |
| [0003](./0003-approval-tables-in-materials.md) | ตารางการอนุมัติอยู่ใน app `materials` | Proposed |

## กติกา
- เปิด ADR ใหม่เมื่อการตัดสินใจ**เปลี่ยนยาก**ภายหลัง หรือทีมเถียงเรื่องเดิมซ้ำ (เช่น เพิ่ม app ใหม่, เลือกวิธีเก็บไฟล์, เลือกบริการส่งอีเมล)
- ADR ผ่าน Pull Request เหมือนโค้ด เปิดเป็น `Proposed` แล้วเปลี่ยนเป็น `Accepted` เมื่อ PR ได้ approve
- ไม่แก้ ADR ที่ Accepted แล้ว ถ้าเปลี่ยนใจให้เขียน ADR ใหม่ แล้วเปลี่ยนตัวเก่าเป็น `Superseded by ADR-XXXX`
- ตั้งชื่อไฟล์ `NNNN-ชื่อเรื่อง-ภาษาอังกฤษ.md`

## Template
```markdown
# ADR NNNN: <ชื่อการตัดสินใจ>

- **Status:** Proposed | Accepted | Deprecated | Superseded by ADR-XXXX
- **Date:** YYYY-MM-DD
- **Issue:** #<เลข>

## Context
ปัญหาหรือแรงกดดันที่ทำให้ต้องตัดสินใจ

## Decision
เราเลือกทำอะไร

## Alternatives considered
ทางเลือกที่ไม่เลือก และเพราะอะไร

## Consequences
ได้อะไร เสียอะไร ต้องทำอะไรเพิ่ม
```
