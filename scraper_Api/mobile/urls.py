from django.urls import path
from .views import GetJobView, GetJobDetailView, GetTotalJobs, GetCompanies, CheckSavedJobsView

urlpatterns = [
    path('', GetJobView.as_view(), name='jobs'),
    path('<int:id>/', GetJobDetailView.as_view(), name='job_detail'),
    path('companies/', GetCompanies.as_view(), name='companies'),
    path('total/', GetTotalJobs.as_view(), name='total_jobs'),
    path('check-saved/', CheckSavedJobsView.as_view(), name='check_saved_jobs'),
]
