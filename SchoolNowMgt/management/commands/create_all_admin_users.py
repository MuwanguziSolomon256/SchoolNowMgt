from django.core.management.base import BaseCommand
from SchoolNowMgt.models import CustomUser, StaffProfile, School


class Command(BaseCommand):
    help = 'Create test users for all admin roles'

    def handle(self, *args, **options):
        # Get or create default school
        school, created = School.objects.get_or_create(
            name='Default School',
            defaults={'location': 'Default'}
        )
        
        self.stdout.write(f"\nSchool: {school.name}\n")

        # Admin roles config
        roles_config = [
            {
                'username': 'head_teacher_test',
                'email': 'headteacher@test.com',
                'first_name': 'Prof',
                'last_name': 'Head Teacher',
                'admin_role': 'head_teacher',
                'role': 'teacher',
                'position': 'Head Teacher'
            },
            {
                'username': 'dept_head_test',
                'email': 'depthead@test.com',
                'first_name': 'Mrs',
                'last_name': 'Department Head',
                'admin_role': 'department_head',
                'role': 'teacher',
                'position': 'Subject Department Head'
            },
            {
                'username': 'matron_test',
                'email': 'matron@test.com',
                'first_name': 'Miss',
                'last_name': 'Matron',
                'support_role': 'welfare_coordinator',
                'role': 'non_teaching_staff',
                'position': 'Matron'
            },
            {
                'username': 'supervisor_test',
                'email': 'supervisor@test.com',
                'first_name': 'Mr',
                'last_name': 'Supervisor',
                'support_role': 'supervisor',
                'role': 'non_teaching_staff',
                'position': 'Shift Supervisor'
            }
        ]

        self.stdout.write("="*80)
        self.stdout.write("CREATING/UPDATING ALL ADMIN ROLE USERS")
        self.stdout.write("="*80 + "\n")

        for config in roles_config:
            username = config['username']
            email = config['email']
            
            self.stdout.write(f"Processing: {email}")
            
            user = CustomUser.objects.filter(username=username).first()
            if not user:
                user = CustomUser.objects.filter(email=email).first()
            
            if user:
                self.stdout.write(f"  ✓ User exists")
            else:
                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    first_name=config['first_name'],
                    last_name=config['last_name'],
                    password='password123',
                    role=config['role'],
                    school=school
                )
                self.stdout.write(f"  ✓ User created")
            
            # Create or update StaffProfile
            profile, created = StaffProfile.objects.get_or_create(user=user)
            
            if 'admin_role' in config:
                profile.teacher_admin_role = config['admin_role']
            if 'support_role' in config:
                profile.support_staff_role = config['support_role']
            profile.position = config['position']
            profile.save()
            
            role_name = config.get('admin_role') or config.get('support_role')
            self.stdout.write(f"  ✓ Profile updated with role: {role_name}\n")

        self.stdout.write("="*80)
        self.stdout.write("FINAL CREDENTIALS")
        self.stdout.write("="*80)
        for config in roles_config:
            self.stdout.write(f"\n{config.get('admin_role') or config.get('support_role').upper()}")
            self.stdout.write(f"  Email: {config['email']}")
            self.stdout.write(f"  Password: password123")
