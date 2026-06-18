#!/usr/bin/env python
"""Clear test attendance records."""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings')
django.setup()

from SchoolNowMgt.models import TeacherAttendance, BreakSession

# Clear all attendance and break records
TeacherAttendance.objects.all().delete()
BreakSession.objects.all().delete()

print("✓ Cleared all TeacherAttendance and BreakSession records")
