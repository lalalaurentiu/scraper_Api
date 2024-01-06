# Generated by Django 4.2.1 on 2023-12-31 16:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("validator", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="City",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("job_city", models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name="County",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("job_county", models.CharField(blank=True, max_length=50)),
            ],
        ),
        migrations.RemoveField(
            model_name="job",
            name="job_location",
        ),
        migrations.AlterField(
            model_name="job",
            name="job_remote",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.DeleteModel(
            name="Location",
        ),
        migrations.AddField(
            model_name="job",
            name="job_city",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="Location",
                to="validator.city",
            ),
        ),
        migrations.AddField(
            model_name="job",
            name="job_county",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="County",
                to="validator.county",
            ),
        ),
    ]