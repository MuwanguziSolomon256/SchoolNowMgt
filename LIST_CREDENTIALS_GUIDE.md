# How to List Test Credentials

## 🚀 Quick Command Reference

### Option 1: Standalone Script (Recommended - No Setup)
```bash
python show_test_credentials.py
```
✅ Works instantly - no Django or venv needed

### Option 2: Django Management Command
```bash
python manage.py list_test_credentials
```
✅ Shows credentials from actual database  
⚠️ Requires activated virtual environment

---

## 📋 Available Formats

### Table Format (Default)
```bash
python show_test_credentials.py
# or
python manage.py list_test_credentials --format=table
```

Output:
```
==========================================================================================
TEST LOGIN CREDENTIALS
==========================================================================================
Role               Username        Email                  Password        Redirect  
------------------------------------------------------------------------------------------
Admin              admin_test      admin@test.com         password123     /admin/   
Teacher            teacher_test    teacher@test.com       password123     /teacher/ 
Support Staff      staff_test      staff@test.com         password123     /         
Parent             parent_test     parent@test.com        password123     /         
==========================================================================================
```

---

### Simple Format
```bash
python show_test_credentials.py --format=simple
# or
python manage.py list_test_credentials --format=simple
```

Output:
```
TEST LOGIN CREDENTIALS:

Admin:
  Email:    admin@test.com
  Username: admin_test
  Password: password123
  Redirect: /admin/

Teacher:
  Email:    teacher@test.com
  Username: teacher_test
  Password: password123
  Redirect: /teacher/
...
```

---

### Copy-Paste Format
```bash
python show_test_credentials.py --format=copy-paste
```

Output:
```
============================================================
COPY-PASTE CREDENTIALS
============================================================

Admin:
admin@test.com / password123

Teacher:
teacher@test.com / password123

Support Staff:
staff@test.com / password123

Parent:
parent@test.com / password123

============================================================
```

---

### JSON Format
```bash
python show_test_credentials.py --format=json
# or
python manage.py list_test_credentials --format=json
```

Output:
```json
[
  {
    "role": "Admin",
    "username": "admin_test",
    "email": "admin@test.com",
    "password": "password123",
    "redirect": "/admin/"
  },
  ...
]
```

---

## 🎯 Common Use Cases

### "I just want to see the credentials right now"
```bash
python show_test_credentials.py
```

### "I want to copy-paste an email/password"
```bash
python show_test_credentials.py --format=copy-paste
```

### "I need a detailed list with all info"
```bash
python show_test_credentials.py --format=simple
```

### "I want to use this in a script (JSON)"
```bash
python show_test_credentials.py --format=json
```

### "I need to know which accounts exist in the database"
```bash
python manage.py list_test_credentials
```
(Shows ✓ for existing, ⚠️ for missing)

---

## 📌 The Standard Test Credentials

All test accounts use password: **`password123`**

| Role | Email | Username |
|------|-------|----------|
| Admin | admin@test.com | admin_test |
| Teacher | teacher@test.com | teacher_test |
| Support Staff | staff@test.com | staff_test |
| Parent | parent@test.com | parent_test |

---

## 🔗 Related Commands

```bash
# Create the test accounts if they don't exist
python manage.py create_test_logins

# List them
python show_test_credentials.py

# Clean up duplicates
python cleanup_all_duplicates.py

# Verify in database
python manage.py shell
```

In the shell:
```python
from SchoolNowMgt.models import CustomUser
CustomUser.objects.filter(username='admin_test').first()
```

