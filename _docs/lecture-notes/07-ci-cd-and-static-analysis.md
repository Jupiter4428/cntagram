# CI/CD Pipelines & Static Code Analysis: GitHub Actions, Flake8, Black, Bandit & Quality Gates

> ที่มา: CN331 สัปดาห์ที่ 12 — CI/CD Pipelines & Static Code Analysis หน่วยที่ 1–4 และบทสรุป
>
> *จากชุดทดสอบบนเครื่องตัวเองสู่ระบบตรวจสอบอัตโนมัติบน GitHub: CI/CD, GitHub Actions, Linters, Security Scan และ Branch Protection*
>
> เนื้อหาที่เกี่ยวข้อง: Coverage.py และ `--fail-under=80` → ดู [06-django-automated-testing.md](06-django-automated-testing.md) · Velocity, Sprint Review/Retro และ DoD → ดู [05-agile-scrum-sprints.md](05-agile-scrum-sprints.md)

---

## ทำไมวิศวกรซอฟต์แวร์ต้องมีระบบอัตโนมัติ CI/CD และ Static Analysis?

**☠️ หายนะของการผสานโค้ดด้วยมือ (Integration Hell)**
- **"Works on My Machine"**: โค้ดรันผ่านบนเครื่องเพื่อน แต่พอนำมารวมกันกลับรันไม่ขึ้นเพราะเวอร์ชันของ Library หรือ Environment ไม่ตรงกัน
- **Merge Fatigue**: สมาชิกในทีมแยกพัฒนาไว้ในกิ่งตนเองนานเกินไปจนเกิด Conflict มหาศาลเมื่อถึงกำหนดรวมโค้ด
- **Inconsistent Styles**: ต่างคนต่างเขียนตามใจชอบ โค้ดยุ่งเหยิง ขาดมาตรฐาน ทำให้อ่านยากและตรวจสอบข้อบกพร่องได้ช้า

**🤖 เกราะป้องกันอัตโนมัติ: CI/CD & Linters**
- **Zero-Human Gatekeeper**: ทุก Pull Request จะถูก Build, Test และ Lint อัตโนมัติในสภาพแวดล้อม Clean Container
- **Immediate Feedback**: แจ้งเตือนข้อผิดพลาดภายใน 2–3 นาทีหลังการ Push ก่อนที่โค้ดเสียจะปนเปื้อนเข้ากิ่งหลัก
- **Enforced Quality**: บังคับใช้มาตรฐานทีมโดยไม่ต้องถกเถียงเรื่องการเคาะวรรคหรือจัดหน้าในระหว่างการรีวิวโค้ด

> 💡 **Takeaway** — **DevOps Paradigm**: *"If it hurts, do it more often, and bring the pain forward."* — Jez Humble การผสานโค้ดอย่างต่อเนื่องช่วยเปลี่ยนความเจ็บปวดของการรวมโค้ดให้กลายเป็นกิจวัตรที่ราบรื่น

---

# หน่วยที่ 1: รากฐาน CI/CD และระบบอัตโนมัติแบบ DevOps

## Continuous Integration (CI) คืออะไร?

**Continuous Integration (CI)** คือแนวปฏิบัติทางวิศวกรรมซอฟต์แวร์ที่สมาชิกทุกคนในทีมรวมโค้ด (Merge) เข้าสู่กิ่งกลาง (Main Branch) อย่างสม่ำเสมอ อย่างน้อยวันละครั้ง:

- **Automated Build Verification**: ทุกการ Push หรือ Pull Request ระบบจะสร้างสภาพแวดล้อมขึ้นมาใหม่และติดตั้งโปรเจกต์อัตโนมัติ
- **Automated Test Suite**: รันชุดทดสอบ (Unit Tests & Integration Tests) เพื่อยืนยันว่าไม่มีฟังก์ชันเดิมพัง
- **Automated Quality Checks**: สแกนตรวจสอบความปลอดภัยและจัดรูปแบบโค้ด

```
Developer Pushes Code   → Git Commit → GitHub PR
CI Runner Triggered     → Checkout → Install → Test → Lint
Status Feedback         → ✓ Green (Mergeable)   ✗ Red (Blocked)
```

