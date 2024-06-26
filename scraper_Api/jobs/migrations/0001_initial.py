# Generated by Django 4.2.9 on 2024-02-03 20:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Company",
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
                ("company", models.CharField(max_length=50)),
                ("scname", models.CharField(blank=True, max_length=50)),
                ("website", models.CharField(blank=True, max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name="Job",
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
                ("country", models.TextField()),
                ("city", models.TextField(blank=True)),
                ("county", models.TextField(blank=True)),
                ("job_link", models.CharField(max_length=200)),
                ("job_title", models.TextField()),
                ("remote", models.CharField(blank=True, max_length=50)),
                ("edited", models.BooleanField(default=False)),
                ("published", models.BooleanField(default=False)),
                ("deleted", models.BooleanField(default=False)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="Company",
                        to="jobs.company",
                    ),
                ),
            ],
        ),
    ]
