# ADR 0002: Service Layer และ Selectors

- **Status:** Accepted
- **Date:** 2026-10-12
- **Issue:** —

## Context
Story ใน Sprint 1–2 มีกฎธุรกิจเยอะ (อัปโหลดได้เฉพาะภาคตัวเอง, ผู้อัปโหลดอนุมัติไฟล์ตัวเองไม่ได้, ข้อสอบต้องอนุมัติสองฝ่าย, ทุกการกระทำของผู้ดูแลต้องลง Audit Log)
ถ้าเขียนทั้งหมดใน view จะได้ Fat View ที่ทดสอบยากและใช้ซ้ำไม่ได้ (เช่น Bulk Import ต้องใช้ logic อัปโหลดเดียวกับหน้าเว็บ)
ถ้ายัดลง `Model.save()` จะเกิด side-effect ที่ไม่ตั้งใจตอน seed ข้อมูลหรือแก้ใน admin
หลักจาก [`lecture-notes/04`](../lecture-notes/04-django-service-layer-and-transactions.md): HackSoft Django Styleguide

## Decision
แต่ละ app แยกโค้ดเป็นชั้น เรียกลงล่างทางเดียว: `views.py` → `services.py` / `selectors.py` → `models.py`

| ไฟล์ | หน้าที่ |
|---|---|
| `views.py` | รับ request → เรียก form / service / selector → ส่ง response (ไม่เกิน ~20 บรรทัดต่อ view) |
| `forms.py` | ตรวจ type, format, ความยาวของ input |
| `services.py` | การเขียนข้อมูล (create/update/delete), กฎธุรกิจ, ตรวจสิทธิ์ระดับธุรกิจ, `@transaction.atomic`, `select_for_update()`, งานต่อเนื่องหลัง commit (`transaction.on_commit`) |
| `selectors.py` | การอ่านข้อมูลอย่างเดียว ไม่มี side-effect รวม `select_related` / `prefetch_related` / `annotate` ไว้ที่นี่ |
| `models.py` | schema, constraint, ความถูกต้องของข้อมูลระดับแถว (`clean()`, `save()` ที่ normalize/validate) และ property ง่ายๆ ห้ามมี side-effect ภายนอก (ส่งอีเมล, เรียก API) |

- service/selector เป็นฟังก์ชัน Python ธรรมดา รับ keyword-only argument (`def submit_document(*, uploader, ...)`) และ**ไม่รับ `request`**
- service แจ้งความผิดพลาดด้วย `ValidationError` / `PermissionDenied` ให้ view แปลงเป็นข้อความหรือ HTTP status
- สร้าง `services.py` / `selectors.py` เมื่อ story แรกที่ต้องใช้มาถึง ไม่ต้องสร้างไฟล์เปล่ารอไว้

## Alternatives considered
- **Fat Views**: เร็วตอนแรก แต่ทดสอบต้องผ่าน HTTP client และใช้ซ้ำกับ Bulk Import / management command ไม่ได้
- **Fat Models**: model บวมเป็น God Object และ side-effect ซ่อนอยู่ใน `save()`
- **Class-based service / repository pattern เต็มรูปแบบ**: ซับซ้อนเกินขนาดโปรเจค

## Consequences
- เทสต์กฎธุรกิจได้ตรงที่ service โดยไม่ต้องจำลอง request
- ไฟล์ต่อ app เพิ่มขึ้น 2 ไฟล์ และทีมต้องรีวิวว่า logic อยู่ถูกชั้น (อยู่ใน DoD)
- method ที่มีอยู่แล้วใน model ซึ่งดูแลความถูกต้องของข้อมูลเอง (เช่น `Document.add_version()` ที่ล็อกแถวกันเลขเวอร์ชันชน, `User.anonymize()`) ยังอยู่ที่ model ได้ เพราะเป็น data integrity ไม่มี side-effect ภายนอก service เรียกใช้ method เหล่านี้ต่อได้
