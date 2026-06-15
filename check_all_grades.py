#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import Grade

print(f"Total grades in database: {Grade.objects.count()}")
print("Recent grades:")
for g in Grade.objects.all().order_by('-created_at')[:10]:
    print(f"  {g.student.first_name if g.student else 'Unknown'} - {g.subject.name if g.subject else 'Unknown'}: {g.score}")
