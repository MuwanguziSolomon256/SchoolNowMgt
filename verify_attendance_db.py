#!/usr/bin/env python
"""Verify attendance database records after AJAX submission"""

import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import StudentAttendance, Student, ActivityLog

# Check today's attendance for Student 1
today = date.today()
student = Student.objects.get(id=6)

attendance_records = StudentAttendance.objects.filter(
    student=student,
    date=today
)

print(f"\n=== Attendance Records for {student.full_name} on {today} ===")
print(f"Total records: {attendance_records.count()}")

for record in attendance_records:
    print(f"  Status: {record.status}")
    print(f"  Synced: {record.synced}")
    print(f"  Created: {record.created_at}")

# Check activity logs for attendance
print(f"\n=== Recent Attendance Activity Logs ===")
activity_logs = ActivityLog.objects.filter(
    activity_type='attendance_marked'
).order_by('-created_at')[:5]

for log in activity_logs:
    print(f"  {log.description}")
    print(f"    Created: {log.created_at}")

print(f"\n✓ Database verification complete!")
