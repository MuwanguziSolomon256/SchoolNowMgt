import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import ClassGrade, Student, Grade, Subject, School
from django.contrib.auth import get_user_model

User = get_user_model()

# Get Year 9 class and school
year_9 = ClassGrade.objects.get(name='Year 9', curriculum='international')
school = School.objects.first()

# Get or create a test parent user for the student
parent_user, created = User.objects.get_or_create(
    username='parent_intl_test',
    defaults={
        'email': 'parent.intl@test.com',
        'role': 'parent',
        'school': school
    }
)
if created:
    parent_user.set_password('test123')
    parent_user.save()
    print(f'Created new parent user: {parent_user.email}')
else:
    print(f'Using existing parent user: {parent_user.email}')

# Create a test student (or get if already exists)
student, created = Student.objects.get_or_create(
    admission_number='INT001',
    defaults={
        'first_name': 'Alice',
        'last_name': 'Student',
        'date_of_birth': '2011-05-15',
        'gender': 'F',
        'class_grade': year_9,
        'curriculum': 'international',
        'status': 'active',
        'parent_user': parent_user,
        'parent_name': 'Anna Student',
        'parent_phone': '0700000001'
    }
)
print(f'Created student: {student.full_name} in {year_9.name}' if created else f'Using existing student: {student.full_name}')

# Create grades for this student in 4 subjects for Semester 1
subjects = Subject.objects.filter(curriculum='international')[:4]
for subject in subjects:
    grade_obj, grade_created = Grade.objects.get_or_create(
        student=student,
        subject=subject,
        academic_year=2026,
        semester='semester_1',
        defaults={
            'score': 75 + (abs(hash(subject.name)) % 20),
            'curriculum': 'international',
            'remarks': 'Good performance'
        }
    )
    if grade_created:
        print(f'  Created grade: {subject.code} - Score: {grade_obj.score}')
    else:
        print(f'  Grade already exists: {subject.code} - Score: {grade_obj.score}')

print('\nDone! Student and grades created for Year 9 international class.')

