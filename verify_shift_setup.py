"""
Verification script to check teacher StaffProfile status.
Shows which teachers have StaffProfile and which don't.
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from SchoolNowMgt.models import CustomUser, StaffProfile

print("=" * 70)
print("TEACHER STAFFPROFILE STATUS CHECK")
print("=" * 70)

teachers = CustomUser.objects.filter(role='teacher', is_active=True)
print(f"\nTotal active teachers: {teachers.count()}\n")

if teachers.count() == 0:
    print("No active teachers found!")
    sys.exit(1)

has_profile = 0
missing_profile = 0

print("Teacher Status:")
print("-" * 70)

for teacher in teachers:
    try:
        profile = StaffProfile.objects.get(user=teacher)
        print(f"✓ {teacher.get_full_name():30} | Employee ID: {profile.employee_id}")
        has_profile += 1
    except StaffProfile.DoesNotExist:
        print(f"✗ {teacher.get_full_name():30} | NO STAFFPROFILE")
        missing_profile += 1

print("-" * 70)
print(f"\nSummary:")
print(f"  With StaffProfile:    {has_profile}")
print(f"  Missing StaffProfile: {missing_profile}")

if missing_profile > 0:
    print(f"\n⚠️  Run 'python manage.py fix_shift_setup' to create missing profiles")
else:
    print(f"\n✓ All teachers have StaffProfile - Shift system ready!")

print("\nTesting shift endpoint compatibility:")
print("-" * 70)

for teacher in teachers:
    try:
        profile = StaffProfile.objects.get(user=teacher, user__role='teacher')
        print(f"✓ Shift endpoints will work for: {teacher.get_full_name()}")
    except StaffProfile.DoesNotExist:
        print(f"✗ Shift endpoints will FAIL for: {teacher.get_full_name()}")

print("=" * 70)
