#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import TeacherTask

print("Pending tasks:")
pending = TeacherTask.objects.filter(status='pending')
for t in pending:
    print(f"  - {t.title} (status: {t.status})")

print("\nCompleted tasks:")
completed = TeacherTask.objects.filter(status='completed')
for t in completed:
    print(f"  - {t.title} (status: {t.status})")
