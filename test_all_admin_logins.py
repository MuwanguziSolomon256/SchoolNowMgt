#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings')
sys.path.insert(0, os.path.dirname(__file__))

django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

print('\n' + '='*70)
print('TESTING ALL REMAINING ADMIN ROLES - COMPLETE LOGIN FLOW')
print('='*70 + '\n')

test_cases = [
    ('Head Teacher', 'headteacher@test.com', '/teacher/admin/head-teacher/'),
    ('Dept Head', 'depthead@test.com', '/teacher/department/'),
    ('Matron', 'matron@test.com', '/teacher/matron/'),
    ('Supervisor', 'supervisor@test.com', '/teacher/support/shift-supervisor/'),
]

for name, email, expected_url in test_cases:
    print(f'\n{name}:')
    print('-' * 50)
    
    try:
        user = User.objects.get(email=email)
        print(f'  Email: {email}')
        print(f'  Username: {user.username}')
        print(f'  Role: {user.role}')
        
        if user.role == 'teacher':
            print(f'  Admin role: {user.staffprofile.teacher_admin_role}')
        else:
            print(f'  Support role: {user.staffprofile.support_staff_role}')
        
        # Test login
        client = Client()
        response = client.post('/auth/login/', {
            'email': email,
            'password': 'password123'
        }, follow=True)
        
        final_url = response.request.get('PATH_INFO', '')
        status = response.status_code
        
        print(f'  Login response status: {status}')
        print(f'  Redirected to: {final_url}')
        print(f'  Expected URL: {expected_url}')
        
        if final_url.endswith(expected_url):
            print(f'  ✅ PASS - Login successful!')
            
            # Check content
            content = response.content.decode('utf-8', errors='ignore')
            if 'dashboard' in content.lower() or 'header' in content.lower():
                print(f'  ✅ Dashboard content verified')
            else:
                print(f'  ⚠️  No dashboard content detected')
        else:
            print(f'  ❌ FAIL - Wrong redirect URL')
            
    except User.DoesNotExist:
        print(f'  ❌ User not found')
    except Exception as e:
        print(f'  ❌ Error: {str(e)}')

print('\n' + '='*70 + '\n')
