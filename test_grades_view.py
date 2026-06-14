#!/usr/bin/env python
"""Test the grades_dashboard view"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from django.test import RequestFactory
from dashboard.teacher_sub_views import grades_dashboard
from SchoolNowMgt.models import CustomUser, StaffProfile
from dashboard.teacher_sub_views import get_teacher_staff_profile

# Get Sarah
sarah = CustomUser.objects.get(id=16)

# Check StaffProfile
try:
    staff = StaffProfile.objects.get(user=sarah)
    print(f'Sarah has StaffProfile: {staff}')
except:
    print('Sarah does NOT have StaffProfile')

# Create a mock request
factory = RequestFactory()
request = factory.get('/teacher/grades/')
request.user = sarah

# Test get_teacher_staff_profile
staff_result = get_teacher_staff_profile(request)
print(f'get_teacher_staff_profile returned: {staff_result}')

# Call the view
try:
    response = grades_dashboard(request)
    print(f'Response type: {type(response).__name__}')
    if hasattr(response, 'status_code'):
        print(f'Status code: {response.status_code}')
    if hasattr(response, 'template_name'):
        print(f'Template: {response.template_name}')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
