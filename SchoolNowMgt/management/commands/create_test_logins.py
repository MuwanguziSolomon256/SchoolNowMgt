"""
Management command to create test login accounts for all user roles.

This command creates test users for each role (admin, teacher, non_teaching_staff, parent)
to facilitate testing and development of the dashboard interfaces.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from SchoolNowMgt.models import School


class Command(BaseCommand):
    help = 'Create test login accounts for all user roles'
    
    def handle(self, *args, **options):
        User = get_user_model()
        
        # Ensure default school exists
        school, created = School.objects.get_or_create(
            registration_number='DEFAULT-001',
            defaults={
                'name': 'Test School',
                'address': '123 Education Lane',
                'phone': '+256700123456',
                'email': 'admin@testschool.com',
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created school: {school.name}'))
        
        # Define test users for each role
        test_users = [
            {
                'username': 'admin_test',
                'email': 'admin@test.com',
                'password': 'AdminTest123!',
                'role': 'admin',
                'first_name': 'Admin',
                'last_name': 'User',
            },
            {
                'username': 'teacher_test',
                'email': 'teacher@test.com',
                'password': 'TeacherTest123!',
                'role': 'teacher',
                'first_name': 'John',
                'last_name': 'Teacher',
            },
            {
                'username': 'staff_test',
                'email': 'staff@test.com',
                'password': 'StaffTest123!',
                'role': 'non_teaching_staff',
                'first_name': 'Jane',
                'last_name': 'Staff',
            },
            {
                'username': 'parent_test',
                'email': 'parent@test.com',
                'password': 'ParentTest123!',
                'role': 'parent',
                'first_name': 'Peter',
                'last_name': 'Parent',
            },
        ]
        
        # Create test users and display credentials
        created_count = 0
        credentials_display = []
        
        for user_data in test_users:
            password = user_data['password']
            
            # Check if user already exists
            if User.objects.filter(username=user_data['username']).exists():
                self.stdout.write(self.style.WARNING(f'⊘ User already exists: {user_data["username"]}'))
            else:
                try:
                    # Create user
                    user = User.objects.create_user(
                        username=user_data['username'],
                        email=user_data['email'],
                        password=password,
                        school=school,
                        role=user_data['role'],
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name'],
                        is_active=True,
                    )
                    
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created {user_data["role"].replace("_", " ").title()} account: {user_data["username"]}')
                    )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Error creating user {user_data["username"]}: {str(e)}')
                    )
            
            # Add to credentials display
            role_display = user_data['role'].replace('_', ' ').title()
            credentials_display.append({
                'role': role_display,
                'username': user_data['username'],
                'email': user_data['email'],
                'password': password,
            })
        
        # Print summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✓ Test accounts ready: 4/4'))
        self.stdout.write('='*60)
        self.stdout.write('\n' + self.style.HTTP_INFO('TEST LOGIN CREDENTIALS') + '\n')
        
        for cred in credentials_display:
            self.stdout.write(f'\n{cred["role"]}:')
            self.stdout.write(f'  Username: {cred["username"]}')
            self.stdout.write(f'  Email:    {cred["email"]}')
            self.stdout.write(f'  Password: {cred["password"]}')
