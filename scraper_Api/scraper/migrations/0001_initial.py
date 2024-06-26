# Generated by Django 4.2.9 on 2024-01-30 16:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Scraper",
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
                ("name", models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name="TestLogs",
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
                ("test_date", models.DateTimeField(auto_now_add=True)),
                ("test_result", models.TextField(blank=True, null=True)),
                ("is_success", models.CharField(max_length=10)),
                (
                    "scraper",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="Scraper",
                        to="scraper.scraper",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="DataSet",
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
                ("date", models.DateField()),
                ("data", models.IntegerField()),
                (
                    "scraper",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ScraperData",
                        to="scraper.scraper",
                    ),
                ),
            ],
        ),
    ]
