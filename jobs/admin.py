from django.contrib import admin
from .models import Employer, Candidate, JobListing, Resume, JobApplication, EmployerNotification

@admin.register(Employer)
class EmployerAdmin(admin.ModelAdmin):
    list_display = ("company_name", "user", "created_at")
    search_fields = ("company_name", "user__username")

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "location")

@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = ("title", "employer", "employment_type", "is_published", "created_at")
    list_filter = ("employment_type", "is_published")
    search_fields = ("title", "description", "employer__company_name")

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("candidate", "label", "uploaded_at")

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ("job", "candidate", "status", "applied_at")
    list_filter = ("status",)

@admin.register(EmployerNotification)
class EmployerNotificationAdmin(admin.ModelAdmin):
    list_display = ("employer", "application", "is_read", "created_at")
    list_filter = ("is_read",)
