"""
Create a fresh test teacher user with unique email
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import School, StaffProfile, CustomUser, TeacherTask, ActivityLog
from django.utils import timezone
from datetime import timedelta

# Delete any existing testteacher user
CustomUser.objects.filter(username='testteacher').delete()

# Get school
school = School.objects.first() or School.objects.create(
    name='Test School',
    registration_number='TS001',
    address='123 Test St',
    phone='+256700000000',
    email='school@test.com'
)

# Create teacher user with unique email
user = CustomUser.objects.create_user(
    username='testteacher',
    email='testteacher@example.com',
    password='testpass123',
    first_name='Test',
    last_name='Teacher',
    role='teacher',
    school=school
)

# Create staff profile
staff = StaffProfile.objects.create(
    user=user,
    employee_id='TT001',
    position='Physics Teacher',
    qualification='BSc Physics',
    salary=2000000,
    date_joined=timezone.now().date()
)

# Create sample tasks
TeacherTask.objects.create(
    teacher=staff,
    title='Grade Term Papers',
    description='Physics Grade 12 papers',
    due_date=timezone.now() + timedelta(hours=4),
    priority='high'
)

TeacherTask.objects.create(
    teacher=staff,
    title='Upload Lecture Slides',
    description='Astrophysics slides',
    due_date=timezone.now() + timedelta(days=1),
    priority='medium'
)

TeacherTask.objects.create(
    teacher=staff,
    title='Attendance Sync',
    description='Sync attendance',
    due_date=timezone.now() - timedelta(hours=2),
    priority='low',
    status='completed'
)

# Create activities
ActivityLog.objects.create(
    teacher=staff,
    activity_type='quiz_submission',
    description='Liam Carter submitted Quiz 3',
    icon_name='assignment',
    severity='info'
)

ActivityLog.objects.create(
    teacher=staff,
    activity_type='message',
    description='New message from Principal',
    icon_name='mail',
    severity='warning'
)

ActivityLog.objects.create(
    teacher=staff,
    activity_type='system_backup',
    description='System backup completed',
    icon_name='backup',
    severity='success'
)

print("✓ Fresh test user created!")
print(f"Email: {user.email}")
print(f"Password: testpass123")
