from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import resolve

from SchoolNowMgt.models import School, StaffProfile


@override_settings(ALLOWED_HOSTS=['127.0.0.1', 'testserver'])
class RegistrationFlowTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name='Test School',
            registration_number='TEST-001',
            address='Main Street',
            phone='123456',
            email='school@example.com',
        )

    def test_teacher_registration_creates_user_and_staff_profile(self):
        response = self.client.post('/auth/register/', {
            'role': 'teacher',
            'first_name': 'Test',
            'last_name': 'Teacher',
            'email': 'teacher-reg@example.com',
            'password1': 'Password123!',
            'password2': 'Password123!',
        }, HTTP_HOST='127.0.0.1')

        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(email='teacher-reg@example.com')
        self.assertEqual(user.role, 'teacher')
        self.assertTrue(StaffProfile.objects.filter(user=user).exists())

    def test_support_staff_registration_creates_user_and_staff_profile(self):
        response = self.client.post('/auth/register/', {
            'role': 'non_teaching_staff',
            'first_name': 'Support',
            'last_name': 'Staff',
            'email': 'support-reg@example.com',
            'password1': 'Password123!',
            'password2': 'Password123!',
        }, HTTP_HOST='127.0.0.1')

        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(email='support-reg@example.com')
        self.assertEqual(user.role, 'non_teaching_staff')
        self.assertTrue(StaffProfile.objects.filter(user=user).exists())

    def test_leadership_role_signups_redirect_to_their_dashboards(self):
        cases = [
            ('dos', 'teacher', '/teacher/admin/dos/'),
            ('deputy_hm', 'teacher', '/teacher/admin/deputy/'),
            ('head_teacher', 'teacher', '/teacher/admin/head-teacher/'),
            ('department_head', 'teacher', '/teacher/department/'),
            ('welfare_coordinator', 'non_teaching_staff', '/teacher/matron/'),
            ('supervisor', 'non_teaching_staff', '/teacher/support/shift-supervisor/'),
        ]

        for admin_role, role, expected_url in cases:
            with self.subTest(admin_role=admin_role):
                email = f'{admin_role}-signup@example.com'
                response = self.client.post('/auth/register/', {
                    'role': role,
                    'first_name': 'Leadership',
                    'last_name': 'User',
                    'email': email,
                    'password1': 'Password123!',
                    'password2': 'Password123!',
                    'admin_role': admin_role,
                }, HTTP_HOST='127.0.0.1')

                self.assertEqual(response.status_code, 302, msg=f'{admin_role} signup failed')
                self.assertRedirects(response, expected_url, fetch_redirect_response=False)

                user = get_user_model().objects.get(email=email)
                if role == 'teacher':
                    self.assertEqual(user.staffprofile.teacher_admin_role, admin_role)
                else:
                    self.assertEqual(user.staffprofile.support_staff_role, admin_role)
