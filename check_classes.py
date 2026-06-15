import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import ClassGrade

print('All ClassGrade objects:')
for cg in ClassGrade.objects.all():
    print(f'  {cg.name} ({cg.curriculum}) - class_teacher: {cg.class_teacher}')

print('\nAll international curriculum classes:')
for cg in ClassGrade.objects.filter(curriculum='international'):
    print(f'  {cg.name} - teacher: {cg.class_teacher}')
