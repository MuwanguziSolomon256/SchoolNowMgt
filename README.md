# School Management System MVP — Django Project

A Django MVP for managing a Ugandan primary school with support for schools, users (with role-based access), and staff profiles.

## Project Structure

```
Management Info Sys/
├── manage.py                      # Django management script
├── db.sqlite3                     # Database (generated after migrations)
├── schoolmgmt_project/            # Project configuration directory
│   ├── __init__.py
│   ├── settings.py               # Django settings (AUTH_USER_MODEL configured)
│   ├── urls.py                   # URL router
│   ├── asgi.py                   # ASGI config
│   └── wsgi.py                   # WSGI config
└── SchoolNowMgt/                 # Main Django app
    ├── migrations/               # Database migrations (auto-generated)
    │   └── __init__.py
    ├── __init__.py
    ├── apps.py                   # App configuration
    ├── models.py                 # Data models: School, CustomUser, StaffProfile
    ├── views.py                  # Views (to be implemented)
    ├── admin.py                  # Django admin (to be configured)
    └── tests.py                  # Tests (to be implemented)
```

## Models Overview

### 1. **School**
Represents a school institution in the system.

**Fields:**
- `name` — School name (CharField, max 200)
- `registration_number` — Unique school registration number (CharField, unique)
- `address` — School address (TextField)
- `phone` — Contact phone (CharField, max 20)
- `email` — Email address (EmailField)
- `logo` — School logo image (ImageField, optional)
- `created_at` — Creation timestamp (DateTimeField, auto-generated)

### 2. **CustomUser** (extends Django's AbstractUser)
Custom user model supporting multiple roles within a school.

**Fields:**
- `username`, `email`, `first_name`, `last_name` — Inherited from AbstractUser
- `role` — User role: admin, teacher, non_teaching_staff, or parent (CharField with choices, indexed)
- `school` — Foreign key to School (each user belongs to one school, indexed)
- `phone` — Contact phone (CharField, max 20, optional)
- `profile_picture` — User profile image (ImageField, optional)
- `is_active` — Account activation status (BooleanField, default=True)

**Available Roles:**
- `admin` — School administrator
- `teacher` — Teaching staff
- `non_teaching_staff` — Support staff (cleaner, cook, security, etc.)
- `parent` — Parent/guardian

### 3. **StaffProfile**
Extended profile for teaching and non-teaching staff members.

**Fields:**
- `user` — One-to-one relationship to CustomUser (teacher or non_teaching_staff only)
- `employee_id` — Unique employee ID (CharField, max 50, unique)
- `position` — Job title (CharField, max 100) — e.g., Class Teacher, Head Teacher, Cleaner
- `qualification` — Educational qualifications (TextField, optional)
- `salary` — Monthly salary (DecimalField, 10 digits, 2 decimal places)
- `date_joined` — Employment start date (DateField)
- `date_left` — Employment end date (DateField, optional, for tracking past employees)
- `is_full_time` — Employment type (BooleanField, default=True)

## Setup Instructions

### 1. Install Dependencies

Create and activate a Python virtual environment, then install Django and Pillow:

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install django pillow
```

### 2. Verify AUTH_USER_MODEL Setting ✅

The `AUTH_USER_MODEL` is already configured in `schoolmgmt_project/settings.py`:

```python
AUTH_USER_MODEL = 'SchoolNowMgt.CustomUser'
```

**This must remain in place before creating any migrations.**

### 3. Create and Run Migrations

Once you're ready to initialize the database:

```bash
# Create migrations for all models
python manage.py makemigrations

# Apply migrations to the database
python manage.py migrate
```

### 4. Create a Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account. This will automatically use the CustomUser model.

### 5. Run the Development Server

```bash
python manage.py runserver
```

Access the admin panel at: `http://127.0.0.1:8000/admin/`

## Next Steps (Not Yet Implemented)

- [ ] Register models in `SchoolNowMgt/admin.py` with appropriate admin classes
- [ ] Create views for user management, school operations, and staff profiles
- [ ] Define URL patterns in `schoolmgmt_project/urls.py`
- [ ] Create templates for admin dashboards and user interfaces
- [ ] Implement signals for user creation/updates if needed
- [ ] Add serializers and API endpoints (if REST API is required)
- [ ] Write comprehensive tests in `SchoolNowMgt/tests.py`
- [ ] Configure media file handling in production
- [ ] Set up email backend for user notifications

## Important Notes

1. **Media Files**: The project is configured to serve uploaded files (logos, profile pictures) during development. For production, configure AWS S3, Azure Blob Storage, or another external storage solution.

2. **Database**: Currently uses SQLite (for development). For production, upgrade to PostgreSQL:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'schoolmgmt_db',
           'USER': 'postgres',
           'PASSWORD': 'your_password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```

3. **Security**: Before deploying:
   - Change `SECRET_KEY` in settings.py to a secure random key
   - Set `DEBUG = False`
   - Configure `ALLOWED_HOSTS` properly
   - Set up HTTPS/SSL
   - Use environment variables for sensitive settings (use python-decouple or similar)

4. **Image Fields**: Ensure `Pillow` is installed for ImageField to work properly.

## Model Relationships

```
School (1) ──── (many) CustomUser
CustomUser (1) ──── (0..1) StaffProfile
```

- A school can have many users (teachers, staff, parents, admins)
- A CustomUser with role 'teacher' or 'non_teaching_staff' can optionally have a StaffProfile
- A StaffProfile cannot exist without a CustomUser

## Development Workflow

1. **Model Changes**: Edit models → Run `makemigrations` → Run `migrate`
2. **Admin Registration**: Add models to `SchoolNowMgt/admin.py` after testing models
3. **Views & URLs**: Implement views once models are finalized
4. **Testing**: Write tests in `SchoolNowMgt/tests.py` for all business logic

---

**Created**: May 2026  
**Status**: MVP Phase — Models Complete ✅
