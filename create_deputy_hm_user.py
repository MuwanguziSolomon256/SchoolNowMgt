#!/usr/bin/env python
import sys
import os

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings')
django.setup()

from authentication.models import CustomUser
from SchoolNowMgt.models import StaffProfile, School

# Get or create default school
school, created = School.objects.get_or_create(
    name='Default School',
    defaults={'location': 'Default'}
)
print(f"\nSchool: {school.name} (ID: {school.id})")

# Check for Deputy HM user
print("\n" + "="*80)
print("CHECKING FOR DEPUTY HM USER")
print("="*80)

deputy_user = CustomUser.objects.filter(email='deputy_hm@test.com').first()

if deputy_user:
    print(f"✓ Deputy HM user exists: {deputy_user.email}")
    try:
        profile = StaffProfile.objects.get(user=deputy_user)
        print(f"  Profile exists - Teacher Admin Role: {profile.teacher_admin_role}")
    except StaffProfile.DoesNotExist:
        print(f"  ✗ No StaffProfile - creating one...")
        profile = StaffProfile.objects.create(
            user=deputy_user,
            teacher_admin_role='deputy_hm',
            employee_id='DEPUTY001',
            position='Deputy Headmaster',
            salary=45000.00
        )
        print(f"  ✓ StaffProfile created with teacher_admin_role='deputy_hm'")
else:
    print(f"✗ Deputy HM user doesn't exist - creating one...")
    deputy_user = CustomUser.objects.create_user(
        email='deputy_hm@test.com',
        username='deputy_hm_test',
        first_name='Deputy',
        last_name='Headmaster',
        password='TestPassword123!',
        role='teacher',
        school=school
    )
    print(f"✓ User created: {deputy_user.email}")
    
    # Create StaffProfile
    profile = StaffProfile.objects.create(
        user=deputy_user,
        teacher_admin_role='deputy_hm',
        employee_id='DEPUTY001',
        position='Deputy Headmaster',
        salary=45000.00
    )
    print(f"✓ StaffProfile created with teacher_admin_role='deputy_hm'")

print("\n" + "="*80)
print("DEPUTY HM USER DETAILS")
print("="*80)
print(f"Email: {deputy_user.email}")
print(f"Username: {deputy_user.username}")
print(f"Password: TestPassword123!")
print(f"Role: {deputy_user.role}")
print(f"School: {deputy_user.school.name}")
print(f"Admin Role: {profile.teacher_admin_role}")
