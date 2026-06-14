#!/usr/bin/env python
"""Setup test data for Sarah Jenkins"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import CustomUser, StaffProfile, ClassGrade, Subject, Timetable, Student
from datetime import date

sarah = CustomUser.objects.get(id=16)  # Sarah Jenkins
print(f'Creating StaffProfile for: {sarah.get_full_name()}')

# Create StaffProfile
staff, created = StaffProfile.objects.get_or_create(
    user=sarah,
    defaults={
        'employee_id': f'EMP{sarah.id:04d}',
        'position': 'Class Teacher',
        'salary': 30000.00,
        'date_joined': date.today(),
        'is_full_time': True
    }
)
status1 = 'created' if created else 'already exists'
print(f'StaffProfile: {status1}')

# Create ClassGrade if not exists
cls, created = ClassGrade.objects.get_or_create(
    name='Form 1A',
    school=sarah.school,
    defaults={
        'class_teacher': staff,
        'level': 1,
        'capacity': 45
    }
)
status2 = 'created' if created else 'already exists'
print(f'ClassGrade: {status2}: {cls}')

# Create Subject and Timetable if not exists
subject, created = Subject.objects.get_or_create(
    code='MAT',
    defaults={'name': 'Mathematics'}
)
status3 = 'created' if created else 'already exists'
print(f'Subject: {status3}: {subject}')

timetable, created = Timetable.objects.get_or_create(
    class_grade=cls,
    subject=subject,
    teacher=staff,
    day_of_week='monday',
    defaults={
        'start_time': '09:00',
        'end_time': '10:00'
    }
)
status4 = 'created' if created else 'already exists'
print(f'Timetable: {status4}')

# Create Students
for i in range(3):
    student, created = Student.objects.get_or_create(
        admission_number=f'STU{cls.id}{i+1:03d}',
        defaults={
            'first_name': f'Student{i+1}',
            'last_name': 'Test',
            'date_of_birth': date(2008, 1, 1),
            'gender': 'M',
            'class_grade': cls,
            'status': 'active'
        }
    )
    status5 = 'created' if created else 'already exists'
    print(f'Student {i+1}: {status5}: {student.full_name}')

print('\n✓ Sarah Jenkins test data setup complete!')
