from django.urls import path
from .views import (JobListCreateView, JobDetailView, ResumeListCreateView, ResumeDetailView,
                   ApplicationListCreateView, ApplicationDetailView, ApplicationStatusUpdateView,
                   NotificationListView)

urlpatterns = [
    path("jobs/", JobListCreateView.as_view(), name="job-list-create"),
    path("jobs/<int:pk>/", JobDetailView.as_view(), name="job-detail"),
    path("resumes/", ResumeListCreateView.as_view(), name="resume-list-create"),
    path("resumes/<int:pk>/", ResumeDetailView.as_view(), name="resume-detail"),
    path("applications/", ApplicationListCreateView.as_view(), name="application-list-create"),
    path("applications/<int:pk>/", ApplicationDetailView.as_view(), name="application-detail"),
    path("applications/<int:pk>/status/", ApplicationStatusUpdateView.as_view(), name="application-status"),
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
]
