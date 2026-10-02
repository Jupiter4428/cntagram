# Project Django

## Tech Stack
- Python 3.x
- Django
- etc..

---

## Setup ก่อนเริ่มพัฒนา (First Time Setup)

### 1. Clone โปรเจค
```bash
git clone <repo-url>
cd projectdjango
```

**Repo นี้ default branch คือ `main`** หลัง clone เสร็จให้สลับไปที่ branch `develop` เองก่อนเริ่มงานทุกครั้ง (ห้ามทำงานหรือแตก branch จาก `main`):
```bash
git checkout develop
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

### 6. สร้าง superuser (สำหรับเข้า admin panel)
```bash
python manage.py createsuperuser
```

### 7. รันเซิร์ฟเวอร์
```bash
python manage.py runserver
```
เข้าใช้งานที่ `http://127.0.0.1:8000/`

---

## ทุกครั้งที่ pull โค้ดใหม่ (Sync ก่อนเริ่มงาน)

```bash
git pull origin develop
pip install -r requirements.txt   # เผื่อมี package ใหม่
python manage.py migrate          # เผื่อมี migration ใหม่
```

---

## Agile Workflow (ก่อนจะส่งโค้ด)

ทีมใช้ระบบ Sprint-based development บน Agile/Scrum โดยมีขั้นตอนดังนี้:

### 1. หยิบงานจาก Backlog / Board
- เช็ค task ใน [Jira / Trello / GitHub Projects ฯลฯ — ระบุเครื่องมือที่ทีมใช้]
- ย้ายสถานะ task เป็น **In Progress** ก่อนเริ่มทำ
- Assign ตัวเองเป็นผู้รับผิดชอบ task

### 2. สร้าง Branch ใหม่จาก `develop`

**กฎสำคัญ: ทุกคนต้องสร้าง branch ของตัวเองใหม่ทุกครั้งที่เริ่มงาน ห้ามทำงานตรงบน `develop` หรือ `main` เด็ดขาด และห้ามใช้ branch ร่วมกับคนอื่น**

ตั้งชื่อ branch ตาม convention:
```
feature/<ชื่อ-feature>      เช่น feature/user-login
bugfix/<ชื่อ-bug>           เช่น bugfix/fix-null-email
hotfix/<ชื่อ-hotfix>        เช่น hotfix/prod-crash
```
```bash
git checkout develop
git pull origin develop
git checkout -b feature/user-login
```

