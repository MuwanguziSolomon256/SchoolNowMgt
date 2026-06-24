#!/usr/bin/env python
"""Create test parent user and link to students - Direct model creation"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from django.contrib.auth.hashers import make_password
from SchoolNowMgt.models import CustomUser, StudentParentRelationship, Student, School

# Create parent user directly (bypassing create_user which requires school)
try:
    parent = CustomUser.objects.create(
        username='parent@test.com',
        email='parent@test.com',
        first_name='John',
        last_name='Parent',
        password=make_password('password123'),
        role='parent',
        school=None,  # Multi-school parent
        phone='256701234567'
    )
    print(f"✓ Created parent user: {parent.email} (ID: {parent.id})")
    print(f"  - Role: {parent.role}")
    print(f"  - School: {parent.school}")
except Exception as e:
    print(f"✗ Failed to create parent: {e}")
    try:
        parent = CustomUser.objects.get(email='parent@test.com', role='parent')
        print(f"✓ Using existing parent: {parent.email}")
    except:
        print("Cannot proceed without parent user")
        exit(1)

# Get schools
schools = School.objects.all()
print(f"\nLinking parent to students across {schools.count()} schools...")

# Get all active students and link to parent
students = Student.objects.filter(status='active')
linked_count = 0

for i, student in enumerate(students):
    school = student.class_grade.school if student.class_grade else schools.first()
    
    try:
        rel, created = StudentParentRelationship.objects.get_or_create(
            parent=parent,
            student=student,
            school=school,
            defaults={
                'relationship_type': 'father' if i % 2 == 0 else 'mother',
                'is_primary_guardian': (i == 0),  # First is primary
                'is_active': True
            }
        )
        if created:
            print(f"  ✓ Linked: {student.full_name} ({school.name})")
            linked_count += 1
        else:
            print(f"  - Already linked: {student.full_name}")
    except Exception as e:
        print(f"  ✗ Failed to link {student.full_name}: {e}")

print(f"\n✓ Total links created: {linked_count}")

# Verify
relationships = StudentParentRelationship.objects.filter(parent=parent)
print(f"✓ Parent now has {relationships.count()} children:")
for rel in relationships:
    print(f"  - {rel.student.full_name} at {rel.school.name} ({rel.get_relationship_type_display()})")
