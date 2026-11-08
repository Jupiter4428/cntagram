# Backup Operations & Disaster Recovery Guide

คู่มือปฏิบัติการสำหรับการสำรองข้อมูล (Backup) และการกู้คืนข้อมูล (Disaster Recovery) ของระบบ CNtagram ตามข้อกำหนด Issue #192 และ ADR 0005 §6

---

## 0. สถานะ Production ที่ตรวจสอบล่าสุด (2026-11-08)

ตรวจจาก Render workspace ปัจจุบันแบบ read-only:

- Web Service `cntagram`: Region Singapore, Plan Free, branch `main`, auto deploy enabled
- PostgreSQL `cntagram-db`: Region Singapore, Plan Free, PostgreSQL 18, status available
- Free PostgreSQL instance มีวันหมดอายุ **2026-12-07**
- Web Service ปัจจุบันไม่มี persistent disk ใน service configuration
- Latest live deploy ที่ตรวจพบ: commit `a3ef619`

ผลกระทบต่อแผน backup:
- Database ต้องพึ่ง offsite logical backup เพราะ Free PostgreSQL ไม่มี production-grade retention แบบ paid plan
- Media Vault บน Free Web Service ไม่ควรถูกถือว่าคงทนข้าม redeploy/restart และ GitHub Actions ไม่สามารถเข้าถึงไฟล์ production ใน runtime ได้
- ก่อนปิด Issue #192 ต้องมีหลักฐาน restore ลง disposable PostgreSQL และหลักฐาน offsite backup ที่รันจริง

## 1. สถาปัตยกรรมและกำหนดการสำรองข้อมูล (Backup Strategy & Schedule)

ระบบ CNtagram กำหนดให้มีการสำรองข้อมูลวันละ 1 ครั้งโดยอัตโนมัติ แต่ต้องแยกตามที่เก็บข้อมูลจริง:\n\n- **PostgreSQL Database Dump**: สำรองจาก GitHub Actions ไป S3 ได้โดยตรง\n- **Protected Media Vault บน Render persistent disk**: GitHub-hosted runner และ Render Cron Job ไม่สามารถเข้าถึง disk ของ Web Service ได้ จึงห้ามนับ `tar media/` บน runner ว่าเป็น production media backup\n- Media Vault จะถือว่าผ่าน AC เมื่อสำรองจาก service ที่ถือ disk จริง หรือย้าย primary media storage ไป private object storage แล้วตั้ง replication/versioning/offsite copy

| รายการ | รายละเอียด |
|---|---|
| **ความถี่และเวลา** | ทุกวัน เวลา **02:17 น. (Asia/Bangkok)** หรือ `19:17 UTC` (ตั้งเป็น cron `17 19 * * *`) |
| **Scheduler** | **GitHub Actions** (`.github/workflows/daily-backup.yml`) หรือ **Render Cron Job** |
| **ฐานข้อมูล** | PostgreSQL Logical Backup ผ่าน `pg_dump -Fc` (Custom Compressed Format) |
| **คลังเอกสาร PDF** | ต้องสำรองจาก runtime ที่เข้าถึง production media จริง หรือย้ายไป private object storage; GitHub Actions checkout ไม่ถือเป็น production media source |
| **สถานที่จัดเก็บ Offsite** | **AWS S3** (Region: `ap-southeast-1` Singapore) เข้ารหัสด้วย `AES256` |
| **ระยะเวลาเก็บรักษา** | 30 วัน (กำหนดผ่าน S3 Lifecycle Expiration Rule) |

---

## 2. การตั้งค่า GitHub Actions Secrets สำหรับ Offsite Backup

สำหรับการรัน `.github/workflows/daily-backup.yml` ให้ตั้งค่า Secrets ใน GitHub Repository (`Settings -> Secrets and variables -> Actions`):

