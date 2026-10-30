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

   Django reads the process environment; `.env.example` is a reference, not an automatically loaded file.
5. Apply migrations: `python manage.py migrate`.
6. Start the server: `python manage.py runserver`.
7. Open `http://127.0.0.1:8000/`.

The app includes a staff-only dashboard, active/inactive student records, search and course/status filters, sorting, pagination, CSV export, student create/detail/edit/delete, and Django admin. Create the first superuser with `python manage.py createsuperuser`, then sign in at `/login/`. Superusers can open **Team** in the navigation to create staff accounts and activate/deactivate them. New accounts are staff admins (not superusers), and Django hashes their passwords. Only superusers can access team management; all staff users can access student management. Existing student records are kept when the status migration is applied and default to active. Signing out uses the header control.

Do not use the development `DJANGO_SECRET_KEY` or `DJANGO_DEBUG=true` in production.

## Tests

Run the app tests with `python manage.py test students --settings=project.test_settings`. The test settings use an in-memory SQLite database, so tests do not require a running MySQL server.
