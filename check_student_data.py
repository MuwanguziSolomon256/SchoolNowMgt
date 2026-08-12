#!/usr/bin/env python
"""Quick diagnostic to check student data in database"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import Student, StaffProfile, ClassGrade

# Get teacher staff profile
staff = StaffProfile.objects.get(user__email='teacher@test.com')

# Get classes assigned to teacher
classes = ClassGrade.objects.filter(class_teacher=staff)

print("=" * 80)
print("STUDENT DATA DIAGNOSTIC")
print("=" * 80)

for cls in classes:
    print(f"\nClass: {cls.name}")
    students = Student.objects.filter(class_grade=cls)
    print(f"Total students: {students.count()}")
    
    for student in students:
        print(f"\n  Student ID: {student.id}")
        print(f"  First Name: '{student.first_name}'")
        print(f"  Last Name: '{student.last_name}'")
        print(f"  Full Name: '{student.get_full_name()}'")
        print(f"  Admission Number: '{student.admission_number}'")
        print(f"  Status: {student.status}")
        print(f"  ---")

print("\n" + "=" * 80)
