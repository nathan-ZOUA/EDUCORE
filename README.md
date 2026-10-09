# EDUCORE

EDUCORE is an English-language learning platform for students, parents, teachers, and administrators. This repository contains the working foundation and core learning workflows; it is not yet a complete production SaaS deployment.

## Current implementation

- React 19 + Vite frontend with responsive public pages, separate learning and staff sign-in entry points, and role-aware workspaces.
- Django REST Framework API with JWT login, registration limited to student/parent accounts, and a custom role-based user model.
- Core academic records: subjects, courses, enrollments, lessons and lesson progress, books, assignments and submissions, quizzes and attempts, scheduled examinations and attempts, grades, attendance, calendar events, notifications, parent-child links, and audit-log storage.
- Role-scoped exam, grade, attendance, calendar, and course-linked internal messaging views in the frontend portal.
- Profile editing with eight preset avatars, per-account photo uploads, a personal photo gallery, and photo selection/deletion.
- Separate teacher and administrator portal routes; administrators can create and search accounts through the EDUCORE interface.
- Server-side access scoping for courses, lessons, submissions, and parent-linked children.
- PostgreSQL configuration, Redis cache/broker configuration, Celery email task, Docker Compose development services, and OpenAPI/Swagger endpoints.

Payment processing, email verification and password reset, production-grade object storage, achievements, advanced reporting, live Channels features (messaging currently polls the REST API), production monitoring, and load testing still require implementation and verification. Do not deploy with development credentials or present unimplemented payment flows as active.

## Project structure

- `backend/` — Django project, `core` app, API, data migration, and tests
- `frontend/` — React application
- `.env.example` — development environment template
- `docker-compose.yml` — local development stack (not a hardened production deployment)
- `render.yaml` — Render Blueprint for the production API, managed PostgreSQL, persistent profile-photo storage, and static frontend

## Local development on Windows (SQLite)

For a quick local setup, do not create a `.env` file; without database variables Django uses a local SQLite file:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Set-Location backend
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The superuser receives the administrator role. Add a subject, teacher, and course using Django admin at `http://localhost:8000/admin/`. Courses are created as drafts; publish them in the admin interface when approved.

In a second PowerShell window:

```powershell
Set-Location frontend
npm install
npm run dev
```

Vite proxies `/api` requests to `http://127.0.0.1:8000`. The API also accepts `VITE_API_URL` (for example, `http://localhost:8000/api`).

## PostgreSQL and Docker development

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Copy `.env.example` when using Docker/PostgreSQL; its `DB_NAME` setting makes Django use PostgreSQL, so the database must be running. The development stack exposes the web app on port `5173`, Django on `8000`, PostgreSQL on `5432`, and Redis on `6379`. The Compose PostgreSQL credentials are development-only. Replace them and use a managed database, TLS, private networking, backups, and secrets management for deployment.

## Render deployment

The `render.yaml` Blueprint is configured for this repository layout (where `EDUCORE` is inside the repository). Push the repository to GitHub, create a Render account, select **New > Blueprint**, connect the repository, and set the Blueprint file path to `DEV/EDUCORE/render.yaml`. Review the generated services, select/confirm the Frankfurt region, and apply the Blueprint. Render creates the PostgreSQL database, the Django/Gunicorn API, persistent photo storage, and the static React frontend; the frontend and API receive HTTPS `onrender.com` addresses without requiring a client domain.

The API service requires a paid plan because it uses a persistent disk for uploaded profile images; PostgreSQL is a separately billed service. The frontend static site is free. Review Render's current prices and resource limits before confirming. Keep the database private, restrict account access, and configure billing alerts.

Wait until all services report **Live**, then open the frontend URL and create the initial administrator once from the API service's Shell using `python manage.py createsuperuser` (working directory `/app`). Use the staff portal to create other accounts. Verify login, course access, image upload, and the `/api/health/` endpoint before inviting the client. Render's PostgreSQL backups and disk snapshots are helpful but do not replace a tested export/restore procedure. Do not use the local SQLite database for production.

The Blueprint does not configure a transactional email provider, password reset, payment processing, or third-party object storage. These features must be configured/implemented separately before they are offered to the client. The current profile media disk is attached to one API instance and requires a paid, single-instance service; plan an object-storage migration before horizontal scaling.

## Useful commands

```powershell
# Backend checks and tests
Set-Location backend
python manage.py check
python manage.py test core
python manage.py makemigrations --check

# Frontend validation
Set-Location ..\frontend
npm run lint
npm run build
```

## API

- Health: `GET /api/health/`
- Register: `POST /api/auth/register/`
- Obtain/refresh JWT: `POST /api/auth/token/`, `POST /api/auth/token/refresh/`
- Current account and dashboard: `GET /api/auth/me/`, `GET /api/dashboard/`
- Profile photo gallery: `GET`/`POST /api/profile/photos/`, `POST /api/profile/photos/<id>/select/`, `DELETE /api/profile/photos/<id>/`
- Administrator account management: `GET`/`POST /api/admin/users/` (administrator role only)
- Learning: `/api/subjects/`, `/api/courses/`, `/api/enrollments/`, `/api/lessons/`, `/api/lesson-progress/`
- Library and academic work: `/api/books/`, `/api/assignments/`, `/api/submissions/`, `/api/quizzes/`, `/api/exams/`, `/api/grades/`, `/api/attendance/`, `/api/calendar/`
- Notifications and family links: `/api/notifications/`, `/api/parent/children/`
- Messaging: `/api/message-contacts/?course=<id>`, `/api/conversations/`, `/api/conversations/<id>/messages/`
- OpenAPI schema and Swagger UI: `/api/schema/`, `/api/docs/`

The API uses pagination. Examination answer keys are omitted from student responses; students must start an open examination before submitting and the server enforces the duration and schedule. Parent data access is derived from explicit `StudentParent` records and enforced by backend querysets; frontend hiding is not treated as authorization.

## Staff portal

Teachers and administrators use the separate staff sign-in at `http://localhost:5173/staff/login`. After login, teachers are directed to their teaching dashboard; administrators are directed to the administration dashboard and can create/search teacher, administrator, student, and parent accounts at `/staff/accounts`. Account creation requires a 12-character password and is restricted by the backend to administrator accounts. Public registration remains limited to students and parents.

For a new local database, bootstrap the first administrator account once with `python manage.py createsuperuser` from the `backend` directory. Subsequent staff account management takes place in the staff portal, not through commands.

## Production checklist

Before deployment, configure a unique `SECRET_KEY`, `DEBUG=False`, exact `ALLOWED_HOSTS`, HTTPS, a managed PostgreSQL database, Redis, email delivery, persistent object storage for profile photos, backups, logging/monitoring, and an appropriate frontend/API origin policy. Uploaded photos are stored on the local filesystem in development; the Compose `profile_media` volume persists them locally, but production should use protected object storage and a configured media-serving layer. Enable `SECURE_HSTS_INCLUDE_SUBDOMAINS` and `SECURE_HSTS_PRELOAD` only after confirming every affected hostname is HTTPS-ready. Run Django's deployment checks and security review, add the remaining product modules, and perform real load tests. No concurrency or availability target has been load-tested or guaranteed.
