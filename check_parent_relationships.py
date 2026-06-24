#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings')
django.setup()

from SchoolNowMgt.models import StudentParentRelationship
from django.contrib.auth import get_user_model

User = get_user_model()
parent = User.objects.filter(email='parent@test.com').first()
print(f"Parent user: {parent}")
print(f"Parent school: {parent.school}")
print(f"Parent role: {parent.role}")

# Check StudentParentRelationship records
relationships = StudentParentRelationship.objects.filter(parent=parent)
print(f"\nRelationships for parent: {relationships.count()}")
for rel in relationships:
    print(f"  - {rel.student.first_name} ({rel.relationship_type}) at {rel.school.name if rel.school else 'None'}")
