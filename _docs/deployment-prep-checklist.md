# Checklist: เตรียมก่อน Deploy (Production)

> ที่มา: CN331 สัปดาห์ที่ 13 — [08-web-security-and-production-deployment.md](./lecture-notes/08-web-security-and-production-deployment.md)  
> โปรเจกต์นี้ใช้แพ็กเกจ Django ชื่อ `portal` (Start Command: `gunicorn portal.wsgi:application`)  
> งานที่เกี่ยวข้อง: SP-4 (เลือกที่ deploy + สำรองข้อมูล)

ใช้เอกสารนี้เป็นเช็กลิสต์ก่อนขึ้น Cloud — ติ๊กทีละข้อแล้วค่อย Push / กด Deploy

---

## 0. ทำไมต้องเตรียมก่อนขึ้นระบบ

บนเครื่องตัวเองรันได้ ≠ พร้อม Production

| ความเสี่ยง | อาการบน Cloud |
|---|---|
| `DEBUG = True` | Error แล้วโชว์ env, secret, SQL, โค้ดทั้งก้อน |
| SQLite บน PaaS | Disk เป็น ephemeral — restart แล้วข้อมูลหาย; concurrency ต่ำ |
| ไม่มี static serving | ปิด Debug แล้วหน้าเว็บไม่มี CSS/JS |
| Secret ใน Git | `SECRET_KEY` / รหัสผ่านรั่วใน repo |

**Production stack ตาม lecture:** Gunicorn + WhiteNoise + Managed PostgreSQL (เช่นบน Render)

---

## 1. ความปลอดภัยในโค้ด (ทำก่อนขึ้น Cloud)

### 1.1 Hardening ใน `settings.py`

- [ ] `DEBUG` อ่านจาก env — production ต้องเป็น `False`
- [ ] `SECRET_KEY` อ่านจาก env — ห้ามฝังค่าจริงใน Git
- [ ] `ALLOWED_HOSTS` ระบุโดเมนจริง (เช่น `.onrender.com`)
- [ ] `CSRF_TRUSTED_ORIGINS` สำหรับ HTTPS POST (เช่น `https://*.onrender.com`) — ไม่ตั้งแล้วฟอร์ม/login จะได้ **403**
- [ ] เมื่อ `DEBUG = False` เปิด HTTPS / cookie hardening:

```python
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = "DENY"
```

### 1.2 เกราะ Django ที่ lecture เน้น (อย่าทำลายตอน refactor)

- [ ] ใช้ ORM / parameterized query — อย่าต่อสตริง SQL จาก input ผู้ใช้
- [ ] เทมเพลตไม่ใส่ `|safe` / `mark_safe()` กับข้อความจากผู้ใช้
- [ ] ฟอร์ม POST มี `{% csrf_token %}` — อย่าใส่ `@csrf_exempt` โดยไม่จำเป็น

---

## 2. แพ็กเกจและ dependency

ติดตั้งแล้ว `pip freeze > requirements.txt` (Cloud อ่านไฟล์นี้ตอน build — `build.sh` จะ `pip install -r` ให้)

| แพ็กเกจ | หน้าที่ |
|---|---|
| `gunicorn` | WSGI server บน Linux (Start Command เท่านั้น) |
| `psycopg2-binary` | ไดรเวอร์ PostgreSQL |
| `dj-database-url` | แปลง `DATABASE_URL` → `DATABASES` |
| `whitenoise` | เสิร์ฟ static เมื่อ `DEBUG = False` |

- [ ] มีครบใน `requirements.txt` พร้อมเวอร์ชัน

---

## 3. ตั้งค่าฐานข้อมูลและ Static (ในโค้ด — คำสั่งรันอยู่ใน `build.sh`)

### 3.1 PostgreSQL ผ่าน `DATABASE_URL` (local ยังใช้ SQLite ได้)

```python
import dj_database_url

DATABASES = {
    "default": dj_database_url.config(
        default="sqlite:///db.sqlite3",
        conn_max_age=600,
        conn_health_checks=True,
    )
}
```

- [ ] แอปเป็น **stateless** — ข้อมูลถาวรอยู่ที่ Managed DB ไม่ใช่ไฟล์บนเว็บเซิร์ฟเวอร์
- [ ] (CNtagram) แผนเก็บ PDF / `MEDIA_ROOT` สอดคล้อง ADR 0003 และ SP-4 — disk บน PaaS หายได้เมื่อ restart

### 3.2 WhiteNoise (settings เท่านั้น)

- [ ] ใส่ `WhiteNoiseMiddleware` **ถัดจาก** `SecurityMiddleware`
- [ ] ตั้ง `STATIC_ROOT` (เช่น `BASE_DIR / "staticfiles"`)
- [ ] ใช้ storage แบบ compressed manifest (ตาม lecture)
- [ ] คำสั่ง `collectstatic` อยู่ใน `build.sh` ด้านล่าง — อย่ารันแยกตอน deploy

---

## 4. `build.sh` — รวมคำสั่งเตรียมรันเซิร์ฟทั้งหมด

ทุกคำสั่งที่ต้องทำก่อนเปิดเซิร์ฟเวอร์ให้อยู่ในไฟล์นี้เท่านั้น  
บน Render ตั้ง **Build Command** = `./build.sh`  
**Start Command** เหลือแค่เปิด Gunicorn (ไม่ใส่ install / migrate / collectstatic ที่นั่น)

