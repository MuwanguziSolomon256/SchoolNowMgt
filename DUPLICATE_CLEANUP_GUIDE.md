# Duplicate Cleanup & Test Credentials Reference

## 📋 Overview

This project has several cleanup scripts. The **new unified script** (`cleanup_all_duplicates.py`) consolidates and improves upon the older scripts.

---

## 🚀 Quick Start: Eliminate Duplicates

Run this single command to clean up all duplicates:

```bash
python cleanup_all_duplicates.py
```

This script:
1. ✅ Finds duplicate emails and keeps the most active/recent user
2. ✅ Removes orphaned staff profiles (when user no longer exists)
3. ✅ Removes orphaned tasks (when staff profile no longer exists)
4. ✅ Removes orphaned activities (when staff profile no longer exists)
5. ✅ Provides detailed reporting of all deletions
6. ✅ Shows final database summary

---

## 📊 Cleanup Script Comparison

| Script | Purpose | Status |
|--------|---------|--------|
| `cleanup_all_duplicates.py` | Comprehensive duplicate & orphan cleanup | ✅ **USE THIS ONE** |
| `cleanup_duplicates.py` | Remove duplicate email accounts | ⚠️ Deprecated |
| `clean_duplicates.py` | Delete all teacher@test.com users | ⚠️ Deprecated |
| `cleanup_test_data.py` | Nuclear option: delete everything | ⚠️ Deprecated |

---

## 🧪 Test Credentials

### Setup Test Accounts

```bash
python manage.py create_test_logins
```

This creates 4 test users with **password: `password123`**

### Credentials Table

| Role | Username | Email | Password | Redirect |
|------|----------|-------|----------|----------|
| **Admin** | admin_test | admin@test.com | password123 | /admin/ |
| **Teacher** | teacher_test | teacher@test.com | password123 | /teacher/ |
| **Staff** | staff_test | staff@test.com | password123 | / |
| **Parent** | parent_test | parent@test.com | password123 | / |

---

## 🔧 Why Test Credentials Fail in PythonAnywhere

### The Problem
When users log in with invalid credentials, the authentication form raises **non-field errors** (not tied to any specific form field). The login template was only displaying **field-level errors**, so users saw a blank form with no error message.

### The Solution
The template now displays non-field errors at the top:

```html
{% if form.non_field_errors %}
    <div class="error-box">
        {% for error in form.non_field_errors %}
            <p>{{ error }}</p>
        {% endfor %}
    </div>
{% endif %}
```

### Error Messages Displayed
- ✓ "Invalid password. Please try again."
- ✓ "No account found with this email address."
- ✓ "This account is registered as {role}, not {selected_role}."
- ✓ "Multiple accounts found. Please contact support."

---

## 🚀 Deployment to PythonAnywhere

### Step-by-Step

```bash
# 1. SSH into PythonAnywhere
cd ~/schoolnow-repo

# 2. Pull latest code
git pull origin main

# 3. Run migrations
python manage.py migrate --settings=schoolmgmt_project.settings.prod

# 4. Ensure default school exists
python manage.py ensure_default_school --settings=schoolmgmt_project.settings.prod

# 5. Create test users (optional)
python manage.py create_test_logins --settings=schoolmgmt_project.settings.prod

# 6. Collect static files
python manage.py collectstatic --noinput --settings=schoolmgmt_project.settings.prod

# 7. Restart web app
touch /var/www/msolomon_pythonanywhere_com_wsgi.py
```

---

## 🔍 Verify After Cleanup

```bash
python manage.py shell
```

Inside the Django shell:

```python
from SchoolNowMgt.models import CustomUser
from django.db.models import Count

# Check for remaining duplicates
duplicates = CustomUser.objects.values('email').annotate(
    count=Count('id')
).filter(count__gt=1)

if duplicates.exists():
    print(f"WARNING: {duplicates.count()} duplicate emails still exist!")
else:
    print("✅ All duplicates eliminated!")

# Check active users
active_users = CustomUser.objects.filter(is_active=True)
print(f"\nActive users: {active_users.count()}")
for user in active_users:
    print(f"  - {user.username} ({user.email})")
```

---

## ⚠️ Common Issues & Solutions

### Issue: Test users don't login
**Solution**: Recreate them
```bash
python manage.py create_test_logins
```

### Issue: Duplicate users in database
**Solution**: Run the cleanup script
```bash
python cleanup_all_duplicates.py
```

### Issue: Login page shows no error on failed login
**Solution**: Check that `templates/auth/unified_auth.html` includes the non-field error block

### Issue: Users can't login on PythonAnywhere but works locally
**Checklist**:
- [ ] Code is pulled and up to date
- [ ] Migrations have run
- [ ] Static files collected
- [ ] Template includes error messages (check above)
- [ ] Test account exists in production database
- [ ] Web app restarted after changes

---

## 📝 Database Schema Reference

### CustomUser Fields
```python
username          # Unique username
email            # Unique email
password         # Hashed password
role             # admin, teacher, parent, non_teaching_staff
is_active        # Whether user can login
is_staff         # Can access Django admin
is_superuser     # Full system access
school           # Foreign key to School
```

### Why Duplicates Happen
1. **Same email, different roles** - User registering with different roles
2. **Test data creation** - Running scripts multiple times
3. **Manual account creation** - Creating accounts without checking for duplicates
4. **Migration issues** - Data imported from old system with duplicates

---

## 🛠️ For Developers

### Adding New Cleanup Logic

Edit `cleanup_all_duplicates.py` to add new cleanup steps:

```python
# After Step 3, before the summary:

# STEP 4: Remove your_custom_thing
print('\n4️⃣  Checking for your_custom_thing...\n')
your_deleted = 0

# ... your logic ...

# Then update summary printing
```

### Running in Production

```bash
# On PythonAnywhere (with proper backups first!)
cd ~/schoolnow-repo
python manage.py shell --settings=schoolmgmt_project.settings.prod < cleanup_all_duplicates.py
```

---

## 📚 Related Files

- [PYTHONANYWHERE_LOGIN_FIX.md](PYTHONANYWHERE_LOGIN_FIX.md) - Details on the login error fix
- [AUTHENTICATION_IMPLEMENTATION.md](AUTHENTICATION_IMPLEMENTATION.md) - Full auth system docs
- [PYTHONANYWHERE_DEPLOYMENT_CHECKLIST.md](PYTHONANYWHERE_DEPLOYMENT_CHECKLIST.md) - Deployment steps

---

## 📞 Support

If issues persist:

1. Check Django logs: `tail -f ~/logs/error.log`
2. Run diagnostic: `python diagnose_login_issues.py`
3. Verify database: `python manage.py dbshell`
4. Check migrations: `python manage.py showmigrations`

