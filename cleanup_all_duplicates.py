"""
Comprehensive duplicate cleanup script
Removes duplicate test users, duplicate emails, and orphaned test data

This script:
1. Finds and removes duplicate test users (keeps one active instance)
2. Removes all duplicate emails (keeps the active/most recent user)
3. Removes orphaned test data (tasks, activities without users)
4. Provides detailed reporting of all deletions
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import CustomUser, StaffProfile, TeacherTask, ActivityLog
from django.db.models import Count

print('\n' + '='*70)
print('COMPREHENSIVE DUPLICATE CLEANUP')
print('='*70)

# ────────────────────────────────────────────────────────────────────────────
# STEP 1: Remove duplicate emails (keep most active/recent)
# ────────────────────────────────────────────────────────────────────────────

print('\n1️⃣  Checking for duplicate email addresses...\n')

duplicates = CustomUser.objects.values('email').annotate(
    count=Count('id')
).filter(count__gt=1).order_by('-count')

email_deleted = 0
email_kept = 0

if duplicates.exists():
    for dup in duplicates:
        email = dup['email']
        count = dup['count']
        users = CustomUser.objects.filter(email__iexact=email).order_by(
            '-is_active',      # Active users first
            '-date_joined'     # Then most recent
        )
        
        print(f'📧 Email: {email} ({count} accounts found)')
        
        keeper = None
        for i, user in enumerate(users):
            if keeper is None:
                keeper = user
                status = '✓ KEEPING' if user.is_active else '⚠ KEEPING (inactive, most recent)'
                print(f'   {status}: {user.username} (ID:{user.id}, role:{user.role}, active:{user.is_active})')
                email_kept += 1
            else:
                print(f'   ✗ DELETING: {user.username} (ID:{user.id}, role:{user.role})')
                user.delete()
                email_deleted += 1
        print()
else:
    print('✓ No duplicate emails found!\n')

# ────────────────────────────────────────────────────────────────────────────
# STEP 2: Remove orphaned StaffProfiles (users don't exist anymore)
# ────────────────────────────────────────────────────────────────────────────

print('\n2️⃣  Checking for orphaned staff profiles...\n')

profile_deleted = 0
all_profiles = StaffProfile.objects.all()

for profile in all_profiles:
    try:
        # Check if user still exists
        _ = profile.user
    except CustomUser.DoesNotExist:
        print(f'   ✗ DELETING orphaned profile: (ID:{profile.id}, employee_id:{profile.employee_id})')
        profile.delete()
        profile_deleted += 1

if profile_deleted == 0:
    print('✓ No orphaned staff profiles found!\n')
else:
    print()

# ────────────────────────────────────────────────────────────────────────────
# STEP 3: Remove orphaned tasks and activities
# ────────────────────────────────────────────────────────────────────────────

print('\n3️⃣  Checking for orphaned tasks and activities...\n')

task_deleted = 0
activity_deleted = 0

# Find tasks with deleted staff
for task in TeacherTask.objects.all():
    try:
        _ = task.teacher
    except StaffProfile.DoesNotExist:
        print(f'   ✗ DELETING orphaned task: "{task.title}" (ID:{task.id})')
        task.delete()
        task_deleted += 1

# Find activities with deleted staff
for activity in ActivityLog.objects.all():
    try:
        _ = activity.teacher
    except StaffProfile.DoesNotExist:
        print(f'   ✗ DELETING orphaned activity: "{activity.description}" (ID:{activity.id})')
        activity.delete()
        activity_deleted += 1

if task_deleted == 0 and activity_deleted == 0:
    print('✓ No orphaned tasks or activities found!\n')
else:
    print()

# ────────────────────────────────────────────────────────────────────────────
# STEP 4: Summary Report
# ────────────────────────────────────────────────────────────────────────────

print('\n' + '='*70)
print('CLEANUP SUMMARY')
print('='*70)
print(f'✓ Duplicate emails fixed:        {email_deleted} deleted, {email_kept} kept')
print(f'✓ Orphaned staff profiles:       {profile_deleted} deleted')
print(f'✓ Orphaned tasks:                {task_deleted} deleted')
print(f'✓ Orphaned activities:           {activity_deleted} deleted')
print(f'\nTotal items cleaned up:          {email_deleted + profile_deleted + task_deleted + activity_deleted}')
print('='*70 + '\n')

# ────────────────────────────────────────────────────────────────────────────
# STEP 5: Final database summary
# ────────────────────────────────────────────────────────────────────────────

print('📊 FINAL DATABASE STATUS:\n')
print(f'   Total users:         {CustomUser.objects.count()}')
print(f'   Total staff:         {StaffProfile.objects.count()}')
print(f'   Total tasks:         {TeacherTask.objects.count()}')
print(f'   Total activities:    {ActivityLog.objects.count()}')

# Check for any remaining duplicates
remaining_dups = CustomUser.objects.values('email').annotate(
    count=Count('id')
).filter(count__gt=1)

if remaining_dups.exists():
    print(f'\n⚠️  WARNING: {remaining_dups.count()} duplicate emails still exist!')
else:
    print('\n✅ All duplicates eliminated!')

print('\n✓ Cleanup complete!\n')
