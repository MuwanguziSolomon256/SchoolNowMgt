from datetime import date

from django.test import TestCase
from django.urls import reverse

from SchoolNowMgt.models import (
    CustomUser,
    School,
    StaffProfile,
    TeacherDepartment,
    Subject,
    ClassGrade,
    Timetable,
)


class TeacherDepartmentSubjectMatchingTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name='Test School',
            registration_number='REG-002',
            address='Test Address',
            phone='123456789',
            email='school2@example.com',
        )
        self.department = TeacherDepartment.objects.create(
            school=self.school,
            name='Mathematics',
            department_type='mathematics',
            description='Core maths department',
        )
        self.maths = Subject.objects.create(
            name='Mathematics',
            code='MTH',
            curriculum='national',
        )
        self.english = Subject.objects.create(
            name='English',
            code='ENG',
            curriculum='national',
        )

    def test_matching_subjects_uses_department_name(self):
        matching = self.department.matching_subjects()
        self.assertIn(self.maths, matching)
        self.assertNotIn(self.english, matching)


class DosTimetableCreationTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name='DOS Test School',
            registration_number='REG-003',
            address='Test Address',
            phone='123456789',
            email='dos@example.com',
        )
        self.dos_user = CustomUser.objects.create_user(
            username='dos_user',
            email='dos@example.com',
            password='password123',
            school=self.school,
            role='teacher',
            first_name='Diana',
            last_name='Owner',
            phone='0711111111',
        )
        self.dos_profile = StaffProfile.objects.create(
            user=self.dos_user,
            employee_id='DOS-001',
            position='Director of Studies',
            salary=0,
            date_joined=date.today(),
            teacher_admin_role='dos',
        )
        self.class_grade = ClassGrade.objects.create(
            name='Primary 5',
            level=5,
            curriculum='national',
            school=self.school,
            capacity=40,
        )
        self.subject = Subject.objects.create(
            name='Mathematics',
            code='MTH',
            curriculum='national',
        )
        self.teacher_user = CustomUser.objects.create_user(
            username='math_teacher',
            email='mathteacher@example.com',
            password='password123',
            school=self.school,
            role='teacher',
            first_name='Math',
            last_name='Teacher',
            phone='0712345678',
        )
        self.teacher_profile = StaffProfile.objects.create(
            user=self.teacher_user,
            employee_id='T-001',
            position='Mathematics Teacher',
            salary=0,
            date_joined=date.today(),
            teacher_admin_role='teacher',
        )

    def test_dos_can_create_timetable_entry(self):
        self.client.force_login(self.dos_user)
        response = self.client.post(
            reverse('teacher:dos:timetable_create'),
            {
                'class_id': self.class_grade.id,
                'subject_id': self.subject.id,
                'teacher_id': self.teacher_profile.id,
                'day_of_week': 'monday',
                'start_time': '08:00',
                'end_time': '09:00',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Timetable.objects.filter(
            class_grade=self.class_grade,
            subject=self.subject,
            teacher=self.teacher_profile,
            day_of_week='monday',
        ).exists())
        self.assertContains(response, 'Timetable entry created successfully')


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


class TeacherLessonPlanCreationTests(TestCase):
    """Tests for teacher lesson plan creation workflow."""

    def setUp(self):
        """Set up test data: school, teacher user, staff profile, class, subject, and timetable."""
        self.school = School.objects.create(
            name='Lesson Plan Test School',
            registration_number='REG-004',
            address='Test Address',
            phone='123456789',
            email='lessonplan@example.com',
        )
        self.teacher_user = CustomUser.objects.create_user(
            username='lesson_teacher',
            email='lessonteacher@example.com',
            password='password123',
            school=self.school,
            role='teacher',
            first_name='Lesson',
            last_name='Teacher',
            phone='0712345678',
        )
        self.teacher_profile = StaffProfile.objects.create(
            user=self.teacher_user,
            employee_id='T-LES-001',
            position='Class Teacher',
            salary=0,
            date_joined=date.today(),
            teacher_admin_role='teacher',
        )
        self.class_grade = ClassGrade.objects.create(
            name='Primary 5',
            level=5,
            curriculum='national',
            school=self.school,
            capacity=40,
        )
        self.subject = Subject.objects.create(
            name='Mathematics',
            code='MTH',
            curriculum='national',
        )
        # Add subject to teacher's profile
        self.teacher_profile.subjects.add(self.subject)
        self.timetable = Timetable.objects.create(
            class_grade=self.class_grade,
            subject=self.subject,
            teacher=self.teacher_profile,
            day_of_week='monday',
            start_time='08:00',
            end_time='09:00',
        )

    def test_teacher_can_create_lesson_plan(self):
        """Test that a teacher can create a lesson plan."""
        self.client.force_login(self.teacher_user)
        response = self.client.post(
            reverse('teacher:lesson_plan_create'),
            {
                'class_id': self.class_grade.id,
                'subject_id': self.subject.id,
                'lesson_date': date.today().isoformat(),
                'topic': 'Introduction to Fractions',
                'objective': 'Students will understand basic fractions',
                'activities': 'Hands-on activity with fraction circles',
                'resources': 'Fraction circle manipulatives',
                'homework': 'Worksheet on fractions',
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_lesson_plan_is_saved_to_database(self):
        """Test that created lesson plan is persisted."""
        from SchoolNowMgt.models import LessonPlan
        self.client.force_login(self.teacher_user)
        self.client.post(
            reverse('teacher:lesson_plan_create'),
            {
                'class_id': self.class_grade.id,
                'subject_id': self.subject.id,
                'lesson_date': date.today().isoformat(),
                'topic': 'Introduction to Fractions',
                'objective': 'Students will understand basic fractions',
                'activities': 'Hands-on activity with fraction circles',
                'resources': 'Fraction circle manipulatives',
                'homework': 'Worksheet on fractions',
            },
        )
        # Verify the lesson plan was created
        self.assertTrue(
            LessonPlan.objects.filter(
                teacher=self.teacher_profile,
                class_grade=self.class_grade,
                subject=self.subject,
                topic='Introduction to Fractions',
            ).exists()
        )

    def test_teacher_lessons_page_displays_plans(self):
        """Test that the lessons page shows teacher's lesson plans."""
        from SchoolNowMgt.models import LessonPlan
        LessonPlan.objects.create(
            teacher=self.teacher_profile,
            class_grade=self.class_grade,
            subject=self.subject,
            lesson_date=date.today(),
            topic='Algebra Basics',
            objective='Understand algebraic expressions',
            activities='Group problem solving',
            resources='Textbooks',
            homework='Practice problems',
        )
        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse('teacher:lessons'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Algebra Basics')
