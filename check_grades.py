#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import Grade, Student, Subject, CustomUser, StaffProfile

# Get the teacher
teacher_user = CustomUser.objects.filter(username='teacher1').first()
staff = StaffProfile.objects.get(user=teacher_user)

# Get the student and subject
alice = Student.objects.filter(first_name='Alice').first()
mathematics = Subject.objects.filter(code='MAT').first()

print(f"Checking grades for {alice.first_name if alice else 'Student not found'} in {mathematics.name if mathematics else 'Subject not found'}...")

if alice and mathematics:
    grades = Grade.objects.filter(student=alice, subject=mathematics).order_by('-created_at')
    print(f"Found {grades.count()} grades:")
    for g in grades:
        print(f"  Score: {g.score}, Created: {g.created_at}")
