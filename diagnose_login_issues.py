#!/usr/bin/env python
"""
Diagnostic script for PythonAnywhere login issues.
Run this on PythonAnywhere to identify configuration problems.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.prod')
django.setup()

from django.conf import settings
from django.contrib.auth import authenticate
from SchoolNowMgt.models import School, CustomUser

print("=" * 70)
print("SchoolNow Login Diagnostic Report")
print("=" * 70)

# 1. Check DEBUG setting
print(f"\n✓ DEBUG: {settings.DEBUG}")
if settings.DEBUG:
    print("  ⚠️  WARNING: DEBUG=True in production! Set DEBUG=False in prod.py")

# 2. Check ALLOWED_HOSTS
print(f"\n✓ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
pythonanywhere_domain = 'msolomon.pythonanywhere.com'
if pythonanywhere_domain not in settings.ALLOWED_HOSTS:
    print(f"  ⚠️  WARNING: {pythonanywhere_domain} not in ALLOWED_HOSTS")

# 3. Check Database
print("\n✓ Database Configuration:")
db_config = settings.DATABASES['default']
print(f"  Engine: {db_config['ENGINE']}")
print(f"  Name: {db_config['NAME']}")

try:
    # Try to count users
    school_count = School.objects.count()
    print(f"  ✓ Schools in database: {school_count}")
    
    if school_count == 0:
        print("  ⚠️  NO SCHOOLS FOUND! Run: python manage.py ensure_default_school")
    
    user_count = CustomUser.objects.count()
    print(f"  ✓ Users in database: {user_count}")
    
    # Check for admin_test user
    admin_user = CustomUser.objects.filter(username='admin_test').first()
    if admin_user:
        print(f"\n✓ Admin Test User Found:")
        print(f"  Email: {admin_user.email}")
        print(f"  Role: {admin_user.role}")
        print(f"  Active: {admin_user.is_active}")
        print(f"  School: {admin_user.school.name if admin_user.school else 'None'}")
        
        # Try to authenticate
        print(f"\n✓ Testing Authentication (try default password 'password123'):")
        authenticated = authenticate(username='admin_test', password='password123')
        if authenticated:
            print(f"  ✓ Authentication successful!")
        else:
            print(f"  ✗ Authentication failed - password may be wrong")
            print(f"  Note: User might have a different password")
    else:
        print("\n✗ Admin test user NOT found!")
        print("  Run: python manage.py create_test_logins")
        
except Exception as e:
    print(f"  ✗ Database Error: {e}")
    print(f"  Try running: python manage.py migrate")

# 4. Check SECRET_KEY
print(f"\n✓ SECRET_KEY configured: {len(settings.SECRET_KEY) > 20}")
if len(settings.SECRET_KEY) < 50:
    print("  ⚠️  WARNING: SECRET_KEY too short! Generate a new one")

# 5. Check EMAIL Settings
print(f"\n✓ EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"  EMAIL_HOST: {settings.EMAIL_HOST}")

# 6. Summary
print("\n" + "=" * 70)
print("TROUBLESHOOTING STEPS:")
print("=" * 70)
print("""
If login is still not working after template fix:

1. **Ensure Database is Initialized:**
   python manage.py migrate
   python manage.py ensure_default_school

2. **Create Test Users:**
   python manage.py create_test_logins

3. **Check Browser Console:**
   - Look for JavaScript errors
   - Check Network tab for failed requests
   - Look for CSRF token issues

4. **Check Django Logs:**
   - tail -f /var/log/pythonanywhere.com.error.log
   - Look for authentication-related errors

5. **Common PythonAnywhere Issues:**
   - Static files not collected: python manage.py collectstatic --noinput
   - Database locked: sqlite3 db.sqlite3 "PRAGMA journal_mode=WAL;"
   - Virtual environment not activated in WSGI file

6. **Test Form Directly:**
   Log in to PythonAnywhere console and run:
   python manage.py shell
   from django.contrib.auth import authenticate
   user = authenticate(username='admin_test', password='password123')
   print(f"User: {user}")
""")
