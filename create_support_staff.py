"""
Create support staff test user
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import School, CustomUser, StaffProfile
from django.utils import timezone
from datetime import date

# Get or create school
school = School.objects.first() or School.objects.create(
    name='Test School',
    registration_number='TS001',
    address='123 Test St',
    phone='+256700000000',
    email='school@test.com'
)

# Delete existing user if present
CustomUser.objects.filter(email='staff@test.com').delete()

# Create support staff user
user = CustomUser.objects.create_user(
    username='staff_test',
    email='staff@test.com',
    password='password123',
    first_name='Support',
    last_name='Staff',
    role='non_teaching_staff',
    school=school
)

# Create staff profile
StaffProfile.objects.create(
    user=user,
    employee_id='STAFF001',
    position='Support Staff',
    qualification='High School',
    salary=500000,
    date_joined=date.today(),
    is_full_time=True
)

print(f'✓ Support staff user created!')
print(f'Email: {user.email}')
print(f'Password: password123')
print(f'Role: {user.role}')
