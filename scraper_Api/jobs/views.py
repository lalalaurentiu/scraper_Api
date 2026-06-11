
from django.shortcuts import get_object_or_404
from uuid import uuid4
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import datetime
import os

from .constants import JOB_SORT_OPTIONS

from .models import Job, JOB_ORIGIN_MANUAL
from company.models import Company, DataSet, Source
from utils.pagination import CustomPagination
from .serializer import (
    GetJobSerializer,
    JobAddSerializer,
    JobAEditSerializer,
)

from company.serializers import CompanySerializer
from django.utils.timezone import datetime

JOB_NOT_FOUND = {"message": "Job not found"}


class JobView(object):
    def build_manual_job_link(self, company_instance, job_id=None):
        if job_id:
            frontend_url = (os.getenv("FRONTEND_URL") or "").rstrip("/")
            job_path = f"/job/{job_id}"
            return f"{frontend_url}{job_path}" if frontend_url else job_path

        return f"manual-temp://company/{company_instance.id}/job/{uuid4()}"

    def parse_expires_at(self, value):
        if not value:
            return None

        expires_at = parse_datetime(value)
        if expires_at is None:
            return False

        if timezone.is_naive(expires_at):
            expires_at = timezone.make_aware(expires_at, timezone.get_current_timezone())

        return expires_at

    def resolve_user_company_instance(self, job, request):
        company_id = job.get("companyId")
        if company_id:
            return request.user.company.filter(id=company_id).first()

        company_name = self.transform_data(job.get("company")).title()
        return request.user.company.filter(company=company_name).first()

    def resolve_company_instance(self, job, request):
        company_name = self.transform_data(job.get("company")).title()
        company_obj = {"company": company_name}

        if job.get("source"):
            company_obj["source"] = job.get("source")

        company_serializer = CompanySerializer(data=company_obj)
        company_serializer.is_valid(raise_exception=True)
        company_instance = company_serializer.save()

        request.user.company.add(company_instance)
        return company_instance

    def update_company_datasets(self, company_job_counts):
        current_date = datetime.now().date()

        for company_id, payload in company_job_counts.items():
            company_instance = payload["company"]
            new_jobs_count = payload["count"]
            existing_data_set = DataSet.objects.filter(
                company=company_instance, date=current_date
            ).first()

            if existing_data_set:
                new_data = existing_data_set.data + new_jobs_count
            else:
                new_data = new_jobs_count

            DataSet.objects.update_or_create(
                company=company_instance,
                date=current_date,
                defaults={"data": new_data},
            )

    def touch_company_dataset(self, company_instance):
        current_date = datetime.now().date()
        DataSet.objects.get_or_create(
            company=company_instance,
            date=current_date,
            defaults={"data": 0},
        )

    def update(self, jobs, attribute):
        if isinstance(jobs, list) and len(jobs) > 0 and hasattr(Job, attribute):
            for job in jobs:
                job_link = self.transform_data(job.get("job_link"))
                job_obj = Job.objects.get(job_link=job_link)

                if not job_obj:
                    return Response(JOB_NOT_FOUND)

                setattr(job_obj, attribute, not getattr(job_obj, attribute))
                job_obj.date = datetime.now()
                job_obj.save()

            return Response({"message": f"Job {attribute}"})
        else:
            return Response(status=400)

    def transformed_jobs(self, jobs):
        data = []
        if isinstance(jobs, list) and len(jobs) > 0:
            for job in jobs:
                source = job.get("source")
                job_obj = {
                    "id": job.get("id"),
                    "job_link": self.transform_data(job.get("job_link")),
                    "job_title": self.transform_data(job.get("job_title")),
                    "description": self.transform_data(job.get("description")),
                    "country": self.transform_data(job.get("country")),
                    "city": self.transform_data(job.get("city")),
                    "county": self.transform_data(job.get("county")),
                    "salary": self.transform_data(job.get("salary")),
                    "salary_min": job.get("salary_min"),
                    "salary_max": job.get("salary_max"),
                    "salary_currency": self.transform_data(job.get("salary_currency")),
                    "remote": self.transform_data(job.get("remote")),
                    "company": self.transform_data(job.get("company")).title(),
                    "companyId": job.get("companyId"),
                    "expires_at": job.get("expires_at"),
                }

                if source:
                    source_obj = Source.objects.filter(sursa=source).first()
                    if source_obj:
                        job_obj["source"] = source_obj.id
                    else:
                        job_obj["source"] = None
                data.append(job_obj)
        return data

    def transform_data(self, data):
        if isinstance(data, str):
            return data
        elif isinstance(data, list):
            data_string = ",".join(
                [str(item).strip() for item in data if isinstance(item, str)]
            )
            return data_string
        else:
            return ""


