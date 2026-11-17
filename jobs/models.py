from pathlib import Path
import uuid
from django.conf import settings
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.utils import timezone

MAX_RESUME_SIZE = 5 * 1024 * 1024

def validate_resume_size(file):
    if file.size > MAX_RESUME_SIZE:
        from django.core.exceptions import ValidationError
        raise ValidationError("Resume must not exceed 5 MB.")

class Employer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="employer_profile")
    company_name = models.CharField(max_length=180)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.company_name

class Candidate(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="candidate_profile")
    phone = models.CharField(max_length=30, blank=True)
    location = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.user.get_full_name() or self.user.username

class JobListing(models.Model):
    class EmploymentType(models.TextChoices):
        FULL_TIME = "full_time", "Full time"
        PART_TIME = "part_time", "Part time"
        CONTRACT = "contract", "Contract"
        INTERNSHIP = "internship", "Internship"
        TEMPORARY = "temporary", "Temporary"
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name="jobs")
    title = models.CharField(max_length=180)
    description = models.TextField()
    location = models.CharField(max_length=160)
    employment_type = models.CharField(max_length=20, choices=EmploymentType.choices)
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closes_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["is_published", "employment_type", "created_at"])]
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.salary_min is not None and self.salary_max is not None and self.salary_min > self.salary_max:
            raise ValidationError({"salary_max": "Maximum salary must be greater than or equal to minimum salary."})
        if self.closes_at and self.closes_at <= timezone.now():
            raise ValidationError({"closes_at": "Closing date must be in the future."})
    @property
    def is_open(self):
        return self.is_published and (self.closes_at is None or self.closes_at > timezone.now())
    def __str__(self): return self.title

def resume_upload_path(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f"resumes/candidate_{instance.candidate_id}/{timezone.now():%Y/%m}/{uuid.uuid4().hex}{suffix}"

class Resume(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="resumes")
    file = models.FileField(upload_to=resume_upload_path, validators=[FileExtensionValidator(["pdf", "doc", "docx"]), validate_resume_size])
    label = models.CharField(max_length=120, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.label or Path(self.file.name).name

class JobApplication(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        REVIEWING = "reviewing", "Reviewing"
        SHORTLISTED = "shortlisted", "Shortlisted"
        REJECTED = "rejected", "Rejected"
        HIRED = "hired", "Hired"
        WITHDRAWN = "withdrawn", "Withdrawn"
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name="applications")
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="applications")
    resume = models.ForeignKey(Resume, on_delete=models.SET_NULL, null=True, blank=True, related_name="applications")
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["job", "candidate"], name="unique_candidate_job_application")]
        ordering = ["-applied_at"]
    def __str__(self): return f"{self.candidate} → {self.job}"

class EmployerNotification(models.Model):
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name="notifications")
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-created_at"]
