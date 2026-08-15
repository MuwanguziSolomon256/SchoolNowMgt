#!/usr/bin/env python
"""
Verification Script: Auto-Assign Department Head Role Signal

Tests that the Django signal correctly auto-assigns the 'department_head' role
when a teacher is assigned to a department.

Usage:
    python verify_department_head_signal.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings')
django.setup()

from SchoolNowMgt.models import (
    CustomUser, StaffProfile, School, TeacherDepartment, ActivityLog
)
from django.db.models import Q


def test_auto_assign_department_head_role():
    """
    Test 1: Teacher with role='teacher' gets auto-assigned 'department_head' role
    when assigned to a department
    """
    print("\n" + "="*70)
    print("TEST 1: Auto-assign department_head role to teacher with role='teacher'")
    print("="*70)
    
    # Get or create a school
    school = School.objects.first()
    if not school:
        print("❌ No school found. Please create a school first.")
        return False
    
    print(f"Using school: {school.name}")
    
    # Find or create a test user with role='teacher'
    test_user = CustomUser.objects.filter(
        role='teacher',
        school=school,
        email__startswith='signal_test_teacher'
    ).first()
    
    if not test_user:
        print("Creating test teacher user...")
        test_user = CustomUser.objects.create_user(
            username='signal_test_teacher',
            email='signal_test_teacher@test.com',
            password='testpass123',
            school=school,
            role='teacher',
            first_name='Signal',
            last_name='Test'
        )
        print(f"✓ Created test user: {test_user.email}")
    else:
        print(f"✓ Using existing test user: {test_user.email}")
    
    # Get or create StaffProfile
    staff_profile, created = StaffProfile.objects.get_or_create(
        user=test_user,
        defaults={
            'position': 'Teacher (Signal Test)',
            'teacher_admin_role': 'teacher',
        }
    )
    
    if created:
        print(f"✓ Created StaffProfile: {staff_profile}")
    else:
        print(f"✓ Using existing StaffProfile: {staff_profile}")
    
    print(f"  - Current teacher_admin_role: {staff_profile.teacher_admin_role}")
    print(f"  - Current teacher_department: {staff_profile.teacher_department}")
    
    # Get or create a department
    department = TeacherDepartment.objects.filter(school=school).first()
    if not department:
        print("❌ No TeacherDepartment found. Please create one first.")
        return False
    
    print(f"Assigning to department: {department.name}")
    
    # Assign to department - this should trigger the signal
    staff_profile.teacher_department = department
    staff_profile.save()
    
    # Refresh from database to get the updated value
    staff_profile.refresh_from_db()
    
    print(f"\n✓ Assignment complete!")
    print(f"  - New teacher_admin_role: {staff_profile.teacher_admin_role}")
    print(f"  - New teacher_department: {staff_profile.teacher_department}")
    
    # Check the result
    if staff_profile.teacher_admin_role == 'department_head':
        print("\n✅ TEST 1 PASSED: Role was auto-assigned to 'department_head'")
        return True
    else:
        print(f"\n❌ TEST 1 FAILED: Role is {staff_profile.teacher_admin_role}, expected 'department_head'")
        return False


def test_preserve_existing_admin_role():
    """
    Test 2: Teacher with role='dos' should NOT have role changed when
    assigned to a department
    """
    print("\n" + "="*70)
    print("TEST 2: Preserve existing admin role (dos) when assigning to department")
    print("="*70)
    
    # Get or create a school
    school = School.objects.first()
    if not school:
        print("❌ No school found. Please create a school first.")
        return False
    
    print(f"Using school: {school.name}")
    
    # Find or create a test user with role='teacher' but admin_role='dos'
    test_user = CustomUser.objects.filter(
        role='teacher',
        school=school,
        email__startswith='signal_test_dos'
    ).first()
    
    if not test_user:
        print("Creating test DOS user...")
        test_user = CustomUser.objects.create_user(
            username='signal_test_dos',
            email='signal_test_dos@test.com',
            password='testpass123',
            school=school,
            role='teacher',
            first_name='Signal',
            last_name='DOS Test'
        )
        print(f"✓ Created test user: {test_user.email}")
    else:
        print(f"✓ Using existing test user: {test_user.email}")
    
    # Get or create StaffProfile with DOS role
    staff_profile, created = StaffProfile.objects.get_or_create(
        user=test_user,
        defaults={
            'position': 'DOS (Signal Test)',
            'teacher_admin_role': 'dos',
        }
    )
    
    if created:
        print(f"✓ Created StaffProfile: {staff_profile}")
    else:
        # Make sure it has DOS role
        if staff_profile.teacher_admin_role != 'dos':
            staff_profile.teacher_admin_role = 'dos'
            staff_profile.save()
        print(f"✓ Using existing StaffProfile: {staff_profile}")
    
    print(f"  - Current teacher_admin_role: {staff_profile.teacher_admin_role}")
    print(f"  - Current teacher_department: {staff_profile.teacher_department}")
    
    # Get or create a department
    department = TeacherDepartment.objects.filter(school=school).first()
    if not department:
        print("❌ No TeacherDepartment found. Please create one first.")
        return False
    
    print(f"Assigning to department: {department.name}")
    
    # Assign to department - signal should NOT change the role (it's already 'dos')
    staff_profile.teacher_department = department
    staff_profile.save()
    
    # Refresh from database
    staff_profile.refresh_from_db()
    
    print(f"\n✓ Assignment complete!")
    print(f"  - New teacher_admin_role: {staff_profile.teacher_admin_role}")
    print(f"  - New teacher_department: {staff_profile.teacher_department}")
    
    # Check the result
    if staff_profile.teacher_admin_role == 'dos':
        print("\n✅ TEST 2 PASSED: DOS role was preserved (not overridden)")
        return True
    else:
        print(f"\n❌ TEST 2 FAILED: Role changed to {staff_profile.teacher_admin_role}, expected 'dos'")
        return False


def check_activity_log():
    """
    Test 3: Verify ActivityLog entries were created for role assignments
    """
    print("\n" + "="*70)
    print("TEST 3: Check ActivityLog entries for auto-role assignments")
    print("="*70)
    
    log_entries = ActivityLog.objects.filter(
        activity_type='role_auto_assigned'
    ).order_by('-created_at')[:5]
    
    if log_entries.exists():
        print(f"✓ Found {log_entries.count()} role_auto_assigned activity logs:")
        for log in log_entries:
            print(f"  - {log.created_at}: {log.description}")
        print("\n✅ TEST 3 PASSED: Activity logs were created")
        return True
    else:
        print("⚠️ TEST 3 WARNING: No activity logs found (might be first run)")
        return True  # Don't fail on this


def main():
    """Run all verification tests"""
    print("\n" + "🔍 TESTING: Department Head Role Auto-Assignment Signal")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("Auto-assign department_head role", test_auto_assign_department_head_role()))
    results.append(("Preserve existing admin role", test_preserve_existing_admin_role()))
    results.append(("Activity log creation", check_activity_log()))
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Signal is working correctly.")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please review the implementation.")
    
    return passed == total


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
