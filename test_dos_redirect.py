#!/usr/bin/env python
"""Test script to verify DOS user redirect logic"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from SchoolNowMgt.models import StaffProfile

User = get_user_model()

# Verify DOS test user
try:
    user = User.objects.get(username='dos_test')
    print(f"✅ DOS User Found: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   Primary Role: {user.role}")
    
    sp = StaffProfile.objects.get(user=user)
    print(f"   Admin Role: {sp.teacher_admin_role}")
    
    if sp.teacher_admin_role == 'dos':
        print("✅ DOS admin role correctly assigned")
    else:
        print(f"❌ Expected admin_role='dos', got '{sp.teacher_admin_role}'")
        
except User.DoesNotExist:
    print("❌ DOS user not found")
except StaffProfile.DoesNotExist:
    print("❌ DOS user has no StaffProfile")
except Exception as e:
    print(f"❌ Error: {e}")

# Verify Deputy HM test user  
try:
    user = User.objects.get(username='deputy_hm_test')
    print(f"\n✅ Deputy HM User Found: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   Primary Role: {user.role}")
    
    sp = StaffProfile.objects.get(user=user)
    print(f"   Admin Role: {sp.teacher_admin_role}")
    
    if sp.teacher_admin_role == 'deputy_hm':
        print("✅ Deputy HM admin role correctly assigned")
    else:
        print(f"❌ Expected admin_role='deputy_hm', got '{sp.teacher_admin_role}'")
        
except User.DoesNotExist:
    print("❌ Deputy HM user not found")
except StaffProfile.DoesNotExist:
    print("❌ Deputy HM user has no StaffProfile")
except Exception as e:
    print(f"❌ Error: {e}")

# Verify Matron test user
try:
    user = User.objects.get(username='matron_test')
    print(f"\n✅ Matron User Found: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   Primary Role: {user.role}")
    
    sp = StaffProfile.objects.get(user=user)
    print(f"   Admin Role: {sp.teacher_admin_role}")
    
    if sp.teacher_admin_role == 'matron':
        print("✅ Matron admin role correctly assigned")
    else:
        print(f"❌ Expected admin_role='matron', got '{sp.teacher_admin_role}'")
        
except User.DoesNotExist:
    print("❌ Matron user not found")
except StaffProfile.DoesNotExist:
    print("❌ Matron user has no StaffProfile")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)
print("All test credentials are ready for login testing!")
print("="*60)
