# ภาคผนวก (รายการที่ต้องแนบ)

| ภาคผนวก | เนื้อหา | แหล่ง | สถานะ |
|---|---|---|---|
| ก | Data Dictionary ฉบับเต็ม (ทุกตาราง ทุก column, constraint, index) | [`database-design.md`](../database-design.md) §3, §5, §6 | พร้อม |
| ข | Architectural Decision Records | [ADR 0001](../adr/0001-modular-monolith-and-app-boundaries.md), [ADR 0002](../adr/0002-service-layer-and-selectors.md), [ADR 0003](../adr/0003-document-storage-and-protected-preview.md) และ ADR ที่เพิ่มภายหลัง | พร้อม (เพิ่มตาม Spike) |
| ค | Product Backlog ฉบับสุดท้าย และ User Story พร้อม AC | [`requirements.md`](../requirements.md) + export จาก GitHub issue | **[เติม: export ตอนจบโครงงาน]** |
| ง | SRS v1 (เอกสารความต้องการฉบับแรก) | [`archive/requirements-srs-v1.pdf`](../archive/requirements-srs-v1.pdf) | พร้อม |
| จ | แนวปฏิบัติของทีม: DoR, DoD, Branch Strategy, Commit Convention | [`CONTRIBUTING.md`](../../CONTRIBUTING.md), [`.github/`](../../.github/) templates | พร้อม |
| ฉ | คู่มือติดตั้งระบบ (Installation Guide) | [`README.md`](../../README.md) หัวข้อ Setup | พร้อม (อัปเดตเมื่อมี `.env` / deploy) |
| ช | คู่มือการใช้งานแยกตามบทบาท (User Manual) | **[เติม: เขียนจากภาพหน้าจอบทที่ 4]** | ยังไม่มี |
| ซ | Test cases และผลการทดสอบดิบ (`test` / `coverage report`) | ผลรันจริง | **[เติม]** |
| ฌ | Sprint Retrospective ทุก Sprint | `_docs/sprintN_retro.md` | **[เติม]** |
| ญ | Burndown Chart และ Velocity Chart ทุก Sprint | GitHub Project Insights | **[เติม]** |
| ฎ | แบบสอบถามความพึงพอใจและผลดิบ | Google Form / SUS | **[เติม ถ้ามีการประเมิน]** |
| ฏ | ตัวอย่างโค้ดสำคัญ (เช่น `User.validate_student_email()`, `Document.add_version()`, service อนุมัติเอกสาร) | `accounts/models.py`, `materials/models.py`, `materials/services.py` | บางส่วนพร้อม |
