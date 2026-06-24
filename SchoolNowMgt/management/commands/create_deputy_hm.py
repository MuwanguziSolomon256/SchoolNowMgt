from django.core.management.base import BaseCommand
from SchoolNowMgt.models import CustomUser, StaffProfile, School


class Command(BaseCommand):
    help = 'Create test users for admin roles'

    def handle(self, *args, **options):
        # Get or create default school
        school, created = School.objects.get_or_create(
            name='Default School',
            defaults={'location': 'Default'}
        )
        self.stdout.write(f"\nSchool: {school.name} (ID: {school.id})")

        # Check for Deputy HM user by username
        self.stdout.write("\n" + "="*80)
        self.stdout.write("CHECKING FOR DEPUTY HM USER")
        self.stdout.write("="*80)

        deputy_user = CustomUser.objects.filter(username='deputy_hm_test').first()

        if not deputy_user:
            deputy_user = CustomUser.objects.filter(email='deputy_hm@test.com').first()

        if deputy_user:
            self.stdout.write(f"✓ Deputy HM user exists: {deputy_user.email} (username: {deputy_user.username})")
            try:
                profile = StaffProfile.objects.get(user=deputy_user)
                self.stdout.write(f"  Profile exists - Teacher Admin Role: {profile.teacher_admin_role}")
                if profile.teacher_admin_role != 'deputy_hm':
                    self.stdout.write(f"  ⚠ Admin role is '{profile.teacher_admin_role}', updating to 'deputy_hm'...")
                    profile.teacher_admin_role = 'deputy_hm'
                    profile.save()
                    self.stdout.write(f"  ✓ Admin role updated to 'deputy_hm'")
            except StaffProfile.DoesNotExist:
                self.stdout.write(f"  ✗ No StaffProfile - creating one...")
                profile = StaffProfile.objects.create(
                    user=deputy_user,
                    teacher_admin_role='deputy_hm',
                    employee_id='DEPUTY001',
                    position='Deputy Headmaster',
                    salary=45000.00
                )
                self.stdout.write(f"  ✓ StaffProfile created with teacher_admin_role='deputy_hm'")
        else:
            self.stdout.write(f"✗ Deputy HM user doesn't exist - creating one...")
            try:
                deputy_user = CustomUser.objects.create_user(
                    email='deputy_hm@test.com',
                    username='deputy_hm_user_' + str(CustomUser.objects.count()),
                    first_name='Deputy',
                    last_name='Headmaster',
                    password='TestPassword123!',
                    role='teacher',
                    school=school
                )
                self.stdout.write(f"✓ User created: {deputy_user.email}")
                
                # Create StaffProfile
                profile = StaffProfile.objects.create(
                    user=deputy_user,
                    teacher_admin_role='deputy_hm',
                    employee_id='DEPUTY001',
                    position='Deputy Headmaster',
                    salary=45000.00
                )
                self.stdout.write(f"✓ StaffProfile created with teacher_admin_role='deputy_hm'")
            except Exception as e:
                self.stdout.write(f"✗ Error creating user: {str(e)}")
                return

        self.stdout.write("\n" + "="*80)
        self.stdout.write("DEPUTY HM USER DETAILS")
        self.stdout.write("="*80)
        self.stdout.write(f"Email: {deputy_user.email}")
        self.stdout.write(f"Username: {deputy_user.username}")
        self.stdout.write(f"Password: TestPassword123!")
        self.stdout.write(f"Role: {deputy_user.role}")
        self.stdout.write(f"School: {deputy_user.school.name}")
        self.stdout.write(f"Admin Role: {profile.teacher_admin_role}")