class AddScraperJobs(APIView, JobView):
    def post(self, request):
        jobs = self.transformed_jobs(request.data)

        if not jobs:
            return Response(status=400)

        posted_jobs = []
        company_job_counts = {}

        for job in jobs:
            company_instance = self.resolve_company_instance(job, request)
            self.touch_company_dataset(company_instance)
            job["company"] = company_instance.id

            job_link = self.transform_data(job.get("job_link"))

            if not Job.objects.filter(job_link=job_link, company=company_instance).exists():
                job_serializer = JobAddSerializer(
                    data=job, context={"request": request}
                )
                job_serializer.is_valid(raise_exception=True)
                job_serializer.save()
                posted_jobs.append(job_serializer.data)
                if company_instance.id not in company_job_counts:
                    company_job_counts[company_instance.id] = {
                        "company": company_instance,
                        "count": 0,
                    }
                company_job_counts[company_instance.id]["count"] += 1

        self.update_company_datasets(company_job_counts)

        return Response(posted_jobs)

    @property
    def delete(self):
        scraper_data = self.transformed_jobs(self.request.data)
        if isinstance(scraper_data, list) and len(scraper_data) > 0:
            company_obj = self.resolve_company_instance(scraper_data[0], self.request)
            database_jobs = list(
                Job.objects.filter(company=company_obj.id).values_list("job_link", flat=True)
            )
            scraper_job_links = {
                self.transform_data(job.get("job_link")) for job in scraper_data
            }
            to_delete = [
                job_link for job_link in database_jobs if job_link not in scraper_job_links
            ]

            for job_link in to_delete:
                Job.objects.filter(job_link=job_link, company=company_obj).delete()


class AddJobs(APIView, JobView):
    def post(self, request):
        jobs = self.transformed_jobs(request.data)

        if not jobs:
            return Response(status=400)

        posted_jobs = []
        company_job_counts = {}

        for job in jobs:
            company_instance = self.resolve_company_instance(job, request)
            self.touch_company_dataset(company_instance)
            job["company"] = company_instance.id

            job_link = self.transform_data(job.get("job_link"))

            if not Job.objects.filter(job_link=job_link, company=company_instance).exists():
                job_serializer = JobAddSerializer(
                    data=job, context={"request": request}
                )
                job_serializer.is_valid(raise_exception=True)
                job_serializer.save()
                posted_jobs.append(job_serializer.data)
                if company_instance.id not in company_job_counts:
                    company_job_counts[company_instance.id] = {
                        "company": company_instance,
                        "count": 0,
                    }
                company_job_counts[company_instance.id]["count"] += 1

        self.update_company_datasets(company_job_counts)

        return Response(posted_jobs)


class AddManualJobs(APIView, JobView):
    def post(self, request):
        jobs = self.transformed_jobs(request.data)

        if not jobs:
            return Response(status=400)

        posted_jobs = []
        company_job_counts = {}

        for job in jobs:
            company_instance = self.resolve_user_company_instance(job, request)
            if not company_instance:
                return Response(status=401)

            self.touch_company_dataset(company_instance)
            job["company"] = company_instance.id
            job["job_link"] = self.build_manual_job_link(company_instance)
            expires_at = self.parse_expires_at(job.get("expires_at"))

            if job.get("expires_at") and expires_at is False:
                return Response({"expires_at": ["Invalid datetime format"]}, status=400)

            job.pop("expires_at", None)

            job_link = self.transform_data(job.get("job_link"))

            if not Job.objects.filter(job_link=job_link, company=company_instance).exists():
                job_serializer = JobAddSerializer(
                    data=job, context={"request": request}
                )
                job_serializer.is_valid(raise_exception=True)
                job_instance = job_serializer.save(
                    origin=JOB_ORIGIN_MANUAL,
                    created_by=request.user,
                    expires_at=expires_at,
                )
                job_instance.job_link = self.build_manual_job_link(company_instance, job_instance.id)
                job_instance.save(update_fields=["job_link"])
                posted_jobs.append(JobAddSerializer(job_instance).data)
                if company_instance.id not in company_job_counts:
                    company_job_counts[company_instance.id] = {
                        "company": company_instance,
                        "count": 0,
                    }
                company_job_counts[company_instance.id]["count"] += 1

        self.update_company_datasets(company_job_counts)

        return Response(posted_jobs)