> 💡 **Takeaway** — **CI Core Purpose**: เป้าหมายหลักของ CI ไม่ใช่แค่การรันเทส แต่คือการตรวจจับปัญหาการผสานโค้ดให้เร็วที่สุด (Fast Feedback) เพื่อให้ต้นทุนในการแก้ปัญหาต่ำที่สุด

## ความแตกต่าง: Continuous Integration vs Delivery vs Deployment

ทำความเข้าใจ 3 ระดับของไปป์ไลน์ในโลกวิศวกรรมซอฟต์แวร์:

| ระดับ | สิ่งที่ทำ | ใครกดปล่อย |
|---|---|---|
| **1. Continuous Integration (CI)** | สร้าง Build, รัน Tests และ Static Analysis ทุกครั้งที่มีการ Commit/PR เพื่อการันตีว่าโค้ดไม่มีข้อบกพร่อง | — (Build → Test → Lint) |
| **2. Continuous Delivery (CD)** | แพ็กเกจโค้ดที่ผ่าน CI เป็น **Release Candidate** พร้อมใช้งานได้ทุกเมื่อ | **มนุษย์กดปุ่มอนุมัติ (Manual Approval)** ก่อนปล่อยสู่ Production |
| **3. Continuous Deployment (CD)** | โค้ดที่ผ่านการทดสอบทุกด่านจะถูก Deploy สู่ Production | อัตโนมัติ **100% โดยไม่ต้องรอมนุษย์** |

> 💡 **Takeaway** — **Pipeline Progression**: CI ยืนยันความถูกต้องของโค้ด Delivery เตรียมความพร้อมของ Artifacts และ Deployment นำคุณค่าไปสู่มือผู้ใช้งานจริง

## QUICK CHECK: CI/CD Concept Differentiation

*(สไลด์ไม่มีเนื้อหาคำถาม)*

## กลยุทธ์การจัดการกิ่งสำหรับ CI: GitHub Flow vs GitFlow

เพื่อให้ CI มีประสิทธิภาพสูงสุด ทีมจำเป็นต้องเลือกรูปแบบ Branching ที่เหมาะสม:

- **GitFlow (แบบดั้งเดิม)**: มีหลายกิ่ง (`master`, `develop`, `release`) ซึ่งสร้างภาระ Merge มหาศาล ไม่เหมาะกับเว็บยุคใหม่
- **GitHub Flow (คล่องตัว เหมาะกับ Agile & CI)**:
  - กิ่ง `main` ต้อง Deploy ได้ตลอดเวลาเสมอ
  - แตกกิ่งสั้น `feature/*` และเปิด Pull Request
  - รัน CI และ Peer Review ก่อน Merge กลับเข้าสู่ `main`

```
feature/enrollment     ╭──●────●──╮
                      ╱            ╲
main  ───────────────●──────●───────●──────
                            ↑
                    CI Check & PR Review
```

> 💡 **Takeaway** — **Branching Rule**: สำหรับโปรเจกต์ CN331 กำหนดให้ใช้ **GitHub Flow** สร้างกิ่งอายุสั้น (Short-lived Branches) และ Merge กลับสู่ `main` ภายใน 1–2 วัน

## QUICK CHECK: Branching Strategy for Fast CI Feedback

*(สไลด์ไม่มีเนื้อหาคำถาม)*

---

# หน่วยที่ 2: สถาปัตยกรรม GitHub Actions และการเขียน Workflow

## องค์ประกอบโครงสร้างของ GitHub Actions (Core Concepts)

GitHub Actions ประกอบด้วยหน่วยการทำงานหลักที่เชื่อมโยงกันอย่างเป็นระบบ:

- **Workflows**: ชุดคำสั่งกระบวนการอัตโนมัติที่นิยามด้วยไฟล์ **YAML** บันทึกไว้ในโฟลเดอร์ `.github/workflows/`
- **Events (ทริกเกอร์)**: เหตุการณ์บน GitHub ที่กระตุ้นให้ Workflow เริ่มทำงาน เช่น `push`, `pull_request`
- **Jobs (กลุ่มงาน)**: ชุดของขั้นตอนย่อยที่รันบน Runner เดียวกัน โดยแต่ละ Job จะทำงานแบบขนานกัน (Parallel) โดยดีฟอลต์
- **Runners**: เซิร์ฟเวอร์เสมือน (VM Container) เช่น `ubuntu-latest` ที่ GitHub เตรียมไว้ให้รันคำสั่ง
- **Steps / Actions**: คำสั่งย่อยใน Job เช่น การ Checkout โค้ด หรือคำสั่งเชลล์ `run: pytest`

