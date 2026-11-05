# ADR 0005: การเลือกแพลตฟอร์ม Deploy, ฐานข้อมูล Production, การจัดเก็บไฟล์เอกสาร และกลยุทธ์การสำรองข้อมูล

- **Status:** Proposed
- **Date:** 2026-11-06
- **Issue:** #139 (SP-4)

## Context
Sprint 3 มีเป้าหมายสำคัญตาม Roadmap คือ "คลังพร้อมใช้งานจริงบน Cloud" เพื่อให้ระบบมีความมั่นคงปลอดภัยและส่งมอบผลิตภัณฑ์ที่ใช้งานได้จริง (Shippable Product) ตามมาตรฐานวิชา CN331 (สัปดาห์ที่ 13, `_docs/lecture-notes/08-web-security-and-production-deployment.md` และ `_docs/requirements.md` §7):

1. **สถาปัตยกรรมเดิมระหว่างพัฒนา (Development):**
   - ใช้ SQLite บน Local Disk ซึ่งเกิดปัญหา Concurrency Lock ทันทีที่มีผู้ใช้พร้อมกัน
   - `portal/settings.py` มี `DEBUG = True`, `SECRET_KEY` ฮาร์ดโค้ด, `ALLOWED_HOSTS = []`, ไม่มี `CSRF_TRUSTED_ORIGINS`
   - ไม่มี Static File Serving Layer (ปิด Debug แล้วหน้าเว็บไม่มี CSS/JS)
   - ไฟล์ PDF เก็บในโฟลเดอร์ Local `media/` ตาม ADR 0003
2. **ความต้องการและข้อจำกัดของระบบ (Production Constraints):**
   - **ความพร้อมใช้งานและการสำรองข้อมูล (NFR §7):** ความพร้อมใช้งานเป้าหมาย ~99%/เดือน, สำรองข้อมูลวันละ 1 ครั้ง และต้องมีกระบวนการกู้คืน (Disaster Recovery) ที่ทดสอบได้จริง
   - **การรักษาความปลอดภัย (OWASP Top 10):** `DEBUG = False`, ข้อมูล Secrets แยกเก็บใน Environment Variables, บังคับใช้ HTTPS, Secure Cookies, HSTS และ CSRF Protection
   - **การปกป้องเอกสาร (ADR 0003):** ห้ามมี Direct URL ไปยังไฟล์ PDF ทุกคำขอเปิดดูหรือดาวน์โหลดต้องผ่าน View ที่ตรวจสิทธิ์ (`materials:document_preview`, `materials:document_download`)
   - **Ephemeral Filesystem บน Cloud PaaS:** คอนเทนเนอร์บน Cloud PaaS ส่วนใหญ่มีระบบไฟล์ชั่วคราว ข้อมูลบน Local Disk จะสูญหายเมื่อคอนเทนเนอร์รีสตาร์ตหรืออัปเดตโค้ด

---

## Decision

### 1. แพลตฟอร์ม Deploy: Render (PaaS)
เลือกใช้ **Render (Web Service)** เป็นแพลตฟอร์มหลักในการ Deploy:
- **Runtime:** Python 3 (Linux Environment)
- **Region:** **Singapore (Southeast Asia)** เพื่อให้ Latency ต่ำที่สุดสำหรับผู้ใช้ในไทย (< 35 ms)
- **Web Application Server:** **Gunicorn** (`portal.wsgi:application`) ทำหน้าที่เป็น WSGI Server ในการจัดการ Request
- **Automated Build & Release:** ควบคุมการขึ้นระบบผ่านสคริปต์ `build.sh` (ติดตั้ง Dependency, รัน `check --deploy`, รวม Static Files ด้วย `collectstatic --noinput`, และรัน Database Migrations) และกำหนด Start Command เป็น `gunicorn portal.wsgi:application`

### 2. ฐานข้อมูล Production: Managed PostgreSQL (Region: Singapore)
- แยกฐานข้อมูลออกจากเซิร์ฟเวอร์เว็บโดยใช้ **Managed PostgreSQL** บน Render (หรือ Neon PostgreSQL) ใน Region Singapore
- เชื่อมต่อผ่านตัวแปรสภาพแวดล้อม `DATABASE_URL` (โดยใช้ `dj-database-url` ใน `settings.py`)
- บน Cloud Web Service จะเชื่อมต่อผ่าน **Internal Database URL** เพื่อความเร็วระดับ Local Network ภายใน Data Center, ไม่คิดค่า Bandwidth ภายนอก และปลอดภัยสูงสุด
- โครงสร้างตารางจะถูก Migrate โดยอัตโนมัติในขั้นตอน `build.sh` ด้วย `python manage.py migrate`

