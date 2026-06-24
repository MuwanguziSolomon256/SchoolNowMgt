from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

test_cases = [
    ('Head Teacher', 'headteacher@test.com', '/teacher/admin/head-teacher/'),
    ('Dept Head', 'depthead@test.com', '/teacher/department/'),
    ('Matron', 'matron@test.com', '/teacher/matron/'),
    ('Supervisor', 'supervisor@test.com', '/teacher/support/shift-supervisor/'),
]

print('\nTesting admin role logins:\n')

for name, email, expected_url in test_cases:
    try:
        user = User.objects.get(email=email)
        admin_role = user.staffprofile.teacher_admin_role if user.staffprofile.teacher_admin_role else 'N/A'
        support_role = user.staffprofile.support_staff_role if user.staffprofile.support_staff_role else 'N/A'
        print(f'{name}: {user.role} / admin_role={admin_role}, support_role={support_role}')
        
        # Test login
        c = Client()
        r = c.post('/auth/login/', {'email': email, 'password': 'password123'}, follow=True)
        final_url = r.request.get('PATH_INFO', '')
        
        if final_url.endswith(expected_url):
            print(f'  ✅ PASS -> {final_url}')
        else:
            print(f'  ❌ FAIL -> {final_url} (expected {expected_url})')
    except User.DoesNotExist:
        print(f'{name}: ❌ User not found')
    except Exception as e:
        print(f'{name}: ❌ ERROR - {str(e)}')
    print()
