"""
Script to clean up duplicate test data
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import CustomUser, StaffProfile, TeacherTask, ActivityLog

# Delete all test data
TeacherTask.objects.all().delete()
ActivityLog.objects.all().delete()
StaffProfile.objects.all().delete()
CustomUser.objects.filter(username='teacher1').delete()

print("✓ Cleaned up test data")
