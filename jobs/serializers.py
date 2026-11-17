from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from .models import Employer, Candidate, JobListing, Resume, JobApplication, EmployerNotification

class EmployerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer
        fields = ["id", "company_name", "website", "description"]

class JobListingSerializer(serializers.ModelSerializer):
    employer = EmployerSerializer(read_only=True)
    class Meta:
        model = JobListing
        fields = ["id", "employer", "title", "description", "location", "employment_type",
                  "salary_min", "salary_max", "is_published", "created_at", "closes_at"]
        read_only_fields = ["id", "employer", "created_at"]

    def validate(self, attrs):
        low = attrs.get("salary_min", getattr(self.instance, "salary_min", None))
        high = attrs.get("salary_max", getattr(self.instance, "salary_max", None))
        if low is not None and high is not None and low > high:
            raise serializers.ValidationError({"salary_max": "Maximum salary must be >= minimum salary."})
        return attrs

class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ["id", "file", "label", "uploaded_at"]
        read_only_fields = ["id", "uploaded_at"]

    def validate_file(self, value):
        name = value.name.lower()
        if not name.endswith((".pdf", ".doc", ".docx")):
            raise serializers.ValidationError("Only PDF, DOC, and DOCX files are accepted.")
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Resume must not exceed 5 MB.")
        content_type = getattr(value, "content_type", "")
        if content_type and content_type not in {
            "application/pdf", "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/octet-stream",
        }:
            raise serializers.ValidationError("Unsupported resume content type.")
        return value

class JobApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    candidate_name = serializers.CharField(source="candidate.user.get_full_name", read_only=True)
    class Meta:
        model = JobApplication
        fields = ["id", "job", "job_title", "candidate_name", "resume", "cover_letter",
                  "status", "applied_at", "updated_at"]
        read_only_fields = ["id", "candidate_name", "status", "applied_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]
        try:
            candidate = request.user.candidate_profile
        except Candidate.DoesNotExist:
            raise serializers.ValidationError("A candidate profile is required.")
        job = attrs["job"]
        if not job.is_open:
            raise serializers.ValidationError({"job": "This job is not currently accepting applications."})
        resume = attrs.get("resume")
        if resume and resume.candidate_id != candidate.id:
            raise serializers.ValidationError({"resume": "You can only attach your own resume."})
        if JobApplication.objects.filter(job=job, candidate=candidate).exists():
            raise serializers.ValidationError({"job": "You have already applied for this job."})
        return attrs

    def create(self, validated_data):
        candidate = self.context["request"].user.candidate_profile
        application = JobApplication.objects.create(candidate=candidate, **validated_data)
        EmployerNotification.objects.create(
            employer=application.job.employer,
            application=application,
            message=f"New application received for {application.job.title}.",
        )
        return application

class ApplicationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = ["status"]

class EmployerNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployerNotification
        fields = ["id", "application", "message", "is_read", "created_at"]
        read_only_fields = fields
