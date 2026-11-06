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
- **การจัดการกับ Ephemeral Disk บน PaaS และผลกระทบตาม Pricing Plan:**
  - *สำหรับ Production เต็มรูปแบบ (Paid Instance):* Render Persistent Disk รองรับบน Instance แบบมีค่าใช้จ่าย (Starter $7/เดือน + ค่า Disk $0.25/GB/เดือน) ทำการ Mount ไว้ที่ `/var/data/media` (กำหนดผ่าน `MEDIA_ROOT = config("MEDIA_ROOT", default=str(BASE_DIR / "media"))`) ทำให้ไฟล์ PDF คงอยู่ถาวรไม่สูญหายเมื่อเซิร์ฟเวอร์รีสตาร์ต
  - *สำหรับ Prototype บน Free Plan ($0/เดือน):* Free Web Service บน Render ไม่มี Persistent Disk ให้ใช้งาน (ระบบไฟล์เป็น Ephemeral 100%) ส่งผลให้ไฟล์ PDF ที่อัปโหลดจะสูญหายทุกครั้งที่มีการ Redeploy หรือเซิร์ฟเวอร์หมุนรอบใหม่ และจำเป็นต้องสำรองไฟล์ PDF ผ่านสคริปต์ `scripts/backup_restore.sh`
  - *แผนขยายระยะยาว (Scalable Storage):* หากเปลี่ยนไปใช้ Object Storage ภายนอก (เช่น Cloudflare R2 หรือ Supabase Storage) จะคงคอนฟิกแบบ Private Bucket 100% แล้วให้ Django View ทำหน้าที่ Stream ข้อมูลหรือสร้าง Pre-signed URL แบบมีอายุสั้นพิเศษ (15–60 วินาที)

### 5. การจัดการค่าคอนฟิกและการเพิ่มความปลอดภัย (Environment & Hardening)
- จัดการ Environment Variables ผ่าน `python-decouple`:
  ```python
  SECRET_KEY = config(
      "SECRET_KEY",
      default="django-insecure-=)*b-=!qgjibnv)o_=wpe&f)tmcwpk#t258#9bg%%ur8&)k@5a",
  )
  DEBUG = config("DEBUG", default=True, cast=bool)
  ALLOWED_HOSTS = config(
      "ALLOWED_HOSTS",
      default="localhost,127.0.0.1",
      cast=Csv(),
  )
  CSRF_TRUSTED_ORIGINS = config(
      "CSRF_TRUSTED_ORIGINS",
      default="",
      cast=Csv(),
  )
  ```
  - ระหว่างพัฒนาบนเครื่อง Local Dev สามารถใช้งานค่าเริ่มต้นได้อย่างสะดวก
  - ในขั้นตอน `build.sh` กำหนดคำสั่ง `python manage.py check --deploy --fail-level WARNING` เพื่อทำหน้าที่เป็น Security Gate สั่งล้ม Build ทันทีหากขึ้น Production โดยไม่ตั้ง `SECRET_KEY` หรือลืมตั้ง `DEBUG=False`
- เมื่อ `DEBUG = False` และไม่อยู่ในโหมดรันเทสต์ (`not TESTING`):
  - เปิดใช้งาน `SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)`
  - กำหนด `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`
  - เปิด Secure Cookie Flags: `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True`, `SESSION_COOKIE_HTTPONLY = True`
  - เปิดใช้ HSTS: `SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=3600, cast=int)` และ `SECURE_HSTS_INCLUDE_SUBDOMAINS = True` (เริ่มต้นจาก 3,600 วินาทีเพื่อความปลอดภัย ไม่ส่ง `*.onrender.com` เข้า Preload list สาธารณะ)
  - กำหนด `X_FRAME_OPTIONS = "DENY"` เพื่อป้องกัน Clickjacking โดยหน้าเอกสารที่ต้อง Preview ภายใน iframe มีการใช้ `@xframe_options_sameorigin` รองรับไว้อย่างถูกต้อง

### 6. กลยุทธ์การสำรองและกู้คืนข้อมูล (Backup & Disaster Recovery Strategy)
- **Automated Daily Database Backup:**
  - บน Render Managed PostgreSQL แบบเสียเงิน (Paid Plan เริ่มต้น $7/เดือน) จะมีระบบ Automated Daily Snapshots ให้บริการอัตโนมัติ
  - บน Render Free PostgreSQL ฐานข้อมูลมีอายุจำกัด 30 วันและไม่มี Automated Snapshots จึงต้องพึ่งพาสคริปต์สำรองข้อมูลภายนอก (Offsite Logical Backup) ด้วย `scripts/backup_restore.sh`
  - สคริปต์สำรองข้อมูลรองรับทั้ง PostgreSQL ผ่านคำสั่ง `pg_dump` แบบ Custom Compressed Format (`-Fc`):
    ```bash
    pg_dump "$DATABASE_URL" -Fc -f "backups/cntagram_backup_$(date +%Y%m%d_%H%M%S).dump"
    ```
    และรองรับ SQLite สำหรับ Local Development/Testing ผ่าน Python SQLite backup API
