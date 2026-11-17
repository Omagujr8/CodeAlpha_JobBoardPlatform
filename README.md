# CodeAlpha Job Board Platform

A Django REST Framework backend for employers, candidates, job listings, resumes, applications, and employer notifications. Scope follows CodeAlpha Backend Task 4. No frontend, payment integration, or external identity provider is included.

## Requirements
- Python 3.10+
- Django 5.2
- Django REST Framework
- SQLite by default (PostgreSQL can be configured with environment variables)

## Quick start
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows; use cp on macOS/Linux
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
API root: http://127.0.0.1:8000/api/ . Admin: http://127.0.0.1:8000/admin/.

Create an Employer or Candidate profile for an existing Django user in Django admin before using protected endpoints. DRF Basic and Session authentication are enabled for development; deploy behind HTTPS and configure a production identity solution only if the project scope later requires one.

## Domain models
- **Employer**: one-to-one profile for a Django user and organization details.
- **JobListing**: owned by an employer; title, description, location, employment type, salary range, and publication/closing dates.
- **Candidate**: one-to-one profile for a Django user.
- **Resume**: candidate-owned PDF/DOC/DOCX file, size-limited to 5 MB.
- **JobApplication**: unique candidate/listing pair, optional resume, cover letter, status and timestamps.
- **EmployerNotification**: stored notification generated when a candidate applies or an application status changes.

## API endpoints
All endpoints are under `/api/`. JSON requests use `Content-Type: application/json`; resume uploads use multipart form data.

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `jobs/` | Public | List/search/filter published jobs |
| POST | `jobs/` | Employer | Create a job |
| GET | `jobs/{id}/` | Public | Job details |
| GET/POST | `resumes/` | Candidate | List/upload own resumes |
| GET | `resumes/{id}/` | Owner | Resume metadata |
| GET/POST | `applications/` | Candidate (GET: owner) | List own / submit application |
| GET | `applications/{id}/` | Candidate or owning employer | Application detail |
| PATCH | `applications/{id}/status/` | Owning employer | Update application status |
| GET | `notifications/` | Employer | List own stored notifications |

### Job search filters
Supported query parameters: `q` (title/description/company), `location` (case-insensitive partial match), `employment_type`, `company`, and `ordering` (`-created_at`, `created_at`, `title`). Example:
```http
GET /api/jobs/?q=python&location=remote&employment_type=full_time
```

### Example: create a job
Authenticated as a user with an Employer profile:
```http
POST /api/jobs/
Content-Type: application/json

{
  "title": "Junior Python Developer",
  "description": "Build and maintain backend APIs.",
  "location": "Remote",
  "employment_type": "full_time",
  "salary_min": "500.00",
  "salary_max": "900.00"
}
```
Response: `201 Created` with the job representation and employer.

### Example: upload a resume
Authenticated as a Candidate; send multipart form data:
```bash
curl -X POST http://127.0.0.1:8000/api/resumes/ \
  -u candidate:password -F "file=@resume.pdf" -F "label=Backend CV"
```
Only PDF, DOC, and DOCX files up to 5 MB are accepted. This is basic extension/content-type validation, not malware scanning.

### Example: apply and track status
```http
POST /api/applications/
Content-Type: application/json

{"job": 1, "resume": 1, "cover_letter": "I am interested in this role."}
```
The candidate can track the returned `status` via `GET /api/applications/{id}/`. The owning employer updates it:
```http
PATCH /api/applications/1/status/
Content-Type: application/json

{"status": "shortlisted"}
```
Allowed statuses: `submitted`, `reviewing`, `shortlisted`, `rejected`, `hired`, `withdrawn`. A stored notification is created for the employer on submission and for the candidate when the status changes.

## Error responses
Validation errors return `400`; unauthenticated requests return `401`; authenticated users without the required role/ownership return `403`; missing records return `404`; duplicate applications return `400`. DRF's standard error format is retained for field-level validation details.

## Tests
```bash
python manage.py test
```
Tests cover job creation and ownership, filtering, resume validation/upload, application submission/duplicate prevention, status updates, notifications, and permission/error paths.

## Production notes
Set a strong `SECRET_KEY`, `DEBUG=False`, and `ALLOWED_HOSTS`; use PostgreSQL, HTTPS, a private media-storage backend, backups, and a malware-scanning pipeline before accepting public uploads. The default local media filesystem and SQLite settings are for development. Do not commit `.env`, uploaded resumes, or secrets.
