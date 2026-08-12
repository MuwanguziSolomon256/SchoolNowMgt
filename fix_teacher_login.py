import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')

import django
django.setup()

from django.contrib.auth import get_user_model, authenticate
from SchoolNowMgt.models import School

User = get_user_model()

school = School.objects.first()
if school is None:
    school = School.objects.create(
        name='Default School',
        registration_number='DEF-001',
        address='Main Campus',
        phone='+256700000000',
        email='school@example.com',
    )

user = User.objects.filter(email='teacher@test.com').first()
if user is None:
    user = User.objects.create_user(
        username='teacher_test',
        email='teacher@test.com',
        password='password123',
        school=school,
        role='teacher',
        first_name='Teacher',
        last_name='Test',
    )

user.username = user.username or 'teacher_test'
user.role = 'teacher'
user.school = user.school or school
user.is_active = True
user.set_password('password123')
user.save()

print('username=', user.username)
print('email=', user.email)
print('role=', user.role)
print('active=', user.is_active)
print('check_password=', user.check_password('password123'))
auth = authenticate(username=user.username, password='password123')
print('auth_user=', auth.username if auth else None)
print('auth_is_not_none=', auth is not None)
