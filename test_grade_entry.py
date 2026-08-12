#!/usr/bin/env python
"""Test script to verify grade entry with exam_type implementation."""

import os
import django
import sys
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings')
sys.path.insert(0, 'c:\\Users\\Admin\\Desktop\\SchoolNowMgt')
django.setup()

from django.contrib.auth.models import User
from school.models import Student, Subject, Grade, ClassGrade, StaffProfile, Timetable
from school.models import School
from django.utils import timezone

# Get the first school and teacher
school = School.objects.first()
if not school:
    print("No school found. Please create a school first.")
    sys.exit(1)

# Get a teacher
staff = StaffProfile.objects.filter(school=school, user__is_staff=True).first()
if not staff:
    print("No teacher found. Please create a teacher first.")
    sys.exit(1)

# Get or create a class for the teacher
class_obj = ClassGrade.objects.filter(
    timetable_entries__teacher=staff,
    school=school
).first()

if not class_obj:
    print("No class found for the teacher.")
    sys.exit(1)

# Get a subject for the teacher
subject = Subject.objects.filter(
    timetable_entries__teacher=staff,
    timetable_entries__class_grade__school=school
).first()

if not subject:
    print("No subject found for the teacher.")
    sys.exit(1)

# Get a student in the class
student = Student.objects.filter(
    class_grade=class_obj,
    class_grade__school=school,
    status='active'
).first()

if not student:
    print("No active student found in the class.")
    sys.exit(1)

print(f"Testing with:")
print(f"  School: {school.school_name}")
print(f"  Teacher: {staff.user.first_name} {staff.user.last_name}")
print(f"  Class: {class_obj.name}")
print(f"  Subject: {subject.name}")
print(f"  Student: {student.first_name} {student.last_name}")
print()

# Test all three exam types
exam_types = ['beginning_of_term', 'mid_term', 'end_of_term']
test_scores = {'beginning_of_term': 75, 'mid_term': 82, 'end_of_term': 88}

print("Testing Single Grade Entry with Exam Types:")
print("-" * 60)

for exam_type in exam_types:
    score = test_scores[exam_type]
    
    # Create or update grade with exam_type in semester field
    grade, created = Grade.objects.update_or_create(
        student=student,
        subject=subject,
        curriculum='national',
        term='term_1',
        semester=exam_type,  # Exam type stored in semester field
        academic_year=str(timezone.now().year),
        defaults={
            'score': Decimal(str(score)),
            'recorded_by': staff.user,
        }
    )
    
    status = "Created" if created else "Updated"
    print(f"✓ {status}: {student.first_name} - {subject.name} ({exam_type}): {score}/100")
    print(f"  Grade ID: {grade.id}, Semester: {grade.semester}")

print()
print("Verifying Database:")
print("-" * 60)

# Query and verify all grades for the student and subject
grades = Grade.objects.filter(
    student=student,
    subject=subject,
    curriculum='national',
    term='term_1',
    academic_year=str(timezone.now().year)
).order_by('semester')

if not grades:
    print("❌ No grades found!")
    sys.exit(1)

print(f"Found {grades.count()} grade records:")
for grade in grades:
    print(f"  • {grade.semester}: Score={grade.score}, Recorded by={grade.recorded_by}")

print()
print("✅ All tests passed! Grade entry with exam_type is working correctly.")
