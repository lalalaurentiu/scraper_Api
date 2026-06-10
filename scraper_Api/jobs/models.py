from django.conf import settings
from rest_framework.response import Response
from company.models import Company
from django.db import models
import hashlib


JOB_ORIGIN_SCRAPER = "scraper"
JOB_ORIGIN_MANUAL = "manual"
JOB_ORIGIN_CHOICES = [
    (JOB_ORIGIN_SCRAPER, "scraper"),
    (JOB_ORIGIN_MANUAL, "manual"),
]

class Job(models.Model):
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="jobs"
    )
    country = models.TextField()
    city = models.TextField(blank=True)
    county = models.TextField(blank=True)
    job_link = models.CharField(max_length=1000)
    job_title = models.TextField()
    description = models.TextField(blank=True, default="")
    salary_min = models.IntegerField(blank=True, null=True)
    salary_max = models.IntegerField(blank=True, null=True)
    salary_currency = models.CharField(max_length=10, blank=True, null=True)
    remote = models.CharField(max_length=50, blank=True)
    edited = models.BooleanField(default=False)
    published = models.BooleanField(default=False)
    origin = models.CharField(max_length=20, choices=JOB_ORIGIN_CHOICES, default=JOB_ORIGIN_SCRAPER)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_jobs",
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.job_title

    @property
    def getJobId(self):
        hash_object = hashlib.md5(self.job_link.encode())
        return hash_object.hexdigest()

    def publish(self):
        self.published = True
        self.save(update_fields=['published'])
        return Response(status=200)

    def unpublish(self):
        self.published = False
        self.save(update_fields=['published'])
        return Response(status=200)
