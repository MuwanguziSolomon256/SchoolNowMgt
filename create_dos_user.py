#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, r'c:\Users\Admin\Desktop\SchoolNowMgt')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SchoolNowMgt.settings')
django.setup()

from django.contrib.auth import get_user_model
from teacher.models import StaffProfile, TeacherProfile
from school.models import School

User = get_user_model()

print("=== Checking Existing Users ===")
for user in User.objects.filter(role='teacher'):
    try:
        sp = StaffProfile.objects.get(user=user)
        print(f"{user.username}: {sp.teacher_admin_role or 'regular teacher'}")
    except StaffProfile.DoesNotExist:
        print(f"{user.username}: No staff profile")

print("\n=== Creating DOS User ===")
school = School.objects.first()
if not school:
    print("ERROR: No school found in database")
    sys.exit(1)

print(f"Using school: {school.name}")

# Create a teacher user
username = 'dos_manager'
email = 'dos@school.local'
password = 'DosPass123!'

try:
    user = User.objects.get(username=username)
    print(f"User {username} already exists")
except User.DoesNotExist:
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        role='teacher',
        school=school
    )
    print(f"Created user: {username}")

# Create or update teacher profile
try:
    tp = TeacherProfile.objects.get(user=user)
    print(f"TeacherProfile already exists for {username}")
except TeacherProfile.DoesNotExist:
    tp = TeacherProfile.objects.create(user=user, school=school)
    print(f"Created TeacherProfile for {username}")

# Create or update staff profile with DOS role
try:
    sp = StaffProfile.objects.get(user=user)
    sp.teacher_admin_role = 'dos'
    sp.school = school
    sp.save()
    print(f"Updated StaffProfile for {username} with DOS role")
except StaffProfile.DoesNotExist:
    sp = StaffProfile.objects.create(
        user=user,
        teacher_admin_role='dos',
        school=school
    )
    print(f"Created StaffProfile for {username} with DOS role")

print(f"\n✓ DOS user created successfully!")
print(f"  Username: {username}")
print(f"  Password: {password}")
print(f"  Login at: http://127.0.0.1:8000/auth/")
