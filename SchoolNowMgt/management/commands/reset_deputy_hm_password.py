from django.core.management.base import BaseCommand
from SchoolNowMgt.models import CustomUser


class Command(BaseCommand):
    help = 'Reset Deputy HM password'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*80)
        self.stdout.write("RESETTING DEPUTY HM PASSWORD")
        self.stdout.write("="*80)

        deputy_user = CustomUser.objects.filter(username='deputy_hm_test').first()
        
        if deputy_user:
            self.stdout.write(f"✓ Found user: {deputy_user.email}")
            deputy_user.set_password('password123')
            deputy_user.save()
            self.stdout.write(f"✓ Password updated to: password123")
            self.stdout.write(f"\n✓ Login Credentials:")
            self.stdout.write(f"  Email: {deputy_user.email}")
            self.stdout.write(f"  Password: password123")
        else:
            self.stdout.write("✗ Deputy HM user not found")
