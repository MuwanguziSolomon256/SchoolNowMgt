# PythonAnywhere Deployment Checklist

## Quick Fix for Login Issues ✅

### The Problem
Login page redirects back without showing error messages.

### The Solution  
Template now displays error messages. Push changes to PythonAnywhere.

---

## Pre-Deployment Verification (Local)

- [ ] Clone/pull latest code locally
- [ ] Run dev server: `python manage.py runserver`
- [ ] Test login at `http://127.0.0.1:8000/auth/login/`
  - Try wrong password
  - Verify error message appears: "Invalid password. Please try again."
- [ ] Try non-existent email
  - Verify error message: "No account found with this email address."

---

## Deployment to PythonAnywhere

### Step 1: SSH into PythonAnywhere
```bash
ssh msolomon@ssh.pythonanywhere.com
cd ~/schoolnow-repo  # or your project directory
```

### Step 2: Pull Latest Code
```bash
git pull origin main
```

### Step 3: Activate Virtual Environment
```bash
source ~/.virtualenvs/venv/bin/activate
```

### Step 4: Run Migrations
```bash
python manage.py migrate --settings=schoolmgmt_project.settings.prod
```

### Step 5: Initialize Database (if first time)
```bash
python manage.py ensure_default_school --settings=schoolmgmt_project.settings.prod
python manage.py create_test_logins --settings=schoolmgmt_project.settings.prod
```

### Step 6: Collect Static Files
```bash
python manage.py collectstatic --noinput --settings=schoolmgmt_project.settings.prod
```

### Step 7: Reload Web App
```bash
# Option A: Through web interface
# Go to pythonanywhere.com → Web tab → Click "Reload"

# Option B: Through SSH (touch WSGI file)
touch /var/www/msolomon_pythonanywhere_com_wsgi.py
```

### Step 8: Test in Browser
- Go to: `https://msolomon.pythonanywhere.com/auth/login/`
- Try logging in with admin@test.com / password123
- Or try with wrong password to see error message
- ✅ Should now see error messages instead of silent redirect

---

## If Login Still Doesn't Work

### Quick Diagnostics
```bash
python diagnose_login_issues.py --settings=schoolmgmt_project.settings.prod
```

### Common Fixes

**Database Issues:**
```bash
# Check if database needs migration
python manage.py showmigrations --settings=schoolmgmt_project.settings.prod
python manage.py migrate --settings=schoolmgmt_project.settings.prod

# Fix SQLite locking (if applicable)
sqlite3 ~/schoolnow-repo/db.sqlite3 "PRAGMA journal_mode=WAL;"
```

**Missing Test Data:**
```bash
# Create default school
python manage.py ensure_default_school --settings=schoolmgmt_project.settings.prod

# Create test users
python manage.py create_test_logins --settings=schoolmgmt_project.settings.prod
```

**Static Files Not Loading:**
```bash
python manage.py collectstatic --noinput --clear --settings=schoolmgmt_project.settings.prod
```

**Check Logs:**
```bash
tail -f /var/log/pythonanywhere.com.error.log
```

---

## What Was Changed

### Files Modified:
- `templates/auth/unified_auth.html` - Added error message display for login failures

### What the Fix Does:
- Shows "Invalid password. Please try again." when wrong password entered
- Shows "No account found with this email address." when email doesn't exist
- Shows role mismatch errors if user selects wrong role
- Prevents silent redirect back to login page

---

## Test Credentials

After setting up:
- **Email**: admin@test.com
- **Password**: password123
- **Role**: Admin

Login should redirect to dashboard at `/school/`

---

## Getting Help

### Check Status
```bash
# Is web app reloading?
python manage.py check --settings=schoolmgmt_project.settings.prod

# Is database accessible?
python manage.py dbshell --settings=schoolmgmt_project.settings.prod

# Test authentication directly
python manage.py shell --settings=schoolmgmt_project.settings.prod
# Then:
from django.contrib.auth import authenticate
user = authenticate(username='admin_test', password='password123')
print(user)  # Should show user object, not None
```

### View Detailed Errors
1. On PythonAnywhere web console: Check error logs
2. Run: `python manage.py runserver 0.0.0.0:8000` and access via browser
3. Look at Django error pages in browser

### Contact
If issues persist, check:
- `/var/log/pythonanywhere.com.error.log` for detailed Django errors
- Browser DevTools (F12) Console tab for client-side errors
- Settings in `schoolmgmt_project/settings/prod.py` for configuration issues
