"""
Management command to create a superuser if one doesn't exist.

Useful for initial deployment when you need admin access.
Uses environment variables or prompts interactively.
"""

from django.core.management.base import BaseCommand
from django.db import ProgrammingError
from decouple import config
from SchoolNowMgt.models import CustomUser, School


class Command(BaseCommand):
    help = 'Create a superuser if one does not already exist'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username for the superuser',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email for the superuser',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for the superuser',
        )

    def handle(self, *args, **options):
        try:
            # Check if CustomUser table exists
            CustomUser.objects.count()
        except ProgrammingError:
            self.stdout.write(
                self.style.ERROR(
                    '✗ CustomUser table does not exist. Migrations may not have run.'
                )
            )
            return

        # Check if a superuser already exists
        if CustomUser.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                self.style.SUCCESS('✓ Superuser already exists')
            )
            return

        # Get credentials from options, environment variables, or defaults
        username = options.get('username') or config('ADMIN_USERNAME', default='admin')
        email = options.get('email') or config('ADMIN_EMAIL', default='admin@schoolnowmgt.com')
        password = options.get('password') or config('ADMIN_PASSWORD', default=None)

        # If no password provided and not from env, prompt user
        if not password:
            self.stdout.write(
                self.style.WARNING(
                    '\nNo password provided. Please set ADMIN_PASSWORD environment variable '
                    'or use --password flag for automated deployment.'
                )
            )
            return

        try:
            # Get or create the default school
            school, _ = School.objects.get_or_create(
                registration_number='DEFAULT-001',
                defaults={
                    'name': 'Default School',
                    'address': 'Not specified',
                    'phone': '0000000000',
                    'email': 'default@school.com',
                }
            )

            # Create the superuser
            superuser = CustomUser.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                school=school,
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Superuser created successfully!\n'
                    f'  Username: {username}\n'
                    f'  Email: {email}\n'
                    f'  School: {school.name}'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to create superuser: {str(e)}')
            )
