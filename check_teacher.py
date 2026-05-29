#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import CustomUser, StaffProfile
from SchoolNowMgt.registration.utils import generate_employee_id

teacher = CustomUser.objects.filter(email='teacher@test.com').first()
print(f"Teacher exists: {teacher}")
if teacher:
    print(f"Teacher role: {teacher.role}")
    print(f"Teacher is_active: {teacher.is_active}")
    try:
        profile = teacher.staffprofile
        print(f"StaffProfile exists: {profile}")
        print(f"Employee ID: {profile.employee_id}")
    except StaffProfile.DoesNotExist:
        print("NO StaffProfile found for this teacher!")
        print("Creating one...")
        profile = StaffProfile.objects.create(
            user=teacher,
            employee_id=generate_employee_id(teacher.school),
            position="Teacher",
            salary=0,
            date_joined="2024-01-01"
        )
        print(f"StaffProfile created! ID: {profile.employee_id}")
else:
    print("Teacher account not found. Creating test accounts...")
    import subprocess
    result = subprocess.run(['python', 'manage.py', 'create_test_logins'], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
