import os
import django
import time
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import ClassGrade, Subject, Timetable, StaffProfile

# Get Year 9 and its teacher
year_9 = ClassGrade.objects.get(name='Year 9', curriculum='international')
teacher = year_9.class_teacher
print(f'Creating timetables for Year 9 with teacher: {teacher}')

# Get all international subjects
subjects = Subject.objects.filter(curriculum='international')
print(f'Found {subjects.count()} international subjects')

# Create timetable entries
days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'monday', 'tuesday', 'wednesday']
times = [(9, 10), (10, 11), (11, 12), (13, 14), (14, 15), (15, 16), (9, 10), (10, 11)]  # (start, end) hours

created_count = 0
for i, subject in enumerate(subjects):
    if i >= len(days):
        break
    
    day = days[i]
    start_hour, end_hour = times[i]
    
    timetable = Timetable.objects.create(
        class_grade=year_9,
        subject=subject,
        curriculum='international',
        teacher=teacher,
        day_of_week=day,
        start_time=f'{start_hour:02d}:00:00',
        end_time=f'{end_hour:02d}:00:00'
    )
    print(f'  ✓ Created: {subject.code} on {day} at {start_hour}:00-{end_hour}:00')
    created_count += 1

print(f'\n✓ Created {created_count} timetable entries for Year 9 international')
