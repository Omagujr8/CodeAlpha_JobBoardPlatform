from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient
from .models import Employer, Candidate, JobListing, Resume, JobApplication, EmployerNotification

User = get_user_model()

class JobBoardAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.employer_user = User.objects.create_user(username="employer", password="Pass12345!")
        self.employer = Employer.objects.create(user=self.employer_user, company_name="Acme Tech")
        self.candidate_user = User.objects.create_user(username="candidate", password="Pass12345!")
        self.candidate = Candidate.objects.create(user=self.candidate_user)
        self.other_user = User.objects.create_user(username="other", password="Pass12345!")
        self.job = JobListing.objects.create(employer=self.employer, title="Python Engineer",
            description="Build APIs", location="Remote", employment_type="full_time")

    def test_public_job_search_and_filters(self):
        response = self.client.get("/api/jobs/?q=python&location=remote&employment_type=full_time")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Python Engineer")
        self.assertEqual(self.client.get("/api/jobs/?q=designer").data["count"], 0)
        self.assertEqual(self.client.get(f"/api/jobs/{self.job.id}/").status_code, 200)

    def test_employer_can_create_job_but_candidate_cannot(self):
        self.client.force_authenticate(self.employer_user)
        response = self.client.post("/api/jobs/", {"title":"Django Developer","description":"Develop services",
            "location":"Lagos","employment_type":"contract"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["employer"]["company_name"], "Acme Tech")
        self.client.force_authenticate(self.candidate_user)
        self.assertEqual(self.client.post("/api/jobs/", {"title":"No","description":"No","location":"Remote",
            "employment_type":"full_time"}, format="json").status_code, 403)

    def test_job_salary_validation(self):
        self.client.force_authenticate(self.employer_user)
        response = self.client.post("/api/jobs/", {"title":"Bad range","description":"x","location":"Remote",
            "employment_type":"full_time","salary_min":"900","salary_max":"100"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_resume_upload_and_bad_extension(self):
        self.client.force_authenticate(self.candidate_user)
        good = SimpleUploadedFile("resume.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        response = self.client.post("/api/resumes/", {"file":good,"label":"CV"}, format="multipart")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.client.get("/api/resumes/").data["count"], 1)
        bad = SimpleUploadedFile("resume.exe", b"bad", content_type="application/octet-stream")
        self.assertEqual(self.client.post("/api/resumes/", {"file":bad}, format="multipart").status_code, 400)

    def test_resume_size_limit(self):
        self.client.force_authenticate(self.candidate_user)
        huge = SimpleUploadedFile("large.pdf", b"x" * (5 * 1024 * 1024 + 1), content_type="application/pdf")
        self.assertEqual(self.client.post("/api/resumes/", {"file":huge}, format="multipart").status_code, 400)

    def test_candidate_can_apply_and_employer_is_notified(self):
        self.client.force_authenticate(self.candidate_user)
        response = self.client.post("/api/applications/", {"job":self.job.id,"cover_letter":"Please consider my application."}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "submitted")
        self.assertEqual(EmployerNotification.objects.filter(employer=self.employer).count(), 1)

    def test_duplicate_application_rejected(self):
        JobApplication.objects.create(job=self.job, candidate=self.candidate)
        self.client.force_authenticate(self.candidate_user)
        response = self.client.post("/api/applications/", {"job":self.job.id}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_candidate_cannot_attach_another_candidates_resume(self):
        other = Candidate.objects.create(user=self.other_user)
        resume = Resume.objects.create(candidate=other, file=SimpleUploadedFile("other.pdf", b"%PDF"))
        self.client.force_authenticate(self.candidate_user)
        response = self.client.post("/api/applications/", {"job":self.job.id,"resume":resume.id}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_employer_updates_status_and_notification_is_recorded(self):
        application = JobApplication.objects.create(job=self.job, candidate=self.candidate)
        self.client.force_authenticate(self.employer_user)
        response = self.client.patch(f"/api/applications/{application.id}/status/", {"status":"shortlisted"}, format="json")
        self.assertEqual(response.status_code, 200)
        application.refresh_from_db()
        self.assertEqual(application.status, "shortlisted")
        self.assertEqual(application.notifications.count(), 1)

    def test_other_employer_cannot_update_application(self):
        another = User.objects.create_user(username="another", password="Pass12345!")
        Employer.objects.create(user=another, company_name="Other Ltd")
        application = JobApplication.objects.create(job=self.job, candidate=self.candidate)
        self.client.force_authenticate(another)
        self.assertEqual(self.client.patch(f"/api/applications/{application.id}/status/", {"status":"rejected"}, format="json").status_code, 403)

    def test_missing_job_returns_400(self):
        self.client.force_authenticate(self.candidate_user)
        self.assertEqual(self.client.post("/api/applications/", {"job":99999}, format="json").status_code, 400)

    def test_unauthenticated_protected_endpoint_returns_401(self):
        self.assertEqual(self.client.post("/api/resumes/", {}).status_code, 401)

    def test_candidate_sees_only_own_applications(self):
        JobApplication.objects.create(job=self.job, candidate=self.candidate)
        self.client.force_authenticate(self.candidate_user)
        self.assertEqual(self.client.get("/api/applications/").data["count"], 1)