### 3. Static Files: WhiteNoise
- ติดตั้ง `whitenoise` โดยแทรก `WhiteNoiseMiddleware` ถัดจาก `SecurityMiddleware`
- ใช้ Storage แบบ `whitenoise.storage.CompressedManifestStaticFilesStorage` เพื่อบีบอัดไฟล์ (Gzip/Brotli) และทำ Far-future Caching ด้วย Content Hashing
- รันคำสั่ง `python manage.py collectstatic --noinput` อัตโนมัติทุกครั้งที่ Deploy ใน `build.sh`

### 4. การจัดเก็บไฟล์เอกสาร PDF (Document Storage & Protected Access)
- **ยืนยันหลักการของ ADR 0003:** ไม่มีการตั้ง `MEDIA_URL` และไม่เปิดให้ Web Server เสิร์ฟโฟลเดอร์ไฟล์เอกสารโดยตรง ทุกคำขอดูไฟล์ยังคงต้องผ่าน View ที่ตรวจสิทธิ์ (`materials:document_preview` และ `materials:document_download`) ซึ่งส่งคืนผ่าน `FileResponse`
- **การจัดการกับ Ephemeral Disk บน PaaS:**
  - *สำหรับ Prototype และ Production บน Render:* ใช้ **Render Persistent Disk** ทำการ Mount ไว้ที่ `/var/data/media` (กำหนดผ่าน `MEDIA_ROOT = config("MEDIA_ROOT", default=str(BASE_DIR / "media"))`) ทำให้ไฟล์ PDF คงอยู่ถาวรไม่สูญหายเมื่อเซิร์ฟเวอร์รีสตาร์ต
  - *แผนขยายระยะยาว (Scalable Storage):* หากเปลี่ยนไปใช้ Object Storage ภายนอก (เช่น Cloudflare R2 หรือ Supabase Storage) จะคงคอนฟิกแบบ Private Bucket 100% แล้วให้ Django View ทำหน้าที่ Stream ข้อมูลหรือสร้าง Pre-signed URL แบบมีอายุสั้นพิเศษ (15–60 วินาที)

### 5. การจัดการค่าคอนฟิกและการเพิ่มความปลอดภัย (Environment & Hardening)
- จัดการ Environment Variables ผ่าน `python-decouple` (หรือ `os.environ`):
  - `DEBUG = config("DEBUG", default=False, cast=bool)`
  - `SECRET_KEY = config("SECRET_KEY")` (บังคับตั้งค่าบน Cloud ห้ามใช้ค่าเริ่มต้น)
  - `ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())`
  - `CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())`
- เมื่อ `DEBUG = False`:
  - เปิดใช้งาน `SECURE_SSL_REDIRECT = True`
  - กำหนด `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`
  - เปิด Secure Cookie Flags: `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True`, `SESSION_COOKIE_HTTPONLY = True`
  - เปิดใช้ HSTS: `SECURE_HSTS_SECONDS = 31536000`, `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`, `SECURE_HSTS_PRELOAD = True`

### 6. กลยุทธ์การสำรองและกู้คืนข้อมูล (Backup & Disaster Recovery Strategy)
- **Automated Daily Database Backup:**
  - ใช้งานระบบ Automated Daily Snapshots บน Managed PostgreSQL ซึ่งทำการ Snapshot สำรองข้อมูลให้อัตโนมัติทุกวัน
  - แผนสำรองข้อมูลภายนอก (Offsite Logical Backup): มีสคริปต์สำรองข้อมูลด้วยคำสั่ง `pg_dump` แบบ Custom Compressed Format (`-Fc`):
    ```bash
    pg_dump "$DATABASE_URL" -Fc -f "backups/cntagram_backup_$(date +%Y%m%d_%H%M%S).dump"
    ```
