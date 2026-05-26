"""
Management command to ensure a default school exists in the database.

This command is called during deployment to create the default school if it doesn't exist.
This is necessary because the School model is required before any users can be created.
"""

from django.core.management.base import BaseCommand
from django.db import connection, ProgrammingError
from SchoolNowMgt.models import School


class Command(BaseCommand):
    help = 'Ensure a default school exists in the database'

    def handle(self, *args, **options):
        try:
            # Try to query the School table to check if it exists
            School.objects.count()
        except ProgrammingError as e:
            self.stdout.write(
                self.style.ERROR(
                    f'✗ School table does not exist. Migrations may not have run successfully.\n'
                    f'  Error: {str(e)}'
                )
            )
            return
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'✗ Database connection error: {str(e)}'
                )
            )
            return
        
        # Create default school if it doesn't exist
        try:
            school, created = School.objects.get_or_create(
                registration_number='DEFAULT-001',
                defaults={
                    'name': 'Default School',
                    'address': 'Not specified',
                    'phone': '0000000000',
                    'email': 'default@school.com',
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created default school: {school.name}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Default school already exists: {school.name}')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to create/fetch default school: {str(e)}')
            )
