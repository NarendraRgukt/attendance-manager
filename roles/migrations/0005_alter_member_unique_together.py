# Generated by Django 4.2.4 on 2023-08-18 12:52

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('roles', '0004_alter_member_organization'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='member',
            unique_together={('organization', 'user')},
        ),
    ]
