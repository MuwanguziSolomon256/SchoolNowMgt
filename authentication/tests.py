from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model

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
