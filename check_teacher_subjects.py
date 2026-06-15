#!/usr/bin/env python
"""Check teacher subjects for grade modal"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import StaffProfile, Timetable, Subject

staff = StaffProfile.objects.first()
if staff:
    print(f'Staff: {staff.user.first_name}')
    timetables = Timetable.objects.filter(teacher=staff)
    print(f'Timetables: {timetables.count()}')
    for t in timetables:
        print(f'  - {t.subject.name if t.subject else "No Subject"} ({t.day_of_week})')
    
    # Check subjects
    subject_ids = Timetable.objects.filter(teacher=staff).values_list('subject_id', flat=True).distinct()
    print(f'\nSubject IDs: {list(subject_ids)}')
    subjects = Subject.objects.filter(id__in=subject_ids)
    print(f'Subjects: {subjects.count()}')
    for s in subjects:
        print(f'  - {s.name} (ID: {s.id})')
else:
    print('No staff found')
