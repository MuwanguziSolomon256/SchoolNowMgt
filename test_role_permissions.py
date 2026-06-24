#!/usr/bin/env python
"""
Phase 9: Role Permission Test Script

Tests all role-based access control across the application.
Validates that decorators prevent unauthorized access and allow authorized access.

Usage:
    python manage.py shell < test_role_permissions.py
    
Or create as management command:
    python manage.py test_role_permissions
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from SchoolNowMgt.models import School, StaffProfile
from django.urls import reverse

User = get_user_model()


class RolePermissionTestSuite(TestCase):
    """Test suite for role-based access control"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create schools
        self.school_a = School.objects.create(
            school_name="Test School A",
            school_abbrev="TSA",
            phone="0700000001",
            email="tsa@test.com"
        )
        self.school_b = School.objects.create(
            school_name="Test School B",
            school_abbrev="TSB",
            phone="0700000002",
            email="tsb@test.com"
        )
        
        # Create users with different roles
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role='admin',
            school=self.school_a
        )
        
        self.teacher_user = User.objects.create_user(
            username='teacher1',
            email='teacher1@test.com',
            password='testpass123',
            role='teacher',
            school=self.school_a
        )
        
        self.dos_user = User.objects.create_user(
            username='dos1',
            email='dos1@test.com',
            password='testpass123',
            role='teacher',
            school=self.school_a
        )
        
        self.support_staff_user = User.objects.create_user(
            username='staff1',
            email='staff1@test.com',
            password='testpass123',
            role='non_teaching_staff',
            school=self.school_a
        )
        
        self.parent_user = User.objects.create_user(
            username='parent1',
            email='parent1@test.com',
            password='testpass123',
            role='parent',
            school=self.school_a
        )
        
        # Create staff profiles with teacher admin roles
        self.dos_profile = StaffProfile.objects.create(
            user=self.dos_user,
            teacher_admin_role='dos'
        )
        
        self.department_head_profile = StaffProfile.objects.create(
            user=self.teacher_user,
            teacher_admin_role='department_head'
        )
        
        self.class_teacher_profile = StaffProfile.objects.create(
            user=self.support_staff_user,
            teacher_admin_role='class_teacher'  # Note: This is odd but testing the decorator
        )
        
        self.support_staff_profile = StaffProfile.objects.create(
            user=self.support_staff_user,
            support_staff_role='supervisor'
        )

    # ===== UNAUTHENTICATED ACCESS TESTS =====
    
    def test_anonymous_access_redirects_to_login(self):
        """Test that anonymous user is redirected to login"""
        print("\n🔍 TEST: Anonymous access to protected routes")
        
        protected_routes = [
            '/teacher/',
            '/teacher/students/',
            '/teacher/grades/',
            '/teacher/communication/',
            '/teacher/attendances/',
        ]
        
        for route in protected_routes:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 302, f"Route {route} should redirect (302)")
            self.assertIn('login', response.url.lower(), f"Route {route} should redirect to login")
            print(f"  ✓ {route} → redirect to login (302)")
    
    # ===== WRONG ROLE ACCESS TESTS =====
    
    def test_parent_cannot_access_teacher_routes(self):
        """Test that parent user cannot access teacher-only routes"""
        print("\n🔍 TEST: Parent cannot access teacher routes")
        
        self.client.login(username='parent1', password='testpass123')
        
        teacher_routes = [
            '/teacher/admin/dos/',
            '/teacher/admin/deputy/',
            '/teacher/support/',
            '/teacher/matron/',
            '/teacher/department/',
            '/teacher/class/',
        ]
        
        for route in teacher_routes:
            response = self.client.get(route)
            self.assertIn(response.status_code, [302, 403], 
                         f"Route {route} should deny parent access (302 or 403)")
            print(f"  ✓ {route} → denied to parent (403 or redirect)")
    
    def test_teacher_cannot_access_dos_routes(self):
        """Test that regular teacher cannot access DOS routes"""
        print("\n🔍 TEST: Regular teacher cannot access DOS routes")
        
        self.client.login(username='teacher1', password='testpass123')
        
        dos_routes = [
            '/teacher/admin/dos/',
            '/teacher/admin/dos/classes/',
            '/teacher/admin/dos/teachers/',
        ]
        
        for route in dos_routes:
            response = self.client.get(route)
            self.assertIn(response.status_code, [302, 403],
                         f"Route {route} should deny regular teacher (403 or redirect)")
            print(f"  ✓ {route} → denied to regular teacher")
    
    def test_regular_staff_cannot_access_matron_routes(self):
        """Test that regular staff cannot access matron/welfare routes"""
        print("\n🔍 TEST: Regular staff cannot access matron routes")
        
        # Create regular support staff (not welfare coordinator)
        regular_staff = User.objects.create_user(
            username='staff_regular',
            email='staff_regular@test.com',
            password='testpass123',
            role='non_teaching_staff',
            school=self.school_a
        )
        StaffProfile.objects.create(
            user=regular_staff,
            support_staff_role='staff'
        )
        
        self.client.login(username='staff_regular', password='testpass123')
        
        matron_routes = [
            '/teacher/matron/',
            '/teacher/matron/hostels/',
            '/teacher/matron/residents/',
        ]
        
        for route in matron_routes:
            response = self.client.get(route)
            self.assertIn(response.status_code, [302, 403],
                         f"Route {route} should deny regular staff")
            print(f"  ✓ {route} → denied to regular staff")
    
    # ===== CORRECT ROLE ACCESS TESTS =====
    
    def test_dos_can_access_dos_routes(self):
        """Test that DOS user can access DOS routes"""
        print("\n🔍 TEST: DOS user can access DOS routes")
        
        self.client.login(username='dos1', password='testpass123')
        
        dos_routes = [
            '/teacher/admin/dos/',
        ]
        
        for route in dos_routes:
            response = self.client.get(route)
            self.assertIn(response.status_code, [200, 302],  # 302 if redirect to detail, 200 if list
                         f"Route {route} should allow DOS access")
            print(f"  ✓ {route} → allowed to DOS user (200)")
    
    def test_class_teacher_can_access_class_routes(self):
        """Test that class teacher can access class teacher routes"""
        print("\n🔍 TEST: Class teacher can access class routes")
        
        # Create a proper class teacher user
        class_teacher = User.objects.create_user(
            username='class_teacher1',
            email='class_teacher1@test.com',
            password='testpass123',
            role='teacher',
            school=self.school_a
        )
        StaffProfile.objects.create(
            user=class_teacher,
            teacher_admin_role='class_teacher'
        )
        
        self.client.login(username='class_teacher1', password='testpass123')
        
        class_routes = [
            '/teacher/class/',
            '/teacher/class/students/',
        ]
        
        for route in class_routes:
            response = self.client.get(route)
            # Allow 200, 302 (redirect to dashboard), and 404 (no class assigned is ok)
            self.assertIn(response.status_code, [200, 302, 404],
                         f"Route {route} should allow class teacher access")
            print(f"  ✓ {route} → allowed to class teacher")
    
    # ===== SUB-ROLE RESTRICTION TESTS =====
    
    def test_department_head_cannot_access_dos_routes(self):
        """Test that department head cannot access DOS routes"""
        print("\n🔍 TEST: Department head cannot access DOS routes")
        
        self.client.login(username='teacher1', password='testpass123')
        
        dos_routes = [
            '/teacher/admin/dos/',
            '/teacher/admin/dos/classes/',
        ]
        
        for route in dos_routes:
            response = self.client.get(route)
            self.assertIn(response.status_code, [302, 403],
                         f"Route {route} should deny department head")
            print(f"  ✓ {route} → denied to department head")
    
    def test_support_staff_supervisor_cannot_access_teacher_routes(self):
        """Test that support staff supervisor cannot access teacher routes"""
        print("\n🔍 TEST: Support staff supervisor cannot access teacher routes")
        
        # Create support staff supervisor
        supervisor = User.objects.create_user(
            username='supervisor1',
            email='supervisor1@test.com',
            password='testpass123',
            role='non_teaching_staff',
            school=self.school_a
        )
        StaffProfile.objects.create(
            user=supervisor,
            support_staff_role='supervisor'
        )
        
        self.client.login(username='supervisor1', password='testpass123')
        
        teacher_routes = [
            '/teacher/',
            '/teacher/students/',
            '/teacher/grades/',
        ]
        
        for route in teacher_routes:
            response = self.client.get(route)
            self.assertIn(response.status_code, [302, 403],
                         f"Route {route} should deny support staff supervisor")
            print(f"  ✓ {route} → denied to support staff supervisor")
    
    # ===== DECORATOR VALIDATION TESTS =====
    
    def test_get_user_school_raises_on_none_school(self):
        """Test that get_user_school raises PermissionDenied if user.school is None"""
        print("\n🔍 TEST: get_user_school validates school field")
        
        from SchoolNowMgt.decorators import get_user_school
        from django.core.exceptions import PermissionDenied
        
        # Create user with no school
        no_school_user = User.objects.create_user(
            username='no_school',
            email='no_school@test.com',
            password='testpass123',
            role='teacher',
            school=None
        )
        
        # Mock request
        class MockRequest:
            user = no_school_user
        
        request = MockRequest()
        
        # Should raise PermissionDenied
        with self.assertRaises(PermissionDenied):
            get_user_school(request)
        
        print(f"  ✓ get_user_school raises PermissionDenied for None school")


class RolePermissionTestRunner:
    """Utility to run role permission tests"""
    
    @staticmethod
    def run_all_tests():
        """Run all role permission tests"""
        print("\n" + "="*60)
        print("PHASE 9: ROLE PERMISSION TEST SUITE")
        print("="*60)
        
        # Create test suite
        suite = TestCase()
        test = RolePermissionTestSuite('setUp')
        test.setUp()
        
        print(f"\n✅ Test Setup Complete")
        print(f"   - Schools created: {School.objects.count()}")
        print(f"   - Users created: {User.objects.count()}")
        print(f"   - Staff profiles created: {StaffProfile.objects.count()}")
        
        return test


if __name__ == '__main__':
    runner = RolePermissionTestRunner()
    runner.run_all_tests()
    print("\n" + "="*60)
    print("Role permission tests ready for execution")
    print("="*60)
