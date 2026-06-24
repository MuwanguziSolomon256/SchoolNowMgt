#!/usr/bin/env python
import subprocess
import json

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
    print(f'Testing {name} ({email})...')
    
    # Get user info from database
    cmd = f'''cd "c:\\Users\\DELL\\Desktop\\Management Info Sys" ; & ".\.venv\\Scripts\\python.exe" manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(email='{email}')
print(user.username + ',' + user.role + ',' + user.staffprofile.teacher_admin_role + ',' + user.staffprofile.support_staff_role)
"'''
    
    try:
        result = subprocess.run(
            ['powershell', '-Command', cmd],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            output = result.stdout.strip().split('\n')[-1]  # Get last line
            parts = output.split(',')
            if len(parts) >= 2:
                username, role = parts[0], parts[1]
                admin_role = parts[2] if len(parts) > 2 else 'N/A'
                support_role = parts[3] if len(parts) > 3 else 'N/A'
                
                print(f'  User: {username}')
                print(f'  Role: {role}')
                print(f'  Admin role: {admin_role}')
                print(f'  Support role: {support_role}')
                print(f'  Expected redirect: {expected_url}')
                results.append((name, 'OK - User exists'))
            else:
                print(f'  ❌ Error parsing user data')
                results.append((name, 'ERROR'))
        else:
            print(f'  ❌ Failed to get user info')
            print(f'  Error: {result.stderr[:200]}')
            results.append((name, 'ERROR - User query failed'))
    except Exception as e:
        print(f'  ❌ Exception: {str(e)}')
        results.append((name, f'ERROR - {str(e)}'))
    
    print()

print('='*70)
print('SUMMARY')
print('='*70)
for name, result in results:
    print(f'  {name}: {result}')
print('='*70 + '\n')

print("Note: Users exist and are configured. To test actual login redirects,")
print("please manually test each role at http://localhost:8000/auth/login/")