| Secret Name | คำอธิบาย | ตัวอย่าง |
|---|---|---|
| `BACKUP_DATABASE_URL` | External PostgreSQL Connection URL (แนะนำใช้ Dedicated Read-Only User) | `postgres://user:pass@dpg-...-a.singapore-postgres.render.com/cntagram` |
| `BACKUP_AWS_ACCESS_KEY_ID` | AWS IAM Access Key ID ของ Service Account สำรองข้อมูล | `AKIAIOSFODNN7EXAMPLE` |
| `BACKUP_AWS_SECRET_ACCESS_KEY` | AWS IAM Secret Access Key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `BACKUP_AWS_REGION` | AWS Region ของ S3 Bucket | `ap-southeast-1` |
| `BACKUP_S3_BUCKET` | ชื่อ S3 Bucket สำหรับเก็บไฟล์สำรอง | `cntagram-production-backups` |

---

## 3. การกำหนดสิทธิ์แบบ Least Privilege และ S3 Lifecycle Policy

### 3.1 IAM Policy สำหรับ Backup Worker (Least Privilege)
สร้าง IAM Policy ที่จำกัดสิทธิ์เฉพาะที่ workflow ปัจจุบันใช้จริง คือ Upload (`s3:PutObject`) และตรวจ object เฉพาะ key ที่สร้างในรอบนั้น (`s3:GetObject`) ภายใต้ prefix `cntagram/`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowBackupUploadAndVerify",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::cntagram-production-backups/cntagram/*"
    },
    {
      "Sid": "AllowBucketListing",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::cntagram-production-backups",
      "Condition": {
        "StringLike": {
          "s3:prefix": [
            "cntagram/*"
          ]
        }
      }
    }
  ]
}
```

### 3.2 S3 30-Day Lifecycle Retention Rule
ตั้งค่า Lifecycle Configuration บน S3 Bucket เพื่อลบไฟล์สำรองที่มีอายุเกิน 30 วันโดยอัตโนมัติ:

```json
{
  "Rules": [
    {
      "ID": "ExpireBackupsAfter30Days",
      "Filter": {
        "Prefix": "cntagram/"
      },
      "Status": "Enabled",
      "Expiration": {
        "Days": 30
      }
    }
  ]
}
```
*สามารถใช้คำสั่ง:*
```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket cntagram-production-backups \
  --lifecycle-configuration file://s3-lifecycle.json
