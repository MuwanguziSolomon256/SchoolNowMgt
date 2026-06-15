import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from django.contrib.auth import get_user_model
from SchoolNowMgt.models import StaffProfile

User = get_user_model()

print('All StaffProfile objects:')
for staff in StaffProfile.objects.all()[:10]:
    print(f'  User: {staff.user.email}')

print('\nLooking for Sarah:')
for user in User.objects.filter(email__icontains='sarah'):
    print(f'  Found: {user.username} - {user.email}')
    try:
        staff = user.staffprofile
        print(f'    Has StaffProfile: Yes')
    except:
        print(f'    Has StaffProfile: No')
