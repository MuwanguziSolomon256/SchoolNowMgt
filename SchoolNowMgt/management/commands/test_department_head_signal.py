"""
Management command to test the department head auto-assignment signal.

Usage:
    python manage.py test_department_head_signal
"""

from django.core.management.base import BaseCommand
from django.db.models import Q
from SchoolNowMgt.models import (
    CustomUser, StaffProfile, School, TeacherDepartment, ActivityLog
)


class Command(BaseCommand):
    help = 'Test the department head auto-assignment signal'

    def add_arguments(self, parser):
        parser.add_argument(
            '--school-id',
            type=int,
            help='ID of the school to test with (uses first school if not provided)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('Testing Department Head Auto-Assignment Signal'))
        self.stdout.write(self.style.SUCCESS('='*70))

        # Get school
        school_id = options.get('school_id')
        if school_id:
            school = School.objects.filter(id=school_id).first()
        else:
            school = School.objects.first()

        if not school:
            self.stdout.write(self.style.ERROR('❌ No school found.'))
            return

        self.stdout.write(f'\n✓ Using school: {school.name}')

        # Create or get test teacher
        test_user, created = CustomUser.objects.get_or_create(
            username='signal_test_dept_head',
            defaults={
                'email': 'signal_test_dept_head@test.com',
                'first_name': 'Signal',
                'last_name': 'Test',
                'role': 'teacher',
                'school': school,
            }
        )
        self.stdout.write(f"{'✓ Created' if created else '✓ Using'} test user: {test_user.email}")

        # Get or create StaffProfile
        staff_profile, created = StaffProfile.objects.get_or_create(
            user=test_user,
            defaults={
                'position': 'Teacher (Signal Test)',
                'teacher_admin_role': 'teacher',
            }
        )
        self.stdout.write(f"{'✓ Created' if created else '✓ Using'} StaffProfile")
        self.stdout.write(f"  - Role before assignment: {staff_profile.teacher_admin_role}")
        self.stdout.write(f"  - Department before: {staff_profile.teacher_department or 'None'}")

        # Get a department
        dept = TeacherDepartment.objects.filter(school=school).first()
        if not dept:
            self.stdout.write(self.style.ERROR(
                '❌ No TeacherDepartment found. Create one first.'
            ))
            return

        self.stdout.write(f'\nAssigning teacher to department: {dept.name}')

        # Clear any previous department assignment (to test fresh assignment)
        if staff_profile.teacher_department != dept:
            staff_profile.teacher_department = None
            staff_profile.save()
            staff_profile.refresh_from_db()

        # Assign to department (this triggers the signal)
        staff_profile.teacher_department = dept
        staff_profile.save()

        # Refresh from database
        staff_profile.refresh_from_db()

        self.stdout.write(f'\n✓ Assignment complete!')
        self.stdout.write(f"  - Role after assignment: {staff_profile.teacher_admin_role}")
        self.stdout.write(f"  - Department after: {staff_profile.teacher_department}")

        # Check result
        if staff_profile.teacher_admin_role == 'department_head':
            self.stdout.write(self.style.SUCCESS(
                '\n✅ SUCCESS: Role was auto-assigned to "department_head"!'
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f'\n❌ FAILED: Role is still "{staff_profile.teacher_admin_role}"'
            ))

        # Check ActivityLog
        logs = ActivityLog.objects.filter(
            activity_type='role_auto_assigned',
            teacher=staff_profile
        ).order_by('-created_at')[:3]

        if logs.exists():
            self.stdout.write(f'\n✓ Activity logs created:')
            for log in logs:
                self.stdout.write(f"  - {log.created_at}: {log.description}")
        else:
            self.stdout.write('\n⚠️  No activity logs found')

        # Test 2: Verify DOS role is preserved
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('Test 2: Preserve DOS role when assigning to department'))
        self.stdout.write(self.style.SUCCESS('='*70))

        # Create or get DOS test user
        dos_user, created = CustomUser.objects.get_or_create(
            username='signal_test_dos',
            defaults={
                'email': 'signal_test_dos@test.com',
                'first_name': 'DOS',
                'last_name': 'Test',
                'role': 'teacher',
                'school': school,
            }
        )
        self.stdout.write(f"{'✓ Created' if created else '✓ Using'} DOS test user: {dos_user.email}")

        dos_profile, created = StaffProfile.objects.get_or_create(
            user=dos_user,
            defaults={
                'position': 'DOS (Signal Test)',
                'teacher_admin_role': 'dos',
            }
        )

        if not created and dos_profile.teacher_admin_role != 'dos':
            dos_profile.teacher_admin_role = 'dos'
            dos_profile.save()

        self.stdout.write(f"  - Role before department assignment: {dos_profile.teacher_admin_role}")

        # Assign DOS user to department
        dos_profile.teacher_department = dept
        dos_profile.save()
        dos_profile.refresh_from_db()

        self.stdout.write(f"  - Role after department assignment: {dos_profile.teacher_admin_role}")

        if dos_profile.teacher_admin_role == 'dos':
            self.stdout.write(self.style.SUCCESS('\n✅ SUCCESS: DOS role was preserved!'))
        else:
            self.stdout.write(self.style.ERROR(
                f'\n❌ FAILED: DOS role changed to {dos_profile.teacher_admin_role}'
            ))

        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('All tests complete!'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
