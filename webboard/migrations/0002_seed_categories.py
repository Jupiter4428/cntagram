"""Data migration to seed default webboard categories."""

from django.db import migrations

DEFAULT_CATEGORIES = [
    (
        "general",
        "ทั่วไป",
        "พูดคุยแลกเปลี่ยนเรื่องทั่วไปในแคมปัส",
        1,
    ),
    (
        "qna",
        "ถาม-ตอบ การเรียน",
        "ปรึกษาปัญหาการเรียน การสอบ และลงทะเบียน",
        2,
    ),
    (
        "reviews",
        "รีวิววิชา & ชีทสรุป",
        "รีวิววิชาเรียน อาจารย์ และแบ่งปันชีทสรุป",
        3,
    ),
    (
        "lifestyle",
        "ไลฟ์สไตล์ & สัพเพเหระ",
        "ร้านอาหาร หอพัก กิจกรรม และมีมสนุกๆ",
        4,
    ),
]


def seed_categories(apps, schema_editor):
    """Seed initial board categories for community webboard."""
    BoardCategory = apps.get_model("webboard", "BoardCategory")
    for slug, name, description, order in DEFAULT_CATEGORIES:
        BoardCategory.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "description": description,
                "order": order,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("webboard", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_categories, migrations.RunPython.noop),
    ]