```
Workflow (ci.yml)     → Trigger: on: [push, pull_request]
  Job: test-and-lint  → Runner: ubuntu-latest
    Steps & Actions   → 1. actions/checkout@v4
                        2. actions/setup-python@v5
                        3. run: pip install -r requirements.txt
                        4. run: python manage.py test
```

> 💡 **Takeaway** — **Declarative Automation**: GitHub Actions ใช้รูปแบบการเขียนแบบ Declarative YAML เพื่อระบุสิ่งที่ต้องการให้ทำในแต่ละขั้นอย่างเป็นลำดับและชัดเจน

## โครงสร้างไฟล์จริง: `.github/workflows/ci.yml`

ตัวอย่างการตั้งค่า Workflow สำหรับระบบ Django ของรายวิชา CN331:
- ระบุชื่อ Workflow ให้ชัดเจน
- ดักจับ Event ทั้งการ Push และ Pull Request ที่กระทำต่อกิ่ง `main`
- กำหนด Environment Variables เช่น `SECRET_KEY` และ `DEBUG=False`
- เริ่มต้นด้วยการ Checkout ซอร์สโค้ดลงสู่เครื่อง Runner

```yaml
name: CN331 Django CI Pipeline

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      SECRET_KEY: ci-temporary-secret-key
      DEBUG: "False"

    steps:
      - name: Check out code
        uses: actions/checkout@v4
```

> 💡 **Takeaway** — **Standard Location**: GitHub จะมองหาเฉพาะไฟล์ที่อยู่ในโฟลเดอร์ `.github/workflows/*.yml` เท่านั้น หากวางผิดตำแหน่งระบบจะไม่เริ่มทำงาน

## การติดตั้ง Python และเร่งความเร็วด้วย Dependency Caching

หากสั่ง `pip install` ใหม่ทั้งหมดทุกรอบ จะเสียเวลาดาวน์โหลดไลบรารีซ้ำซาก:
- ใช้ `actions/setup-python@v5` พร้อมเปิดออปชัน `cache: 'pip'`
- หากไฟล์ `requirements.txt` ไม่มีการเปลี่ยนแปลง GitHub Actions จะดึง Cache เดิมมาใช้ทันที ช่วยลดเวลาจาก 2 นาทีเหลือเพียง 10 วินาที!
- อัปเกรด pip และติดตั้ง Dependencies ให้พร้อมสำหรับทั้งการเทสและการตรวจสอบสไตล์โค้ด

```yaml
      - name: Set up Python runtime
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install flake8 black bandit coverage

      - name: Run Django Automated Tests
        run: |
          python manage.py test --noinput
```

> 💡 **Takeaway** — **Cache Optimization**: การใส่ `cache: 'pip'` เป็น Best Practice ที่ทีมวิศวกรซอฟต์แวร์ทุกคนต้องทำ เพื่อประหยัดโควตา Free Tier Minutes ของ GitHub

## การตรวจสอบความครอบคลุม (Coverage Gate) ใน CI

เชื่อมโยงความรู้จากสัปดาห์ที่ 11: เราสามารถสั่งให้ CI ล้มเหลวทันทีหากอัตรา Coverage ต่ำกว่าเกณฑ์ที่กำหนด!
- ใช้คำสั่ง `coverage run` รันเทส
- ตรวจสอบเกณฑ์ขั้นต่ำด้วยคำสั่ง `coverage report --fail-under=80`
- หากความครอบคลุมได้ 79% คำสั่งนี้จะคืน Exit Code เป็น 1 ซึ่งทำให้ GitHub Actions สั่งตัดตก (Red) ทันที
- จัดเก็บรายงาน HTML ไว้เป็น Artifact เพื่อเปิดดูรายละเอียดในภายหลังได้

