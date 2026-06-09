#!/usr/bin/env python
"""
Retrieve the latest user logins from the system.
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from SchoolNowMgt.models import CustomUser
from django.contrib.sessions.models import Session
from django.utils import timezone

print("\n" + "="*80)
print("LATEST USER LOGINS")
print("="*80)

# Get users with recent last_login timestamps
recent_logins = CustomUser.objects.filter(
    last_login__isnull=False
).order_by('-last_login')[:20]

if recent_logins.exists():
    print(f"\nLast {min(20, recent_logins.count())} Logins:\n")
    print(f"{'#':<3} {'Username':<20} {'Full Name':<25} {'Role':<20} {'School':<25} {'Last Login':<25}")
    print("-" * 140)
    
    for idx, user in enumerate(recent_logins, 1):
        last_login = user.last_login.strftime("%Y-%m-%d %H:%M:%S") if user.last_login else "Never"
        username = user.username[:19]
        full_name = user.get_full_name()[:24]
        role = user.get_role_display()[:19]
        school = user.school.name[:24]
        
        print(f"{idx:<3} {username:<20} {full_name:<25} {role:<20} {school:<25} {last_login:<25}")
else:
    print("\nNo login records found.")

print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)

# Count active users in last 24 hours
now = timezone.now()
last_24h = CustomUser.objects.filter(
    last_login__gte=now - timedelta(hours=24),
    last_login__isnull=False
).count()

last_7d = CustomUser.objects.filter(
    last_login__gte=now - timedelta(days=7),
    last_login__isnull=False
).count()

last_30d = CustomUser.objects.filter(
    last_login__gte=now - timedelta(days=30),
    last_login__isnull=False
).count()

total_users = CustomUser.objects.filter(last_login__isnull=False).count()
never_logged = CustomUser.objects.filter(last_login__isnull=True).count()

print(f"\nActive Users (Last 24 Hours): {last_24h}")
print(f"Active Users (Last 7 Days): {last_7d}")
print(f"Active Users (Last 30 Days): {last_30d}")
print(f"Total Users Who Have Logged In: {total_users}")
print(f"Users Who Have Never Logged In: {never_logged}")
print(f"Total Users in System: {CustomUser.objects.count()}")

print("\n" + "="*80 + "\n")
