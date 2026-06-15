#!/usr/bin/env python
"""
Fix teacher StaffProfile setup for shift management system.
Creates missing StaffProfiles for all teacher users.
"""

import os
import sys
import django
import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from SchoolNowMgt.models import CustomUser, StaffProfile

def main():
    print("=" * 70)
    print("FIXING TEACHER STAFFPROFILE SETUP")
    print("=" * 70)
    
    # Find all teacher users
    teachers = CustomUser.objects.filter(role='teacher', is_active=True)
    print(f"\nFound {teachers.count()} active teacher(s)")
    
    created_count = 0
    existing_count = 0
    
    for teacher in teachers:
        try:
            staff_profile, created = StaffProfile.objects.get_or_create(
                user=teacher,
                defaults={
                    'employee_id': f"TEA{teacher.id:04d}",
                    'position': 'Teacher',
                    'salary': 0.00,
                    'date_joined': datetime.date.today(),
                    'is_full_time': True
                }
            )
            
            if created:
                print(f"✓ CREATED  StaffProfile for: {teacher.get_full_name()} ({teacher.username})")
                created_count += 1
            else:
                print(f"✓ EXISTS   StaffProfile for: {teacher.get_full_name()} ({teacher.username})")
                existing_count += 1
                
        except Exception as e:
            print(f"✗ ERROR    {teacher.get_full_name()}: {str(e)}")
    
    print("\n" + "=" * 70)
    print(f"Summary: {created_count} created, {existing_count} already existed")
    print("=" * 70)
    
    # Verify shift endpoints will work
    print("\nVerifying shift endpoint compatibility...")
    verify_count = 0
    for teacher in teachers:
        try:
            StaffProfile.objects.get(user=teacher, user__role='teacher')
            verify_count += 1
        except StaffProfile.DoesNotExist:
            print(f"✗ FAIL: {teacher.get_full_name()} - no StaffProfile found!")
    
    print(f"✓ {verify_count}/{teachers.count()} teachers ready for shift management")
    print("\nShift endpoints should now work correctly!")

if __name__ == '__main__':
    main()