class GetJobData(APIView):
    serializer_class = GetJobSerializer
    pagination_class = CustomPagination

    def get(self, request):
        company_id = request.GET.get("id",)
        search = request.GET.get("search") or ""
        order_query = request.GET.get("order") or "all"
        order_by = JOB_SORT_OPTIONS.get(order_query)
        user = request.user
        user_companies = user.company.all()

        if user_companies.filter(id=company_id).exists():
            company = get_object_or_404(Company, id=company_id)
            queryset = Job.objects.filter(
                company=company.id, job_title__icontains=search
            ).order_by(order_by)
            paginator = self.pagination_class()
            result_page = paginator.paginate_queryset(queryset, request)
            serializer = self.serializer_class(result_page, many=True)

            jobs = []
            for job in serializer.data:
                job["company"] = company.company
                job["country"] = [
                ] if not job["country"] else job["country"].split(",")
                job["city"] = [] if not job["city"] else job["city"].split(",")
                job["county"] = [] if not job["county"] else job["county"].split(
                    ",")

                jobs.append(job)

            return paginator.get_paginated_response(jobs)
        else:
            return Response(status=401)

    def post(self, request):
        company = request.data.get("company")
        user = request.user
        user_companies = user.company.all()

        if user_companies.filter(company=company.title()).exists():
            company = get_object_or_404(Company, company=company.title())
            queryset = Job.objects.filter(company=company.id)
            paginator = self.pagination_class()
            result_page = paginator.paginate_queryset(queryset, request)
            serializer = self.serializer_class(result_page, many=True)

            jobs = []
            for job in serializer.data:
                job["company"] = company.company
                job["country"] = job["country"].split(",")
                job["city"] = job["city"].split(",")
                job["county"] = job["county"].split(",")

                jobs.append(job)

            return paginator.get_paginated_response(jobs)
        else:
            return Response(status=401)


class GetJobDetail(APIView):
    serializer_class = GetJobSerializer

    def get(self, request, id):
        job = Job.objects.filter(id=id).select_related("company").first()
        if not job:
            return Response(status=404)

        if not request.user.company.filter(id=job.company_id).exists():
            return Response(status=401)

        serialized_job = self.serializer_class(job).data
        serialized_job["company"] = job.company.company
        serialized_job["country"] = [] if not serialized_job["country"] else serialized_job["country"].split(",")
        serialized_job["city"] = [] if not serialized_job["city"] else serialized_job["city"].split(",")
        serialized_job["county"] = [] if not serialized_job["county"] else serialized_job["county"].split(",")

        return Response(serialized_job)


class EditJob(APIView, JobView):
    def post(self, request):
        jobs = self.transformed_jobs(request.data)
        for job in jobs:
            try:
                company = request.user.company.get(
                    id=self.transform_data(job.get("companyId")).title())
                job["company"] = company.id

                serializer = JobAEditSerializer(
                    data=job, context={"request": request})
                serializer.is_valid(raise_exception=True)
                serializer.save()

            except Exception:
                return Response(status=404)

        return Response({"message": "Job edited"})


class DeleteJob(APIView, JobView):
    def post(self, request):
        jobs = self.transformed_jobs(request.data)
        print(jobs)

        if not jobs:
            return Response(status=400)

        for job in jobs:
            try:
                company = request.user.company.get(
                    id=self.transform_data(job.get("companyId")).title())
                job_link = self.transform_data(job.get("job_link"))
                job_obj = Job.objects.get(
                    job_link=job_link, company=company.id)

                if not job_obj:
                    return Response(JOB_NOT_FOUND)

                job_obj.delete()
            except Exception:
                return Response(status=404)

        return Response({"message": "Job deleted"})


class PublishJob(APIView, JobView):
    def post(self, request):
        response = self.update(request.data, "published")
        return response
