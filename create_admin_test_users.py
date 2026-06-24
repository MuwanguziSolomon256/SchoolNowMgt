"""
Script to create test user accounts for administrative role testing
"""
import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import CustomUser, School, StaffProfile, TeacherDepartment, Department
from django.db import transaction

# Get or create test school
school, _ = School.objects.get_or_create(
    name='Test School',
    defaults={'registration_number': 'TS001', 'address': 'Test Address', 'phone': '+256700000000', 'email': 'test@school.com'}
)
print(f"✓ School: {school.name} (ID: {school.id})")

test_accounts = []

try:
    with transaction.atomic():
        # 1. DOS User
        dos_user, created = CustomUser.objects.get_or_create(
            username='test_dos',
            defaults={
                'email': 'dos@test.com',
                'first_name': 'Director',
                'last_name': 'Studies',
                'role': 'teacher',
                'school': school,
                'is_staff': True
            }
        )
        if created:
            dos_user.set_password('password123')
            dos_user.save()
        # Always ensure staff profile exists
        staff_profile, _ = StaffProfile.objects.get_or_create(
            user=dos_user,
            defaults={
                'employee_id': 'EMP_DOS_001',
                'position': 'Director of Studies',
                'salary': 0,
                'date_joined': date.today(),
                'teacher_admin_role': 'dos'
            }
        )
        print(f"✓ DOS user: {dos_user.email}")
        test_accounts.append(('DOS', dos_user.email, 'password123'))

        # 2. Deputy HM User
        deputy_user, created = CustomUser.objects.get_or_create(
            username='test_deputy_hm',
            defaults={
                'email': 'deputy@test.com',
                'first_name': 'Deputy',
                'last_name': 'Headmaster',
                'role': 'teacher',
                'school': school,
                'is_staff': True
            }
        )
        if created:
            deputy_user.set_password('password123')
            deputy_user.save()
        staff_profile, _ = StaffProfile.objects.get_or_create(
            user=deputy_user,
            defaults={
                'employee_id': 'EMP_DHM_001',
                'position': 'Deputy Headmaster',
                'salary': 0,
                'date_joined': date.today(),
                'teacher_admin_role': 'deputy_hm'
            }
        )
        print(f"✓ Deputy HM user: {deputy_user.email}")
        test_accounts.append(('Deputy HM', deputy_user.email, 'password123'))

        # 3. Matron User (Support Staff)
        matron_user, created = CustomUser.objects.get_or_create(
            username='test_matron',
            defaults={
                'email': 'matron@test.com',
                'first_name': 'Matron',
                'last_name': 'Staff',
                'role': 'non_teaching_staff',
                'school': school,
                'is_staff': False
            }
        )
        if created:
            matron_user.set_password('password123')
            matron_user.save()
        dept, _ = Department.objects.get_or_create(
            school=school,
            name='Hostels',
            defaults={'department_type': 'matron', 'is_active': True}
        )
        staff_profile, _ = StaffProfile.objects.get_or_create(
            user=matron_user,
            defaults={
                'employee_id': 'EMP_MAT_001',
                'position': 'Matron',
                'salary': 0,
                'date_joined': date.today(),
                'support_department': dept,
                'support_staff_role': 'welfare_coordinator'
            }
        )
        print(f"✓ Matron user: {matron_user.email}")
        test_accounts.append(('Matron/Welfare', matron_user.email, 'password123'))

        # 4. Subject Dept Head User (Teacher)
        dept_head_user, created = CustomUser.objects.get_or_create(
            username='test_dept_head',
            defaults={
                'email': 'depthead@test.com',
                'first_name': 'Department',
                'last_name': 'Head',
                'role': 'teacher',
                'school': school,
                'is_staff': True
            }
        )
        if created:
            dept_head_user.set_password('password123')
            dept_head_user.save()
        teacher_dept, _ = TeacherDepartment.objects.get_or_create(
            school=school,
            name='Mathematics',
            defaults={'department_type': 'mathematics', 'is_active': True}
        )
        staff_profile, _ = StaffProfile.objects.get_or_create(
            user=dept_head_user,
            defaults={
                'employee_id': 'EMP_DH_001',
                'position': 'Subject Department Head',
                'salary': 0,
                'date_joined': date.today(),
                'teacher_admin_role': 'department_head',
                'teacher_department': teacher_dept
            }
        )
        print(f"✓ Subject Dept Head user: {dept_head_user.email}")
        test_accounts.append(('Subject Dept Head', dept_head_user.email, 'password123'))

    print("\n" + "="*70)
    print("TEST CREDENTIALS FOR ADMIN ROLE TESTING")
    print("="*70)
    print(f"{'Role':<20} | {'Email':<25} | {'Password':<15}")
    print("-"*70)
    for role, email, password in test_accounts:
        print(f"{role:<20} | {email:<25} | {password:<15}")
    print("="*70)
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
