from datetime import date

from django.test import TestCase
from django.urls import reverse

from SchoolNowMgt.models import CustomUser, School, StaffProfile, StaffAttendance


class ShiftSupervisorDashboardTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name='Test School',
            registration_number='REG-002',
            address='Test Address',
            phone='123456789',
            email='school2@example.com',
        )
        self.user = CustomUser.objects.create_user(
            username='supervisor',
            email='supervisor@example.com',
            password='password123',
            school=self.school,
            role='non_teaching_staff',
            first_name='Ada',
            last_name='Lovelace',
        )
        self.staff_profile = StaffProfile.objects.create(
            user=self.user,
            employee_id='EMP-002',
            position='Shift Supervisor',
            salary=0,
            date_joined=date.today(),
            support_staff_role='supervisor',
        )

    def test_shift_supervisor_dashboard_loads(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('teacher:support_staff:shift_supervisor_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Operations Command Center')

    def test_shift_attendance_list_loads(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('teacher:support_staff:shift_attendance_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Shift Attendance')

    def test_support_staff_navigation_dashboards_load(self):
        self.client.force_login(self.user)
        pages = [
            ('messages_dashboard', 'Messages Center'),
            ('calendar_dashboard', 'Calendar Overview'),
            ('announcements_dashboard', 'Announcements'),
            ('payments_dashboard', 'Payments Overview'),
            ('staff_roster_dashboard', 'Staff Roster'),
            ('maintenance_dashboard', 'Maintenance Board'),
            ('supply_requests_dashboard', 'Supply Requests'),
        ]

        for url_name, expected_text in pages:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(f'teacher:support_staff:{url_name}'))
                self.assertEqual(response.status_code, 200, msg=url_name)
                self.assertContains(response, expected_text)
