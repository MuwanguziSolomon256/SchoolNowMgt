#!/usr/bin/env python
"""Test script to clear today's attendance and test fresh clock-in"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings')
django.setup()

from SchoolNowMgt.models import TeacherAttendance, BreakSession, StaffProfile
from django.utils import timezone

# Get Sarah's profile
sarah = StaffProfile.objects.get(user__first_name='Sarah')
today = timezone.now().date()
current_time = timezone.now()

print(f"\n📅 Current Date: {today}")
print(f"⏰ Current Time: {current_time.strftime('%H:%M:%S')}")

# Delete today's records to allow fresh clock-in
deleted_count, _ = TeacherAttendance.objects.filter(staff=sarah, date=today).delete()
print(f"\n✓ Deleted {deleted_count} attendance record(s) for {today}")
print(f"✓ Teacher can now clock in fresh")
print(f"\n🔄 Go to dashboard and click 'Clock In' to test at {current_time.strftime('%H:%M %p')}")