### 3. พัฒนาและ Commit
- Commit บ่อยๆ เป็นก้อนเล็กๆ ที่มีความหมาย
- เขียน commit message ตามรูปแบบใน [Commit Message Convention](#-commit-message-convention) ด้านล่าง เช่น
  ```
  feat: add login form validation
  fix: correct date format in invoice
  ```
- รันเทสก่อน commit ทุกครั้ง (ถ้ามี test suite)
  ```bash
  python manage.py test
  ```

### 4. Push และเปิด Pull Request (PR) / Merge Request (MR)

เมื่อทำงานใน branch ของตัวเองเสร็จแล้ว ให้ push ขึ้น branch ของตัวเองก่อน (ไม่ push ตรงเข้า `develop`/`main`/`master` เด็ดขาด):
```bash
git push origin feature/user-login
```
- จากนั้นเปิด PR จาก branch ของตัวเองเข้า `develop` เพื่อเข้ากระบวนการ review ตามขั้นตอนถัดไป
- ใส่คำอธิบายว่า PR นี้ทำอะไร, เกี่ยวกับ task ไหน, วิธีทดสอบ
- แนบ screenshot/ผลลัพธ์ถ้าเกี่ยวกับ UI

### 5. Code Review
- ต้องมีอย่างน้อย **1 คนรีวิวและ approve** ก่อน merge
- แก้ตาม comment ที่ reviewer ให้มา
- ห้าม self-merge โดยไม่มีคน approve

### 6. Merge เข้า `develop`
- ใช้ **Squash and Merge** หรือ **Merge commit** ตามที่ทีมตกลงกัน
- ลบ branch ทิ้งหลัง merge เสร็จ

### 7. อัปเดตสถานะ Task
- ย้าย task บน board ไปเป็น **Done** หรือ **Ready for QA** ตาม workflow ของทีม

### 8. Sprint Review / Retrospective
- นำงานที่เสร็จไป demo ใน Sprint Review
- ร่วมพูดคุยใน Retrospective ว่าอะไรควรปรับปรุงในสปรินท์ถัดไป

---

## 📝 Commit Message Convention

ทีมใช้รูปแบบ [Conventional Commits](https://www.conventionalcommits.org/) เพื่อให้ประวัติ commit อ่านง่ายและตรวจสอบย้อนหลังได้

### รูปแบบ
```
<type>: <คำอธิบายสั้นๆ>

[รายละเอียดเพิ่มเติม (ถ้าจำเป็น)]
```

### Type ที่ใช้
| Type | ใช้เมื่อ | ตัวอย่าง |
|---|---|---|
| `feat` | เพิ่มฟีเจอร์ใหม่ | `feat: add user login page` |
| `fix` | แก้บั๊ก | `fix: correct date format in invoice` |
| `docs` | แก้ไขเอกสารเท่านั้น (README, CONTRIBUTING ฯลฯ) | `docs: update setup instructions` |
| `style` | ปรับ format/โค้ดสไตล์ที่ไม่กระทบการทำงาน (เว้นวรรค, semicolon, CSS ล้วนๆ) | `style: format views.py with black` |
| `refactor` | ปรับโครงสร้างโค้ดโดยไม่เพิ่มฟีเจอร์และไม่แก้บั๊ก | `refactor: extract order logic into service` |
| `perf` | ปรับปรุงประสิทธิภาพ | `perf: add index to product table` |
| `test` | เพิ่มหรือแก้ไข test | `test: add unit tests for login form` |
| `chore` | งานจุกจิกที่ไม่เกี่ยวกับโค้ดหลัก (อัปเดต dependency, แก้ config) | `chore: update requirements.txt` |
| `build` | เปลี่ยนแปลงระบบ build หรือ dependency ภายนอก | `build: upgrade Django to 5.0` |
| `ci` | แก้ไข CI/CD pipeline | `ci: add GitHub Actions test workflow` |
| `revert` | ย้อน commit ก่อนหน้า | `revert: revert "feat: add user login page"` |

### กฎการเขียน
- ใช้ **type เป็นตัวพิมพ์เล็กทั้งหมด** ตามด้วย `:` และเว้นวรรค 1 ครั้ง
- คำอธิบายขึ้นต้นด้วย **คำกริยา** (add, fix, update, remove ...) และไม่ต้องลงท้ายด้วยจุด
- ความยาวบรรทัดแรกไม่ควรเกิน **72 ตัวอักษร**
- **1 commit = 1 เรื่อง** อย่ารวมหลายงานไว้ใน commit เดียว
- ถ้าต้องการระบุขอบเขต สามารถใส่ scope ในวงเล็บได้ เช่น `feat(auth): add password reset`
- ถ้าเกี่ยวข้องกับ task ให้อ้างอิงใน body หรือท้าย message เช่น `Refs #12`

### ตัวอย่างที่ดี ✅
```
feat: add login form validation
fix(auth): prevent null email on signup
docs: add commit message convention
refactor: split views into separate modules
chore: remove unused imports
```

### ตัวอย่างที่ไม่ดี ❌
```
update                    # ไม่มี type และไม่บอกว่าแก้อะไร
Fix bug.                  # type ตัวพิมพ์ใหญ่, ไม่ชัดเจน, มีจุดท้ายประโยค
feat:add stuff and fix x  # ไม่เว้นวรรค และรวมหลายเรื่องใน commit เดียว
```

---

## ✅ Checklist ก่อนส่งโค้ด (ก่อนเปิด PR)

- [ ] Pull โค้ดล่าสุดจาก `develop` และ merge/rebase เข้า branch ตัวเองแล้ว
- [ ] รันโค้ดแล้วไม่มี error
- [ ] รัน test ผ่านทั้งหมด
- [ ] ไม่มีไฟล์ `.env`, `db.sqlite3`, หรือไฟล์ credential หลุดไปใน commit
- [ ] Commit message สื่อความหมายชัดเจน และตรงตาม Commit Message Convention
- [ ] อัปเดต `requirements.txt` ถ้ามีการติดตั้ง package ใหม่
- [ ] ลบ debug code / print ที่ไม่จำเป็นออก
- [ ] ย้ายสถานะ task บน board ให้ตรงกับความคืบหน้าจริง

---

## Project Structure
```
projectdjango/
├── portal/          # Django project config (settings, urls, wsgi/asgi)
├── manage.py
├── requirements.txt
└── README.md
```

## Branch Strategy
| Branch | ใช้ทำอะไร |
|---|---|
| `main` | โค้ด production เท่านั้น |
| `develop` | โค้ดล่าสุดของทีม รวม feature ที่เสร็จแล้ว |
| `feature/*` | พัฒนา feature ใหม่ |
| `bugfix/*` | แก้บั๊กที่ไม่เร่งด่วน |
| `hotfix/*` | แก้บั๊กด่วนบน production |
