from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import JobListing, Resume, JobApplication, EmployerNotification
from .serializers import (JobListingSerializer, ResumeSerializer, JobApplicationSerializer,
                          ApplicationStatusSerializer, EmployerNotificationSerializer)
from .permissions import IsEmployer, IsCandidate, IsApplicationParticipant

class JobListCreateView(generics.ListCreateAPIView):
    serializer_class = JobListingSerializer
    def get_permissions(self):
        return [permissions.AllowAny()] if self.request.method == "GET" else [IsEmployer()]
    def get_queryset(self):
        qs = JobListing.objects.select_related("employer").filter(is_published=True)
        q = self.request.query_params.get("q")
        location = self.request.query_params.get("location")
        employment_type = self.request.query_params.get("employment_type")
        company = self.request.query_params.get("company")
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(employer__company_name__icontains=q))
        if location:
            qs = qs.filter(location__icontains=location)
        if employment_type:
            qs = qs.filter(employment_type=employment_type)
        if company:
            qs = qs.filter(employer__company_name__icontains=company)
        ordering = self.request.query_params.get("ordering")
        if ordering in {"created_at", "-created_at", "title"}:
            qs = qs.order_by(ordering)
        return qs
    def perform_create(self, serializer):
        serializer.save(employer=self.request.user.employer_profile)

class JobDetailView(generics.RetrieveAPIView):
    queryset = JobListing.objects.select_related("employer").filter(is_published=True)
    serializer_class = JobListingSerializer
    permission_classes = [permissions.AllowAny()]

class ResumeListCreateView(generics.ListCreateAPIView):
    serializer_class = ResumeSerializer
    permission_classes = [IsCandidate]
    def get_queryset(self):
        return Resume.objects.filter(candidate=self.request.user.candidate_profile)
    def perform_create(self, serializer):
        serializer.save(candidate=self.request.user.candidate_profile)

class ResumeDetailView(generics.RetrieveAPIView):
    serializer_class = ResumeSerializer
    permission_classes = [IsCandidate]
    def get_queryset(self):
        return Resume.objects.filter(candidate=self.request.user.candidate_profile)

class ApplicationListCreateView(generics.ListCreateAPIView):
    serializer_class = JobApplicationSerializer
    def get_permissions(self):
        return [IsCandidate()] if self.request.method == "POST" else [IsCandidate()]
    def get_queryset(self):
        return JobApplication.objects.filter(candidate=self.request.user.candidate_profile).select_related("job", "candidate__user")
    def perform_create(self, serializer):
        serializer.save()

class ApplicationDetailView(generics.RetrieveAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated, IsApplicationParticipant]
    queryset = JobApplication.objects.select_related("job", "candidate__user")

class ApplicationStatusUpdateView(APIView):
    permission_classes = [IsEmployer]
    def patch(self, request, pk):
        application = get_object_or_404(JobApplication.objects.select_related("job__employer", "candidate"), pk=pk)
        if application.job.employer.user_id != request.user.id:
            raise PermissionDenied("You can only update applications for your own jobs.")
        serializer = ApplicationStatusSerializer(application, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        old_status = application.status
        application.status = serializer.validated_data["status"]
        application.save(update_fields=["status", "updated_at"])
        if old_status != application.status:
            EmployerNotification.objects.create(
                employer=application.job.employer,
                application=application,
                message=f"Application status changed to {application.get_status_display()}.",
            )
        return Response(JobApplicationSerializer(application, context={"request": request}).data)

class NotificationListView(generics.ListAPIView):
    serializer_class = EmployerNotificationSerializer
    permission_classes = [IsEmployer]
    def get_queryset(self):
        return EmployerNotification.objects.filter(employer=self.request.user.employer_profile)
