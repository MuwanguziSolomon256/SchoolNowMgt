# PythonAnywhere Login Issues - Analysis & Fix

## Problem Summary
When attempting to log in on PythonAnywhere, users were redirected back to the unified login page with no error messages displayed, making it appear as if the login credentials weren't being processed.

## Root Cause Identified ✅

The authentication template (`templates/auth/unified_auth.html`) was **not displaying non-field form errors**.

### How It Works:
1. User submits credentials via the login form
2. Form validation runs in `UnifiedLoginForm.clean()` method
3. If authentication fails, errors are raised (e.g., "Invalid password", "No account found with this email")
4. These errors become **non-field errors** (not tied to a specific form field)
5. **The template only displayed field-level errors**, not non-field errors
6. Result: User sees blank re-rendered form with no error message

### Error Types in Django Forms:
```python
# Field-level errors (displayed)
form.email.errors      # ✅ Was shown
form.password.errors   # ✅ Was shown

# Non-field errors (NOT displayed before fix)
form.non_field_errors()  # ❌ Was hidden
form.errors as a dict    # ❌ Was hidden
```

---

## Solution Implemented ✅

### Template Fix
Added non-field error display section to `templates/auth/unified_auth.html`:

```html
<!-- Non-field form errors (authentication errors) -->
{% if form.non_field_errors %}
    <div class="mb-4 sm:mb-6 p-3 sm:p-4 rounded-lg bg-error-container border border-error">
        {% for error in form.non_field_errors %}
            <p class="text-error font-body-md text-xs sm:text-sm">{{ error }}</p>
        {% endfor %}
    </div>
{% endif %}
```

This error block is positioned right above the login form, showing:
- "No account found with this email address."
- "Invalid password. Please try again."
- "This account is registered as a {role}, not a {selected_role}."
- "Multiple accounts found with this email. Please contact support."

---

## Deployment Steps for PythonAnywhere

### 1. **Pull Latest Changes**
```bash
cd ~/schoolnow-repo
git pull origin main
```

### 2. **Run Database Migrations**
```bash
python manage.py migrate --settings=schoolmgmt_project.settings.prod
```

### 3. **Ensure Default School Exists**
```bash
python manage.py ensure_default_school --settings=schoolmgmt_project.settings.prod
```

### 4. **Create Test Users (if needed)**
```bash
python manage.py create_test_logins --settings=schoolmgmt_project.settings.prod
```

### 5. **Collect Static Files**
```bash
python manage.py collectstatic --noinput --settings=schoolmgmt_project.settings.prod
```

### 6. **Restart Web App**
- Go to PythonAnywhere web app console
- Click "Reload" button
- Or use: `touch /var/www/msolomon_pythonanywhere_com_wsgi.py`

---

## What to Check if Login Still Fails

### Check 1: Database Status
```bash
python manage.py shell --settings=schoolmgmt_project.settings.prod
```

Inside Django shell:
```python
from SchoolNowMgt.models import CustomUser, School

# Check schools exist
print("Schools:", School.objects.count())

# Check admin_test user exists
admin = CustomUser.objects.filter(username='admin_test').first()
print("Admin user:", admin)
if admin:
    print(f"  Email: {admin.email}")
    print(f"  Role: {admin.role}")
    print(f"  Active: {admin.is_active}")

# Test authentication
from django.contrib.auth import authenticate
user = authenticate(username='admin_test', password='password123')
print(f"Authentication result: {user}")
```

### Check 2: Browser Console Errors
- Open browser DevTools (F12 → Console tab)
- Look for JavaScript errors
- Check Network tab for failed requests
- Look for CSRF token issues

### Check 3: PythonAnywhere Error Logs
- SSH into PythonAnywhere: `ssh @ssh.pythonanywhere.com`
- Check error log: `tail -f /var/log/pythonanywhere.com.error.log`
- Look for Django errors related to authentication

### Check 4: WSGI Configuration
Verify `/var/www/msolomon_pythonanywhere_com_wsgi.py` has:
```python
import os
import sys

# Add project to path
path = '/home/msolomon/schoolnow-repo'
if path not in sys.path:
    sys.path.insert(0, path)

# Virtual environment
activate_this = '/home/msolomon/.virtualenvs/venv/bin/activate_this.py'
exec(open(activate_this).read(), {'__file__': activate_this})

# Django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'schoolmgmt_project.settings.prod'

from django.wsgi import get_wsgi_application
application = get_wsgi_application()
```

---

## Common Issues on PythonAnywhere

### Issue 1: SQLite Database Locked
**Symptom**: Timeout errors when trying to log in

**Solution**: Enable WAL mode
```bash
sqlite3 ~/schoolnow-repo/db.sqlite3 "PRAGMA journal_mode=WAL;"
```

Or switch to PostgreSQL (recommended for production)

### Issue 2: Static Files Not Found (404 errors for CSS/JS)
**Symptom**: Login page loads but styling is missing

**Solution**:
```bash
python manage.py collectstatic --noinput --settings=schoolmgmt_project.settings.prod
```

### Issue 3: Environment Variables Missing
**Symptom**: Email configuration or other settings errors

**Solution**: Create `.env` file in project root:
```
DEBUG=False
SECRET_KEY=your-50-character-random-key-here
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
```

### Issue 4: Wrong Settings Module
**Symptom**: DEBUG=True in console output

**Solution**: Verify prod.py is being used:
```bash
python manage.py shell --settings=schoolmgmt_project.settings.prod
# should show DEBUG = False
```

---

## Diagnostic Script

Run this on PythonAnywhere to get a full diagnostic report:
```bash
python diagnose_login_issues.py --settings=schoolmgmt_project.settings.prod
```

This will check:
- ✓ DEBUG setting
- ✓ ALLOWED_HOSTS configuration
- ✓ Database status and schema
- ✓ Test user existence
- ✓ Authentication functionality
- ✓ SECRET_KEY configuration
- ✓ Email settings

---

## Testing Locally Before Deploying

Before pushing to PythonAnywhere, verify the fix works locally:

```bash
# Terminal 1: Start dev server
python manage.py runserver

# Terminal 2: Test login with invalid password
# Go to: http://127.0.0.1:8000/auth/login/
# 1. Select Admin role
# 2. Enter: admin@test.com
# 3. Enter wrong password: wrongpassword
# 4. You should now SEE error: "Invalid password. Please try again."
```

---

## Summary of Fix

| Aspect | Before | After |
|--------|--------|-------|
| Invalid credentials | Blank form rerendered | Error message displayed |
| User feedback | Silent failure | Clear error explanation |
| Debugging | Hard to troubleshoot | Errors visible immediately |
| User experience | Frustrating | Helpful |

The fix is **simple but critical**: displaying non-field form errors so users know why their login failed.

---

## Files Modified

- `templates/auth/unified_auth.html` - Added non-field error display block

## Files Created

- `diagnose_login_issues.py` - Diagnostic utility for troubleshooting

## Related Code

**Form validation** (`authentication/forms.py`):
```python
def clean(self):
    # This is where errors are raised as ValidationError
    # These become non-field errors
```

**View handling** (`authentication/views.py`):
```python
if form.is_valid():
    # Success path
else:
    # Re-render with form (now with visible errors)
    return render(request, 'auth/unified_auth.html', context)
```
