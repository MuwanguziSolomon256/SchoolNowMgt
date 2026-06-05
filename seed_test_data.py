"""
Script to create test data for teacher dashboard testing
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from django.contrib.auth import get_user_model
from SchoolNowMgt.models import School, StaffProfile, CustomUser, TeacherTask, ActivityLog
from datetime import datetime, timedelta
from django.utils import timezone

# Get or create school
school, _ = School.objects.get_or_create(
    name='Test School',
    defaults={
        'registration_number': 'TS001',
        'address': '123 Test St',
        'phone': '+256700000000',
        'email': 'school@test.com'
    }
)

# Create or get teacher user
teacher_user, created = CustomUser.objects.get_or_create(
    username='teacher1',
    defaults={
        'email': 'teacher@test.com',
        'first_name': 'Sarah',
        'last_name': 'Jenkins',
        'role': 'teacher',
        'school': school
    }
)

if created:
    teacher_user.set_password('password123')
    teacher_user.save()
    print(f"Created teacher user: {teacher_user.username}")
else:
    print(f"Teacher user already exists: {teacher_user.username}")

# Get or create staff profile
staff_profile, staff_created = StaffProfile.objects.get_or_create(
    user=teacher_user,
    defaults={
        'employee_id': 'TE001',
        'position': 'Senior Physics Teacher',
        'qualification': 'BSc Physics, MEd',
        'salary': 2500000,
        'date_joined': timezone.now().date()
    }
)

if staff_created:
    print(f"Created staff profile for {teacher_user.get_full_name()}")
else:
    print(f"Staff profile already exists for {teacher_user.get_full_name()}")

# Create sample tasks
task1, _ = TeacherTask.objects.get_or_create(
    teacher=staff_profile,
    title='Grade Term Papers',
    defaults={
        'description': 'Physics Grade 12 papers',
        'due_date': timezone.now() + timedelta(hours=4),
        'priority': 'high',
        'status': 'pending'
    }
)

task2, _ = TeacherTask.objects.get_or_create(
    teacher=staff_profile,
    title='Upload Lecture Slides',
    defaults={
        'description': 'Astrophysics slides for next lesson',
        'due_date': timezone.now() + timedelta(days=1),
        'priority': 'medium',
        'status': 'pending'
    }
)

task3, _ = TeacherTask.objects.get_or_create(
    teacher=staff_profile,
    title='Attendance Sync',
    defaults={
        'description': 'Sync attendance records',
        'due_date': timezone.now() - timedelta(hours=2),
        'priority': 'low',
        'status': 'completed'
    }
)

print(f"Created {TeacherTask.objects.filter(teacher=staff_profile).count()} tasks")

# Create sample activities
activity1, _ = ActivityLog.objects.get_or_create(
    teacher=staff_profile,
    activity_type='quiz_submission',
    defaults={
        'description': 'Liam Carter submitted Quiz 3',
        'icon_name': 'assignment',
        'severity': 'info'
    }
)

activity2, _ = ActivityLog.objects.get_or_create(
    teacher=staff_profile,
    activity_type='message',
    defaults={
        'description': 'New message from Principal',
        'icon_name': 'mail',
        'severity': 'warning'
    }
)

activity3, _ = ActivityLog.objects.get_or_create(
    teacher=staff_profile,
    activity_type='system_backup',
    defaults={
        'description': 'System backup completed',
        'icon_name': 'backup',
        'severity': 'success'
    }
)

print(f"Created {ActivityLog.objects.filter(teacher=staff_profile).count()} activities")
print("\n✓ Test data created successfully!")
print(f"Login with: teacher@test.com / password123")