```yaml
      - name: Run Tests with Coverage Enforcement
        run: |
          coverage run --source='.' manage.py test
          coverage report -m --fail-under=80

      - name: Generate HTML Report Artifact
        if: always()
        run: coverage html

      - name: Upload Coverage Artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: code-coverage-report
          path: htmlcov/
```

> 💡 **Takeaway** — **Enforceable DoD**: การใส่พารามิเตอร์ `--fail-under=80` ช่วยเปลี่ยนข้อตกลงปากเปล่าในทีมให้กลายเป็น "กฎเหล็กทางวิศวกรรม" ที่ไม่มีใครสามารถละเลยได้

## QUICK CHECK: Dependency Caching in GitHub Actions

*(สไลด์ไม่มีเนื้อหาคำถาม)*

## การจัดการความลับ (GitHub Encrypted Secrets & Security)

**☢️ กฎเหล็กความปลอดภัยหมายเลข 1** — **ห้ามฮาร์ดโค้ดข้อมูลความลับ (Secrets / API Keys) ลงใน Git Repository อย่างเด็ดขาด!** เช่น Database Passwords, Stripe Secret Keys หรือ API Tokens

**วิธีใช้งาน GitHub Encrypted Secrets**:
1. ไปที่ Repo **Settings → Secrets and variables → Actions**
2. สร้าง Secret ใหม่ เช่น `STRIPE_SECRET_KEY`
3. อ้างอิงใน `ci.yml` ผ่านตัวแปร `${{ secrets.STRIPE_SECRET_KEY }}`

```yaml
    steps:
      - name: Run Integration Tests
        env:
          # Retrieve secret from GitHub secret store
          STRIPE_API_KEY: ${{ secrets.STRIPE_API_KEY }}
          DATABASE_URL: ${{ secrets.TEST_DB_URL }}
        run: |
          python manage.py test
```

**Log Masking Mechanism** — GitHub จะทำการปิดบัง (Mask) ข้อความที่เป็น Secret ในหน้า Logs ให้กลายเป็นดอกจัน `***` อัตโนมัติ เพื่อป้องกันข้อมูลหลุด

> 💡 **Takeaway** — **Zero Hardcoded Secrets**: เก็บความลับของระบบไว้ใน GitHub Secrets หรือไฟล์ `.env` ที่ระบุไว้ใน `.gitignore` เสมอ

## QUICK CHECK: Secrets Management in CI Pipelines

*(สไลด์ไม่มีเนื้อหาคำถาม)*

---

# หน่วยที่ 3: การวิเคราะห์โค้ดสถิต Linters และเครื่องมือตรวจความปลอดภัย

## การทดสอบแบบไดนามิก (Dynamic) กับการวิเคราะห์แบบสถิต (Static Analysis)

วิศวกรรมซอฟต์แวร์ที่สมบูรณ์ต้องอาศัยทั้งสองเสาหลักคู่กัน:

| | Static Analysis (สัปดาห์นี้) | Dynamic Testing (สัปดาห์ที่ 11) |
|---|---|---|
| **เครื่องมือ** | Flake8, Black, Bandit | Django TestCase, Pytest |
| **วิธีตรวจ** | ตรวจสอบโครงสร้างข้อความและไวยากรณ์ (AST) **โดยไม่ต้องสั่งรันโค้ด** | รันโค้ดจริง ตรวจสอบพฤติกรรม |
| **จับอะไรได้** | Unused variables, Imports และสไตล์ PEP 8 (Style/Smell) | Logic errors, Status codes |
| **ความเร็ว / สิ่งที่ต้องใช้** | เร็วมาก ไม่ต้องรันโค้ด | ต้องอาศัย Database และ Python runtime จำลอง |

**Production Ready Code** = ผ่านทั้งสองด่านพร้อมกัน

> 💡 **Takeaway** — **Complementary Roles**: Static Analysis ช่วยกวาดล้างข้อผิดพลาดผิวเผินและจัดระเบียบโค้ดให้สะอาด เพื่อให้ Unit Tests มุ่งเน้นตรวจสอบ Business Logic ได้อย่างเต็มที่

## การตรวจจับ Code Smells ด้วย Flake8 (PEP 8 Linter)

