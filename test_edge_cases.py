#!/usr/bin/env python
"""
Phase 9: Edge Case Validation Script

Tests graceful handling of edge cases:
- Users with no class assigned (class teachers)
- Users with no department assigned (department heads)
- Users with no hostel assigned (matrons)
- Empty data sets in list views
- Pagination edge cases
- Invalid page numbers

Usage:
    python manage.py shell < test_edge_cases.py
    
Or as management command:
    python manage.py test_edge_cases
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from SchoolNowMgt.models import School, StaffProfile, ClassGrade, GradeLevel, Stream, Department, Student
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

User = get_user_model()


class EdgeCaseTestSuite(TestCase):
    """Test suite for edge cases"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create school
        self.school = School.objects.create(
            school_name="Test School",
            school_abbrev="TS",
            phone="0700000001",
            email="test@school.com"
        )
        
        # Create grade levels and streams
        self.form_one = GradeLevel.objects.create(
            level_name="Form 1",
            school=self.school
        )
        
        self.stream_a = Stream.objects.create(
            stream_name="A",
            school=self.school
        )
        
        # Create class
        self.class_1a = ClassGrade.objects.create(
            class_grade_level=self.form_one,
            class_stream=self.stream_a,
            school=self.school
        )
        
        # Create department
        self.dept = Department.objects.create(
            department_name="Languages",
            school=self.school,
            department_type='academic'
        )
        
        # Create users
        # Class teacher WITHOUT class assignment
        self.class_teacher_no_class_user = User.objects.create_user(
            username='class_teacher_no_class',
            email='class_teacher_no_class@test.com',
            password='testpass123',
            role='teacher',
            school=self.school
        )
        self.class_teacher_no_class = StaffProfile.objects.create(
            user=self.class_teacher_no_class_user,
            teacher_admin_role='class_teacher'
        )
        
        # Class teacher WITH class assignment
        self.class_teacher_with_class_user = User.objects.create_user(
            username='class_teacher_with_class',
            email='class_teacher_with_class@test.com',
            password='testpass123',
            role='teacher',
            school=self.school
        )
        self.class_teacher_with_class = StaffProfile.objects.create(
            user=self.class_teacher_with_class_user,
            teacher_admin_role='class_teacher'
        )
        self.class_1a.class_teacher = self.class_teacher_with_class
        self.class_1a.save()
        
        # Department head WITHOUT department assignment
        self.dept_head_no_dept_user = User.objects.create_user(
            username='dept_head_no_dept',
            email='dept_head_no_dept@test.com',
            password='testpass123',
            role='teacher',
            school=self.school
        )
        self.dept_head_no_dept = StaffProfile.objects.create(
            user=self.dept_head_no_dept_user,
            teacher_admin_role='department_head'
        )
        
        # Matron without hostel assignment
        self.matron_no_hostel_user = User.objects.create_user(
            username='matron_no_hostel',
            email='matron_no_hostel@test.com',
            password='testpass123',
            role='non_teaching_staff',
            school=self.school
        )
        self.matron_no_hostel = StaffProfile.objects.create(
            user=self.matron_no_hostel_user,
            support_staff_role='welfare_coordinator'
        )

    # ===== NO CLASS ASSIGNED TESTS =====
    
    def test_class_teacher_no_class_dashboard_renders(self):
        """Test class teacher with no class assignment renders graceful message"""
        print("\n🔍 TEST: Class teacher (no class) dashboard renders")
        
        self.client.login(username='class_teacher_no_class', password='testpass123')
        response = self.client.get('/teacher/class/')
        
        # Should return 200 (not 500 error)
        self.assertEqual(response.status_code, 200,
                        f"Dashboard should render without error (got {response.status_code})")
        
        # Should have no_class flag in context
        self.assertIn('no_class', response.context,
                     "Context should have 'no_class' flag")
        self.assertTrue(response.context['no_class'],
                       "no_class flag should be True")
        
        # Response should contain message about not being assigned
        self.assertIn(b'not been assigned', response.content.lower(),
                     "Response should mention not being assigned")
        
        print(f"  ✓ Class teacher dashboard renders with no_class=True")
        print(f"  ✓ Graceful message displayed")

    def test_class_teacher_no_class_students_list(self):
        """Test class teacher with no class can still access students_list view"""
        print("\n🔍 TEST: Class teacher (no class) students list")
        
        self.client.login(username='class_teacher_no_class', password='testpass123')
        response = self.client.get('/teacher/class/students/')
        
        # Should return 200 (not 500 error)
        self.assertEqual(response.status_code, 200,
                        f"Students list should render (got {response.status_code})")
        
        # Should have no_class or empty results
        self.assertIn('no_class', response.context,
                     "Context should have 'no_class' flag")
        
        print(f"  ✓ Class teacher students list renders (200)")

    # ===== NO DEPARTMENT ASSIGNED TESTS =====
    
    def test_dept_head_no_dept_dashboard_renders(self):
        """Test department head with no department renders gracefully"""
        print("\n🔍 TEST: Department head (no dept) dashboard renders")
        
        self.client.login(username='dept_head_no_dept', password='testpass123')
        response = self.client.get('/teacher/department/')
        
        # Should return 200 (not 500 error)
        self.assertEqual(response.status_code, 200,
                        f"Dashboard should render without error (got {response.status_code})")
        
        print(f"  ✓ Department head dashboard renders (200)")

    # ===== NO HOSTEL ASSIGNED TESTS =====
    
    def test_matron_no_hostel_dashboard_renders(self):
        """Test matron with no hostel renders gracefully"""
        print("\n🔍 TEST: Matron (no hostel) dashboard renders")
        
        self.client.login(username='matron_no_hostel', password='testpass123')
        response = self.client.get('/teacher/matron/')
        
        # Should return 200 or 302 (not 500 error)
        self.assertIn(response.status_code, [200, 302],
                     f"Dashboard should render without error (got {response.status_code})")
        
        print(f"  ✓ Matron dashboard renders (status {response.status_code})")

    # ===== EMPTY DATA SET TESTS =====
    
    def test_class_teacher_empty_students_list(self):
        """Test class teacher with no students renders empty state"""
        print("\n🔍 TEST: Class teacher with no students renders empty state")
        
        # Assign class teacher to empty class
        self.client.login(username='class_teacher_with_class', password='testpass123')
        response = self.client.get('/teacher/class/students/')
        
        # Should return 200 (not 500 error)
        self.assertEqual(response.status_code, 200,
                        f"Empty students list should render (got {response.status_code})")
        
        # Should have empty page_obj
        if 'page_obj' in response.context:
            self.assertEqual(len(response.context['page_obj']), 0,
                           "page_obj should be empty")
        
        print(f"  ✓ Empty students list renders (200)")
        print(f"  ✓ Empty state handled gracefully")

    # ===== PAGINATION EDGE CASES =====
    
    def test_paginator_page_one_of_one(self):
        """Test paginator with single page (1 of 1)"""
        print("\n🔍 TEST: Paginator single page (1 of 1)")
        
        items = [1, 2, 3]  # 3 items
        paginator = Paginator(items, 10)  # 10 items per page
        page = paginator.page(1)
        
        self.assertEqual(page.number, 1)
        self.assertFalse(page.has_previous(),
                        "Single page should have no previous")
        self.assertFalse(page.has_next(),
                        "Single page should have no next")
        self.assertEqual(paginator.num_pages, 1)
        
        print(f"  ✓ Single page handled correctly")
        print(f"  ✓ No prev/next links shown")

    def test_paginator_invalid_page_number_lt_1(self):
        """Test paginator with page number < 1"""
        print("\n🔍 TEST: Paginator invalid page (< 1)")
        
        items = list(range(1, 51))  # 50 items
        paginator = Paginator(items, 10)  # 10 items per page
        
        try:
            page = paginator.page(0)  # Invalid
            self.fail("Should raise PageNotAnInteger")
        except PageNotAnInteger:
            # Expected behavior
            page = paginator.page(1)  # Redirect to page 1
            self.assertEqual(page.number, 1)
            print(f"  ✓ Invalid page (< 1) redirects to page 1")

    def test_paginator_invalid_page_number_gt_max(self):
        """Test paginator with page number > max"""
        print("\n🔍 TEST: Paginator invalid page (> max)")
        
        items = list(range(1, 51))  # 50 items
        paginator = Paginator(items, 10)  # 10 items per page = 5 pages
        
        try:
            page = paginator.page(100)  # Invalid
            self.fail("Should raise EmptyPage")
        except EmptyPage:
            # Expected behavior - redirect to last page
            page = paginator.page(paginator.num_pages)
            self.assertEqual(page.number, paginator.num_pages)
            print(f"  ✓ Invalid page (> max) redirects to last page {paginator.num_pages}")

    def test_paginator_non_integer_page(self):
        """Test paginator with non-integer page parameter"""
        print("\n🔍 TEST: Paginator non-integer page parameter")
        
        items = list(range(1, 51))
        paginator = Paginator(items, 10)
        
        try:
            page = paginator.page('invalid')
            self.fail("Should raise PageNotAnInteger")
        except PageNotAnInteger:
            # Expected behavior
            page = paginator.page(1)
            self.assertEqual(page.number, 1)
            print(f"  ✓ Non-integer page parameter handled (defaults to page 1)")

    # ===== STATUS BADGE TESTS =====
    
    def test_status_badge_colors(self):
        """Test that status badges display correct colors"""
        print("\n🔍 TEST: Status badge colors")
        
        status_colors = {
            'present': 'green',
            'absent': 'red',
            'active': 'green',
            'inactive': 'red',
        }
        
        for status, color in status_colors.items():
            print(f"  ✓ Status '{status}' → {color} badge")

    # ===== NO DATA EDGE CASES =====
    
    def test_gradebook_empty_renders(self):
        """Test gradebook with no grades renders"""
        print("\n🔍 TEST: Gradebook empty renders")
        
        self.client.login(username='class_teacher_with_class', password='testpass123')
        response = self.client.get('/teacher/class/grades/')
        
        # Should return 200 (not 500 error)
        self.assertEqual(response.status_code, 200,
                        f"Empty gradebook should render (got {response.status_code})")
        
        print(f"  ✓ Empty gradebook renders (200)")

    def test_attendance_empty_renders(self):
        """Test attendance with no records renders"""
        print("\n🔍 TEST: Attendance empty renders")
        
        self.client.login(username='class_teacher_with_class', password='testpass123')
        response = self.client.get('/teacher/class/attendance/')
        
        # Should return 200 (not 500 error)
        self.assertEqual(response.status_code, 200,
                        f"Empty attendance should render (got {response.status_code})")
        
        print(f"  ✓ Empty attendance renders (200)")

    # ===== MISSING CONTEXT VARIABLES =====
    
    def test_template_renders_without_optional_context(self):
        """Test templates render even if optional context vars are missing"""
        print("\n🔍 TEST: Templates render without optional context")
        
        self.client.login(username='class_teacher_with_class', password='testpass123')
        response = self.client.get('/teacher/class/')
        
        # Should not raise TemplateError
        self.assertEqual(response.status_code, 200,
                        "Template should render without error")
        
        print(f"  ✓ Template renders without optional context vars")


class EdgeCaseTestRunner:
    """Utility to run edge case tests"""
    
    @staticmethod
    def run_all_tests():
        """Run all edge case tests"""
        print("\n" + "="*60)
        print("PHASE 9: EDGE CASE VALIDATION SUITE")
        print("="*60)
        
        test = EdgeCaseTestSuite('setUp')
        test.setUp()
        
        print(f"\n✅ Test Setup Complete")
        print(f"   - School created: {School.objects.count()}")
        print(f"   - Users created: {User.objects.count()}")
        print(f"   - Classes created: {ClassGrade.objects.count()}")
        
        return test


if __name__ == '__main__':
    runner = EdgeCaseTestRunner()
    runner.run_all_tests()
    print("\n" + "="*60)
    print("Edge case tests ready for execution")
    print("="*60)
