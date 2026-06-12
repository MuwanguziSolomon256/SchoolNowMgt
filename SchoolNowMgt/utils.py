"""
Utility functions for dashboard operations including password generation, CSV parsing,
and message recipient resolution.
"""

import csv
import io
import string
import secrets
from datetime import datetime
from django.db import transaction
from .models import CustomUser, Message, MessageRecipient, MessageTemplate, ClassGrade, StaffProfile, Student


def generate_temp_password(length=12):
    """
    Generate a cryptographically secure temporary password.
    
    Args:
        length (int): Length of the password. Default is 12 characters.
        
    Returns:
        str: Randomly generated password with alphanumeric characters.
    """
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


def generate_employee_id(school, prefix='EMP'):
    """
    Generate a unique employee ID for the school.
    
    Args:
        school: School object
        prefix (str): Prefix for the employee ID (default: 'EMP')
        
    Returns:
        str: Unique employee ID in format 'EMP-YYYYMMDD-XXXX'
    """
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d')
    # Count staff profiles where the user belongs to this school
    existing_count = StaffProfile.objects.filter(user__school=school).count()
    count_str = str(existing_count + 1).zfill(4)
    return f"{prefix}-{timestamp}-{count_str}"


def parse_csv_upload(csv_file, form_type='staff'):
    """
    Parse uploaded CSV file and return list of dictionaries and list of errors.
    
    Args:
        csv_file: Django uploaded file object
        form_type (str): Either 'staff' or 'student' - determines expected columns
        
    Returns:
        tuple: (rows_list, errors_list) where:
            - rows_list: List of dict with parsed data
            - errors_list: List of dict with row number and error message
    """
    rows = []
    errors = []
    
    if form_type == 'staff':
        required_columns = ['first_name', 'last_name', 'email', 'position']
        optional_columns = ['date_joined', 'is_teacher', 'phone']
    else:  # student
        required_columns = ['first_name', 'last_name', 'class', 'gender', 'parent_name', 'parent_phone']
        optional_columns = ['date_of_birth']
    
    try:
        # Read CSV file
        decoded_file = csv_file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        csv_reader = csv.DictReader(io_string)
        
        # Check if columns exist
        if not csv_reader.fieldnames:
            errors.append({
                'row': 1,
                'error': 'CSV file is empty or invalid format'
            })
            return rows, errors
        
        # Validate required columns
        missing_columns = [col for col in required_columns if col not in csv_reader.fieldnames]
        if missing_columns:
            errors.append({
                'row': 1,
                'error': f"Missing required columns: {', '.join(missing_columns)}"
            })
            return rows, errors
        
        # Parse each row
        for row_num, row in enumerate(csv_reader, start=2):  # Start from 2 to account for header
            # Check if row is empty
            if not any(row.values()):
                continue
            
            # Validate required fields
            row_errors = []
            for col in required_columns:
                if not row.get(col, '').strip():
                    row_errors.append(f"Missing required field: {col}")
            
            if row_errors:
                errors.append({
                    'row': row_num,
                    'error': '; '.join(row_errors)
                })
                continue
            
            # Basic email validation for staff
            if form_type == 'staff' and row.get('email'):
                if '@' not in row['email']:
                    errors.append({
                        'row': row_num,
                        'error': 'Invalid email format'
                    })
                    continue
            
            # Add to rows if no errors
            rows.append({
                'first_name': row.get('first_name', '').strip(),
                'last_name': row.get('last_name', '').strip(),
                'email': row.get('email', '').strip() if form_type == 'staff' else None,
                'position': row.get('position', '').strip() if form_type == 'staff' else None,
                'is_teacher': row.get('is_teacher', '').lower() in ['true', '1', 'yes'] if form_type == 'staff' else None,
                'class': row.get('class', '').strip() if form_type == 'student' else None,
                'gender': row.get('gender', '').strip() if form_type == 'student' else None,
                'parent_name': row.get('parent_name', '').strip() if form_type == 'student' else None,
                'parent_phone': row.get('parent_phone', '').strip() if form_type == 'student' else None,
                'date_of_birth': row.get('date_of_birth', '').strip() if form_type == 'student' else None,
                'date_joined': row.get('date_joined', '').strip() if form_type == 'staff' else None,
            })
    
    except Exception as e:
        errors.append({
            'row': 1,
            'error': f"Error reading CSV file: {str(e)}"
        })
    
    return rows, errors