- **การกู้คืนข้อมูล (Restore Procedure):**
  - กู้คืนฐานข้อมูลผ่านคำสั่ง `pg_restore`:
    ```bash
    pg_restore --clean --if-exists --no-owner --no-privileges -d "$DATABASE_URL" "backups/<backup_file>.dump"
    ```
  - จัดทำขั้นตอนการทดสอบ Restore จริงลงในคู่มือและสคริปต์ Wizard เพื่อให้มั่นใจว่าเมื่อเกิดเหตุฉุกเฉินสามารถนำข้อมูลกลับมาได้ภายใน RTO < 1 ชั่วโมง และ RPO ≤ 24 ชั่วโมง
- **การสำรองไฟล์เอกสาร (PDF Backups):**
  - มีสคริปต์ Archive บีบอัดโฟลเดอร์ `media/vault` เป็น `tar.gz` ประจำวันเพื่อเก็บสำรองไว้นอกเซิร์ฟเวอร์

---

## Alternatives considered

| ตัวเลือก | ข้อดี | ข้อเสีย / เหตุผลที่ไม่เลือก |
|---|---|---|
| **Render (PaaS)** *(เลือก)* | • มีในเนื้อหาและคู่มือหลักของวิชา CN331 (Lecture 08)<br/>• มี Managed PostgreSQL ในสิงคโปร์ (Latency ต่ำ)<br/>• รองรับ Gunicorn, WhiteNoise, Auto-Deploy จาก GitHub ง่ายดาย<br/>• มี SSL อัตโนมัติ | • Free Web Service มีอาการ Sleep เมื่อไม่มีคนเข้า (แก้ได้โดยเตรียมพร้อมก่อนพรีเซนต์) |
| **Railway (PaaS)** | • Developer Experience ดีมาก, สั่งสร้าง PostgreSQL ได้ในคลิกเดียว<br/>• ไม่ Sleep | • ให้เครดิตทดลองใช้เพียง $5 ครั้งเดียว (ไม่มี Free Tier ถาวร)<br/>• Data Center ส่วนใหญ่อยู่สหรัฐฯ/ยุโรป ทำให้ Latency สูงกว่าสิงคโปร์ |
| **Fly.io** | • ทำงานผ่าน Micro-VMs รวดเร็ว<br/>• มี Region Singapore (`sin`)<br/>• มี Persistent Volume ฟรี | • บังคับผูกบัตรเครดิตเพื่อยืนยันตัวตนตั้งแต่เริ่มต้น<br/>• การคอนฟิก `fly.toml` และ Dockerfile ซับซ้อนกว่าสำหรับทีม |
| **Cloud VM ของมหาวิทยาลัย / คณะ** | • ทรัพยากรเครื่องฟรีและไม่มีขีดจำกัดด้านเวลา | • ขั้นตอนการขออนุมัติใช้งานและการเปิดพอร์ตเครือข่ายใช้เวลานาน ไม่ทันกรอบเวลา Sprint<br/>• ต้องตั้งค่า Nginx, Let's Encrypt, Security Hardening และ Firewall เองทั้งหมด |

---

## Consequences

1. **สิ่งที่ได้ (Positive Outcomes):**
   - มีสภาพแวดล้อม Production ที่ได้มาตรฐานตามแนวทางวิชา CN331 และ Twelve-Factor App
   - ฐานข้อมูลแยกอิสระจาก Application Container รองรับ Concurrency สูงและมี Daily Backup
   - Static Files ถูกบีบอัดและเสิร์ฟอย่างรวดเร็วผ่าน WhiteNoise โดยไม่ต้องพึ่ง Nginx เพิ่มเติม
   - เอกสาร PDF ได้รับการรักษาความปลอดภัยตามหลักการของ ADR 0003 อย่างสมบูรณ์
2. **สิ่งที่ต้องแลก / งานที่ต้องทำเพิ่ม (Trade-offs & Next Steps):**
   - ต้องเพิ่ม Dependency: `gunicorn`, `psycopg2-binary`, `dj-database-url`, `whitenoise` ใน `requirements.txt`
   - ต้องสร้างไฟล์ `build.sh` และ `Procfile` ที่รากโปรเจกต์
   - ต้องปรับแก้ `portal/settings.py` ให้อ่านค่าจาก Decouple และรองรับทั้ง SQLite (Local dev) และ PostgreSQL (Production)
   - ต้องสร้าง Wizard Script เพื่อช่วยให้สมาชิกในทีมตั้งค่า Environment Variables และรันคำสั่ง Backup/Restore ได้อย่างถูกต้องโดยไม่ผิดพลาด

