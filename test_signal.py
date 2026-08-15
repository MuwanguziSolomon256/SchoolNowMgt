#!/usr/bin/env python
"""
Simple test to verify the department head auto-assignment signal works.
This uses Django's shell infrastructure to properly initialize Django.

Usage:
    python manage.py shell < test_signal.py
"""

from SchoolNowMgt.models import (
    CustomUser, StaffProfile, School, TeacherDepartment, ActivityLog
)

print("\n" + "="*70)
print("Testing Department Head Auto-Assignment Signal")
print("="*70)

# Get a school
school = School.objects.first()
if not school:
    print("❌ No school found.")
    exit(1)

print(f"\n✓ Using school: {school.name}")

# Create or get a test teacher
test_user, created = CustomUser.objects.get_or_create(
    username='dept_head_test_user',
    defaults={
        'email': 'dept_head_test@example.com',
        'first_name': 'Test',
        'last_name': 'Teacher',
        'role': 'teacher',
        'school': school,
    }
)
print(f"{'✓ Created' if created else '✓ Using'} test user: {test_user.email}")

# Get or create StaffProfile
staff_profile, created = StaffProfile.objects.get_or_create(
    user=test_user,
    defaults={
        'position': 'Teacher (Test)',
        'teacher_admin_role': 'teacher',
    }
)
print(f"{'✓ Created' if created else '✓ Using'} StaffProfile")
print(f"  - Role before assignment: {staff_profile.teacher_admin_role}")
print(f"  - Department before assignment: {staff_profile.teacher_department}")

# Get a department
dept = TeacherDepartment.objects.filter(school=school).first()
if not dept:
    print("❌ No TeacherDepartment found. Cannot test.")
    exit(1)

print(f"\nAssigning teacher to department: {dept.name}")

# Assign to department (this should trigger the signal)
staff_profile.teacher_department = dept
staff_profile.save()

# Refresh from DB
staff_profile.refresh_from_db()

print(f"\n✓ Assignment complete!")
print(f"  - Role after assignment: {staff_profile.teacher_admin_role}")
print(f"  - Department after assignment: {staff_profile.teacher_department}")

# Check result
if staff_profile.teacher_admin_role == 'department_head':
    print("\n✅ SUCCESS: Role was auto-assigned to 'department_head'!")
else:
    print(f"\n❌ FAILED: Role is still '{staff_profile.teacher_admin_role}'")

# Check ActivityLog
logs = ActivityLog.objects.filter(
    activity_type='role_auto_assigned',
    teacher=staff_profile
).order_by('-created_at')

if logs.exists():
    print(f"\n✓ Activity logs created:")
    for log in logs[:3]:
        print(f"  - {log.created_at}: {log.description}")
else:
    print(f"\n⚠️ No activity logs found (might be expected)")

print("\n" + "="*70)
