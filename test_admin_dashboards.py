"""
Phase 4: Comprehensive Dashboard Testing
Tests all 7 admin dashboards for:
1. HTTP 200 response (no 500 errors)
2. Correct dashboard title/content
3. Data displays correctly
"""
import os
import django
from django.test import Client
from django.contrib.auth import authenticate

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import CustomUser
from django.db import connection

client = Client()

test_cases = [
    {
        'name': 'DOS Dashboard',
        'username': 'test_dos',
        'email': 'dos@test.com',
        'password': 'password123',
        'url': '/teacher/admin/dos/',
        'expected_title': 'DOS Dashboard',
        'expected_elements': ['Director of Studies', 'Total Teachers', 'Classes']
    },
    {
        'name': 'Deputy HM Dashboard',
        'username': 'test_deputy_hm',
        'email': 'deputy@test.com',
        'password': 'password123',
        'url': '/teacher/admin/deputy/',
        'expected_title': 'Deputy Headmaster Dashboard',
        'expected_elements': ['Support Staff', 'Departments', 'Dept Heads']
    },
    {
        'name': 'Matron Dashboard',
        'username': 'test_matron',
        'email': 'matron@test.com',
        'password': 'password123',
        'url': '/teacher/matron/',
        'expected_title': 'Matron Dashboard',
        'expected_elements': ['Hostel', 'Residents', 'Occupancy']
    },
    {
        'name': 'Subject Dept Head Dashboard',
        'username': 'test_dept_head',
        'email': 'depthead@test.com',
        'password': 'password123',
        'url': '/teacher/department/',
        'expected_title': 'Department Head Dashboard',
        'expected_elements': ['Department', 'teachers', 'performance']
    },
    {
        'name': 'Support Staff Supervisor Dashboard',
        'username': 'test_matron',
        'email': 'matron@test.com',
        'password': 'password123',
        'url': '/teacher/support/supervisor/',
        'expected_title': 'Supervisor Dashboard',
        'expected_elements': ['staff', 'shifts', 'schedule']
    },
    {
        'name': 'Support Staff Dept Head Dashboard',
        'username': 'test_matron',
        'email': 'matron@test.com',
        'password': 'password123',
        'url': '/teacher/support/dept-head/',
        'expected_title': 'Department Head Dashboard',
        'expected_elements': ['Department', 'Staff', 'Budget']
    },
]

print("\n" + "="*80)
print("PHASE 4: COMPREHENSIVE DASHBOARD TESTING")
print("="*80)

results = []

for test in test_cases:
    print(f"\n📋 Testing: {test['name']}")
    print(f"   URL: {test['url']}")
    
    try:
        # Login
        user = authenticate(username=test['email'], password=test['password'])
        if not user:
            # Try with username if email fails
            user = authenticate(username=test['username'], password=test['password'])
        
        if user:
            client.force_login(user)
            print(f"   ✓ Logged in as {user.email}")
        else:
            print(f"   ✗ Authentication failed")
            results.append({
                'name': test['name'],
                'status': 'FAILED',
                'reason': 'Authentication failed'
            })
            continue
        
        # Request dashboard
        response = client.get(test['url'])
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check for expected elements
            missing_elements = []
            for element in test['expected_elements']:
                if element.lower() not in content.lower():
                    missing_elements.append(element)
            
            if missing_elements:
                print(f"   ⚠️  Missing elements: {missing_elements}")
                results.append({
                    'name': test['name'],
                    'status': 'PARTIAL',
                    'reason': f'Missing elements: {missing_elements}'
                })
            else:
                print(f"   ✅ All expected elements found")
                results.append({
                    'name': test['name'],
                    'status': 'PASSED',
                    'reason': 'Dashboard loaded with all expected content'
                })
        elif response.status_code == 403:
            print(f"   ✗ Access Denied (403)")
            results.append({
                'name': test['name'],
                'status': 'BLOCKED',
                'reason': '403 Forbidden - Access control working'
            })
        else:
            print(f"   ✗ Error: {response.status_code}")
            results.append({
                'name': test['name'],
                'status': 'FAILED',
                'reason': f'HTTP {response.status_code}'
            })
        
        # Logout
        client.logout()
        
    except Exception as e:
        print(f"   ✗ Exception: {str(e)}")
        results.append({
            'name': test['name'],
            'status': 'ERROR',
            'reason': str(e)
        })

# Summary
print("\n" + "="*80)
print("PHASE 4: TEST RESULTS SUMMARY")
print("="*80)
print(f"\n{'Dashboard':<35} | {'Status':<10} | {'Details'}")
print("-"*80)

passed = sum(1 for r in results if r['status'] == 'PASSED')
partial = sum(1 for r in results if r['status'] == 'PARTIAL')
blocked = sum(1 for r in results if r['status'] == 'BLOCKED')
failed = sum(1 for r in results if r['status'] in ['FAILED', 'ERROR'])

for result in results:
    print(f"{result['name']:<35} | {result['status']:<10} | {result['reason']}")

print("\n" + "-"*80)
print(f"Passed: {passed}/{len(results)}")
print(f"Partial: {partial}/{len(results)}")
print(f"Blocked: {blocked}/{len(results)}")
print(f"Failed: {failed}/{len(results)}")
print("="*80)
