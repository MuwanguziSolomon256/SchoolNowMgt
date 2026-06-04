"""
Script to create a test parent account
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import CustomUser, School

# Get or create school
school = School.objects.first()
if not school:
    school = School.objects.create(
        name='Test School',
        registration_number='TS001',
        address='123 Test St',
        phone='+256700000000',
        email='school@test.com'
    )

# Create or get parent user
parent_user, created = CustomUser.objects.get_or_create(
    username='parent1',
    defaults={
        'email': 'parent@test.com',
        'first_name': 'John',
        'last_name': 'Smith',
        'role': 'parent',
        'school': school
    }
)

if created:
    parent_user.set_password('password123')
    parent_user.save()
    print(f"✓ Created parent user: {parent_user.username} ({parent_user.email})")
else:
    # Update password anyway
    parent_user.set_password('password123')
    parent_user.save()
    print(f"✓ Parent user already exists: {parent_user.username} ({parent_user.email})")

print("\nTest Credentials:")
print(f"Email: {parent_user.email}")
print(f"Password: password123")
print(f"Role: {parent_user.role}")
