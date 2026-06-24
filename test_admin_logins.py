import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()

# Define test cases for remaining roles
test_cases = [
    {
        'name': 'Head Teacher',
        'email': 'headteacher@test.com',
        'password': 'password123',
        'expected_redirect': '/teacher/admin/head-teacher/'
    },
    {
        'name': 'Dept Head',
        'email': 'depthead@test.com',
        'password': 'password123',
        'expected_redirect': '/teacher/department/'
    },
    {
        'name': 'Matron',
        'email': 'matron@test.com',
        'password': 'password123',
        'expected_redirect': '/teacher/matron/'
    },
    {
        'name': 'Supervisor',
        'email': 'supervisor@test.com',
        'password': 'password123',
        'expected_redirect': '/teacher/support/shift-supervisor/'
    },
]

print("Testing admin role logins:\n")

for test in test_cases:
    client = Client()
    print(f"Testing {test['name']} ({test['email']})...")
    
    # Check if user exists first
    try:
        user = User.objects.get(email=test['email'])
        print(f"  User exists: {user.username}")
        print(f"  Role: {user.role}")
        if hasattr(user, 'staffprofile'):
            print(f"  Admin role: {user.staffprofile.teacher_admin_role}")
            print(f"  Support role: {user.staffprofile.support_staff_role}")
    except User.DoesNotExist:
        print(f"  ERROR: User not found!")
        continue
    
    # Try to login
    response = client.post('/auth/login/', {
        'email': test['email'],
        'password': test['password']
    }, follow=True)
    
    # Get the final URL after redirects
    final_url = response.request.get('PATH_INFO', '')
    
    print(f"  Final URL: {final_url}")
    print(f"  Expected: {test['expected_redirect']}")
    print(f"  Status code: {response.status_code}")
    
    if final_url.endswith(test['expected_redirect']):
        print(f"  ✅ PASS")
    else:
        print(f"  ❌ FAIL")
    
    print()
