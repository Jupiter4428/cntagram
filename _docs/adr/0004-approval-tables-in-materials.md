# ADR 0004: ตารางการอนุมัติอยู่ใน app `materials`

- **Status:** Proposed
- **Date:** 2026-10-21
- **Issue:** #33

## Context
ADR 0001 ให้ตกลงว่าตารางที่เกี่ยวกับการอนุมัติ การดาวน์โหลด และการร้องเรียนอยู่ app ไหน US-6 (#30) สร้าง `approval` และ US-9 (#33) สร้าง `doc_type_required_role` ไว้ใน `materials` ตามด้วย `download_log` (US-8), `report` (US-32) และ `takedown_request` (US-33)

ตารางเหล่านี้อ้าง `document` / `doc_type` (อยู่ใน `materials`) และ `role` / `app_user` (อยู่ใน `accounts`) และกฎ "ครบตามกฎแล้วเปลี่ยนเป็น `published`" หรือ "ตัดสินเรื่องร้องเรียนแล้วซ่อนเอกสารเป็น `hidden`" ต้องเขียนตารางดังกล่าวกับ `document.status` ใน transaction เดียวกัน

## Decision
`Approval`, `DocTypeRequiredRole`, `DownloadLog`, `Report` และ `TakedownRequest` อยู่ใน `materials/models.py` กฎการเขียนอยู่ใน `materials/services.py` และการอ่านสถานะอยู่ใน `materials/selectors.py`

## Alternatives considered
- **app ใหม่ `approvals`**: แยกชัด แต่ `approvals` ต้อง import `materials` (เพื่อเปลี่ยน `document.status`) และ `materials` ไม่ควร import กลับ ได้ app ที่เล็กมากและทุก story อนุมัติต้องแก้สอง app
- **ไว้ใน `accounts` คู่กับ `role`**: ผิดทิศ dependency ของ ADR 0001 (`accounts` import `materials` ไม่ได้)

## Consequences
- ทิศ import ตาม ADR 0001 ไม่เปลี่ยน (`materials` import `accounts` และ `catalog` ได้)
- `materials` ใหญ่ขึ้น ถ้าเกิน ~1,000 บรรทัดต่อไฟล์ค่อยพิจารณาแยกเป็น package หรือ app ใน ADR ใหม่
