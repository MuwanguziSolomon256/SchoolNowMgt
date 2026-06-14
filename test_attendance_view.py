#!/usr/bin/env python
"""Test attendance marking endpoint"""

import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from dashboard.teacher_sub_views import mark_attendance_ajax

# Get Sarah
User = get_user_model()
sarah = User.objects.get(id=16)

# Create a test request with attendance data
factory = RequestFactory()
payload = {
    'class_id': 3,
    'attendance_data': {'6': 'present'},  # Student ID 6 with present status
    'is_online': True
}

request = factory.post(
    '/teacher/api/attendances/mark/',
    data=json.dumps(payload),
    content_type='application/json'
)
request.user = sarah

# Call the view
try:
    response = mark_attendance_ajax(request)
    print(f'Response status: {response.status_code}')
    print(f'Response content: {response.content.decode()}')
except Exception as e:
    import traceback
    print(f'Error: {e}')
    traceback.print_exc()
