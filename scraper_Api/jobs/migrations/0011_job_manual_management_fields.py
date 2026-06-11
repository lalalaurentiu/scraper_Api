from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("jobs", "0010_job_salary_currency"),
    ]

    operations = [
        migrations.AddField(
            model_name="job",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, blank=True, null=True),
        ),
        migrations.AddField(
            model_name="job",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_jobs",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="job",
            name="expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="job",
            name="origin",
            field=models.CharField(
                choices=[("scraper", "scraper"), ("manual", "manual")],
                default="scraper",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="job",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, blank=True, null=True),
        ),
    ]
