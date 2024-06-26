# Generated by Django 4.2.9 on 2024-03-08 10:05

from django.db import migrations
import json
import os


def load_initial_data(apps, schema_editor):
    County = apps.get_model("orase", "County")
    City = apps.get_model("orase", "City")

    with open(
        os.path.join(os.path.dirname(__file__), "counties.json"), "r"
    ) as f:
        counties = json.load(f)
        for county in counties:
            county_instance = County.objects.create(
                name=county["county"],
                abreviate=county["abreviation"],
                municipality=county["city"],
            )

            county_instance.save()

            for city in county["cities"]:
                city_instance = City.objects.create(
                    name=city,
                    county=county_instance,
                )

                city_instance.save()


class Migration(migrations.Migration):

    dependencies = [
        ("orase", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(load_initial_data),
    ]
