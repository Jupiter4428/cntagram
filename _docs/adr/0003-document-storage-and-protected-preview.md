# ADR 0003: การเก็บไฟล์เอกสารและ Preview ผ่าน View ที่ตรวจสิทธิ์

- **Status:** Proposed
- **Date:** 2026-10-16
- **Issue:** #31 (US-7), SP-3

## Context
US-7 ต้องให้ผู้ใช้กดเปิดอ่าน PDF บนหน้าเว็บได้ทันที แต่ NFR กำหนดว่าลิงก์ดาวน์โหลด/preview ต้องตรวจสิทธิ์ทุกครั้ง และห้ามมี Direct URL (`_docs/requirements.md` §7, SP-3)
ถ้าเสิร์ฟไฟล์ผ่าน `MEDIA_URL` แบบปกติของ Django ใครได้ลิงก์ไปก็เปิดไฟล์ได้ รวมถึงไฟล์ที่ยัง `pending` หรือถูกซ่อน (`hidden`) แล้ว

## Decision
- เก็บไฟล์ใน `MEDIA_ROOT = BASE_DIR / "media"` ผ่าน `default_storage` ส่วน `DocumentVersion.storage_path` เก็บ path สัมพัทธ์กับ `MEDIA_ROOT`
- **ไม่ตั้ง `MEDIA_URL`** และไม่ map URL ใดไปที่โฟลเดอร์ `media/` ดังนั้นไฟล์จะเปิดได้ผ่าน view เท่านั้น
- view `materials:document_preview` ต้อง `@login_required` และหาเอกสารจาก `selectors.published_documents()` (ไม่ใช่ published ตอบ 404) จากนั้นส่งไฟล์เวอร์ชันล่าสุดด้วย `FileResponse` แบบ inline
- หน้าเอกสารฝังไฟล์ด้วย `<iframe>` ที่ชี้ไปที่ view นั้น และใส่ `@xframe_options_sameorigin` เฉพาะ view นี้ ส่วน view อื่นยังใช้ `X-Frame-Options: DENY` ตามค่าตั้งต้น
- โฟลเดอร์ `media/` อยู่ใน `.gitignore`

## Alternatives considered
- **เสิร์ฟผ่าน `MEDIA_URL` / static server**: ง่ายที่สุด แต่เป็น Direct URL ที่ข้ามการตรวจสิทธิ์ ผิด NFR
- **Signed URL หมดอายุ (เช่น S3 presigned)**: ปลอดภัยและไม่กินแรง Django แต่ต้องมี object storage ซึ่งยังไม่มีจนถึง Sprint 3 (SP-4 Deploy)
- **`X-Sendfile` / `X-Accel-Redirect`**: ให้ web server ส่งไฟล์หลัง Django ตรวจสิทธิ์แล้ว ประหยัดกว่า แต่ต้องตั้งค่า nginx ซึ่งยังไม่มีในเครื่อง dev ตัดสินใจอีกครั้งตอน deploy
- **PDF.js render ฝั่ง client**: คุมหน้าตาได้มากกว่า แต่ยังต้องมี endpoint ส่งไฟล์ที่ตรวจสิทธิ์อยู่ดี เลื่อนไว้ให้ฝั่ง FE ตัดสินใจ

## Consequences
- ทุกคำขอไฟล์ผ่าน Django จึงตรวจสิทธิ์ได้ครบ แต่ต้องแลกกับ worker ที่ถูกใช้ระหว่างส่งไฟล์ ซึ่งรับได้กับขนาดไฟล์ ≤ 50 MB และจำนวนผู้ใช้ระดับคณะ
- ตอนอัปโหลด (US-5) ตรวจแล้วว่าไฟล์เป็น PDF จริง (MIME ที่ browser ส่งมา + magic bytes `%PDF-`) แต่ยังไม่เช็ก `DocumentVersion.scan_status` เพราะตัวสแกนเป็นงานของ US-21 จึงทิ้ง TODO ไว้ใน view และ US-21 ต้องปิดเรื่องนี้
- ไฟล์ที่เกิน `max_upload_mb` ถูก `MaxSizeUploadHandler` ข้ามตั้งแต่ตอนรับ จึงไม่ลง temp file ทั้งก้อน แต่ Django ยังอ่าน byte ที่เหลือของ request ทิ้งจนจบ ตอน deploy (SP-4) ต้องตั้งเพดานขนาด request ที่ web server ด้วย (เช่น `client_max_body_size` ของ nginx ให้เกิน 50 MB เล็กน้อย)
- US-8 (ดาวน์โหลด + นับสถิติ) ต้องใช้รูปแบบเดียวกัน คือ view ที่ตรวจสิทธิ์ แล้วส่ง `FileResponse` แบบ attachment
- ตอน deploy (SP-4) ให้ทบทวนว่าจะเปลี่ยนไปใช้ `X-Accel-Redirect` หรือ signed URL หรือไม่ ถ้าเปลี่ยนให้เขียน ADR ใหม่มาแทนฉบับนี้
