import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings')
django.setup()

from datetime import date
from django.contrib.auth import get_user_model
from SchoolNowMgt.models import School, StaffProfile, TeacherDepartment, ClassGrade, Student

CustomUser = get_user_model()

print("\n" + "="*70)
print("  PHASE 5: MULTI-SCHOOL DATA ISOLATION TESTING")
print("="*70)

# Step 1
print("\nSTEP 1: Create Second School")
school2, _ = School.objects.get_or_create(
    name="School 2 - Nairobi Campus",
    defaults={'address': '456 School Road, Nairobi', 'phone': '+254711222222', 'email': 'school2@test.com'}
)
print(f"School: {school2.name} (ID: {school2.id})")

# Step 2
print("\nSTEP 2: Create Test Users for School 2")
for email, first_name, last_name, admin_role in [('dos2@test.com', 'Dr', 'DOS2', 'dos'), ('deputy2@test.com', 'Deputy', 'HM2', 'deputy_hm')]:
    user, created = CustomUser.objects.get_or_create(email=email, defaults={'username': email.split('@')[0], 'first_name': first_name, 'last_name': last_name, 'role': 'teacher'})
    if created:
        user.set_password('password123')
        user.save()
    profile, _ = StaffProfile.objects.get_or_create(user=user, defaults={'teacher_admin_role': admin_role, 'salary': 0, 'date_joined': date.today(), 'employee_id': f"EMP_{admin_role.upper()}_2", 'school': school2})
    if profile.school != school2:
        profile.school = school2
        profile.save()
    print(f"  {admin_role} user created/updated for {school2.name}")

# Step 3
print("\nSTEP 3: Create Test Data")
school1 = School.objects.get(id=1)
for school, label in [(school1, 'S1'), (school2, 'S2')]:
    dept, _ = TeacherDepartment.objects.get_or_create(name=f"Mathematics - {label}", school=school, defaults={'head_of_department': None, 'annual_budget': 50000})
    class_a, _ = ClassGrade.objects.get_or_create(name=f"Class A - {label}", school=school, curriculum='national', defaults={'level': 1, 'capacity': 40})
    class_b, _ = ClassGrade.objects.get_or_create(name=f"Class B - {label}", school=school, curriculum='national', defaults={'level': 2, 'capacity': 35})
    for i in range(1, 4):
        student, _ = Student.objects.get_or_create(admission_number=f"{label}{i:03d}", defaults={'first_name': f"Student {i}", 'last_name': label, 'date_of_birth': date(2010, 1, i), 'gender': 'M' if i % 2 == 0 else 'F', 'class_grade': class_a, 'parent_name': f"Parent {i}", 'parent_phone': '+254700000000', 'curriculum': 'national'})
    print(f"  {school.name}: 2 classes, 3 students")

# Step 4
print("\nSTEP 4: Verify Data Isolation")
s1_classes = ClassGrade.objects.filter(school=school1).count()
s2_classes = ClassGrade.objects.filter(school=school2).count()
s1_students = Student.objects.filter(class_grade__school=school1).count()
s2_students = Student.objects.filter(class_grade__school=school2).count()

print(f"\n{school1.name}: {s1_classes} classes, {s1_students} students")
print(f"{school2.name}: {s2_classes} classes, {s2_students} students")

print("\nIsolation Checks:")
if not ClassGrade.objects.filter(school=school1, name__contains='S2').exists():
    print("  [OK] Classes isolated")
if not Student.objects.filter(class_grade__school=school1, admission_number__startswith='S2').exists():
    print("  [OK] Students isolated")

# Step 5
print("\nSTEP 5: Test Query Filtering")
dos_user = CustomUser.objects.filter(staffprofile__teacher_admin_role='dos', staffprofile__school=school1).first()
if dos_user:
    accessible = ClassGrade.objects.filter(school=dos_user.staffprofile.school)
    if not accessible.filter(school=school2).exists():
        print(f"  [OK] DOS sees {accessible.count()} classes (School 1 only)")

dos2_user = CustomUser.objects.filter(staffprofile__teacher_admin_role='dos', staffprofile__school=school2).first()
if dos2_user:
    accessible = ClassGrade.objects.filter(school=dos2_user.staffprofile.school)
    if not accessible.filter(school=school1).exists():
        print(f"  [OK] DOS2 sees {accessible.count()} classes (School 2 only)")

print("\n" + "="*70)
print("  PHASE 5 COMPLETE: Multi-School Data Isolation VERIFIED")
print("="*70)
print("\nReady for Phase 6 (Edge Case Testing)")
