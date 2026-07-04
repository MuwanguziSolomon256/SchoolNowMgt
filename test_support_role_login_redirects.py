from django.test import TestCase
from django.contrib.auth import get_user_model
from SchoolNowMgt.models import School, StaffProfile

User = get_user_model()


class SupportRoleLoginRedirectTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name='Test School',
            registration_number='TEST-001',
            address='Test Address',
            phone='0700000000',
            email='testschool@example.com'
        )

        self.matron_user = User.objects.create_user(
            username='matron_redirect_test',
            email='matron_redirect_test@test.com',
            password='password123',
            role='non_teaching_staff',
            school=self.school,
        )
        StaffProfile.objects.create(
            user=self.matron_user,
            teacher_admin_role='matron',
        )

        self.supervisor_user = User.objects.create_user(
            username='supervisor_redirect_test',
            email='supervisor_redirect_test@test.com',
            password='password123',
            role='non_teaching_staff',
            school=self.school,
        )
        StaffProfile.objects.create(
            user=self.supervisor_user,
            teacher_admin_role='shift_supervisor',
        )

    def test_matron_login_redirects_to_matron_dashboard(self):
        response = self.client.post('/auth/login/', {
            'role': 'non_teaching_staff',
            'email': 'matron_redirect_test@test.com',
            'password': 'password123',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Matron Dashboard')

    def test_supervisor_login_redirects_to_shift_supervisor_dashboard(self):
        response = self.client.post('/auth/login/', {
            'role': 'non_teaching_staff',
            'email': 'supervisor_redirect_test@test.com',
            'password': 'password123',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Shift Supervisor')
