import hashlib
from django.db import models
from company.models import Company
from django.utils.timezone import datetime
from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


class Job(models.Model):
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="Company"
    )
    country = models.TextField()
    city = models.TextField(blank=True)
    county = models.TextField(blank=True)
    job_link = models.CharField(max_length=300)
    job_title = models.TextField()
    remote = models.CharField(max_length=50, blank=True)
    edited = models.BooleanField(default=False)
    published = models.BooleanField(default=False)
    date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.job_title

    @property
    def getJobId(self):
        hash_object = hashlib.md5(self.job_link.encode())
        return hash_object.hexdigest()

    def save(self, *args, **kwargs):
        if self.published:
            if not self.date:
                self.date = datetime.now()
            self.publish()
        super(Job, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        requests.post(
            f"{DATABASE_URL}delete/", headers={"Content-Type": "application/json"},
            json={"urls": [self.job_link]}
        )
        super(Job, self).delete(*args, **kwargs)

    def publish(self):
        url = f"{DATABASE_URL}update/"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        }
        city = city = set(x.strip().split(" ")[0]
                          for x in self.city.split(","))

        response = requests.post(url=url, headers=headers,
                                 json=[
                                     {
                                         "job_link": self.job_link,
                                         "job_title": self.job_title,
                                         "company": self.company.company,
                                         "country": self.country.split(","),
                                         "city": list(city),
                                         "county": self.county.split(","),
                                         "remote": self.remote.split(","),
                                     }
                                 ])
        return response
