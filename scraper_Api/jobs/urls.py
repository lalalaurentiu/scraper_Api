from django.urls import path
from . import views

urlpatterns = [
    path('get/', views.GetJobData.as_view()),
    path('get/<int:id>/', views.GetJobDetail.as_view()),
    path('add/', views.AddScraperJobs.as_view()),
    path('user-add/', views.AddJobs.as_view()),
    path('manual-add/', views.AddManualJobs.as_view()),
    path('edit/', views.EditJob.as_view()),
    path('delete/', views.DeleteJob.as_view()),
    path('publish/', views.PublishJob.as_view()),
]
