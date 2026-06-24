from django.core.management.base import BaseCommand
from SchoolNowMgt.models import CustomUser


class Command(BaseCommand):
    help = 'Reset passwords for all admin role test users'

    def handle(self, *args, **options):
        users_config = [
            {'email': 'headteacher@test.com', 'label': 'Head Teacher'},
            {'email': 'depthead@test.com', 'label': 'Department Head'},
            {'email': 'matron@test.com', 'label': 'Matron'},
            {'email': 'supervisor@test.com', 'label': 'Shift Supervisor'}
        ]

        self.stdout.write("\n" + "="*80)
        self.stdout.write("RESETTING PASSWORDS FOR ALL ADMIN USERS")
        self.stdout.write("="*80 + "\n")

        for config in users_config:
            user = CustomUser.objects.filter(email=config['email']).first()
            if user:
                user.set_password('password123')
                user.save()
                self.stdout.write(f"✓ {config['label']}: {config['email']}")
                self.stdout.write(f"  Password reset to: password123\n")
            else:
                self.stdout.write(f"✗ User not found: {config['email']}\n")

        self.stdout.write("="*80)
        self.stdout.write("TEST CREDENTIALS - Ready to Login")
        self.stdout.write("="*80 + "\n")
        
        for config in users_config:
            self.stdout.write(f"  {config['label']}")
            self.stdout.write(f"    Email: {config['email']}")
            self.stdout.write(f"    Password: password123\n")
