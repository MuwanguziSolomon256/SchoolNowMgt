#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings')
django.setup()

from authentication.models import CustomUser
from SchoolNowMgt.models import StaffProfile

print("\n" + "="*100)
print("ALL ADMIN ROLE USERS")
print("="*100 + "\n")

# Get all users
all_users = CustomUser.objects.all().select_related('school')

for user in all_users:
    try:
        profile = StaffProfile.objects.get(user=user)
        if user.role == 'teacher':
            admin_role = profile.teacher_admin_role if profile.teacher_admin_role else 'None'
            print(f"[TEACHER] Email: {user.email:25} | Name: {user.get_full_name():25} | Admin Role: {admin_role}")
        elif user.role == 'non_teaching_staff':
            support_role = profile.support_staff_role if profile.support_staff_role else 'None'
            print(f"[SUPPORT] Email: {user.email:25} | Name: {user.get_full_name():25} | Support Role: {support_role}")
    except StaffProfile.DoesNotExist:
        print(f"[NO PROFILE] Email: {user.email:25} | Name: {user.get_full_name():25} | Role: {user.role}")

print("\n" + "="*100 + "\n")