- **การกู้คืนข้อมูล (Restore Procedure):**
  - กู้คืนฐานข้อมูลผ่านคำสั่ง `pg_restore`:
    ```bash
    pg_restore --clean --if-exists --no-owner --no-privileges -d "$DATABASE_URL" "backups/<backup_file>.dump"
    ```
    หรือกู้คืน SQLite จากไฟล์ backup ได้ทันที พร้อมตรวจสอบความสมบูรณ์ของตารางและจำนวนแถว
  - จัดทำขั้นตอนการทดสอบ Restore จริงลงในสคริปต์ `scripts/backup_restore.sh test` ซึ่งทำการสำรองและกู้คืนเปรียบเทียบข้อมูลแถวจริง เพื่อให้มั่นใจในเกณฑ์ RTO < 1 ชั่วโมง และ RPO ≤ 24 ชั่วโมง
- **การสำรองไฟล์เอกสาร (PDF Backups):**
  - สคริปต์ Archive บีบอัดโฟลเดอร์เอกสารตาม `MEDIA_ROOT` (หรือ `media/`) เป็น `tar.gz` ประจำวันเพื่อเก็บสำรองไว้นอกเซิร์ฟเวอร์

---

## Alternatives considered

| ตัวเลือก | ค่าใช้จ่ายต่อเดือน | ข้อดี | ข้อเสีย / เหตุผลที่ไม่เลือก |
|---|---|---|---|
| **Render (PaaS)** *(เลือก)* | • **Free Tier:** $0/เดือน<br/>• **Production (Paid):** ~$14.25/เดือน (Starter $7 + DB $7 + Disk $0.25) | • มีในเนื้อหาและคู่มือหลักของวิชา CN331 (Lecture 08)<br/>• มี Managed PostgreSQL ในสิงคโปร์ (Latency ต่ำ)<br/>• รองรับ Gunicorn, WhiteNoise, Auto-Deploy จาก GitHub ง่ายดาย<br/>• มี SSL อัตโนมัติ | • Free Web Service มีอาการ Sleep เมื่อไม่มีคนเข้า และไม่มี Persistent Disk<br/>• Free DB หมดอายุใน 30 วันและไม่มี Auto Snapshot |
| **Railway (PaaS)** | ~$5–$10/เดือน (เครดิตทดลองฟรี $5 ครั้งเดียว) | • Developer Experience ดีมาก, สั่งสร้าง PostgreSQL ได้ในคลิกเดียว<br/>• ไม่ Sleep | • ไม่มี Free Tier ถาวร<br/>• Data Center ส่วนใหญ่อยู่สหรัฐฯ/ยุโรป ทำให้ Latency สูงกว่าสิงคโปร์ |
| **Fly.io** | ~$5/เดือน (มี Free Allowance บางส่วน) | • ทำงานผ่าน Micro-VMs รวดเร็ว<br/>• มี Region Singapore (`sin`)<br/>• มี Persistent Volume ฟรี | • บังคับผูกบัตรเครดิตเพื่อยืนยันตัวตนตั้งแต่เริ่มต้น<br/>• การคอนฟิก `fly.toml` และ Dockerfile ซับซ้อนกว่าสำหรับทีม |
| **Cloud VM ของมหาวิทยาลัย / คณะ** | $0/เดือน | • ทรัพยากรเครื่องฟรีและไม่มีขีดจำกัดด้านเวลา | • ขั้นตอนการขออนุมัติใช้งานและการเปิดพอร์ตเครือข่ายใช้เวลานาน ไม่ทันกรอบเวลา Sprint<br/>• ต้องตั้งค่า Nginx, Let's Encrypt, Security Hardening และ Firewall เองทั้งหมด |

---

## Consequences

1. **สิ่งที่ได้ (Positive Outcomes):**
   - มีสภาพแวดล้อม Production ที่ได้มาตรฐานตามแนวทางวิชา CN331 และ Twelve-Factor App
   - ฐานข้อมูลแยกอิสระจาก Application Container รองรับ Concurrency สูงและมี Daily Backup
   - Static Files ถูกบีบอัดและเสิร์ฟอย่างรวดเร็วผ่าน WhiteNoise โดยไม่ต้องพึ่ง Nginx เพิ่มเติม
   - เอกสาร PDF ได้รับการรักษาความปลอดภัยตามหลักการของ ADR 0003 อย่างสมบูรณ์
   - มีกระบวนการทดสอบ Backup & Restore จริงที่ตรวจสอบจำนวนแถวของข้อมูล
2. **สิ่งที่ต้องแลก / งานที่ต้องทำเพิ่ม (Trade-offs & Next Steps):**
   - **กรณีใช้งาน Render Free Tier ($0/เดือน):** PDF จะสูญหายทุกครั้งที่มีการ Redeploy เนื่องจากไม่มี Persistent Disk และ Managed DB จะไม่มี Auto Daily Snapshot ต้องรันสคริปต์ `scripts/backup_restore.sh` เป็นระยะด้วยตนเองหรือตั้ง Cron Job ภายนอก
   - **กรณีใช้งาน Production Plan (~$14.25/เดือน):** ต้องจัดเตรียมงบประมาณสำหรับ Starter Instance, Managed DB และ Persistent Disk
   - ต้องเพิ่ม Dependency: `gunicorn`, `psycopg2-binary`, `dj-database-url`, `whitenoise` ใน `requirements.txt`
   - ต้องสร้างไฟล์ `build.sh` และ `Procfile` ที่รากโปรเจกต์
   - ต้องปรับแก้ `portal/settings.py` ให้อ่านค่าจาก Decouple และรองรับทั้ง SQLite (Local dev) และ PostgreSQL (Production)
   - ต้องสร้าง Wizard Script เพื่อช่วยให้สมาชิกในทีมตั้งค่า Environment Variables และรันคำสั่ง Backup/Restore ได้อย่างถูกต้องโดยไม่ผิดพลาด

