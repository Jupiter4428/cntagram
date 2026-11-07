from django.core.management import call_command
from django.db import migrations


def create_cache_table(apps, schema_editor):
    call_command("createcachetable")


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_user_counter"),
    ]
    operations = [
        migrations.RunPython(create_cache_table, migrations.RunPython.noop),
    ]
