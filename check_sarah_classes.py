#!/usr/bin/env python
"""Check Sarah's class assignments"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import CustomUser, StaffProfile, ClassGrade
from dashboard.teacher_sub_views import get_teacher_classes

sarah = CustomUser.objects.get(id=16)
print(f'Sarah: {sarah.get_full_name()}, School: {sarah.school}')

try:
    staff = StaffProfile.objects.get(user=sarah)
    print(f'StaffProfile: {staff}')
    
    # Get classes using the view function
    classes = get_teacher_classes(staff)
    class_list = list(classes.values_list('name', flat=True))
    print(f'Classes (via get_teacher_classes): {class_list}')
    
    # Check all ClassGrades
    all_classes = ClassGrade.objects.filter(school=sarah.school)
    for cls in all_classes:
        print(f'  Class: {cls.name}, Teacher: {cls.class_teacher}')
    
except Exception as e:
    import traceback
    print(f'Error: {e}')
    traceback.print_exc()