**Flake8** รวม PyFlakes (ตรวจบั๊ก), Pycodestyle (ตรวจ PEP 8) และ McCabe (ตรวจความซับซ้อน):
- ตรวจจับตัวแปรและ Imports ที่ไม่ได้ใช้
- ตรวจสอบความยาวบรรทัด (`max-line-length`)
- ละเว้นโฟลเดอร์ Migration เสมอ (`*/migrations/*`) เพราะเป็นโค้ดที่ Django สร้างขึ้นอัตโนมัติ

สร้างไฟล์คอนฟิก `.flake8` ไว้ที่ Root ของโปรเจกต์:

```ini
# .flake8 configuration file
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    */migrations/*,
    venv,
    .venv

# Run linter via terminal:
# flake8 .
```

> 💡 **Takeaway** — **Lint Configuration**: การกำหนดไฟล์คอนฟิก `.flake8` ช่วยสร้างขอบเขตการตรวจสอบที่เป็นธรรมและขจัด Warning ที่ไม่จำเป็น

## ตัวอย่างจริง: ข้อผิดพลาดจาก Flake8 และแนวทางแก้ไข (Failure vs Fix)

**❌ CI Log: การตัดตกโดย Flake8 (Exit Code 1)**

```
$ flake8 .
views.py:4:1: F401 'sys' imported but unused
views.py:18:89: E501 line too long (92 > 88)
services.py:22:5: F841 local variable 'temp' unused
Error: Process completed with exit code 1.
```

- **F401**: อิมพอร์ตโมดูลมาแต่ไม่ได้ใช้งานจริง
- **E501**: บรรทัดยาวเกินกำหนด 88 ตัวอักษร
- **F841**: ประกาศตัวแปรรับค่าแต่ไม่เคยใช้

**✅ Local Terminal Fix: แก้ไขและตรวจสอบก่อน Push**

```bash
# 1. Run Flake8 locally
flake8 .

# 2. Fix lines: remove unused imports & vars
# 3. Verify that output is clean (code 0)
flake8 . && echo "Flake8 passed cleanly!"

# 4. Commit and push safely
git commit -am "fix(style): resolve flake8"
git push origin feature/my-branch
```

> 💡 **Takeaway** — **Local Validation**: ตรวจสอบด้วยคำสั่ง `flake8 .` บนเครื่องตนเองให้ผ่านก่อนเปิด Pull Request เสมอ เพื่อไม่ให้ไปป์ไลน์ของทีมติดสถานะสีแดง

## การจัดรูปแบบอัตโนมัติด้วย Black (Deterministic Formatter)

**Black** คือ Formatter ที่เปลี่ยนรูปแบบโค้ดทั้งโปรเจกต์ให้ตรงกัน 100%:
- **End Code Review Bikeshedding**: ตัดข้อพิพาทในทีมเกี่ยวกับการเคาะวรรคหรือเครื่องหมายคำพูด
- **Deterministic Output**: โค้ดแบบเดียวกันจะถูกฟอร์แมตออกมาเป็นผลลัพธ์แบบเดียวกันเสมอ ไม่ว่าใครจะเป็นผู้เขียน
- **Check Mode in CI**: สั่งรันใน CI ด้วยออปชัน `--check`: `black --check --diff .`

```python
# Before Black (messy):
def reg(student,course,is_audit=False):
  return Enrollment.objects.create(
    student=student,course=course)

# After running black . (PEP 8 format):
def reg(student, course, is_audit=False):
    return Enrollment.objects.create(
        student=student, course=course
    )
```

> 💡 **Takeaway** — **Automate Formatting**: ให้นักพัฒนาสั่ง `black .` บนเครื่องตนเองก่อน Commit หรือตั้งค่า Format on Save ใน VS Code

## การสแกนความปลอดภัยซอร์สโค้ดด้วย Bandit (Security Linter)

**Bandit** คือเครื่องมือวิเคราะห์ทางสถิตที่ค้นหาช่องโหว่ความปลอดภัยที่พบบ่อยในโค้ดภาษา Python:
- ตรวจจับคำสั่งอันตราย เช่น `eval()`, `exec()`
- ตรวจจับการ Hardcoded รหัสผ่านหรือ Token (`B105`)
- ตรวจจับการใช้ PRNG ไม่ปลอดภัย (`random` แทน `secrets`) สำหรับโทเค็นรหัสผ่าน (`B311`)
- ตรวจจับ Raw SQL Injection risks

