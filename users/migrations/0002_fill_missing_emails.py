from django.db import migrations

def fill_missing_emails(apps, schema_editor):
    User = apps.get_model("users", "User")
    for user in User.objects.all():
        if not user.email:
            user.email = f"{user.username}@placeholder.local"
            user.save()

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),  # или твоя предыдущая миграция
    ]

    operations = [
        migrations.RunPython(fill_missing_emails),
    ]
