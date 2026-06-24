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

test_cases = [
    ('Head Teacher', 'headteacher@test.com', '/teacher/admin/head-teacher/'),
    ('Dept Head', 'depthead@test.com', '/teacher/department/'),
    ('Matron', 'matron@test.com', '/teacher/matron/'),
    ('Supervisor', 'supervisor@test.com', '/teacher/support/shift-supervisor/'),
]

print('\n' + '='*70)
print('TESTING REMAINING ADMIN ROLES')
print('='*70 + '\n')

results = []

for name, email, expected_url in test_cases:
    try:
        user = User.objects.get(email=email)
        admin_role = user.staffprofile.teacher_admin_role if user.staffprofile.teacher_admin_role else 'N/A'
        support_role = user.staffprofile.support_staff_role if user.staffprofile.support_staff_role else 'N/A'
        print(f'Testing {name}:')
        print(f'  User: {user.username} ({email})')
        print(f'  Role: {user.role}')
        print(f'  Admin role: {admin_role}')
        print(f'  Support role: {support_role}')
        
        # Test login
        c = Client()
        r = c.post('/auth/login/', {'email': email, 'password': 'password123'}, follow=True)
        final_url = r.request.get('PATH_INFO', '')
        status = r.status_code
        
        print(f'  Login response status: {status}')
        print(f'  Final URL: {final_url}')
        print(f'  Expected URL: {expected_url}')
        
        if final_url.endswith(expected_url):
            print(f'  ✅ PASS')
            results.append((name, 'PASS'))
        else:
            print(f'  ❌ FAIL')
            results.append((name, 'FAIL'))
    except User.DoesNotExist:
        print(f'{name}: ❌ User not found')
        results.append((name, 'ERROR - User not found'))
    except Exception as e:
        print(f'{name}: ❌ ERROR - {str(e)}')
        results.append((name, f'ERROR - {str(e)}'))
    print()

print('='*70)
print('SUMMARY')
print('='*70)
for name, result in results:
    status_symbol = '✅' if result == 'PASS' else '❌'
    print(f'{status_symbol} {name}: {result}')
print('='*70 + '\n')