def resolve_message_recipients(message_obj):
    """
    Resolve the list of recipient users based on message recipient_type and filters.
    
    Args:
        message_obj: Message instance with recipient_type, target_class, etc.
        
    Returns:
        QuerySet: CustomUser objects who should receive this message
    """
    school = message_obj.sender.school
    recipients = CustomUser.objects.filter(school=school, is_active=True)
    
    if message_obj.recipient_type == 'all_teachers':
        recipients = recipients.filter(role='teacher')
    elif message_obj.recipient_type == 'all_staff':
        recipients = recipients.filter(role='non_teaching_staff')
    elif message_obj.recipient_type == 'all_staff_combined':
        recipients = recipients.filter(role__in=['teacher', 'non_teaching_staff'])
    elif message_obj.recipient_type == 'all_parents':
        recipients = recipients.filter(role='parent')
    elif message_obj.recipient_type == 'class_specific':
        # Get all students in the target class
        students = Student.objects.filter(
            class_grade=message_obj.target_class,
            school=school
        )
        # Get their parent users
        recipients = CustomUser.objects.filter(
            student__in=students,
            school=school,
            role='parent'
        ).distinct()
    elif message_obj.recipient_type == 'individual':
        recipients = recipients.filter(id=message_obj.target_user.id)
    
    return recipients


def create_message_recipients(message_obj, recipient_users_qs):
    """
    Create MessageRecipient entries for a message and all its recipients.
    
    Args:
        message_obj: Message instance
        recipient_users_qs: QuerySet of CustomUser objects
        
    Returns:
        int: Number of MessageRecipient entries created
    """
    message_recipients = [
        MessageRecipient(
            message=message_obj,
            recipient=user
        )
        for user in recipient_users_qs
    ]
    
    created = MessageRecipient.objects.bulk_create(message_recipients)
    return len(created)


def replace_message_placeholders(body, recipient_user):
    """
    Replace placeholders in message body with actual user data.
    
    Supported placeholders:
    - {first_name}: User's first name
    - {last_name}: User's last name
    - {full_name}: User's full name
    - {school_name}: User's school name
    
    Args:
        body (str): Message body with placeholders
        recipient_user: CustomUser instance
        
    Returns:
        str: Message body with placeholders replaced
    """
    replacements = {
        '{first_name}': recipient_user.first_name or '',
        '{last_name}': recipient_user.last_name or '',
        '{full_name}': recipient_user.get_full_name() or recipient_user.username,
        '{school_name}': recipient_user.school.school_name if recipient_user.school else '',
    }
    
    result = body
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    
    return result


def send_staff_credentials_email(email, full_name, username, temp_password, school_name):
    """
    Send staff credentials via email (optional future feature).
    
    Args:
        email (str): Staff email address
        full_name (str): Staff full name
        username (str): Staff username
        temp_password (str): Temporary password
        school_name (str): School name
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # This is a placeholder for future email implementation
    # When implemented, this should use Django's send_mail or a service like SendGrid
    try:
        from django.core.mail import send_mail
        subject = f"Your {school_name} Staff Portal Credentials"
        message = f"""
Hello {full_name},

You have been onboarded to the {school_name} Staff Portal.

Username: {username}
Temporary Password: {temp_password}

Please log in and change your password immediately for security.

