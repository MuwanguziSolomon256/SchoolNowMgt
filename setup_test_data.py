#!/usr/bin/env python
"""Setup test data for teacher sub-dashboards testing"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import School, CustomUser, StaffProfile, ClassGrade, Subject, Timetable, Student
from django.utils import timezone
from datetime import date

# Check if teacher exists
teacher = CustomUser.objects.filter(role='teacher').first()
if teacher:
    print(f"✓ Teacher found: {teacher.get_full_name()}")
    print(f"  School: {teacher.school}")
    
    # Check StaffProfile
    try:
        staff = StaffProfile.objects.get(user=teacher)
        print(f"✓ StaffProfile exists")
    except:
        print(f"✗ No StaffProfile - creating one...")
        staff = StaffProfile.objects.create(
            user=teacher,
            employee_id=f"EMP{teacher.id:04d}",
            position='Class Teacher',
            salary=30000.00,
            date_joined=date.today(),
            is_full_time=True
        )
        print(f"✓ StaffProfile created")
    
    # Check ClassGrade with class_teacher
    classes_as_teacher = ClassGrade.objects.filter(class_teacher=staff)
    print(f"  Classes as teacher: {classes_as_teacher.count()}")
    
    # If no classes, create one
    if not classes_as_teacher.exists():
        print(f"✗ No classes assigned as teacher - creating test data...")
        school = teacher.school
        cls, created = ClassGrade.objects.get_or_create(
            name='Form 1A',
            school=school,
            defaults={
                'class_teacher': staff,
                'level': 1
            }
        )
        if created:
            cls.class_teacher = staff
            cls.save()
            print(f"✓ ClassGrade created: {cls}")
        else:
            cls.class_teacher = staff
            cls.save()
            print(f"✓ ClassGrade exists (updated teacher): {cls}")
        
        # Add a subject and timetable
        subject = Subject.objects.first()
        if not subject:
            subject = Subject.objects.create(name='Mathematics', code='MAT')
        timetable, _ = Timetable.objects.get_or_create(
            class_grade=cls,
            subject=subject,
            day_of_week='monday',
            defaults={
                'teacher': staff,
                'start_time': '09:00',
                'end_time': '10:00'
            }
        )
        print(f"✓ Timetable created for {subject.name}")
        
        # Create test students
        for i in range(3):
            student, created = Student.objects.get_or_create(
                admission_number=f"STU{cls.id}{i+1:03d}",
                defaults={
                    'first_name': f"Student{i+1}",
                    'last_name': "Test",
                    'date_of_birth': date(2008, 1, 1),
                    'gender': 'M',
                    'class_grade': cls,
                    'status': 'active'
                }
            )
            if created:
                print(f"✓ Student created: {student.full_name}")
            else:
                print(f"✓ Student exists: {student.full_name}")
else:
    print("✗ No teacher found in database")

print("\n✓ Test data setup complete!")
