"""
Management command to fix teacher StaffProfile setup.
Run: python manage.py fix_shift_setup
"""

from django.core.management.base import BaseCommand
from SchoolNowMgt.models import CustomUser, StaffProfile
import datetime


class Command(BaseCommand):
    help = 'Create missing StaffProfiles for teacher users to enable shift management'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('FIXING TEACHER STAFFPROFILE SETUP'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        # Find all teacher users
        teachers = CustomUser.objects.filter(role='teacher', is_active=True)
        self.stdout.write(f'\nFound {teachers.count()} active teacher(s)\n')
        
        created_count = 0
        existing_count = 0
        
        for teacher in teachers:
            try:
                staff_profile, created = StaffProfile.objects.get_or_create(
                    user=teacher,
                    defaults={
                        'employee_id': f"TEA{teacher.id:04d}",
                        'position': 'Teacher',
                        'salary': 0.00,
                        'date_joined': datetime.date.today(),
                        'is_full_time': True
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ CREATED  StaffProfile for: {teacher.get_full_name()} ({teacher.username})'
                        )
                    )
                    created_count += 1
                else:
                    self.stdout.write(
                        f'✓ EXISTS   StaffProfile for: {teacher.get_full_name()} ({teacher.username})'
                    )
                    existing_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ ERROR    {teacher.get_full_name()}: {str(e)}')
                )
        
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(
            self.style.SUCCESS(f'Summary: {created_count} created, {existing_count} already existed')
        )
        self.stdout.write('=' * 70)
        
        # Verify shift endpoints will work
        self.stdout.write('\nVerifying shift endpoint compatibility...')
        verify_count = 0
        for teacher in teachers:
            try:
                StaffProfile.objects.get(user=teacher, user__role='teacher')
                verify_count += 1
            except StaffProfile.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'✗ FAIL: {teacher.get_full_name()} - no StaffProfile found!')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ {verify_count}/{teachers.count()} teachers ready for shift management')
        )
        self.stdout.write(self.style.SUCCESS('\nShift endpoints should now work correctly!'))
