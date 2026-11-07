#!/usr/bin/env bash
# build.sh — รันอัตโนมัติทุกครั้งก่อน start web process
set -o errexit

# 1) ติดตั้ง dependency จาก requirements.txt
pip install -r requirements.txt

# 2) ตรวจความพร้อม Production (ล้ม build ถ้ายังไม่ผ่าน)
python manage.py check --deploy --fail-level WARNING

# 3) รวม static files สำหรับ WhiteNoise
python manage.py collectstatic --noinput

# 4) ย้าย schema ฐานข้อมูลและเติมข้อมูลตั้งต้น (รันซ้ำได้โดยไม่สร้างซ้ำ)
python manage.py migrate
python manage.py seed_catalog
python manage.py seed_materials

# 5) สร้าง admin จาก ENV และผูกสิทธิ์ super_admin (ข้ามได้ถ้าไม่มีรหัสหรืออีเมล; ไม่ fail ถ้ามีบัญชีแล้ว)
if [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
  export DJANGO_SUPERUSER_NICKNAME="${DJANGO_SUPERUSER_NICKNAME:-CNtagramStaff}"
  export DJANGO_SUPERUSER_DEPARTMENT="${DJANGO_SUPERUSER_DEPARTMENT:-CN}"
  # Existing admin is normal on repeat deploys; other errors must fail the build.
  if python manage.py shell -c 'import os, sys; from django.contrib.auth import get_user_model; sys.exit(0 if get_user_model().objects.filter(email=os.environ["DJANGO_SUPERUSER_EMAIL"]).exists() else 1)'; then
    echo "Superuser email already exists; skipping creation."
  else
    python manage.py createsuperuser --noinput
  fi
fi
python manage.py seed_roles

