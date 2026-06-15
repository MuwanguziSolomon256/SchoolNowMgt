import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import ClassGrade, StaffProfile
from django.contrib.auth import get_user_model

User = get_user_model()

# Get Sarah Jenkins
sarah = User.objects.get(username='sarah_jenkins')
print(f'Found user: {sarah.email}')

# Get Year 9 class
year_9 = ClassGrade.objects.get(name='Year 9', curriculum='international')
print(f'Found class: {year_9.name} ({year_9.curriculum})')

# Assign Sarah as teacher
year_9.class_teacher = sarah.staffprofile
year_9.save()
print(f'Assigned {sarah.email} as teacher for Year 9')

# Verify
year_9.refresh_from_db()
print(f'Year 9 class_teacher is now: {year_9.class_teacher}')
