# Student Directory

A Django student-management app with a staff-only dashboard, student directory, MySQL database, and responsive server-rendered interface.

## Setup

1. Install Python 3.14. This project uses Django 5.2 LTS so it can connect to MySQL 8.0; Python 3.14 is the newest Python version officially supported by Django 5.2.
2. Create the MySQL database and application user. For example, in the MySQL client:

   ```sql
   CREATE DATABASE students_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER IF NOT EXISTS 'student_app'@'localhost' IDENTIFIED BY 'choose-a-private-password';
   ALTER USER 'student_app'@'localhost' IDENTIFIED BY 'choose-a-private-password';
   GRANT ALL PRIVILEGES ON students_db.* TO 'student_app'@'localhost';
   ```

   Use the new password for `DB_PASSWORD`; don't use the MySQL root account for the app.
3. Create and activate a Python 3.14 virtual environment, then install dependencies:

   ```powershell
   py -3.14 -m venv .venv314
   .\.venv314\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

   Use this new environment rather than an existing `.venv` created with Python 3.15.
4. Copy `.env.example` to `.env`, then set the MySQL username and password in `.env`. Django loads `.env` automatically; it is excluded from Git. For a deployed application, use a dedicated database user rather than MySQL root.

   ```powershell
   Copy-Item .env.example .env
   ```

5. Apply migrations: `python manage.py migrate`.
6. Start the server: `python manage.py runserver`.
7. Open `http://127.0.0.1:8000/`.

The app includes a staff-only dashboard, active/inactive student records, search and course/status filters, sorting, pagination, CSV export, student create/detail/edit/delete, and Django admin. Create the first superuser with `python manage.py createsuperuser`, then sign in at `/login/`. Superusers can open **Team** in the navigation to create staff accounts and activate/deactivate them. New accounts are staff admins (not superusers), and Django hashes their passwords. Only superusers can access team management; all staff users can access student management. Existing student records are kept when the status migration is applied and default to active. Signing out uses the header control.

Do not use the development `DJANGO_SECRET_KEY` or `DJANGO_DEBUG=true` in production.

## Deployment

This is a Python/Django server app with a MySQL database, so it needs a host that runs Python processes (static hosts such as Netlify can't run it). The repository includes a ready-made configuration for [Render](https://render.com):

1. Create a hosted MySQL 8 database (for example Aiven, Railway, or PlanetScale-compatible MySQL) and note its host, port, database name, user, and password.
2. In Render, choose **New → Blueprint** and select this repository. Render reads `render.yaml`, which uses `uitproject` as the root directory, runs `build.sh` (install dependencies, collect static files, run migrations), and starts the app with Gunicorn.
3. When prompted, enter `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT`. `DJANGO_SECRET_KEY` is generated automatically, `DJANGO_DEBUG` is `false`, and `DB_SSL` is `true` (set it to `false` if your provider doesn't use TLS).
4. After the first deploy, open the Render **Shell** and run `python manage.py createsuperuser`.

Render's hostname is added to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` automatically. For a custom domain, add it to `DJANGO_ALLOWED_HOSTS` and add `https://your-domain` to `DJANGO_CSRF_TRUSTED_ORIGINS`. Other hosts that support a `Procfile` (Railway, Heroku-style platforms) can use the included `Procfile` with `build.sh` as the build step.

## Tests

Run the app tests with `python manage.py test students --settings=project.test_settings`. The test settings use an in-memory SQLite database, so tests do not require a running MySQL server.
