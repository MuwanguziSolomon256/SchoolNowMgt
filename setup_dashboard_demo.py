#!/usr/bin/env python
"""
Setup script to create test users for dashboard demonstration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import CustomUser, School, StaffProfile, Student, ClassGrade, FeePayment, FeeStructure, Event
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

# Create a test school
school, created = School.objects.get_or_create(
    registration_number='TEST-SCHOOL-001',
    defaults={
        'name': 'Test Academy',
        'address': '123 Test Street',
        'phone': '+256700000000',
        'email': 'admin@testacademy.edu'
    }
)
print(f"School: {school.name} (created={created})")

# Delete existing test user to avoid conflicts
CustomUser.objects.filter(username='headmaster_test').delete()

# Create headmaster user
headmaster = CustomUser.objects.create_user(
    username='headmaster_test',
    email='headmaster@testacademy.edu',
    password='Headmaster@123',
    first_name='Dr.',
    last_name='Alistair',
    role='teacher',
    school=school
)
print(f"✓ Created headmaster user: {headmaster.email}")

# Create staff profile for headmaster
staff_profile, created = StaffProfile.objects.get_or_create(
    user=headmaster,
    defaults={
        'employee_id': 'HM-001',
        'position': 'Headmaster',
        'teacher_admin_role': 'head_teacher',
        'date_joined': timezone.now().date(),
        'salary': Decimal('5000000'),
    }
)
print(f"✓ Created staff profile (created={created})")

# Create test data for dashboard
# 1. Create class grades
classes = []
for i in range(1, 7):
    cls, created = ClassGrade.objects.get_or_create(
        name=f'Senior {i}',
        level=i,
        school=school,
        defaults={'curriculum': 'national'}
    )
    classes.append(cls)
    print(f"✓ Class: {cls.name}")

# 2. Create fee structure
for cls in classes[:2]:  # Just for first 2 classes
    FeeStructure.objects.get_or_create(
        class_grade=cls,
        term='term_1',
        academic_year='2024',
        defaults={
            'amount': Decimal('500000'),
            'description': 'Term 1 Tuition'
        }
    )

# 3. Create students (mix of day scholars and boarding)
for i in range(1, 11):
    curriculum = 'national' if i % 2 == 0 else 'international'
    Student.objects.get_or_create(
        admission_number=f'ADM-{i:04d}',
        defaults={
            'first_name': f'Student',
            'last_name': f'{i}',
            'date_of_birth': '2008-01-15',
            'gender': 'M' if i % 2 == 0 else 'F',
            'curriculum': curriculum,
            'class_grade': classes[i % len(classes)],
            'parent_name': f'Parent {i}',
            'parent_phone': '+256700000000',
            'status': 'active'
        }
    )

print(f"✓ Created 10 students")

# 4. Create fee payments (for financial dashboard data)
students = Student.objects.filter(class_grade__school=school)
for student in students[:5]:
    FeePayment.objects.get_or_create(
        student=student,
        fee_structure=FeeStructure.objects.filter(class_grade=student.class_grade).first(),
        defaults={
            'amount_paid': Decimal('450000'),
            'payment_date': timezone.now().date(),
            'payment_method': 'bank_transfer',
            'received_by': headmaster,
            'balance_after': Decimal('50000')
        }
    )

print(f"✓ Created fee payments")

# 5. Create events
today = timezone.now().date()
events_data = [
    ('Staff Inset Day', 'meeting', today, today),
    ('Governors Meeting', 'meeting', today + timedelta(days=1), today + timedelta(days=1)),
    ('Alumni Dinner', 'activity', today + timedelta(days=2), today + timedelta(days=2)),
    ('Science Fair 2024', 'activity', today + timedelta(days=7), today + timedelta(days=7)),
    ('Guest Lecture: AI', 'activity', today + timedelta(days=7), today + timedelta(days=7)),
]

for title, event_type, start_date, end_date in events_data:
    Event.objects.get_or_create(
        school=school,
        title=title,
        defaults={
            'event_type': event_type,
            'start_date': start_date,
            'end_date': end_date,
            'created_by': headmaster
        }
    )

print(f"✓ Created {len(events_data)} events")

print("\n" + "="*60)
print("✓✓✓ Setup Complete! ✓✓✓")
print("="*60)
print(f"\nLogin Credentials:")
print(f"  Email: {headmaster.email}")
print(f"  Username: {headmaster.username}")
print(f"  Password: Headmaster@123")
print(f"\nAccess Dashboard at:")
print(f"  http://127.0.0.1:8000/teacher/admin/head-teacher/headmaster/")
print("="*60)
