from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0011_job_manual_management_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="job",
            name="description",
            field=models.TextField(blank=True, default=""),
        ),
    ]
