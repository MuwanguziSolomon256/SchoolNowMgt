"""
Management command to ensure a default school exists in the database.

This command is called during deployment to create the default school if it doesn't exist.
This is necessary because the School model is required before any users can be created.
"""

from django.core.management.base import BaseCommand
from django.db import connection
from SchoolNowMgt.models import School


class Command(BaseCommand):
    help = 'Ensure a default school exists in the database'

    def handle(self, *args, **options):
        # Check if SchoolNowMgt_school table exists
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS(SELECT FROM information_schema.tables WHERE table_name = 'SchoolNowMgt_school')"
            )
            table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            self.stdout.write(
                self.style.WARNING('School table does not exist yet. Migrations may not have run.')
            )
            return
        
        # Create default school if it doesn't exist
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
