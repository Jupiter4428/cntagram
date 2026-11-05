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