```python
# Run security scan in CI:
# bandit -r . -x */tests/*,*/migrations/*

# Example dangerous pattern flagged by Bandit:
import random

# BAD (B311): Pseudo-random for security
reset_token = random.randint(100000, 999999)

# GOOD: Cryptographically strong PRNG
import secrets
reset_token = secrets.token_urlsafe(32)
```

> 💡 **Takeaway** — **Security Shift-Left**: รัน Bandit ใน CI เพื่อสกัดกั้นช่องโหว่ร้ายแรงก่อนที่แอปพลิเคชันจะถูกนำไปเผยแพร่จริง

## ตัวอย่างจริง: ข้อผิดพลาดจาก Bandit และการแก้ไข (Security Remediation)

**🛡️ CI Warning (Bandit Exit Code 1)**

```
$ bandit -r . -x */tests/*,*/migrations/*
>> Issue: [B105:hardcoded_password_string]
   Possible hardcoded password: 'jwt_key_99'
   Location: config/settings.py:42
>> Issue: [B311:blacklist] Standard pseudo-
   random generators not suitable for crypto
   Location: users/services.py:15
[results] Total issues: 2 (High: 0, Med: 2)
```

**🔒 Security Remediation: แนวทางแก้ไข**

```python
# Fix 1: Read secrets from Environment
import os
SECRET_KEY = os.environ.get("SECRET_KEY")

# Fix 2: Use secrets module for tokens
import secrets
reset_token = secrets.token_urlsafe(32)

# Fix 3: Run local security scan
# bandit -r . -x */tests/*,*/migrations/*
```

> 💡 **Takeaway** — **Remediation Rule**: ห้ามใช้ข้อยกเว้น (`# nosec`) เพื่อซ่อนปัญหาความปลอดภัย ให้แก้ไขที่ต้นตอของโค้ดด้วยการใช้ Environment Variables และโมดูล Cryptographic เสมอ

## การผนวก Linters และ Security Scanners เข้าสู่ `ci.yml`

รวมด่านการตรวจสอบทั้งหมดเข้าด้วยกันเป็น Pipeline ที่สมบูรณ์ใน GitHub Actions:
1. ตรวจสอบฟอร์แมตโค้ดด้วย `black --check`
2. ตรวจสอบความถูกต้องและสไตล์ด้วย `flake8`
3. สแกนความปลอดภัยด้วย `bandit`
4. รันชุดทดสอบพร้อมบังคับ Coverage ด้วย `coverage`

หากขั้นตอนใดไม่ผ่าน ไปป์ไลน์จะหยุดทำงานและขึ้นสถานะสีแดงทันที

```yaml
      - name: Code Formatting Check (Black)
        run: black --check --diff .

      - name: Static Code Linting (Flake8)
        run: flake8 .

      - name: Security Vulnerability Scan (Bandit)
        run: bandit -r . -x */tests/*,*/migrations/*

      - name: Run Test Suite & Enforce Coverage
        run: |
          coverage run --source='.' manage.py test
          coverage report -m --fail-under=80
```

> 💡 **Takeaway** — **Multi-Layered Gates**: การมีด่านตรวจสอบหลายชั้นช่วยการันตีว่าโค้ดที่ผ่านเข้ากิ่งหลักจะมีทั้งความปลอดภัย รูปแบบที่สะอาด และพฤติกรรมที่ถูกต้อง

## QUICK CHECK: Linter vs Dynamic Test Detection

*(สไลด์ไม่มีเนื้อหาคำถาม)*

## QUICK CHECK: Security Linting with Bandit

*(สไลด์ไม่มีเนื้อหาคำถาม)*

---

# หน่วยที่ 4: การตรวจทานโค้ด การปิด Sprint 2 และเปิดตัว Sprint 3

## การตั้งค่า Branch Protection Rules บน GitHub (Quality Enforcer)

