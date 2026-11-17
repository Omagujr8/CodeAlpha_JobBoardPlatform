# Generated for CodeAlpha Job Board Platform.
import jobs.models
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="Candidate", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("phone", models.CharField(blank=True, max_length=30)),
            ("location", models.CharField(blank=True, max_length=120)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="candidate_profile", to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name="Employer", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("company_name", models.CharField(max_length=180)),
            ("website", models.URLField(blank=True)),
            ("description", models.TextField(blank=True)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="employer_profile", to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name="JobListing", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("title", models.CharField(max_length=180)),
            ("description", models.TextField()),
            ("location", models.CharField(max_length=160)),
            ("employment_type", models.CharField(choices=[("full_time", "Full time"), ("part_time", "Part time"), ("contract", "Contract"), ("internship", "Internship"), ("temporary", "Temporary")], max_length=20)),
            ("salary_min", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, validators=[django.core.validators.MinValueValidator(0)])),
            ("salary_max", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, validators=[django.core.validators.MinValueValidator(0)])),
            ("is_published", models.BooleanField(default=True)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("updated_at", models.DateTimeField(auto_now=True)),
            ("closes_at", models.DateTimeField(blank=True, null=True)),
            ("employer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="jobs", to="jobs.employer")),
        ], options={"ordering": ["-created_at"]}),
        migrations.CreateModel(name="Resume", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("file", models.FileField(upload_to=jobs.models.resume_upload_path, validators=[django.core.validators.FileExtensionValidator(["pdf", "doc", "docx"]), jobs.models.validate_resume_size])),
            ("label", models.CharField(blank=True, max_length=120)),
            ("uploaded_at", models.DateTimeField(auto_now_add=True)),
            ("candidate", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="resumes", to="jobs.candidate")),
        ]),
        migrations.CreateModel(name="JobApplication", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("cover_letter", models.TextField(blank=True)),
            ("status", models.CharField(choices=[("submitted", "Submitted"), ("reviewing", "Reviewing"), ("shortlisted", "Shortlisted"), ("rejected", "Rejected"), ("hired", "Hired"), ("withdrawn", "Withdrawn")], default="submitted", max_length=20)),
            ("applied_at", models.DateTimeField(auto_now_add=True)),
            ("updated_at", models.DateTimeField(auto_now=True)),
            ("candidate", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="applications", to="jobs.candidate")),
            ("job", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="applications", to="jobs.joblisting")),
            ("resume", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="applications", to="jobs.resume")),
        ], options={"ordering": ["-applied_at"]}),
        migrations.CreateModel(name="EmployerNotification", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("message", models.CharField(max_length=255)),
            ("is_read", models.BooleanField(default=False)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("application", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="jobs.jobapplication")),
            ("employer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="jobs.employer")),
        ], options={"ordering": ["-created_at"]}),
        migrations.AddConstraint(model_name="jobapplication", constraint=models.UniqueConstraint(fields=("job", "candidate"), name="unique_candidate_job_application")),
        migrations.AddIndex(model_name="joblisting", index=models.Index(fields=["is_published", "employment_type", "created_at"], name="job_pub_type_created_idx")),
    ]
