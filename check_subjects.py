#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings')
django.setup()

from SchoolNowMgt.models import StaffProfile, Timetable, Subject

staff = StaffProfile.objects.filter(user__username='sarah').first()
if staff:
    print(f'Teacher: {staff.user.username}')
    timetables = Timetable.objects.filter(teacher=staff)
    print(f'Timetable entries: {timetables.count()}')
    for t in timetables:
        print(f'  - {t.subject.name if t.subject else "No subject"} on {t.day_of_week} {t.start_time}')
    
    # Get subjects via the query in the view
    subject_ids = Timetable.objects.filter(teacher=staff).values_list('subject_id', flat=True).distinct()
    subjects = Subject.objects.filter(id__in=subject_ids)
    print(f'Subjects from query: {subjects.count()}')
    for s in subjects:
        print(f'  - {s.name}')
else:
    print('Teacher not found')
