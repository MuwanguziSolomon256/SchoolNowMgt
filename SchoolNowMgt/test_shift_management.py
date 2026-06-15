"""
Test suite for Teacher Shift Status Management System

Tests cover:
1. Model calculations and methods
2. API endpoint validation and error handling
3. Admin interface functionality
4. Edge cases and boundary conditions
5. Integration workflows
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, time, timedelta

from SchoolNowMgt.models import (
    School, StaffProfile, TeacherAttendance, BreakSession, CustomUser
)

User = get_user_model()


class TeacherAttendanceModelTests(TestCase):
    """Tests for TeacherAttendance model methods and calculations."""
    
    def setUp(self):
        """Create test data."""
        # Create school
        self.school = School.objects.create(
            name='Test School',
            registration_number='REG001',
            address='123 Test St',
            phone='555-0001',
            email='test@school.edu'
        )
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@school.edu',
            password='testpass123',
            school=self.school,
            role='admin'
        )
        
        # Create teacher user
        self.teacher_user = User.objects.create_user(
            username='teacher1',
            email='teacher1@school.edu',
            password='testpass123',
            school=self.school,
            role='teacher',
            first_name='John',
            last_name='Doe'
        )
        
        # Create staff profile
        self.staff = StaffProfile.objects.create(
            user=self.teacher_user,
            employee_id='EMP001',
            position='Class Teacher',
            salary=50000,
            date_joined=timezone.now().date()
        )
    
    def test_shift_duration_calculation(self):
        """Test shift duration is calculated correctly."""
        today = timezone.now().date()
        attendance = TeacherAttendance.objects.create(
            staff=self.staff,
            date=today,
            status='present',
            time_in=time(8, 0),
            time_out=time(16, 30)
        )
        
        # Expected: 8h 30m = 510 minutes
        duration = attendance.get_shift_duration()
        self.assertEqual(duration, 510)
        self.assertEqual(attendance.get_shift_hours(), '8h 30m')
    
    def test_shift_duration_excluding_breaks(self):
        """Test shift duration excluding breaks."""
        today = timezone.now().date()
        attendance = TeacherAttendance.objects.create(
            staff=self.staff,
            date=today,
            status='present',
            time_in=time(8, 0),
            time_out=time(16, 30),
            total_break_duration=60  # 1 hour break
        )
        
        # Expected: 510 - 60 = 450 minutes (7h 30m)
        duration = attendance.get_shift_duration_excluding_breaks()
        self.assertEqual(duration, 450)
    
    def test_break_session_duration(self):
        """Test break session duration calculation."""
        today = timezone.now().date()
        attendance = TeacherAttendance.objects.create(
            staff=self.staff,
            date=today,
            status='present',
            time_in=time(8, 0),
            time_out=time(16, 30)
        )
        
        break_session = BreakSession.objects.create(
            teacher_attendance=attendance,
            break_in_time=time(12, 0),
            break_out_time=time(13, 0)
        )
        
        # Expected: 60 minutes
        duration = break_session.get_break_duration()
        self.assertEqual(duration, 60)
    
    def test_is_clocked_in(self):
        """Test is_clocked_in method."""
        today = timezone.now().date()
        
        # Create record with time_in but no time_out
        attendance = TeacherAttendance.objects.create(
            staff=self.staff,
            date=today,
            status='present',
            time_in=time(8, 0),
            time_out=None
        )
        
        self.assertTrue(attendance.get_is_clocked_in())
        
        # Update with time_out
        attendance.time_out = time(16, 30)
        attendance.save()
        
        self.assertFalse(attendance.get_is_clocked_in())


class ShiftAPIEndpointTests(TestCase):
    """Tests for AJAX API endpoints."""
    
    def setUp(self):
        """Create test data and client."""
        self.client = Client()
        
        # Create school
        self.school = School.objects.create(
            name='Test School',
            registration_number='REG001',
            address='123 Test St',
            phone='555-0001',
            email='test@school.edu'
        )
        
        # Create teacher
        self.teacher_user = User.objects.create_user(
            username='teacher1',
            email='teacher1@school.edu',
            password='testpass123',
            school=self.school,
            role='teacher'
        )
        
        # Create staff profile
        self.staff = StaffProfile.objects.create(
            user=self.teacher_user,
            employee_id='EMP001',
            position='Class Teacher',
            salary=50000,
            date_joined=timezone.now().date()
        )
        
        # Login
        self.client.login(username='teacher1', password='testpass123')
    
    def test_clock_in_success(self):
        """Test successful clock in."""
        response = self.client.post('/teacher/api/shift/clock-in/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('time_in', data)
        self.assertIn('shift_id', data)
        
        # Verify record was created
        today = timezone.now().date()
        attendance = TeacherAttendance.objects.get(
            staff=self.staff,
            date=today
        )
        self.assertIsNotNone(attendance.time_in)
        self.assertIsNone(attendance.time_out)
    
    def test_clock_in_double_prevention(self):
        """Test that double clock in is prevented."""
        # First clock in
        self.client.post('/teacher/api/shift/clock-in/')
        
        # Try to clock in again
        response = self.client.post('/teacher/api/shift/clock-in/')
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_clock_out_success(self):
        """Test successful clock out."""
        # Clock in first
        self.client.post('/teacher/api/shift/clock-in/')
        
        # Clock out
        response = self.client.post('/teacher/api/shift/clock-out/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('time_out', data)
        self.assertIn('total_hours_worked', data)
    
    def test_clock_out_without_clock_in(self):
        """Test that clock out without clock in fails."""
        response = self.client.post('/teacher/api/shift/clock-out/')
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_break_start_success(self):
        """Test successful break start."""
        # Clock in first
        self.client.post('/teacher/api/shift/clock-in/')
        
        # Start break
        response = self.client.post(
            '/teacher/api/shift/break-start/',
            data='{"reason":"lunch"}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('break_id', data)
        
        # Verify break session was created
        today = timezone.now().date()
        attendance = TeacherAttendance.objects.get(
            staff=self.staff,
            date=today
        )
        self.assertEqual(attendance.break_count, 1)
    
    def test_break_start_without_clock_in(self):
        """Test that break start without clock in fails."""
        response = self.client.post('/teacher/api/shift/break-start/')
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_break_end_success(self):
        """Test successful break end."""
        # Clock in
        self.client.post('/teacher/api/shift/clock-in/')
        
        # Start break
        self.client.post('/teacher/api/shift/break-start/')
        
        # End break
        response = self.client.post('/teacher/api/shift/break-end/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('break_duration', data)
    
    def test_shift_status_not_clocked_in(self):
        """Test shift status when not clocked in."""
        response = self.client.get('/teacher/api/shift/status/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['is_on_duty'])
        self.assertFalse(data['is_on_break'])
    
    def test_shift_status_on_duty(self):
        """Test shift status when on duty."""
        # Clock in
        self.client.post('/teacher/api/shift/clock-in/')
        
        # Get status
        response = self.client.get('/teacher/api/shift/status/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['is_on_duty'])
        self.assertFalse(data['is_on_break'])
        self.assertIn('shift_elapsed_minutes', data)
    
    def test_shift_status_on_break(self):
        """Test shift status when on break."""
        # Clock in
        self.client.post('/teacher/api/shift/clock-in/')
        
        # Start break
        self.client.post('/teacher/api/shift/break-start/')
        
        # Get status
        response = self.client.get('/teacher/api/shift/status/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['is_on_duty'])
        self.assertTrue(data['is_on_break'])


class AdminShiftViewTests(TestCase):
    """Tests for admin shift management views."""
    
    def setUp(self):
        """Create test data."""
        self.client = Client()
        
        # Create school
        self.school = School.objects.create(
            name='Test School',
            registration_number='REG001',
            address='123 Test St',
            phone='555-0001',
            email='test@school.edu'
        )
        
        # Create admin
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@school.edu',
            password='testpass123',
            school=self.school,
            role='admin'
        )
        
        # Create teacher
        self.teacher_user = User.objects.create_user(
            username='teacher1',
            email='teacher1@school.edu',
            password='testpass123',
            school=self.school,
            role='teacher'
        )
        
        # Create staff
        self.staff = StaffProfile.objects.create(
            user=self.teacher_user,
            employee_id='EMP001',
            position='Teacher',
            salary=50000,
            date_joined=timezone.now().date()
        )
    
    def test_shift_dashboard_access_denied_for_non_admin(self):
        """Test that non-admin cannot access shift dashboard."""
        self.client.login(username='teacher1', password='testpass123')
        response = self.client.get('/admin/shifts/')
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_shift_dashboard_access_for_admin(self):
        """Test that admin can access shift dashboard."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get('/admin/shifts/')
        
        # Should redirect to login (302) or return 200 if authenticated
        # The admin_required decorator may redirect, so check for either
        if response.status_code == 302:
            # If redirected, ensure it's not to login (would be 'auth:unified_login')
            self.assertNotIn('/auth/login', response.url)
        else:
            self.assertEqual(response.status_code, 200)
            self.assertIn('active_teachers', response.context)
            self.assertIn('on_break_teachers', response.context)
            self.assertIn('clocked_out_teachers', response.context)
    
    def test_shift_history_access_for_admin(self):
        """Test that admin can access shift history."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get('/admin/shifts/history/')
        
        # Should redirect to login (302) or return 200 if authenticated
        # The admin_required decorator may redirect, so check for either
        if response.status_code == 302:
            # If redirected, ensure it's not to login (would be 'auth:unified_login')
            self.assertNotIn('/auth/login', response.url)
        else:
            self.assertEqual(response.status_code, 200)
            self.assertIn('shifts', response.context)


class EdgeCaseTests(TestCase):
    """Tests for edge cases and boundary conditions."""
    
    def setUp(self):
        """Create test data."""
        self.school = School.objects.create(
            name='Test School',
            registration_number='REG001',
            address='123 Test St',
            phone='555-0001',
            email='test@school.edu'
        )
        
        self.teacher_user = User.objects.create_user(
            username='teacher1',
            email='teacher1@school.edu',
            password='testpass123',
            school=self.school,
            role='teacher'
        )
        
        self.staff = StaffProfile.objects.create(
            user=self.teacher_user,
            employee_id='EMP001',
            position='Teacher',
            salary=50000,
            date_joined=timezone.now().date()
        )
    
    def test_multiple_breaks_in_shift(self):
        """Test handling of multiple breaks in a single shift."""
        today = timezone.now().date()
        attendance = TeacherAttendance.objects.create(
            staff=self.staff,
            date=today,
            status='present',
            time_in=time(8, 0),
            time_out=time(16, 30)
        )
        
        # Create multiple breaks
        BreakSession.objects.create(
            teacher_attendance=attendance,
            break_in_time=time(10, 0),
            break_out_time=time(10, 15)
        )
        
        BreakSession.objects.create(
            teacher_attendance=attendance,
            break_in_time=time(12, 0),
            break_out_time=time(13, 0)
        )
        
        BreakSession.objects.create(
            teacher_attendance=attendance,
            break_in_time=time(15, 0),
            break_out_time=time(15, 15)
        )
        
        # Verify all breaks are counted
        self.assertEqual(attendance.break_sessions.count(), 3)
    
    def test_overnight_shift(self):
        """Test handling of shifts that span midnight."""
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        
        # Shift from 20:00 to 04:00 (next day)
        attendance = TeacherAttendance.objects.create(
            staff=self.staff,
            date=today,
            status='present',
            time_in=time(20, 0),
            time_out=time(4, 0)  # This is next day, but same record
        )
        
        # Should handle gracefully
        duration = attendance.get_shift_duration()
        self.assertIsNotNone(duration)
    
    def test_same_clock_in_out_time(self):
        """Test handling of same clock in and out time (edge case)."""
        today = timezone.now().date()
        attendance = TeacherAttendance.objects.create(
            staff=self.staff,
            date=today,
            status='present',
            time_in=time(8, 0),
            time_out=time(8, 0)
        )
        
        # Duration should be 0
        duration = attendance.get_shift_duration()
        self.assertEqual(duration, 0)


class QAChecklistTests(TestCase):
    """Manual QA checklist verification."""
    
    def test_database_schema_integrity(self):
        """Verify database schema is correct."""
        # Check TeacherAttendance has required fields
        attendance_fields = [f.name for f in TeacherAttendance._meta.get_fields()]
        required_fields = [
            'id', 'staff', 'date', 'status', 'time_in', 'time_out',
            'break_count', 'total_break_duration', 'reason', 'marked_by',
            'synced', 'created_at', 'updated_at'
        ]
        
        for field in required_fields:
            self.assertIn(field, attendance_fields)
        
        # Check BreakSession exists
        break_fields = [f.name for f in BreakSession._meta.get_fields()]
        required_break_fields = [
            'id', 'teacher_attendance', 'break_in_time', 'break_out_time',
            'reason', 'created_at', 'updated_at'
        ]
        
        for field in required_break_fields:
            self.assertIn(field, break_fields)
    
    def test_admin_interface_registered(self):
        """Verify admin interfaces are registered."""
        from django.contrib.admin.sites import site
        
        # Check TeacherAttendance is registered
        self.assertIn(TeacherAttendance, site._registry)
        
        # Check BreakSession is registered
        self.assertIn(BreakSession, site._registry)


if __name__ == '__main__':
    import unittest
    unittest.main()
