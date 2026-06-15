#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import CustomUser, StaffProfile

print("All teachers:")
teachers = CustomUser.objects.filter(role='teacher')
for t in teachers:
    print(f"  Username: {t.username}, Name: {t.get_full_name()}")
    try:
        staff = StaffProfile.objects.get(user=t)
        print(f"    StaffProfile exists: {staff}")
    except:
        print(f"    No StaffProfile")
