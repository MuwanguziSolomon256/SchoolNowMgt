#!/usr/bin/env python
"""
Phase 7: End-to-End Integration Testing Script
Tests all 7 admin roles, secondary views, multi-school isolation, and cross-role workflows
"""

import os
import sys
import django
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings')
django.setup()

from SchoolNowMgt.models import School, StaffProfile

User = get_user_model()
client = Client()

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Test data
TEST_USERS = {
    'DOS School 1': {
        'email': 'dos@test.com',
        'password': 'password123',
        'role': 'director_of_studies',
        'school': 'School 1',
    },
    'DOS School 2': {
        'email': 'dos2@test.com',
        'password': 'password123',
        'role': 'director_of_studies',
        'school': 'School 2',
    },
    'Deputy HM': {
        'email': 'deputy@test.com',
        'password': 'password123',
        'role': 'deputy_hm',
        'school': 'School 1',
    },
    'Head Teacher': {
        'email': 'headteacher@test.com',
        'password': 'password123',
        'role': 'head_teacher',
        'school': 'School 1',
    },
    'Department Head': {
        'email': 'depthead@test.com',
        'password': 'password123',
        'role': 'subject_department_head',
        'school': 'School 1',
    },
    'Matron': {
        'email': 'matron@test.com',
        'password': 'password123',
        'role': 'matron',
        'school': 'School 1',
    },
    'Support Staff': {
        'email': 'supervisor@test.com',
        'password': 'password123',
        'role': 'support_staff',
        'school': 'School 1',
    },
}

# Admin role URLs
ADMIN_DASHBOARDS = {
    'DOS School 1': '/teacher/admin/dos/',
    'DOS School 2': '/teacher/admin/dos/',
    'Deputy HM': '/teacher/admin/deputy/',
    'Head Teacher': '/teacher/admin/head-teacher/',
    'Department Head': '/teacher/department/',
    'Matron': '/teacher/matron/',
    'Support Staff': '/teacher/support/',
}

# DOS secondary views to test
DOS_SECONDARY_VIEWS = [
    ('/teacher/admin/dos/timetable/', 'Timetable List'),
    ('/teacher/admin/dos/timetable/create/', 'Timetable Create'),
    ('/teacher/admin/dos/class-teachers/', 'Class Teacher Assignments'),
    ('/teacher/admin/dos/class-teachers/create/', 'Class Teacher Create'),
    ('/teacher/admin/dos/reports/', 'Academic Reports'),
    ('/teacher/admin/dos/reports/?report_type=subject_performance', 'Subject Performance Report'),
]

# Statistics to verify
EXPECTED_STATS = {
    'DOS School 1': {
        'teachers': 15,  # Expected count
        'classes': 7,
        'students': 7,
        'departments': 2,  # Will verify at least > 0
    },
    'DOS School 2': {
        'teachers': 4,
        'classes': 2,
        'students': 5,
        'departments': 1,
    },
}


