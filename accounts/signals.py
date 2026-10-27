from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, UserCounter


@receiver(post_save, sender=User)
def count_created_user(sender, instance, created, **kwargs):
    """นับผู้ใช้ที่สร้างใหม่ทุกทาง (create_user, ฟอร์ม Django admin) ใช้ F() กันนับหายตอนสร้างพร้อมกัน"""
    if created:
        UserCounter.objects.filter(pk=1).update(total=F("total") + 1)
