from datetime import date

from django.test import TestCase
from django.urls import reverse

from SchoolNowMgt.models import CustomUser, School, StaffProfile


class DeputyDashboardNavigationTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name='Test School',
            registration_number='REG-001',
            address='Test Address',
            phone='123456789',
            email='school@example.com',
        )
        self.user = CustomUser.objects.create_user(
            username='deputy',
            email='deputy@example.com',
            password='password123',
            school=self.school,
            role='teacher',
            first_name='Jane',
            last_name='Doe',
            phone='0712345678',
        )
        self.staff_profile = StaffProfile.objects.create(
            user=self.user,
            employee_id='EMP-001',
            position='Deputy Headmaster',
            salary=0,
            date_joined=date.today(),
            teacher_admin_role='deputy_hm',
        )

    def test_deputy_profile_page_is_available(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('SchoolNowMgt:deputy_hm:profile'))
        self.assertEqual(response.status_code, 200)

    def test_deputy_discipline_log_page_is_available(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('SchoolNowMgt:deputy_hm:discipline_log'))
        self.assertEqual(response.status_code, 200)

    def test_deputy_staff_tracking_page_shows_dashboard_heading(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('SchoolNowMgt:deputy_hm:support_staff_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Staff Tracking Dashboard')
