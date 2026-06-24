#!/usr/bin/env python
"""Check parent system database state"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import CustomUser, StudentParentRelationship, Student, School

# Check if parent users exist
parent_users = CustomUser.objects.filter(role='parent', school__isnull=True)
print(f"Existing parent users (school=NULL): {parent_users.count()}")
for p in parent_users[:3]:
    print(f"  - {p.email} ({p.get_full_name()})")

# Check relationships
relationships = StudentParentRelationship.objects.all()
print(f"\nExisting StudentParentRelationship records: {relationships.count()}")

# Check schools
schools = School.objects.all()
print(f"\nSchools in system: {schools.count()}")
for s in schools:
    print(f"  - {s.name}")

# Check students
students = Student.objects.all()[:5]
print(f"\nFirst 5 students:")
for s in students:
    print(f"  - {s.full_name} (Admission: {s.admission_number}, Status: {s.status})")
