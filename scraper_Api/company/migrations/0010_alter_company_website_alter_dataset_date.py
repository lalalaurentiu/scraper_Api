# Generated by Django 4.2.9 on 2024-07-27 21:39

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("company", "0009_alter_dataset_date"),
    ]

    operations = [
        migrations.AlterField(
            model_name="company",
            name="website",
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AlterField(
            model_name="dataset",
            name="date",
            field=models.DateField(
                default=datetime.datetime(2024, 7, 27, 21, 39, 28, 859334)
            ),
        ),
    ]