เพื่อป้องกันไม่ให้สมาชิกในทีมสามารถใช้คำสั่ง `git push origin main` ข้ามระบบตรวจสอบได้โดยตรง:
- **Require Pull Request Before Merging**: ห้าม Push โค้ดตรงเข้ากิ่ง `main` ทุกคนต้องทำงานผ่าน Branch และเปิด PR เท่านั้น
- **Require Status Checks to Pass**: เลือก Workflow ของ CI ให้เป็นเงื่อนไขบังคับ (Status Check must be Green) หากเทสหรือ lint ตก ปุ่ม Merge จะถูกล็อก (Disabled)
- **Require Approvals**: กำหนดให้ต้องมีเพื่อนร่วมทีมอย่างน้อย 1 คนรีวิวและกด Approve ก่อนจึงจะรวมโค้ดได้
- **Include Administrators**: บังคับใช้กฎนี้แม้แต่กับหัวหน้าทีมเพื่อความเสมอภาคทางวิศวกรรม

```
Developer Opens PR     → feature → main
Enforced Branch Gates  → ✓ CI Tests Pass (100%)
                         ✓ Coverage ≥ 80%
                         ✓ Linters & Bandit Pass
                         ✓ 1+ Peer Approval
Merge Allowed!         → Safe Integration into main
```

> 💡 **Takeaway** — **Governance Rule**: สำหรับทุกกลุ่มใน CN331 กิ่ง `main` ต้องตั้งค่า Branch Protection เสมอ เพื่อรับประกันว่าไม่มีโค้ดเสียหลุดเข้าสู่กิ่งหลัก

## มารยาทและมาตรฐานการเปิด Pull Request (PR Template)

Pull Request ที่ดีช่วยให้ผู้ตรวจทานเข้าใจบริบทได้อย่างรวดเร็ว:
- สร้างไฟล์ `.github/pull_request_template.md`
- บังคับให้ผู้เปิด PR ระบุ:
  - User Story หรือ Issue ที่เกี่ยวข้อง
  - สรุปการเปลี่ยนแปลง (Summary of Changes)
  - หลักฐานการทดสอบ (Test Evidence)
  - รายการตรวจความเรียบร้อย (Checklist)

```markdown
<!-- .github/pull_request_template.md -->
### Related Issue
Closes #42 (User Story: Course Drop)

### Summary of Changes
- Implemented drop_course_service
- Added unit tests with 92% coverage
- Verified Flake8 and Black compliance

### Test Evidence
- [x] Unit tests pass locally
- [x] Coverage >= 80% & CI pass

### Checklist for Reviewer
- [ ] Follows project architecture
- [ ] No hardcoded secrets
```

> 💡 **Takeaway** — **Engineering Professionalism**: การเขียน PR Description ที่ชัดเจนแสดงถึงวุฒิภาวะทางวิศวกรรมและช่วยลดเวลาในการทำ Code Review ลงได้เกินครึ่ง

## QUICK CHECK: Branch Protection & Quality Enforcement

*(สไลด์ไม่มีเนื้อหาคำถาม)*

## การปิดรอบ Sprint 2: Sprint Review & Retrospective

**📈 Sprint 2 Review (การส่งมอบงาน)**
- **Demonstrate Working Software**: แสดงการทำงานของ Service Layer, Selectors และชุดทดสอบที่ทำงานผ่านจริง
- **Calculate Actual Velocity**:

  **Velocity = Σ Story Points of "Done" Stories**

  นำค่าความเร็วจริงใน Sprint 2 มาเปรียบเทียบกับ Sprint 1 เพื่อดูพัฒนาการของทีม

**💬 Sprint 2 Retrospective (การปรับปรุงทีม)**
- **What Went Well?**: ชุดทดสอบและ CI ช่วยจับข้อผิดพลาดเรื่องอะไรได้บ้าง?
- **What Could Be Improved?**: มีสมาชิกคนใดติดปัญหาเรื่อง Lint หรือ Branch Conflict หรือไม่?
- **Action Items for Sprint 3**: ตั้งเป้าหมายร่วมกันในการนำระบบขึ้นสู่ Cloud และรักษาความปลอดภัยในรอบสุดท้าย

> 💡 **Takeaway** — **Agile Governance**: การคำนวณ Actual Velocity ช่วยให้การประเมินงานใน Sprint 3 วางแผนได้แม่นยำ ไม่แบกงานเกินกำลัง

## เปิดตัว Sprint 3 (สัปดาห์ที่ 12–13): การเตรียมความพร้อมสู่ Production