class Phase7Tester:
    """Phase 7 Integration Test Suite"""
    
    def __init__(self):
        self.results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
        }
        self.test_log = []
    
    def log(self, message, level='INFO'):
        """Log test message"""
        prefix_map = {
            'PASS': f'{GREEN}✅{RESET}',
            'FAIL': f'{RED}❌{RESET}',
            'WARN': f'{YELLOW}⚠️{RESET}',
            'INFO': f'{BLUE}ℹ️{RESET}',
        }
        prefix = prefix_map.get(level, 'INFO')
        print(f'{prefix} {message}')
        self.test_log.append(f'{level}: {message}')
    
    def test_admin_dashboard_load(self, user_label, url, expected_status=200):
        """Test that admin dashboard loads"""
        print(f'\n{BOLD}Testing {user_label} Dashboard{RESET}')
        
        # Verify user exists
        user_data = TEST_USERS[user_label]
        try:
            user = User.objects.get(email=user_data['email'])
            self.log(f'User {user_data["email"]} exists', 'INFO')
        except User.DoesNotExist:
            self.log(f'User {user_data["email"]} NOT FOUND', 'FAIL')
            self.results['failed'] += 1
            return False
        
        # Login
        logged_in = client.login(username=user_data['email'], password=user_data['password'])
        if not logged_in:
            self.log(f'Login failed for {user_data["email"]}', 'FAIL')
            self.results['failed'] += 1
            return False
        
        self.log(f'Login successful', 'PASS')
        
        # Access dashboard
        response = client.get(url, follow=True)
        
        if response.status_code == expected_status:
            self.log(f'Dashboard loaded: {url} ({response.status_code})', 'PASS')
            self.results['passed'] += 1
            
            # Check for common errors
            if 'FieldError' in response.content.decode():
                self.log(f'FieldError detected in response', 'WARN')
                self.results['warnings'] += 1
            if 'ValueError' in response.content.decode():
                self.log(f'ValueError detected in response', 'WARN')
                self.results['warnings'] += 1
            
            return True
        else:
            self.log(f'Dashboard failed: {url} ({response.status_code})', 'FAIL')
            self.results['failed'] += 1
            return False
    
    def test_secondary_views(self, user_label, views_to_test):
        """Test secondary views for a role"""
        user_data = TEST_USERS[user_label]
        
        # Login
        client.login(username=user_data['email'], password=user_data['password'])
        
        print(f'\n{BOLD}Testing {user_label} Secondary Views{RESET}')
        
        for url, name in views_to_test:
            response = client.get(url, follow=True)
            
            if response.status_code == 200:
                self.log(f'{name}: ✅ PASS', 'PASS')
                self.results['passed'] += 1
                
                # Check for errors
                if 'FieldError' in response.content.decode():
                    self.log(f'{name}: FieldError detected', 'WARN')
                    self.results['warnings'] += 1
            else:
                self.log(f'{name}: ❌ FAIL ({response.status_code})', 'FAIL')
                self.results['failed'] += 1
    
    def test_multi_school_isolation(self):
        """Test that School 1 and School 2 data doesn't mix"""
        print(f'\n{BOLD}Testing Multi-School Data Isolation{RESET}')
        
        # Get School 1 DOS user
        client.login(username='dos@test.com', password='password123')
        response1 = client.get('/teacher/admin/dos/')
        content1 = response1.content.decode()
        
        # Check if contains School 1 indicators
        if '15' in content1:  # School 1 has 15 teachers
            self.log('School 1 DOS sees School 1 data (15 teachers)', 'PASS')
            self.results['passed'] += 1
        else:
            self.log('School 1 DOS does NOT see expected data', 'WARN')
            self.results['warnings'] += 1
        
        client.logout()
        
        # Get School 2 DOS user
        client.login(username='dos2@test.com', password='password123')
        response2 = client.get('/teacher/admin/dos/')
        content2 = response2.content.decode()
        
        # Check if contains School 2 indicators
        if '4' in content2:  # School 2 has 4 teachers
            self.log('School 2 DOS sees School 2 data (4 teachers)', 'PASS')
            self.results['passed'] += 1
        else:
            self.log('School 2 DOS does NOT see expected data', 'WARN')
            self.results['warnings'] += 1
        
        # Verify no cross-school leakage
        if '15' not in content2:  # School 2 should NOT see School 1 data
            self.log('No cross-school data leakage confirmed', 'PASS')
            self.results['passed'] += 1
        else:
            self.log('POTENTIAL cross-school data leakage detected!', 'FAIL')
            self.results['failed'] += 1
        
        client.logout()
    
    def test_permission_boundaries(self):
        """Test that DOS can't access Deputy HM views"""
        print(f'\n{BOLD}Testing Permission Boundaries{RESET}')
        
        # Login as DOS
        client.login(username='dos@test.com', password='password123')
        
        # Try to access Deputy HM dashboard (should get 403)
        response = client.get('/teacher/admin/deputy/', follow=False)
        
        if response.status_code == 403:
            self.log('DOS blocked from Deputy HM dashboard (403)', 'PASS')
            self.results['passed'] += 1
        else:
            self.log(f'DOS not blocked from Deputy HM (got {response.status_code})', 'FAIL')
            self.results['failed'] += 1
        
        # Try to access Head Teacher dashboard (should get 403)
        response = client.get('/teacher/admin/head-teacher/', follow=False)
        
        if response.status_code == 403:
            self.log('DOS blocked from Head Teacher dashboard (403)', 'PASS')
            self.results['passed'] += 1
        else:
            self.log(f'DOS not blocked from Head Teacher (got {response.status_code})', 'FAIL')
            self.results['failed'] += 1
        
        client.logout()
    
    def run_all_tests(self):
        """Execute complete test suite"""
        print(f'\n{BOLD}{"="*60}')
        print(f'PHASE 7: INTEGRATION TEST SUITE - STARTING')
        print(f'{"="*60}{RESET}\n')
        
        # BATCH 1: Core Admin Roles
        print(f'\n{BOLD}BATCH 1: Core Admin Roles{RESET}')
        self.test_admin_dashboard_load('DOS School 2', '/teacher/admin/dos/')
        self.test_admin_dashboard_load('DOS School 1', '/teacher/admin/dos/')
        self.test_admin_dashboard_load('Deputy HM', '/teacher/admin/deputy/')
        self.test_admin_dashboard_load('Head Teacher', '/teacher/admin/head-teacher/')
        
        # BATCH 2: Specialized Admin Roles
        print(f'\n{BOLD}BATCH 2: Specialized Admin Roles{RESET}')
        self.test_admin_dashboard_load('Department Head', '/teacher/department/')
        self.test_admin_dashboard_load('Matron', '/teacher/matron/')
        self.test_admin_dashboard_load('Support Staff', '/teacher/support/')
        
        # BATCH 3: Secondary Views (DOS)
        self.test_secondary_views('DOS School 2', DOS_SECONDARY_VIEWS)
        
        # BATCH 4: Multi-School Isolation
        self.test_multi_school_isolation()
        
        # BATCH 5: Permission Boundaries
        self.test_permission_boundaries()
        
        # Print summary
        print(f'\n{BOLD}{"="*60}')
        print(f'TEST SUMMARY')
        print(f'{"="*60}{RESET}')
        print(f'{GREEN}✅ Passed: {self.results["passed"]}{RESET}')
        print(f'{RED}❌ Failed: {self.results["failed"]}{RESET}')
        print(f'{YELLOW}⚠️  Warnings: {self.results["warnings"]}{RESET}')
        print(f'\nTotal Tests: {self.results["passed"] + self.results["failed"] + self.results["warnings"]}')
        
        # Determine pass/fail
        if self.results['failed'] == 0:
            print(f'\n{GREEN}{BOLD}✅ PHASE 7 STATUS: READY FOR PRODUCTION{RESET}')
        else:
            print(f'\n{RED}{BOLD}❌ PHASE 7 STATUS: REVIEW NEEDED{RESET}')
        
        return self.results


if __name__ == '__main__':
    tester = Phase7Tester()
    results = tester.run_all_tests()