```

---

## 3.3 ข้อจำกัดของ Render Persistent Disk และ Media Backup\n\nRender persistent disk เข้าถึงได้เฉพาะ service instance ที่ผูก disk อยู่เท่านั้น ดังนั้น workflow บน GitHub Actions จะสำรองได้เฉพาะฐานข้อมูลที่เชื่อมผ่าน network และไฟล์ที่มีอยู่บน runner เท่านั้น\n\n**ผลต่อ Issue #192:** การสำรอง Media Vault จะยังไม่ถือว่าผ่านจนกว่าจะมีหนึ่งในสองแนวทางต่อไปนี้:\n1. ย้าย media ไป private object storage แล้วตั้ง offsite copy/versioning/lifecycle ที่ตรวจสอบได้ หรือ\n2. เพิ่มกลไก backup ที่รันจาก Web Service/runtime ที่ถือ persistent disk และ upload archive ออกไป S3 โดยไม่เปิดไฟล์ media เป็น public URL\n\nห้ามแนบหลักฐานจาก `media/` ใน GitHub checkout แล้วอ้างว่าเป็น production media backup\n\n## 4. การทดสอบและซักซ้อมการกู้คืน (Disaster Recovery Rehearsal)

คำสั่ง `bash scripts/backup_restore.sh test` ใช้สำหรับทดสอบความสมบูรณ์ของกระบวนการ Backup และ Restore จริง:

### 4.1 ขั้นตอนการทดสอบบน PostgreSQL
1. จัดเตรียมฐานข้อมูลทดสอบชั่วคราว (Disposable DB) เช่น บน Render หรือ Local/Cloud โดยชื่อฐานข้อมูลต้องมีคำว่า `_restore_test` หรือ `test`
2. กำหนดค่าตัวแปร:
   ```bash
   export DATABASE_URL="postgres://<prod_or_source_user>:<pass>@<host>/cntagram"
   export RESTORE_TEST_DATABASE_URL="postgres://<user>:<pass>@<host>/cntagram_restore_test"
   ```
3. สั่งรันการทดสอบ:
   ```bash
   bash scripts/backup_restore.sh test
   ```
4. **สิ่งที่จะเกิดขึ้นและเงื่อนไขการผ่าน:**
   - สคริปต์จะ dump ข้อมูลจาก `DATABASE_URL`
   - ตรวจสอบความถูกต้องของไฟล์ dump ด้วย `pg_restore --list` (หากเครื่องไม่มี `pg_restore` สคริปต์จะสั่งล้มทันที)
   - Restore ข้อมูลลงใน `RESTORE_TEST_DATABASE_URL` (ห้ามชี้ซ้ำกับต้นทาง และชื่อต้องมีคำว่า `_restore_test` หรือ `test`)
   - รันการเปรียบเทียบจำนวนแถว (`SELECT count(*)`) ของทุกตารางใน Schema `public` ระหว่างต้นทางกับฐานข้อมูลทดสอบ
   - หากจำนวนแถวของทุกตารางตรงกัน 100% สคริปต์จะแสดงผล:
     ```text
     ✓ PostgreSQL table row verification passed (N tables matched 100%)
     ==> Backup and Restore verification passed 100%! Ready for production.
     ```

---

## 5. การกู้คืนข้อมูลยามฉุกเฉินและการป้องกัน Production Overwrite

เพื่อป้องกันอุบัติเหตุจากการ Restore ทับฐานข้อมูล Production โดยไม่ตั้งใจ สคริปต์ `scripts/backup_restore.sh restore` มีระบบป้องกันหลายชั้น:

### 5.1 เงื่อนไขความปลอดภัย
- สำหรับ **SQLite:** ต้องระบุ `ALLOW_DESTRUCTIVE_RESTORE=YES`
- สำหรับ **PostgreSQL บน Production:** หาก URL ชี้ไปยังโดเมน production (เช่น `render.com`, `onrender.com`) หรือชื่อฐานข้อมูลไม่ใช่ `test`/`localhost` สคริปต์จะบังคับให้ระบุ:
  1. `ALLOW_DESTRUCTIVE_RESTORE=YES`
  2. `CONFIRM_PRODUCTION_RESTORE="<target_db_name>"` (ต้องสะกดชื่อฐานข้อมูลให้ตรงกับใน URL ทุกตัวอักษร)

### 5.2 ตัวอย่างคำสั่งกู้คืน Production
```bash
ALLOW_DESTRUCTIVE_RESTORE=YES \
CONFIRM_PRODUCTION_RESTORE="cntagram" \
bash scripts/backup_restore.sh restore "backups/db_20261108_021700.dump" "postgres://user:pass@host/cntagram"
```
*หากไม่ระบุ `CONFIRM_PRODUCTION_RESTORE` หรือระบุไม่ตรง สคริปต์จะปฏิเสธการทำงานและคืนค่า exit code 1 ทันที*

---

## 6. การตรวจสอบผลและการแจ้งเตือนเมื่อเกิดข้อผิดพลาด (Monitoring & Alerting)

1. **GitHub Actions Log & Status:**
   - สรุปผลการรันปรากฏในแท็บ Actions ของ Repository
   - มีขั้นตอนยืนยันการมีอยู่ของไฟล์ใน S3 Bucket (`aws s3 ls ... | grep -q ...`)
2. **การแจ้งเตือนความล้มเหลว (Failure Notifications):**
   - ใน `.github/workflows/daily-backup.yml` มี Step `Notify on backup failure` ที่กำหนดเงื่อนไข `if: failure()`
   - GitHub จะส่งอีเมลแจ้งเตือนอัตโนมัติไปยัง Repository Administrators เมื่อ Workflow แบบ Scheduled รันล้มเหลว