**Sprint 3** เป็นสปรินต์สุดท้ายของการพัฒนา ก่อนการนำเสนอในสัปดาห์ที่ 14:
- **Sprint 3 Goal**: *"Hardened, Secure, and Deployed to Cloud"*
- **Key Backlog Categories**:
  - **Web Security**: ป้องกัน OWASP Top 10, XSS, CSRF
  - **Production Config**: ล็อก `DEBUG=False`, WhiteNoise
  - **Cloud Deployment**: รันบน Render ร่วมกับ PostgreSQL
  - **Final Release**: สร้าง Release Tag และเอกสารคู่มือ

| Sprint | สัปดาห์ | เนื้อหาหลัก |
|---|---|---|
| Sprint 1 | Weeks 6–7 | Core CRUD, Forms, Models |
| Sprint 2 | Weeks 10–12 | Architecture, Testing, CI/CD |
| Sprint 3 | Weeks 12–13 | Security, Deployment, Release |

> 💡 **Takeaway** — **Final Sprint Focus**: ใน Sprint 3 ทีมจะไม่เพิ่มฟีเจอร์แปลกใหม่ที่เสี่ยงต่อการพัง แต่จะเน้นการขัดเกลาคุณภาพ ความปลอดภัย และความเสถียรบนระบบคลาวด์จริง

## QUICK CHECK: Sprint 3 Planning Priority

*(สไลด์ไม่มีเนื้อหาคำถาม)*

---

# สรุปบทเรียน: ตารางสังเคราะห์องค์ความรู้

## ตารางสังเคราะห์องค์ความรู้ (ตอนที่ 1): องค์ประกอบสำคัญของระบบ CI/CD

| องค์ประกอบ | ตำแหน่งจัดเก็บ / คำสั่ง | หน้าที่ทางวิศวกรรม | ความสำคัญ |
|---|---|---|---|
| **Workflow Config** | `.github/workflows/*.yml` | นิยามเหตุการณ์และขั้นตอนทั้งหมดในรูป Declarative | สูงสุด |
| **Runner Machine** | `runs-on: ubuntu-latest` | สภาพแวดล้อม Clean Container ชั่วคราวสำหรับรันคำสั่ง | สูงสุด |
| **Dependency Cache** | `cache: 'pip'` ใน setup-python | ป้องกันการดาวน์โหลดซ้ำ ลดเวลา Build ลงกว่า 80% | สูงมาก |
| **Encrypted Secrets** | `${{ secrets.KEY }}` | ป้องกันรหัสผ่านรั่วไหลสู่ Public Git Repository | วิกฤต (Critical) |

> 💡 **Takeaway** — **Automation Takeaway**: ระบบ CI ที่ดีต้องรันได้รวดเร็ว (ภายใน 3–5 นาที) และให้ผลลัพธ์ที่เชื่อถือได้แบบ Deterministic

## ตารางสังเคราะห์องค์ความรู้ (ตอนที่ 2): เปรียบเทียบเครื่องมือ Static Analysis

| เครื่องมือ | ประเภทการตรวจสอบ | จุดเด่น / หน้าที่เฉพาะ | โหมดการใช้งาน |
|---|---|---|---|
| **Flake8** | Linter (Style & Smells) | ตรวจสอบ PEP 8, Unused imports, Complexity | ตรวจจับ (Check only) |
| **Black** | Code Formatter | จัดฟอร์แมตโค้ดอัตโนมัติแบบตายตัว (Deterministic) | จัดหน้า (Auto-format) |
| **Bandit** | Security Scanner | สแกนหาช่องโหว่ความปลอดภัย, Hardcoded passwords | ตรวจจับความปลอดภัย |
| **Coverage.py** | Test Coverage | วัดเปอร์เซ็นต์โค้ดที่รันผ่านชุดทดสอบ (`--fail-under`) | กำหนดเกณฑ์ขั้นต่ำ |

> 💡 **Takeaway** — **Tool Synergy**: ใช้งาน Black เพื่อจัดหน้า → Flake8 เพื่อตรวจตรรกะ → Bandit เพื่อตรวจความปลอดภัย → และ Coverage เพื่อยืนยันคุณภาพ
