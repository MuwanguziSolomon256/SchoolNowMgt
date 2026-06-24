#!/usr/bin/env python
"""
Enhanced test account setup with role-specific staff profiles.

This script creates test accounts with specific admin roles:
- DOS (Director of Studies)
- Deputy Headmaster
- Department Head
- Head Teacher
- Class Teacher
- Matron
- Supervisor
- Support Staff with specific roles
"""

import os
import sys
import django
from datetime import date

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from django.contrib.auth import get_user_model
from SchoolNowMgt.models import School, StaffProfile
from django.db import IntegrityError

User = get_user_model()

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def get_or_create_school():
    """Get or create the test school"""
    school, created = School.objects.get_or_create(
        registration_number='DEFAULT-001',
        defaults={
            'name': 'Test School',
            'address': '123 Education Lane',
            'phone': '+256700123456',
            'email': 'admin@testschool.com',
        }
    )
    return school

def create_test_staff_profiles(school):
    """Create test staff profiles with various admin roles"""
    
    test_staff = [
        {
            'username': 'dos_test',
            'email': 'dos@test.com',
            'password': 'password123',
            'role': 'teacher',
            'first_name': 'Dr',
            'last_name': 'DOS',
            'admin_role': 'dos',
            'position': 'Director of Studies',
            'employee_id': 'EMP001',
        },
        {
            'username': 'deputy_hm_test',
            'email': 'deputyhm@test.com',
            'password': 'password123',
            'role': 'teacher',
            'first_name': 'Mr',
            'last_name': 'Deputy Headmaster',
            'admin_role': 'deputy_hm',
            'position': 'Deputy Headmaster',
            'employee_id': 'EMP002',
        },
        {
            'username': 'dept_head_test',
            'email': 'depthead@test.com',
            'password': 'password123',
            'role': 'teacher',
            'first_name': 'Mrs',
            'last_name': 'Department Head',
            'admin_role': 'department_head',
            'position': 'Subject Department Head',
            'employee_id': 'EMP003',
        },
        {
            'username': 'head_teacher_test',
            'email': 'headteacher@test.com',
            'password': 'password123',
            'role': 'teacher',
            'first_name': 'Prof',
            'last_name': 'Head Teacher',
            'admin_role': 'head_teacher',
            'position': 'Head Teacher',
            'employee_id': 'EMP004',
        },
        {
            'username': 'class_teacher_test',
            'email': 'classteacher@test.com',
            'password': 'password123',
            'role': 'teacher',
            'first_name': 'Miss',
            'last_name': 'Class Teacher',
            'admin_role': 'teacher',
            'position': 'Class Teacher',
            'employee_id': 'EMP005',
        },
        {
            'username': 'matron_test',
            'email': 'matron@test.com',
            'password': 'password123',
            'role': 'non_teaching_staff',
            'first_name': 'Mama',
            'last_name': 'Matron',
            'admin_role': 'matron',
            'position': 'Hostel Matron',
            'employee_id': 'EMP006',
        },
        {
            'username': 'supervisor_test',
            'email': 'supervisor@test.com',
            'password': 'password123',
            'role': 'non_teaching_staff',
            'first_name': 'Mr',
            'last_name': 'Supervisor',
            'admin_role': 'shift_supervisor',
            'position': 'Shift Supervisor',
            'employee_id': 'EMP007',
        },
        {
            'username': 'support_dept_head_test',
            'email': 'supporthead@test.com',
            'password': 'password123',
            'role': 'non_teaching_staff',
            'first_name': 'Ms',
            'last_name': 'Support Head',
            'admin_role': 'support_dept_head',
            'position': 'Support Department Head',
            'employee_id': 'EMP008',
        },
    ]
    
    created_count = 0
    credentials = []
    
    for staff_data in test_staff:
        admin_role = staff_data.pop('admin_role')
        position = staff_data.pop('position')
        employee_id = staff_data.pop('employee_id')
        password = staff_data['password']
        
        # Check if user exists
        user = User.objects.filter(username=staff_data['username']).first()
        
        if user:
            print(f"{Colors.YELLOW}⊘ User already exists: {staff_data['username']}{Colors.END}")
        else:
            try:
                # Create user
                user = User.objects.create_user(
                    username=staff_data['username'],
                    email=staff_data['email'],
                    password=password,
                    school=school,
                    role=staff_data['role'],
                    first_name=staff_data['first_name'],
                    last_name=staff_data['last_name'],
                    is_active=True,
                )
                created_count += 1
                print(f"{Colors.GREEN}✓ Created user: {staff_data['username']}{Colors.END}")
            except Exception as e:
                print(f"{Colors.RED}✗ Error creating user {staff_data['username']}: {str(e)}{Colors.END}")
                continue
        
        # Create or update StaffProfile with admin role
        if user:
            try:
                staff_profile, created = StaffProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'employee_id': employee_id,
                        'position': position,
                        'teacher_admin_role': admin_role,
                        'salary': 45000.00,
                        'date_joined': date.today(),
                        'is_full_time': True,
                    }
                )
                
                # Update admin role if profile already existed
                if not created:
                    staff_profile.teacher_admin_role = admin_role
                    staff_profile.position = position
                    staff_profile.save()
                    print(f"{Colors.CYAN}  └─ StaffProfile updated: {admin_role}{Colors.END}")
                else:
                    print(f"{Colors.GREEN}  └─ StaffProfile created: {admin_role}{Colors.END}")
                
            except Exception as e:
                print(f"{Colors.RED}  ✗ Error creating StaffProfile: {str(e)}{Colors.END}")
        
        # Add to credentials display
        role_display = f"{position} ({admin_role})"
        credentials.append({
            'role': role_display,
            'username': staff_data['username'],
            'email': staff_data['email'],
            'password': password,
        })
    
    return credentials

