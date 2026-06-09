# Test Credentials & Login Issues Guide

## ✅ Test Credentials

### Quickest Way to View All Credentials

```bash
# Option 1: Django management command (shows from database)
python manage.py list_test_credentials

# Option 2: Standalone script (instant, no Django setup needed)
python show_test_credentials.py

# Different formats available:
python manage.py list_test_credentials --format=table      # Pretty table
python manage.py list_test_credentials --format=simple     # Simple list
python manage.py list_test_credentials --format=json       # JSON format
python manage.py list_test_credentials --format=copy-paste # Copy-paste ready

python show_test_credentials.py --format=simple
python show_test_credentials.py --format=json
python show_test_credentials.py --format=copy-paste
```

After running `python manage.py create_test_logins`, use these credentials:

### Admin Account
- **Username**: admin_test
- **Email**: admin@test.com
- **Password**: password123
- **Role**: Admin
- **Redirect**: `/admin/` dashboard

### Teacher Account
- **Username**: teacher_test
- **Email**: teacher@test.com
- **Password**: password123
- **Role**: Teacher
- **Redirect**: `/teacher/` dashboard

### Support Staff Account
- **Username**: staff_test
- **Email**: staff@test.com
- **Password**: password123
- **Role**: Non-Teaching Staff
- **Redirect**: `/` (home page)

### Parent Account
- **Username**: parent_test
- **Email**: parent@test.com
- **Password**: password123
- **Role**: Parent
- **Redirect**: `/` (home page)

---

## 🔧 Why They Don't Work in PythonAnywhere

### Root Cause
The login template wasn't displaying **non-field errors** (authentication errors). When users entered wrong credentials:
1. Form validation ran and caught the error
2. Error was raised as a **non-field error** (not tied to a field)
3. Template only displayed **field-level errors**
4. Result: Users saw blank form with no message

### Error Types in Django Forms
```python
form.email.errors      # ✅ Field errors (displayed)
form.password.errors   # ✅ Field errors (displayed)
form.non_field_errors() # ❌ Auth errors (WAS NOT displayed)
```

### Solution Applied
Added this to `templates/auth/unified_auth.html`:
```html
{% if form.non_field_errors %}
    <div class="mb-4 sm:mb-6 p-3 sm:p-4 rounded-lg bg-error-container border border-error">
        {% for error in form.non_field_errors %}
            <p class="text-error font-body-md text-xs sm:text-sm">{{ error }}</p>
        {% endfor %}
    </div>
{% endif %}
```

---

## 🚀 Deploying to PythonAnywhere

```bash
# 1. Pull latest changes
cd ~/schoolnow-repo
git pull origin main

# 2. Run migrations
python manage.py migrate --settings=schoolmgmt_project.settings.prod

# 3. Ensure default school exists
python manage.py ensure_default_school --settings=schoolmgmt_project.settings.prod

# 4. Create test users (if needed)
python manage.py create_test_logins --settings=schoolmgmt_project.settings.prod

# 5. Collect static files
python manage.py collectstatic --noinput --settings=schoolmgmt_project.settings.prod

# 6. Restart web app
touch /var/www/msolomon_pythonanywhere_com_wsgi.py
```

---

## 🔍 Testing the Fix

1. Navigate to `http://yourdomain.com/auth/login/`
2. Select a role (e.g., "Teacher")
3. Try with **wrong password**: Should see error message
4. Try with **non-existent email**: Should see error message
5. Try with **correct credentials**: Should login successfully

---

## 📋 Database Verification

Inside Django shell:
```bash
python manage.py shell --settings=schoolmgmt_project.settings.prod
```

```python
from SchoolNowMgt.models import CustomUser, School

# Check schools
School.objects.count()  # Should be > 0

# Check for test users
CustomUser.objects.filter(username='admin_test').first()
CustomUser.objects.filter(username='teacher_test').first()
```

---

## ⚠️ Common Issues

### Issue: Login redirects to login page with no error
**Solution**: Template not displaying non-field errors. Check that the error block is in `templates/auth/unified_auth.html`

### Issue: User exists but can't login
**Solution**: Password might be wrong. Recreate test accounts:
```bash
python manage.py create_test_logins --settings=schoolmgmt_project.settings.prod
```

### Issue: School doesn't exist
**Solution**: Run:
```bash
python manage.py ensure_default_school --settings=schoolmgmt_project.settings.prod
```

