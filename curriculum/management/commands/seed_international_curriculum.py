"""
Django management command to seed international curriculum test data.

Creates Year 9-12 classes and IGCSE/IB subjects for testing the gradebook.

Usage:
    python manage.py seed_international_curriculum
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from SchoolNowMgt.models import School, ClassGrade, Subject


class Command(BaseCommand):
    help = 'Seed international curriculum (IGCSE/IB) classes and subjects for testing'
    
    def handle(self, *args, **options):
        # Get or create the first school
        school = School.objects.first()
        if not school:
            school = School.objects.create(
                name='Test School',
                registration_number='TEST001',
                address='Test Address',
                phone='+256700000000',
                email='test@school.com'
            )
            self.stdout.write(self.style.SUCCESS(f'Created school: {school.name}'))
        
        # Create Year 9-12 international classes
        year_levels = [
            (9, 'Year 9'),
            (10, 'Year 10'),
            (11, 'Year 11'),
            (12, 'Year 12'),
        ]
        
        created_classes = []
        for level, name in year_levels:
            class_grade, created = ClassGrade.objects.get_or_create(
                name=name,
                level=level,
                school=school,
                curriculum='international',
                defaults={'capacity': 30}
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created class: {class_grade.name} (Level {level})')
                )
                created_classes.append(class_grade)
            else:
                self.stdout.write(
                    self.style.WARNING(f'✗ Class already exists: {class_grade.name}')
                )
        
        # Create IGCSE subjects
        igcse_subjects = [
            ('ENG-IG', 'English Language', 'international'),
            ('MTH-IG', 'Mathematics', 'international'),
            ('SCI-IG', 'Science (Combined)', 'international'),
            ('HIS-IG', 'History', 'international'),
            ('GEO-IG', 'Geography', 'international'),
            ('ICT-IG', 'Information Technology', 'international'),
            ('ART-IG', 'Art & Design', 'international'),
            ('PE-IG', 'Physical Education', 'international'),
        ]
        
        created_subjects = []
        for code, name, curriculum in igcse_subjects:
            subject, created = Subject.objects.get_or_create(
                code=code,
                name=name,
                curriculum=curriculum
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created subject: {code} - {name}')
                )
                created_subjects.append(subject)
            else:
                self.stdout.write(
                    self.style.WARNING(f'✗ Subject already exists: {code}')
                )
        
        # Summary
        self.stdout.write('\n' + self.style.SUCCESS('='*60))
        self.stdout.write(
            self.style.SUCCESS(
                f'International curriculum seed completed!\n'
                f'  Classes created: {len(created_classes)}\n'
                f'  Subjects created: {len(created_subjects)}'
            )
        )
        self.stdout.write(self.style.SUCCESS('='*60))
