# Project Django (CN331)

ระบบเว็บบอร์ดกลางสำหรับแชร์และค้นหาเอกสารสรุป/ชีทของนักศึกษาวิศวกรรม พัฒนาด้วย Django ตามแนวทาง Agile/Scrum ในรายวิชา CN331

## สารบัญ
1. [Tech Stack](#tech-stack)
2. [Setup ก่อนเริ่มพัฒนา](#setup-ก่อนเริ่มพัฒนา-first-time-setup)
3. [Sync ก่อนเริ่มงานทุกครั้ง](#ทุกครั้งที่-pull-โค้ดใหม่-sync-ก่อนเริ่มงาน)
4. [Project Structure](#project-structure)
5. [Branch Strategy](#branch-strategy)
6. [For Contributing](#for-contributing)

---

## Tech Stack
- Python 3.12+
- Django 5.1 ขึ้นไป (สถาปัตยกรรม MVT, ใช้ Function-Based Views เป็นหลัก) — models ใช้ `CheckConstraint(condition=...)` ซึ่งมีตั้งแต่ 5.1
- Bootstrap 5 (ผ่าน CDN) สำหรับ UI
- SQLite (ตอนพัฒนา) และ PostgreSQL (production): Django ORM ทำให้สลับได้โดยไม่ต้องแก้โค้ด Model
- Git + GitHub (Pull Request, Projects, Actions)
- Automated Tests ด้วย `python manage.py test`
- CI/CD ด้วย GitHub Actions (เริ่มใน Sprint 2)

---

## Setup ก่อนเริ่มพัฒนา (First Time Setup)

### 0. เครื่องมือที่ต้องมี
- Python 3.12+ (ติ๊ก **Add to PATH** ตอนติดตั้ง)
- Git และบัญชี GitHub
- VS Code พร้อมส่วนเสริม **Python** และ **Git Graph**

ตั้งค่าตัวตนของ Git ครั้งแรก (ข้อมูลนี้ติดไปกับทุก commit):
```bash
git config --global user.name "ชื่อของคุณ"
git config --global user.email "you@example.com"
git config --global init.defaultBranch main
git config --list      # ตรวจสอบ
```

### 1. Clone โปรเจค
```bash
git clone <repo-url>
cd projectdjango
```

**Repo นี้ default branch คือ `main`** หลัง clone เสร็จให้สลับไปที่ branch `develop` เองก่อนเริ่มงานทุกครั้ง (ห้ามทำงานหรือแตก branch จาก `main`):
```bash
git switch develop
git pull origin develop
```

### 2. สร้างและเปิดใช้งาน Virtual Environment
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. ติดตั้ง dependencies
```bash
pip install -r requirements.txt
```

### 4. สร้างไฟล์ `.env`
คัดลอกจาก `.env.example` แล้วแก้ค่าตามเครื่องตัวเอง
```bash
cp .env.example .env
```
ตัวอย่างค่าที่ต้องตั้ง:
```
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

**ห้าม commit ไฟล์ `.env` ขึ้น git เด็ดขาด** (มีอยู่ใน `.gitignore` แล้ว)

### 5. Migrate ฐานข้อมูล
```bash
python manage.py migrate
```

> ⚠️ **Custom User Model:** โปรเจคใช้ `accounts.User` (สืบทอด `AbstractBaseUser` + `PermissionsMixin`) และตั้ง `AUTH_USER_MODEL = 'accounts.User'` ใน `settings.py` ไว้แล้ว **ห้ามแก้หรือลบบรรทัดนี้** เพราะต้องตั้งก่อนสั่ง `migrate` ครั้งแรกสุดของโปรเจค การเปลี่ยนย้อนหลังทำให้ฐานข้อมูลพัง (`InconsistentMigrationHistory`) อย่าสร้าง migration ของ user เอง ถ้าไม่แน่ใจให้ถามทีมก่อน (ดูรายละเอียดที่ [Database และ Models](./CONTRIBUTING.md#database-และ-models))

### 6. สร้าง superuser (สำหรับเข้า admin panel)
User ผูกกับภาควิชา (`department` ห้ามว่าง) จึงต้องมี Department อย่างน้อย 1 แถวก่อน
```bash
python manage.py shell -c "from catalog.models import Department; Department.objects.get_or_create(code='CN', defaults={'name_th': 'วิศวกรรมคอมพิวเตอร์', 'name_en': 'Computer Engineering'})"
python manage.py createsuperuser
```
ระบบ login ด้วย **อีเมล** (ไม่มี username) ตอน `createsuperuser` จะถามตามลำดับ: Email, Student id (10 หลัก ตัวที่ 3–4 ต้องเป็น `10` เช่น `6710000001`), Nickname, Department (ใส่ id ของภาค เช่น `1`), Password

### 7. รันเซิร์ฟเวอร์
```bash
python manage.py runserver
```
เข้าใช้งานที่ `http://127.0.0.1:8000/` (หน้า admin ที่ `/admin/`)

---

## ทุกครั้งที่ pull โค้ดใหม่ (Sync ก่อนเริ่มงาน)

```bash
git status                        # เช็คว่าไม่มีงานค้างที่ยังไม่ได้ commit
git fetch origin                  # ดึงข้อมูลล่าสุดมาดูก่อน (ยังไม่แตะไฟล์ในเครื่อง)
git pull origin develop           # fetch + merge
pip install -r requirements.txt   # เผื่อมี package ใหม่
python manage.py migrate          # เผื่อมี migration ใหม่
```

หลังมีคน merge PR เข้า `develop` ทุกคนควรรันชุดนี้ใหม่ทันที เพื่อไม่ให้แก้ไฟล์บนโค้ดเก่าแล้วเกิด conflict ตอนท้าย

---

## Project Structure
```
projectdjango/
├── portal/          # Django project config (settings, urls, wsgi/asgi)
├── accounts/        # User, Role, UserRole (US-1, US-2)
├── catalog/         # Department, Batch, Course, BatchCourse, SystemSetting (US-3, US-4)
├── documents/       # DocType, ExamPeriod, Document, ExamDetail, DocumentVersion (US-5)
├── manage.py
├── requirements.txt
└── README.md
```

ภายในแต่ละ app (เช่น `catalog/`, `accounts/`) ใช้โครงสร้างตามนี้
```
<app>/
├── models.py
├── forms.py                      # Form / ModelForm
├── views.py
├── urls.py                       # app_name + urlpatterns
├── admin.py
├── tests.py  (หรือโฟลเดอร์ tests/)
├── migrations/                   # commit ขึ้น Git
└── templates/<app>/              # เช่น courses/templates/courses/course_detail.html
templates/                        # base.html และ includes/_navbar.html (ส่วนกลาง)
static/                           # css, js, img ส่วนกลาง
```

## Branch Strategy
| Branch | ใช้ทำอะไร |
|---|---|
| `main` | โค้ด production เท่านั้น |
| `develop` | โค้ดล่าสุดของทีม รวม feature ที่เสร็จแล้ว |
| `feature/*` | พัฒนา feature ใหม่ |
| `bugfix/*` | แก้บั๊กที่ไม่เร่งด่วน |
| `hotfix/*` | แก้บั๊กด่วนบน production |

---

## For Contributing
ขั้นตอนการทำงานแบบ Agile/Scrum, มาตรฐานโค้ด Django, Commit Convention, การเปิด PR และ Definition of Done อยู่ใน [CONTRIBUTING.md](./CONTRIBUTING.md) อ่านให้จบก่อนเปิด Pull Request ครั้งแรก