#!/usr/bin/env python
"""
Diagnostic & Assignment Script for Teacher Classes

Purpose:
1. Find teacher account by email
2. Verify StaffProfile exists
3. Show available classes in their school
4. Show which classes have students
5. Assign teacher to those classes
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import CustomUser, StaffProfile, ClassGrade, Student
from django.db.models import Count

# Teacher email we're looking for
TEACHER_EMAIL = 'teacher@test.com'

print("=" * 80)
print(f"DIAGNOSTIC & ASSIGNMENT: {TEACHER_EMAIL}")
print("=" * 80)

# Step 1: Find teacher account
print("\n[1] Finding teacher account...")
teacher = CustomUser.objects.filter(email=TEACHER_EMAIL).first()

if not teacher:
    print(f"✗ ERROR: No teacher found with email {TEACHER_EMAIL}")
    exit(1)

print(f"✓ Teacher found: {teacher.get_full_name() or teacher.email}")
print(f"  - User ID: {teacher.id}")
print(f"  - Role: {teacher.role}")
print(f"  - School: {teacher.school}")
print(f"  - Is Active: {teacher.is_active}")

# Step 2: Check StaffProfile
print("\n[2] Checking StaffProfile...")
try:
    staff = StaffProfile.objects.get(user=teacher)
    print(f"✓ StaffProfile exists")
    print(f"  - Employee ID: {staff.employee_id}")
    print(f"  - Position: {staff.position}")
    print(f"  - Teacher Admin Role: {staff.teacher_admin_role}")
except StaffProfile.DoesNotExist:
    print(f"✗ ERROR: No StaffProfile for this teacher")
    print(f"  Creating StaffProfile...")
    from SchoolNowMgt.registration.utils import generate_employee_id
    staff = StaffProfile.objects.create(
        user=teacher,
        employee_id=generate_employee_id(teacher.school),
        position='Teacher',
        salary=0,
        is_full_time=True
    )
    print(f"✓ StaffProfile created with employee_id: {staff.employee_id}")

# Step 3: List all classes in teacher's school
print("\n[3] Classes in your school...")
all_classes = ClassGrade.objects.filter(school=teacher.school).annotate(
    student_count=Count('students')
).order_by('level', 'name')

if not all_classes.exists():
    print("✗ No classes found in your school")
    exit(1)

print(f"Total classes: {all_classes.count()}")
for cls in all_classes:
    students_count = cls.students.count()
    current_teacher = cls.class_teacher.user.email if cls.class_teacher else "None"
    assigned_to_you = "✓ YOU" if cls.class_teacher == staff else ""
    print(f"  - {cls.name} (Level {cls.level}): {students_count} students | Teacher: {current_teacher} {assigned_to_you}")

# Step 4: Check currently assigned classes
print("\n[4] Your currently assigned classes...")
my_classes = ClassGrade.objects.filter(class_teacher=staff)
if my_classes.exists():
    print(f"✓ You are assigned to {my_classes.count()} class(es):")
    for cls in my_classes:
        print(f"  - {cls.name}: {cls.students.count()} students")
else:
    print("✗ Not assigned to any classes yet")

# Step 5: Get classes with students that you're NOT assigned to
print("\n[5] Available classes to assign (with students)...")
classes_to_assign = all_classes.exclude(class_teacher=staff).filter(students__status='active').distinct()

if not classes_to_assign.exists():
    print("✗ No classes with students available for assignment")
    print("\nTrying to assign ANY classes with students...")
    classes_to_assign = all_classes.filter(students__isnull=False).exclude(class_teacher=staff).distinct()

if classes_to_assign.exists():
    print(f"Found {classes_to_assign.count()} class(es) to assign:")
    for cls in classes_to_assign:
        print(f"  → {cls.name} ({cls.level}): {cls.students.count()} students")
else:
    print("✗ No classes with students found")
    print("\nStatus: There may not be any classes with students in your school.")
    print("Consider running: python setup_test_data.py")
    exit(1)

# Step 6: Assign teacher to classes
print("\n[6] ASSIGNING TEACHER TO CLASSES...")
assignments_made = 0
for cls in classes_to_assign:
    old_teacher = cls.class_teacher
    cls.class_teacher = staff
    cls.save()
    assignments_made += 1
    print(f"  ✓ Assigned to: {cls.name} ({cls.students.count()} students)")

print(f"\n✓ SUCCESS: Assigned to {assignments_made} class(es)")

# Step 7: Verify assignment
print("\n[7] VERIFICATION...")
my_classes_after = ClassGrade.objects.filter(class_teacher=staff)
total_students = Student.objects.filter(class_grade__class_teacher=staff, status='active').count()

print(f"✓ You are now assigned to {my_classes_after.count()} class(es)")
print(f"✓ Total active students visible: {total_students}")

if total_students > 0:
    print(f"\n✅ READY! Visit: http://127.0.0.1:8000/teacher/students/")
    print(f"   You should now see {total_students} student(s)")
else:
    print(f"\n⚠️  No active students found. Check student status.")

print("\n" + "=" * 80)
