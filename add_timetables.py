#!/usr/bin/env python
"""Add timetable entries for teacher"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import StaffProfile, Timetable, Subject, ClassGrade, CustomUser

# Get Sarah teacher
teacher_user = CustomUser.objects.filter(username='teacher1').first()
if not teacher_user:
    print("Teacher 'sarah' not found")
    exit(1)

try:
    staff = StaffProfile.objects.get(user=teacher_user)
    print(f"Found teacher: {staff.user.get_full_name()}")
except:
    print("StaffProfile not found for sarah")
    exit(1)

# Get the class
cls = ClassGrade.objects.filter(class_teacher=staff).first()
if not cls:
    print(f"No classes assigned to {staff.user.get_full_name()}")
    exit(1)

print(f"Found class: {cls.name}")

# Create or get subjects
subjects_to_create = [
    {'name': 'English Language', 'code': 'ENG'},
    {'name': 'Mathematics', 'code': 'MAT'},
    {'name': 'Science', 'code': 'SCI'},
]

for subj_data in subjects_to_create:
    subject, created = Subject.objects.get_or_create(
        code=subj_data['code'],
        defaults={'name': subj_data['name']}
    )
    print(f"{'Created' if created else 'Found'} subject: {subject.name}")
    
    # Create timetable - one for each subject on different days
    day_time_map = {
        'ENG': ('monday', '09:00', '10:00'),
        'MAT': ('wednesday', '10:00', '11:00'),
        'SCI': ('friday', '11:00', '12:00'),
    }
    
    if subj_data['code'] in day_time_map:
        day, start, end = day_time_map[subj_data['code']]
        timetable, created = Timetable.objects.get_or_create(
            teacher=staff,
            subject=subject,
            class_grade=cls,
            day_of_week=day,
            defaults={
                'start_time': start,
                'end_time': end
            }
        )
        if created:
            print(f"  Created timetable: {day} {start}-{end}")
        else:
            print(f"  Timetable already exists: {day} {start}-{end}")

print("\nDone!")
