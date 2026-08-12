#!/usr/bin/env python
"""Test grade entry API with exam_type parameter."""

import json
import requests
from requests.auth import HTTPBasicAuth

# Configuration
BASE_URL = 'http://127.0.0.1:8000'
TEACHER_USERNAME = 'teacher'  # Update with actual teacher username
TEACHER_PASSWORD = 'teacherpass'  # Update with actual teacher password

def test_single_entry():
    """Test single grade entry with exam_type."""
    print("\n" + "="*60)
    print("Testing Single Grade Entry with Exam Type")
    print("="*60)
    
    # Start a session to maintain authentication
    session = requests.Session()
    
    # Login first
    login_url = f'{BASE_URL}/teacher/login/'
    login_data = {
        'username': TEACHER_USERNAME,
        'password': TEACHER_PASSWORD,
    }
    
    print(f"\n1. Logging in as {TEACHER_USERNAME}...")
    r = session.post(login_url, data=login_data)
    if r.status_code != 200:
        print(f"   ✗ Login failed: {r.status_code}")
        return False
    print(f"   ✓ Login successful")
    
    # Get CSRF token from grade entry page
    print(f"\n2. Fetching CSRF token...")
    grade_url = f'{BASE_URL}/teacher/grades/entry/'
    r = session.get(grade_url)
    if r.status_code != 200:
        print(f"   ✗ Failed to fetch grade entry page: {r.status_code}")
        return False
    
    # Extract CSRF token from the HTML
    import re
    csrf_pattern = r'<input[^>]*name=[\'\"]csrfmiddlewaretoken[\'\"][^>]*value=[\'\"]([^\'\"]+)[\'\"]'
    match = re.search(csrf_pattern, r.text)
    if not match:
        print(f"   ✗ Could not find CSRF token")
        return False
    csrf_token = match.group(1)
    print(f"   ✓ CSRF token obtained")
    
    # Test submission with exam_type
    print(f"\n3. Submitting single grade with exam_type='beginning_of_term'...")
    api_url = f'{BASE_URL}/teacher/grades/entry/'
    headers = {
        'X-CSRFToken': csrf_token,
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/json',
    }
    
    # You would need to use actual IDs from your database
    grade_data = {
        'entry_type': 'single',
        'student_id': 1,
        'subject_id': 1,
        'exam_type': 'beginning_of_term',
        'term': '1',
        'year': '2026',
        'score': 75
    }
    
    r = session.post(api_url, json=grade_data, headers=headers)
    print(f"   Status: {r.status_code}")
    
    try:
        response_data = r.json()
        if response_data.get('success'):
            print(f"   ✓ Grade submitted successfully")
            print(f"   Response: {json.dumps(response_data, indent=2)}")
            return True
        else:
            print(f"   ✗ Grade submission failed")
            print(f"   Error: {response_data.get('error', 'Unknown error')}")
            return False
    except json.JSONDecodeError:
        print(f"   ✗ Invalid JSON response: {r.text[:200]}")
        return False

def test_bulk_entry():
    """Test bulk grade entry with exam_type."""
    print("\n" + "="*60)
    print("Testing Bulk Grade Entry with Exam Type")
    print("="*60)
    
    session = requests.Session()
    
    # Login first
    login_url = f'{BASE_URL}/teacher/login/'
    login_data = {
        'username': TEACHER_USERNAME,
        'password': TEACHER_PASSWORD,
    }
    
    print(f"\n1. Logging in as {TEACHER_USERNAME}...")
    r = session.post(login_url, data=login_data)
    if r.status_code != 200:
        print(f"   ✗ Login failed: {r.status_code}")
        return False
    print(f"   ✓ Login successful")
    
    # Get CSRF token
    print(f"\n2. Fetching CSRF token...")
    grade_url = f'{BASE_URL}/teacher/grades/entry/'
    r = session.get(grade_url)
    if r.status_code != 200:
        print(f"   ✗ Failed to fetch grade entry page: {r.status_code}")
        return False
    
    import re
    csrf_pattern = r'<input[^>]*name=[\'\"]csrfmiddlewaretoken[\'\"][^>]*value=[\'\"]([^\'\"]+)[\'\"]'
    match = re.search(csrf_pattern, r.text)
    if not match:
        print(f"   ✗ Could not find CSRF token")
        return False
    csrf_token = match.group(1)
    print(f"   ✓ CSRF token obtained")
    
    # Test bulk submission with exam_type
    print(f"\n3. Submitting bulk grades with exam_type='mid_term'...")
    api_url = f'{BASE_URL}/teacher/grades/entry/'
    headers = {
        'X-CSRFToken': csrf_token,
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/json',
    }
    
    bulk_data = {
        'entry_type': 'bulk',
        'class_id': 1,
        'subject_id': 1,
        'exam_type': 'mid_term',
        'term': '1',
        'year': '2026',
        'grades': {
            '1': 75,
            '2': 82,
            '3': 88,
        }
    }
    
    r = session.post(api_url, json=bulk_data, headers=headers)
    print(f"   Status: {r.status_code}")
    
    try:
        response_data = r.json()
        if response_data.get('success'):
            print(f"   ✓ Bulk grades submitted successfully")
            print(f"   Response: {json.dumps(response_data, indent=2)}")
            return True
        else:
            print(f"   ✗ Bulk submission failed")
            print(f"   Error: {response_data.get('error', 'Unknown error')}")
            return False
    except json.JSONDecodeError:
        print(f"   ✗ Invalid JSON response: {r.text[:200]}")
        return False

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Grade Entry API Test Suite")
    print("="*60)
    
    print("\nNote: This test requires the Django development server running")
    print("and teacher credentials configured in the test.")
    
    try:
        # Check if server is running
        r = requests.get(f'{BASE_URL}/', timeout=2)
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Django development server is not running at " + BASE_URL)
        print("  Start the server with: python manage.py runserver")
        exit(1)
    
    # Run tests
    single_result = test_single_entry()
    bulk_result = test_bulk_entry()
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Single Entry Test: {'✓ PASSED' if single_result else '✗ FAILED'}")
    print(f"Bulk Entry Test: {'✓ PASSED' if bulk_result else '✗ FAILED'}")
    print("="*60 + "\n")
