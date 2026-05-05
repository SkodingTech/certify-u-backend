# Mirrors the migration already applied on the live DB
# (created on 2026-02-22 by an earlier deployment). Kept verbatim so the
# new repo's migration history stays in sync with the live database.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0011_regulatoryauthority_regulatorycompliance_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Certificate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=False)),
                ('certificate_id', models.CharField(max_length=100, unique=True)),
                ('issued_at', models.DateTimeField(auto_now_add=True)),
                ('download_url', models.URLField(blank=True)),
                ('expiry_date', models.DateField(blank=True, null=True)),
                ('is_revoked', models.BooleanField(default=False)),
                ('revocation_reason', models.TextField(blank=True, null=True)),
                ('enrollment', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='certificate', to='courses.enrollment')),
                ('issued_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='courses.regulatoryauthority')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