def display_credentials(base_creds, admin_creds):
    """Display all test credentials"""
    
    print(f"\n{Colors.BOLD}{'='*70}")
    print(f"{'TEST LOGIN CREDENTIALS - ALL ROLES'}{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")
    
    print(f"{Colors.CYAN}{Colors.BOLD}PRIMARY ROLES (Basic Access):{Colors.END}")
    print(f"{'-'*70}")
    for cred in base_creds:
        print(f"\n{Colors.BOLD}{cred['role']}:{Colors.END}")
        print(f"  Username: {cred['username']}")
        print(f"  Email:    {cred['email']}")
        print(f"  Password: {cred['password']}")
    
    print(f"\n\n{Colors.CYAN}{Colors.BOLD}ADMINISTRATIVE ROLES (Enhanced Features):{Colors.END}")
    print(f"{'-'*70}")
    for cred in admin_creds:
        print(f"\n{Colors.BOLD}{cred['role']}:{Colors.END}")
        print(f"  Username: {cred['username']}")
        print(f"  Email:    {cred['email']}")
        print(f"  Password: {cred['password']}")
    
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.GREEN}✓ Total accounts ready: {4 + len(admin_creds)}{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}\n{Colors.END}")

def get_existing_credentials():
    """Get credentials from existing base test users"""
    base_creds = [
        {
            'role': 'Admin',
            'username': 'admin_test',
            'email': 'admin@test.com',
            'password': 'password123',
        },
        {
            'role': 'Teacher (Basic)',
            'username': 'teacher_test',
            'email': 'teacher@test.com',
            'password': 'password123',
        },
        {
            'role': 'Support Staff (Basic)',
            'username': 'staff_test',
            'email': 'staff@test.com',
            'password': 'password123',
        },
        {
            'role': 'Parent',
            'username': 'parent_test',
            'email': 'parent@test.com',
            'password': 'password123',
        },
    ]
    return base_creds

if __name__ == '__main__':
    print(f"\n{Colors.CYAN}{Colors.BOLD}Setting up enhanced test accounts with admin roles...{Colors.END}\n")
    
    school = get_or_create_school()
    print(f"{Colors.GREEN}✓ Using school: {school.name}{Colors.END}\n")
    
    base_creds = get_existing_credentials()
    admin_creds = create_test_staff_profiles(school)
    
    display_credentials(base_creds, admin_creds)
