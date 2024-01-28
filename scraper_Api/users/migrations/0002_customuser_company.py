# Generated by Django 4.2.9 on 2024-01-28 09:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("validator", "0012_remove_company_user"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="company",
            field=models.ManyToManyField(
                blank=True, related_name="Companies", to="validator.company"
            ),
        ),
    ]
