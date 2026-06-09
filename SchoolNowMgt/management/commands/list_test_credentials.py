"""
Django management command to display test login credentials.

Usage:
    python manage.py list_test_credentials
    python manage.py list_test_credentials --format=table
    python manage.py list_test_credentials --format=json
    python manage.py list_test_credentials --format=simple
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from SchoolNowMgt.models import School
import json


class Command(BaseCommand):
    help = 'Display test login credentials for all roles'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            default='table',
            choices=['table', 'json', 'simple', 'copy-paste'],
            help='Output format: table, json, simple, or copy-paste'
        )
    
    def handle(self, *args, **options):
        User = get_user_model()
        output_format = options['format']
        
        # Define standard test credentials
        standard_creds = [
            {
                'role': 'Admin',
                'username': 'admin_test',
                'email': 'admin@test.com',
                'password': 'password123',
                'redirect': '/admin/',
            },
            {
                'role': 'Teacher',
                'username': 'teacher_test',
                'email': 'teacher@test.com',
                'password': 'password123',
                'redirect': '/teacher/',
            },
            {
                'role': 'Support Staff',
                'username': 'staff_test',
                'email': 'staff@test.com',
                'password': 'password123',
                'redirect': '/',
            },
            {
                'role': 'Parent',
                'username': 'parent_test',
                'email': 'parent@test.com',
                'password': 'password123',
                'redirect': '/',
            },
        ]
        
        # Check which ones actually exist in database
        existing_creds = []
        missing_creds = []
        
        for cred in standard_creds:
            user = User.objects.filter(username=cred['username']).first()
            if user:
                existing_creds.append({**cred, 'exists': True})
            else:
                missing_creds.append({**cred, 'exists': False})
        
        # Output in requested format
        if output_format == 'table':
            self._output_table(existing_creds, missing_creds)
        elif output_format == 'json':
            self._output_json(existing_creds, missing_creds)
        elif output_format == 'simple':
            self._output_simple(existing_creds, missing_creds)
        elif output_format == 'copy-paste':
            self._output_copy_paste(existing_creds, missing_creds)
    
    def _output_table(self, existing, missing):
        """Pretty table format"""
        self.stdout.write('\n' + '='*90)
        self.stdout.write(self.style.SUCCESS('TEST LOGIN CREDENTIALS'))
        self.stdout.write('='*90)
        
        if existing:
            self.stdout.write('\n' + self.style.SUCCESS('✓ AVAILABLE ACCOUNTS:\n'))
            
            # Headers
            header = f"{'Role':<18} {'Username':<15} {'Email':<22} {'Password':<15} {'Redirect':<10}"
            self.stdout.write(self.style.HTTP_INFO(header))
            self.stdout.write('-'*90)
            
            # Rows
            for cred in existing:
                row = (
                    f"{cred['role']:<18} "
                    f"{cred['username']:<15} "
                    f"{cred['email']:<22} "
                    f"{cred['password']:<15} "
                    f"{cred['redirect']:<10}"
                )
                self.stdout.write(self.style.SUCCESS(row))
        
        if missing:
            self.stdout.write('\n' + self.style.WARNING('⚠ MISSING ACCOUNTS:\n'))
            
            for cred in missing:
                self.stdout.write(
                    self.style.WARNING(
                        f"  {cred['role']:<18} - {cred['email']}"
                    )
                )
            
            self.stdout.write(
                self.style.WARNING(
                    '\n  Create them with: python manage.py create_test_logins\n'
                )
            )
        
        self.stdout.write('='*90 + '\n')
    
    def _output_simple(self, existing, missing):
        """Simple list format"""
        self.stdout.write('\nTEST LOGIN CREDENTIALS:\n')
        
        for cred in existing:
            self.stdout.write(f"\n{cred['role']}:")
            self.stdout.write(f"  Email:    {cred['email']}")
            self.stdout.write(f"  Username: {cred['username']}")
            self.stdout.write(f"  Password: {cred['password']}")
            self.stdout.write(f"  Redirect: {cred['redirect']}")
        
        if missing:
            self.stdout.write('\n\nMISSING ACCOUNTS:')
            for cred in missing:
                self.stdout.write(f"  - {cred['role']} ({cred['email']})")
            self.stdout.write('\nCreate them: python manage.py create_test_logins')
        
        self.stdout.write('')
    
    def _output_json(self, existing, missing):
        """JSON format"""
        output = {
            'available': existing,
            'missing': missing,
        }
        self.stdout.write(json.dumps(output, indent=2))
    
    def _output_copy_paste(self, existing, missing):
        """Ready-to-copy-paste format"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write('COPY-PASTE CREDENTIALS')
        self.stdout.write('='*60 + '\n')
        
        for cred in existing:
            self.stdout.write(f"\n{cred['role']}:")
            self.stdout.write(f"{cred['email']} / {cred['password']}")
        
        if missing:
            self.stdout.write('\n\n⚠  Missing accounts - run:')
            self.stdout.write('python manage.py create_test_logins')
        
        self.stdout.write('\n' + '='*60 + '\n')
