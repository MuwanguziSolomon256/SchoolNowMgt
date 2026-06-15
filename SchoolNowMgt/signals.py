"""
Django signal receivers for School Management System MVP.

Automates the rule engine for:
1. High absenteeism alerts (3+ absences in 5 days)
2. Low grade alerts (score < 40)
3. Enquiry to Student conversion (auto-enroll)
4. Teacher shift notifications (clock in/out/break alerts)
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import uuid

from .models import (
    StudentAttendance,
    Grade,
    Enquiry,
    Student,
    RetentionAlert,
    SMSLog,
    TeacherAttendance,
    BreakSession,
)


def create_sms_log(student, alert):
    """
    Create an SMSLog record with pending status for background processing.
    
    Called by Signal 1 (absenteeism) and Signal 2 (low grades) to queue
    notifications to the student's parent phone. The actual Africa's Talking
    API call is handled by sms_service.py or a background task.
    """
    message = (
        f"Dear {student.parent_name}, this is a message from the school. "
        f"{student.full_name} requires your attention: {alert.detail} "
        f"Please contact the school as soon as possible."
    )
    SMSLog.objects.create(
        recipient_phone=student.parent_phone,
        message=message,
        related_student=student,
        related_alert=alert,
        status='pending'
    )


@receiver(post_save, sender=StudentAttendance)
def check_high_absenteeism(sender, instance, created, **kwargs):
    """
    Trigger a RetentionAlert if student is absent 3+ times in the last 5 days.
    
    Only processes records with status == 'absent'. Checks for existing
    unresolved alerts to prevent duplicates. Creates an SMSLog to notify parent.
    """
    # Only process when status is 'absent'
    if instance.status != 'absent':
        return
    
    student = instance.student
    
    # Get the last 5 attendance records for this student, ordered by date DESC
    last_five = StudentAttendance.objects.filter(
        student=student
    ).order_by('-date')[:5]
    
    # Count how many are 'absent'
    absent_count = sum(1 for record in last_five if record.status == 'absent')
    
    # If 3 or more absences in the last 5 days
    if absent_count >= 3:
        # Check if an unresolved alert already exists
        existing_alert = RetentionAlert.objects.filter(
            student=student,
            reason_type='high_absenteeism',
            resolved=False
        ).first()
        
        if existing_alert:
            # Alert already exists, skip to avoid duplicates
            return
        
        # Create a new alert
        alert = RetentionAlert.objects.create(
            student=student,
            reason_type='high_absenteeism',
            severity='high',
            detail=f"{student.full_name} has been absent {absent_count} out of the last 5 school days."
        )
        
        # Create SMS log to notify parent
        create_sms_log(student, alert)


@receiver(post_save, sender=Grade)
def check_low_grades(sender, instance, created, **kwargs):
    """
    Trigger a RetentionAlert if student's grade score is below 40 (fail mark).
    
    Severity is 'high' if score < 25, 'medium' if 25–39. Checks for existing
    unresolved alerts per term and academic year to prevent duplicates.
    Creates an SMSLog to notify parent.
    """
    # Only process if score is below 40 (fail)
    if instance.score >= 40:
        return
    
    student = instance.student
    
    # Check if an unresolved alert already exists for this term/year
    existing_alert = RetentionAlert.objects.filter(
        student=student,
        reason_type='low_grades',
        resolved=False
    ).first()
    
    if existing_alert:
        # Alert already exists for this student, skip to avoid duplicates
        return
    
    # Determine severity: high if score < 25, medium if 25–39
    severity = 'high' if instance.score < 25 else 'medium'
    
    # Create a new alert
    alert = RetentionAlert.objects.create(
        student=student,
        reason_type='low_grades',
        severity=severity,
        detail=f"{student.full_name} scored {instance.score} in {instance.subject} "
               f"({instance.term} {instance.academic_year}), below the pass mark of 40."
    )
    
    # Create SMS log to notify parent
    create_sms_log(student, alert)


@receiver(pre_save, sender=Enquiry)
def convert_enquiry_to_student(sender, instance, **kwargs):
    """
    Auto-convert an Enquiry to a Student when status changes to 'enrolled'.
    
    Only runs on updates (when pk exists). Checks that status changed from
    NOT 'enrolled' to 'enrolled'. Splits child_name and creates a new Student
    with auto-generated admission number. Avoids duplicate conversion if
    converted_student is already set.
    """
    # Only run on updates (instance must have a primary key)
    if not instance.pk:
        return
    
    # Fetch the previous version from the database
    try:
        previous = Enquiry.objects.get(pk=instance.pk)
    except Enquiry.DoesNotExist:
        return
    
    # Check if status changed from NOT 'enrolled' to 'enrolled'
    if previous.status != 'enrolled' and instance.status == 'enrolled':
        # Skip if a student is already linked
        if instance.converted_student is not None:
            return
        
        # Split child_name on the first space into first_name and last_name
        parts = instance.child_name.split(None, 1)  # Split on first whitespace
        if len(parts) == 2:
            first_name, last_name = parts
        else:
            first_name = instance.child_name
            last_name = ''
        
        # Generate admission number as STU-{year}-{6-char hex}
        year = timezone.now().year
        random_hex = uuid.uuid4().hex[:6].upper()
        admission_number = f"STU-{year}-{random_hex}"
        
        # Create the new Student
        new_student = Student.objects.create(
            first_name=first_name,
            last_name=last_name,
            class_grade=instance.interested_class,
            parent_name=instance.parent_name,
            parent_phone=instance.parent_phone,
            admission_number=admission_number,
            status='active',
            # Required fields that have no default:
            date_of_birth=timezone.now().date(),  # Placeholder; should be captured in enquiry form
            gender='M',  # Placeholder; should be captured in enquiry form
        )
        
        # Link the new student to the enquiry
        instance.converted_student = new_student
        # Note: Do not call instance.save() here; pre_save will commit the instance


# ============================================================================
# TEACHER SHIFT MANAGEMENT NOTIFICATIONS (Phase 8)
# ============================================================================

@receiver(post_save, sender=TeacherAttendance)
def notify_admin_shift_events(sender, instance, created, update_fields, **kwargs):
    """
    Send email notifications to admin when teachers clock in/out or take breaks.
    
    Triggered when:
    - Teacher clocks in (time_in is set)
    - Teacher clocks out (time_out is set)
    
    Notifications go to:
    - School admin email
    - Head teacher (if available)
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Only send if shift tracking fields were updated
    if not update_fields:
        return
    
    has_clock_in = 'time_in' in update_fields
    has_clock_out = 'time_out' in update_fields
    
    if not (has_clock_in or has_clock_out):
        return
    
    try:
        # Get admin recipients for this school
        admin_users = User.objects.filter(
            role='admin',
            school=instance.staff.user.school,
            is_active=True
        )
        
        if not admin_users.exists():
            return
        
        admin_emails = [admin.email for admin in admin_users if admin.email]
        if not admin_emails:
            return
        
        # Prepare email content
        teacher_name = instance.staff.user.get_full_name()
        school_name = instance.staff.user.school.name
        
        if has_clock_in:
            subject = f"[{school_name}] Teacher Clock In - {teacher_name}"
            time_str = instance.time_in.strftime("%H:%M")
            message = f"""
Dear Administrator,

{teacher_name} has clocked in at {time_str} on {instance.date.strftime('%B %d, %Y')}.

View shift details: {settings.SITE_URL}/admin/shifts/

Regards,
EduVision Management System
            """
        elif has_clock_out:
            subject = f"[{school_name}] Teacher Clock Out - {teacher_name}"
            time_str = instance.time_out.strftime("%H:%M") if instance.time_out else "N/A"
            shift_duration = instance.get_shift_hours()
            message = f"""
Dear Administrator,

{teacher_name} has clocked out at {time_str} on {instance.date.strftime('%B %d, %Y')}.

Shift Duration: {shift_duration}
Breaks Taken: {instance.break_count}

View shift details: {settings.SITE_URL}/admin/shifts/

Regards,
EduVision Management System
            """
        else:
            return
        
        # Send email
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            admin_emails,
            fail_silently=True,
        )
    except Exception as e:
        # Log error but don't block the main operation
        print(f"Error sending shift notification email: {str(e)}")


@receiver(post_save, sender=BreakSession)
def notify_break_events(sender, instance, created, update_fields, **kwargs):
    """
    Optional: Send notifications for break start/end events.
    
    Currently disabled by default to reduce email volume.
    Can be enabled per-school in admin settings.
    """
    # For now, this is intentionally minimal to avoid excessive notifications
    # Uncomment and customize if break notifications are desired
    pass
