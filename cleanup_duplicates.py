"""
Script to clean up duplicate email accounts
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import CustomUser
from django.db.models import Count

# Find emails with multiple accounts
duplicates = CustomUser.objects.values('email').annotate(count=Count('id')).filter(count__gt=1)

print(f"Found {duplicates.count()} emails with duplicate accounts\n")

for dup in duplicates:
    email = dup['email']
    count = dup['count']
    users = CustomUser.objects.filter(email__iexact=email).order_by('-is_active', '-date_joined')
    
    print(f"Email: {email} ({count} accounts)")
    
    # Keep the first active user, delete the rest
    keeper = None
    for i, user in enumerate(users):
        if keeper is None and user.is_active:
            keeper = user
            print(f"  ✓ Keeping: {user.username} (ID: {user.id}, active={user.is_active}, role={user.role})")
        else:
            print(f"  ✗ Deleting: {user.username} (ID: {user.id}, active={user.is_active}, role={user.role})")
            user.delete()
    
    # If no active user, keep the most recent
    if keeper is None and users.exists():
        keeper = users.first()
        print(f"  ✓ Keeping (no active): {keeper.username} (ID: {keeper.id})")
    
    print()

print("Cleanup complete!")