```bash
#!/usr/bin/env bash
# build.sh — รันอัตโนมัติทุกครั้งก่อน start web process
set -o errexit

# 1) ติดตั้ง dependency จาก requirements.txt
pip install -r requirements.txt

# 2) ตรวจความพร้อม Production (ล้ม build ถ้ายังไม่ผ่าน)
python manage.py check --deploy

# 3) รวม static files สำหรับ WhiteNoise
python manage.py collectstatic --noinput

# 4) ย้าย schema ฐานข้อมูล (PostgreSQL ผ่าน DATABASE_URL)
python manage.py migrate

# 5) สร้าง admin จาก ENV (ข้ามได้ถ้าไม่มีรหัส; ไม่ fail ถ้ามีบัญชีแล้ว)
if [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py createsuperuser \
    --noinput --username admin \
    --email admin@example.com || true
fi
```

- [ ] สร้างไฟล์ `build.sh` ที่ root ของ repo ตามบล็อกด้านบน
- [ ] `chmod a+x build.sh` แล้ว commit สิทธิ์ executable
- [ ] ไม่รัน `pip install` / `check --deploy` / `collectstatic` / `migrate` / `createsuperuser` แยกนอกสคริปต์ตอน deploy

### Start Command / `Procfile` (เปิดเซิร์ฟอย่างเดียว)

```
web: gunicorn portal.wsgi:application
```

---

## 5. บน Render (ลำดับตาม lecture)

### 5.1 สร้าง Managed PostgreSQL

- [ ] New → PostgreSQL
- [ ] Region: **Singapore** (ใกล้ผู้ใช้ไทย)
- [ ] รอสถานะ Available
- [ ] คัดลอก **Internal Database URL** สำหรับ Web Service (อย่าใช้ External ใน production app)

### 5.2 สร้าง Web Service

- [ ] New → Web Service → เชื่อม GitHub repo
- [ ] Region: **Singapore** (ต้องตรงกับ DB)
- [ ] Branch: กิ่งที่ส่งมอบ (เช่น `main`)
- [ ] Runtime: Python 3
- [ ] Build Command: `./build.sh` ← รันคำสั่งใน §4 ทั้งหมด
- [ ] Start Command: `gunicorn portal.wsgi:application` ← เปิดเซิร์ฟอย่างเดียว
- [ ] Auto-Deploy: Yes (ถ้าต้องการ deploy ทุกครั้งที่ push กิ่งหลัก)

### 5.3 Environment Variables (ห้ามใส่ใน Git)

| Key | Value |
|---|---|
| `PYTHON_VERSION` | เช่น `3.12.0` |
| `DEBUG` | `False` |
| `SECRET_KEY` | สตริงสุ่มยาว 50+ ตัวอักษร |
| `DATABASE_URL` | **Internal** URL ของ PostgreSQL |
| `ALLOWED_HOSTS` | `.onrender.com` (หรือโดเมนจริง) |
| `CSRF_TRUSTED_ORIGINS` | `https://*.onrender.com` |
| `DJANGO_SUPERUSER_PASSWORD` | รหัส admin (อ่านใน `build.sh`) |

### 5.4 หลัง Deploy — ตรวจ Logs และหน้าเว็บ

- [ ] Build Log: ขั้นใน `build.sh` ผ่านครบ (`pip install` → `check --deploy` → `collectstatic` → `migrate` → superuser)
- [ ] Deploy: มี `Listening at: http://0.0.0.0:...` และ **"Your service is live"**
- [ ] เปิด URL จริง: HTTPS มีกุญแจล็อก
- [ ] CSS/JS โหลดได้ (ไม่ 404)
- [ ] หน้าแรก HTTP 200 ไม่ใช่ 500
- [ ] ล็อกอิน `/admin/` ได้ด้วย superuser จาก ENV

---

## 6. Production Gate (สรุปจากตาราง lecture)

ระบบยังไม่พร้อมนำเสนอถ้าข้อใดข้อหนึ่งยังไม่ผ่าน:

| รายการ | ตั้งค่า / คำสั่ง | สถานะ |
|---|---|---|
| Debug Mode | `DEBUG = False` | บังคับ |
| Allowed Hosts | `ALLOWED_HOSTS = [...]` | บังคับ |
| CSRF Whitelist | `CSRF_TRUSTED_ORIGINS` | บังคับ |
| Static Serving | WhiteNoise + `collectstatic` ใน `build.sh` | บังคับ |
| Production DB | Managed PostgreSQL + `migrate` ใน `build.sh` | บังคับ |
| Security Audit | `check --deploy` ใน `build.sh` → 0 issues | บังคับ |

---

## 7. หลังขึ้นระบบแล้ว (Sprint 3 / Release)

- [ ] ใส่ **Live Demo URL** ใน `README.md`
- [ ] อัปเดต C4 Container ฉบับ production (TD-4 / SP-4)
- [ ] ทดลองสำรอง + กู้คืนอย่างน้อย 1 ครั้ง (เป้าตาม requirements / SP-4)
- [ ] เมื่อพร้อมส่งมอบ: tag `v1.0.0` แล้ว freeze โค้ดก่อนวันนำเสนอ

```bash
git checkout main && git pull origin main
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

---

## อ้างอิงสั้นๆ

- Lecture ฉบับเต็ม: [`lecture-notes/08-web-security-and-production-deployment.md`](./lecture-notes/08-web-security-and-production-deployment.md)
- Spike deploy ของทีม: [`.scratch/backlog/sp-4-deployment.md`](../.scratch/backlog/sp-4-deployment.md)
- Django: [Deployment checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- Render: [Deploy Django](https://render.com/docs/deploy-django)