Best regards,
School Management System
        """
        send_mail(subject, message, 'noreply@schoolnow.com', [email])
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False


# ============================================================================
# PARENT MESSAGING UTILITIES
# ============================================================================

def get_parent_messageable_recipients(parent_user):
    """
    Get list of teachers and staff that a parent can send messages to.
    
    Returns class teachers for all of parent's children + admin staff.
    
    Args:
        parent_user: CustomUser instance with role='parent'
        
    Returns:
        QuerySet: CustomUser objects (teachers/staff) the parent can message
    """
    from .models import Student, ClassGrade
    
    if parent_user.role != 'parent':
        return CustomUser.objects.none()
    
    # Get all classes where parent's children are enrolled
    student_classes = Student.objects.filter(
        parents=parent_user,
        status='active',
        school=parent_user.school
    ).values_list('class_grade_id', flat=True).distinct()
    
    # Get all teachers assigned to those classes
    class_teachers = CustomUser.objects.filter(
        teacher__class_grades__in=student_classes,
        school=parent_user.school,
        is_active=True,
        role='teacher'
    ).distinct()
    
    # Get admin/staff marked as messageable
    admin_staff = CustomUser.objects.filter(
        school=parent_user.school,
        is_active=True,
        role__in=['admin', 'non_teaching_staff']
    )
    
    # Combine and return distinct
    recipients = (class_teachers | admin_staff).distinct().order_by('first_name', 'last_name')
    return recipients


def get_parent_unread_count(parent_user):
    """
    Get count of unread messages for a parent.
    
    Args:
        parent_user: CustomUser instance with role='parent'
        
    Returns:
        int: Number of unread messages
    """
    from .models import MessageRecipient
    
    return MessageRecipient.objects.filter(
        recipient=parent_user,
        read_at__isnull=True
    ).count()


def get_parent_messages(parent_user, filter_type='all'):
    """
    Get messages for a parent (both received from admin and sent to staff).
    
    Args:
        parent_user: CustomUser instance
        filter_type: 'all', 'received', 'sent', 'unread'
        
    Returns:
        List: Message objects with related data (sorted by created_at descending)
        
    Note: Returns a list instead of QuerySet because Django doesn't support
    ordering after union() in all databases (especially SQLite).
    """
    from .models import Message, MessageRecipient
    
    if filter_type == 'received':
        # Messages admin sent to parent
        message_ids = MessageRecipient.objects.filter(
            recipient=parent_user
        ).values_list('message_id', flat=True)
        messages = Message.objects.filter(
            id__in=message_ids,
            sender_type='admin'
        ).select_related('sender')
        return sorted(messages, key=lambda x: x.created_at, reverse=True)
    
    elif filter_type == 'sent':
        # Messages parent sent to staff/admin
        messages = Message.objects.filter(
            sender=parent_user,
            sender_type='parent'
        ).select_related('sender')
        return sorted(messages, key=lambda x: x.created_at, reverse=True)
    
    elif filter_type == 'unread':
        # Unread received messages
        message_ids = MessageRecipient.objects.filter(
            recipient=parent_user,
            read_at__isnull=True
        ).values_list('message_id', flat=True)
        messages = Message.objects.filter(
            id__in=message_ids,
            sender_type='admin'
        ).select_related('sender')
        return sorted(messages, key=lambda x: x.created_at, reverse=True)
    
    else:  # 'all'
        # All messages (received + sent)
        received_ids = MessageRecipient.objects.filter(
            recipient=parent_user
        ).values_list('message_id', flat=True)
        
        received_messages = list(Message.objects.filter(
            id__in=received_ids,
            sender_type='admin'
        ).select_related('sender'))
        
        sent_messages = list(Message.objects.filter(
            sender=parent_user,
            sender_type='parent'
        ).select_related('sender'))
        
        # Combine and sort by created_at descending
        all_messages = received_messages + sent_messages
        return sorted(all_messages, key=lambda x: x.created_at, reverse=True)

