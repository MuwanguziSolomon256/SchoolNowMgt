"""
Clean up duplicate users
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import CustomUser

# Delete all duplicates
CustomUser.objects.filter(email='teacher@test.com').delete()
print("✓ All teacher@test.com users deleted")
