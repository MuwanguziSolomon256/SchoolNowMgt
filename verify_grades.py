#!/usr/bin/env python
"""Verify grade data stored in database."""

import os
import sys

os.chdir('c:\\Users\\Admin\\Desktop\\SchoolNowMgt')
sys.path.insert(0, 'c:\\Users\\Admin\\Desktop\\SchoolNowMgt')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings')

import django
django.setup()

from SchoolNowMgt.models import Grade
from django.utils import timezone

# Find all grades and show their data
grades = Grade.objects.all().order_by('-id')[:20]

print("\n" + "="*70)
print("Recent Grades in Database (last 20)")
print("="*70)

if not grades:
    print("No grades found in database.")
else:
    print(f"\nTotal grades found: {grades.count()}")
    print()
    
    for grade in grades:
        print(f"ID: {grade.id}")
        print(f"  Student: {grade.student.get_full_name() if grade.student else 'N/A'}")
        print(f"  Subject: {grade.subject.name if grade.subject else 'N/A'}")
        print(f"  Score: {grade.score}")
        print(f"  Term: '{grade.term}' (type: {type(grade.term).__name__})")
        print(f"  Semester (Exam Type): '{grade.semester}'")
        print(f"  Academic Year: {grade.academic_year}")
        print()

print("="*70)
print("Analysis")
print("="*70)

# Check what term formats exist
terms = Grade.objects.values_list('term', flat=True).distinct()
print(f"\nUnique term values in database: {list(terms)}")

# Check what years exist
years = Grade.objects.values_list('academic_year', flat=True).distinct()
print(f"Unique academic years: {list(years)}")

# Show counts by term
print(f"\nGrades by term:")
for term in terms:
    count = Grade.objects.filter(term=term).count()
    print(f"  term='{term}': {count} grades")
