#!/usr/bin/env python
"""Fix password hash for dos2@test.com user"""
import os
import django
import sys

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings')

# Setup Django - must happen before importing models
try:
    django.setup()
except Exception as e:
    print(f"Django setup error: {e}")
    print("Trying alternative approach...")
    sys.exit(1)

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

CustomUser = get_user_model()

try:
    user = CustomUser.objects.get(email='dos2@test.com')
    user.set_password('password123')
    user.save()
    print(f"✓ Password set correctly for dos2@test.com")
    print(f"  Hash: {user.password[:60]}...")
except Exception as e:
    print(f"Error: {e}")
