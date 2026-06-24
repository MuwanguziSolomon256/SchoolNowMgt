"""
Management command to create admin users with specific roles.

Usage:
    python manage.py create_admin_user \
        --email=dos@test.com \
        --password=MyPassword123! \
        --first-name=Jane \
        --last-name=Doe \
        --role=dos \
        --school="School Name"
    
    python manage.py create_admin_user \
        --email=deputy@test.com \
        --password=MyPassword456! \
        --first-name=John \
        --last-name=Smith \
        --role=deputy_hm \
        --school="School Name"
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import authenticate
from SchoolNowMgt.models import CustomUser, School, StaffProfile
from SchoolNowMgt.registration.utils import generate_employee_id
from datetime import date


class Command(BaseCommand):
    help = 'Create an admin/staff user with a specific role'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email address for the new user'
        )
        parser.add_argument(
            '--password',
            type=str,
            required=True,
            help='Password for the new user'
        )
        parser.add_argument(
            '--first-name',
            type=str,
            required=True,
            help='First name of the user'
        )
        parser.add_argument(
            '--last-name',
            type=str,
            required=True,
            help='Last name of the user'
        )
        parser.add_argument(
            '--role',
            type=str,
            choices=['teacher', 'dos', 'deputy_hm', 'head_teacher', 'department_head'],
            required=True,
            help='Administrative role for the user'
        )
        parser.add_argument(
            '--school',
            type=str,
            required=True,
            help='Name or ID of the school'
        )
        parser.add_argument(
            '--phone',
            type=str,
            default='',
            help='Phone number (optional)'
        )
        parser.add_argument(
            '--position',
            type=str,
            default='',
            help='Position/Title (optional)'
        )

    def handle(self, *args, **options):
        email = options['email'].lower()
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        role = options['role']
        school_name = options['school']
        phone = options['phone']
        position = options['position'] or self._get_role_display_name(role)

        # Get or validate school
        try:
            # Try to get by name first
            school = School.objects.filter(name__iexact=school_name).first()
            if not school:
                # Try as ID
                school = School.objects.get(id=int(school_name))
        except (ValueError, School.DoesNotExist):
            raise CommandError(f'School "{school_name}" not found')

        # Check if user already exists
        if CustomUser.objects.filter(email=email).exists():
            raise CommandError(f'User with email "{email}" already exists')

        try:
            with transaction.atomic():
                # Create CustomUser
                user = CustomUser(
                    username=email,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    role='teacher',  # All admin users are teachers in this system
                    school=school,
                    is_active=True,
                    is_staff=True,
                )
                user.set_password(password)
                user.save()

                # Generate unique employee ID
                employee_id = generate_employee_id(school)

                # Create StaffProfile with specified admin role
                staff_profile = StaffProfile(
                    user=user,
                    employee_id=employee_id,
                    position=position,
                    date_joined=date.today(),
                    salary=0,
                    is_full_time=True,
                    teacher_admin_role=role,
                )
                staff_profile.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Successfully created {role.upper()} user:\n'
                        f'  Email: {email}\n'
                        f'  Name: {first_name} {last_name}\n'
                        f'  School: {school.name}\n'
                        f'  Employee ID: {employee_id}\n'
                        f'  Role: {self._get_role_display_name(role)}'
                    )
                )

        except Exception as e:
            raise CommandError(f'Error creating user: {str(e)}')

    def _get_role_display_name(self, role):
        """Get display name for role."""
        roles = {
            'teacher': 'Class/Subject Teacher',
            'dos': 'Director of Studies',
            'department_head': 'Subject Department Head',
            'head_teacher': 'Head Teacher',
            'deputy_hm': 'Deputy Headmaster',
        }
        return roles.get(role, role)
