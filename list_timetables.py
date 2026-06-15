#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import CustomUser, StaffProfile, Timetable

teacher_user = CustomUser.objects.filter(username='teacher1').first()
staff = StaffProfile.objects.get(user=teacher_user)

print(f"Timetables for {staff.user.get_full_name()}:")
timetables = Timetable.objects.filter(teacher=staff)
for t in timetables:
    print(f"  {t.day_of_week} {t.start_time}-{t.end_time}: {t.subject.name if t.subject else 'No subject'} (Class: {t.class_grade.name})")
