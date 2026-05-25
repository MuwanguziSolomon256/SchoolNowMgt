"""
Django management command to dispatch pending SMS queue to Africa's Talking.

Usage:
    python manage.py send_pending_sms                # Send up to 50 pending SMS
    python manage.py send_pending_sms --limit 10     # Send up to 10 pending SMS
    python manage.py send_pending_sms --dry-run      # Preview pending SMS without sending

This command queries SMSLog records with status='pending', processes them in order
(oldest first), and updates their status to 'sent' or 'failed' based on the provider
response from Africa's Talking.

Designed for cron scheduling (every 5-10 minutes) to maintain a low-latency queue
without requiring Celery/Redis infrastructure.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from SchoolNowMgt.models import SMSLog
from SchoolNowMgt.sms_service import send_sms


class Command(BaseCommand):
    help = 'Dispatch all SMSLog records with status=pending to Africa\'s Talking'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Max number of messages to send per run (default 50)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print messages without sending them',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        dry_run = options['dry_run']

        # Query pending SMS logs, ordered by sent_at (oldest first)
        pending = SMSLog.objects.filter(
            status='pending'
        ).select_related(
            'related_student', 'related_alert'
        ).order_by('sent_at')[:limit]

        total = pending.count()

        if total == 0:
            self.stdout.write("No pending SMS messages.")
            return

        self.stdout.write(f"Found {total} pending message(s).")

        sent_count = 0
        failed_count = 0

        for log in pending:
            if dry_run:
                self.stdout.write(
                    f"[DRY RUN] To: {log.recipient_phone} | "
                    f"Msg: {log.message[:60]}..."
                )
                continue

            # Send the SMS via Africa's Talking
            success, provider_response = send_sms(
                log.recipient_phone,
                log.message,
            )

            # Update the log with response and status
            log.provider_response = provider_response
            log.status = 'sent' if success else 'failed'
            log.save(update_fields=['status', 'provider_response'])

            if success:
                sent_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Sent to {log.recipient_phone}"
                    )
                )
            else:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Failed to {log.recipient_phone}: "
                        f"{provider_response[:80]}"
                    )
                )

        if not dry_run:
            self.stdout.write(
                f"\n{self.style.SUCCESS(f'Done. Sent: {sent_count}')} | "
                f"{self.style.ERROR(f'Failed: {failed_count}')}"
            )


# ════════════════════════════════════════════════════════════════════════════════
# CRON SETUP INSTRUCTIONS
# ════════════════════════════════════════════════════════════════════════════════
#
# To run every 5 minutes on a production server, add this line to your crontab:
#
#   crontab -e
#
# Then add:
#
#   */5 * * * * /path/to/venv/bin/python /path/to/manage.py send_pending_sms
#
# Example (adjust paths to your deployment):
#
#   */5 * * * * /home/django/schoolmgmt_venv/bin/python /home/django/schoolmgmt/manage.py send_pending_sms >> /var/log/schoolmgmt_sms.log 2>&1
#
# ════════════════════════════════════════════════════════════════════════════════
# TESTING IN DEVELOPMENT
# ════════════════════════════════════════════════════════════════════════════════
#
# Preview pending messages without sending:
#
#   python manage.py send_pending_sms --dry-run
#
# Send up to 10 pending messages:
#
#   python manage.py send_pending_sms --limit 10
#
# Send all pending messages (default 50):
#
#   python manage.py send_pending_sms
#
# ════════════════════════════════════════════════════════════════════════════════
# AFRICA'S TALKING SANDBOX MODE
# ════════════════════════════════════════════════════════════════════════════════
#
# By default, AT_SANDBOX = True in settings.py. In sandbox mode, Africa's Talking
# does NOT send real SMS messages — it simulates delivery. This is safe for development.
#
# To test with REAL SMS (production mode):
#   1. Switch AT_SANDBOX = False in settings.py
#   2. Ensure AT_API_KEY is a PRODUCTION API key
#   3. Ensure AT_SENDER_ID is a registered shortcode or sender ID with your provider
#
# NEVER switch to production mode without thoroughly testing on sandbox first.
#
# ════════════════════════════════════════════════════════════════════════════════
# MANUAL RE-QUEUE OF FAILED SMS
# ════════════════════════════════════════════════════════════════════════════════
#
# Failed SMS are marked with status='failed' and stored in the Django admin under
# SMSLog. To re-queue a failed message for retry:
#
#   1. Go to Django admin: /admin/SchoolNowMgt/smslog/
#   2. Find the failed message (status='failed')
#   3. Change status back to 'pending'
#   4. Click Save
#   5. Next cron run will attempt delivery again
#
# This manual approach ensures that network glitches don't auto-spam users, and
# allows the admin to review and adjust messages before re-sending.
#
# ════════════════════════════════════════════════════════════════════════════════
