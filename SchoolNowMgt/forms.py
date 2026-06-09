from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime
import csv
import io
import re
import secrets
import string
from .models import (
    Enquiry, StudentAttendance, ClassGrade, Student, 
    CustomUser, StaffProfile, Message, MessageTemplate,
    School
)


class EnquiryForm(forms.ModelForm):
    """
    Form for parent enquiries about school admission.
    Includes validation for Ugandan phone numbers.
    """

    class Meta:
        model = Enquiry
        fields = ['parent_name', 'parent_phone', 'child_name', 'interested_class']
        exclude = ['status', 'notes', 'enquiry_date', 'converted_student', 'followed_up_by', 'school']
        widgets = {
            'parent_name': forms.TextInput(attrs={
                'placeholder': 'e.g. Sarah Nakato',
                'class': 'form-input'
            }),
            'parent_phone': forms.TextInput(attrs={
                'placeholder': 'e.g. 0772 123 456',
                'class': 'form-input'
            }),
            'child_name': forms.TextInput(attrs={
                'placeholder': 'e.g. Brian Ssebunya',
                'class': 'form-input'
            }),
            'interested_class': forms.Select(attrs={
                'class': 'form-input'
            }),
        }

    def clean_parent_phone(self):
        """
        Validate Ugandan phone number formats.
        Accepts:
          - 0772123456 (starts with 0)
          - +256772123456 (starts with +256)
          - 256772123456 (starts with 256)
        """
        phone = self.cleaned_data.get('parent_phone', '').strip()

        if not phone:
            raise ValidationError("Phone number is required.")

        # Accept three formats: 0772..., +256772..., 256772...
        if not (phone.startswith('0') or phone.startswith('+256') or phone.startswith('256')):
            raise ValidationError(
                "Enter a valid Ugandan phone number, e.g. 0772 123 456"
            )

        return phone


class AttendanceMarkingForm(forms.Form):
    """
    Form to select a class and date for marking attendance.
    Per-student status fields are generated dynamically in the view.
    """

    class_grade = forms.ModelChoiceField(
        queryset=ClassGrade.objects.all(),
        widget=forms.Select(attrs={'class': 'form-input'}),
        label='Select Class'
    )

    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-input'
        }),
        label='Date',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial date to today
        from django.utils import timezone
        self.fields['date'].initial = timezone.now().date()


# ============================================================================
# ADMIN ONBOARDING & MESSAGING FORMS (Phase 2)
# ============================================================================


def generate_temp_password(length=12):
    """Generate a cryptographically secure temporary password."""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(chars) for _ in range(length))


class StaffOnboardingForm(forms.Form):
    """
    Single staff onboarding form for admins to create teachers or support staff.
    Auto-generates temporary password on success.
    """
    
    POSITION_CHOICES = [
        ('Class Teacher', 'Class Teacher'),
        ('Head Teacher', 'Head Teacher'),
        ('Subject Teacher', 'Subject Teacher'),
        ('Deputy Head', 'Deputy Head'),
        ('Cleaner', 'Cleaner'),
        ('Security', 'Security'),
        ('Groundskeeper', 'Groundskeeper'),
        ('Administrator', 'Administrator'),
        ('Support Staff', 'Support Staff'),
    ]
    
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'First name', 'class': 'form-input'})
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Last name', 'class': 'form-input'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Email address', 'class': 'form-input'})
    )
    position = forms.ChoiceField(
        choices=POSITION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    date_joined = forms.DateField(
        initial=timezone.now().date,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'})
    )
    is_teacher = forms.BooleanField(
        required=False,
        label="Is this a teacher?",
        help_text="Check if this person teaches classes"
    )
    
    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email
    
    def clean_date_joined(self):
        date_joined = self.cleaned_data['date_joined']
        if date_joined > timezone.now().date():
            raise ValidationError("Date joined cannot be in the future.")
        return date_joined


class BulkStaffUploadForm(forms.Form):
    """
    Bulk staff onboarding form for CSV file upload.
    Expected CSV columns: first_name, last_name, email, position, date_joined
    """
    
    csv_file = forms.FileField(
        label="Upload CSV file",
        help_text="CSV with columns: first_name, last_name, email, position, date_joined, is_teacher",
        widget=forms.FileInput(attrs={'accept': '.csv', 'class': 'form-input'})
    )
    
    def clean_csv_file(self):
        file = self.cleaned_data['csv_file']
        if not file.name.endswith('.csv'):
            raise ValidationError("File must be a CSV file.")
        
        try:
            content = file.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(content))
            
            required_cols = {'first_name', 'last_name', 'email', 'position', 'date_joined'}
            if not reader.fieldnames:
                raise ValidationError("CSV file is empty.")
            
            missing_cols = required_cols - set(reader.fieldnames)
            if missing_cols:
                raise ValidationError(f"Missing required columns: {', '.join(missing_cols)}")
            
            rows = list(reader)
            if not rows:
                raise ValidationError("CSV file has no data rows.")
            
            # Basic validation of data
            for idx, row in enumerate(rows, start=2):  # start=2 because row 1 is header
                if not row['email']:
                    raise ValidationError(f"Row {idx}: Email is required.")
                if not row['first_name'] or not row['last_name']:
                    raise ValidationError(f"Row {idx}: First and last name are required.")
                
                # Validate email
                if '@' not in row['email']:
                    raise ValidationError(f"Row {idx}: Invalid email format.")
        
        except UnicodeDecodeError:
            raise ValidationError("File must be UTF-8 encoded.")
        except Exception as e:
            raise ValidationError(f"Error reading CSV: {str(e)}")
        
        return file


class StudentOnboardingForm(forms.Form):
    """
    Single student onboarding form for admins to create new students.
    Auto-generates admission number on success.
    """
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'First name', 'class': 'form-input'})
    )
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Last name', 'class': 'form-input'})
    )
    class_grade = forms.ModelChoiceField(
        queryset=ClassGrade.objects.all(),
        widget=forms.Select(attrs={'class': 'form-input'}),
        label="Class"
    )
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        widget=forms.RadioSelect()
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        help_text="Optional (can be estimated or updated later)"
    )
    parent_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Parent/Guardian name', 'class': 'form-input'})
    )
    parent_phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. 0772 123 456', 'class': 'form-input'})
    )
    
    def clean_parent_phone(self):
        phone = self.cleaned_data['parent_phone'].strip()
        if not phone:
            raise ValidationError("Parent phone is required.")
        if not (phone.startswith('0') or phone.startswith('+256') or phone.startswith('256')):
            raise ValidationError("Enter a valid Ugandan phone number.")
        return phone
    
    def clean_date_of_birth(self):
        dob = self.cleaned_data['date_of_birth']
        if dob and dob > timezone.now().date():
            raise ValidationError("Date of birth cannot be in the future.")
        return dob


class BulkStudentUploadForm(forms.Form):
    """
    Bulk student onboarding form for CSV file upload.
    Expected CSV columns: first_name, last_name, class, parent_name, parent_phone, gender, date_of_birth (optional)
    """
    
    csv_file = forms.FileField(
        label="Upload CSV file",
        help_text="CSV with columns: first_name, last_name, class, parent_name, parent_phone, gender, date_of_birth",
        widget=forms.FileInput(attrs={'accept': '.csv', 'class': 'form-input'})
    )
    
    def clean_csv_file(self):
        file = self.cleaned_data['csv_file']
        if not file.name.endswith('.csv'):
            raise ValidationError("File must be a CSV file.")
        
        try:
            content = file.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(content))
            
            required_cols = {'first_name', 'last_name', 'class', 'parent_name', 'parent_phone', 'gender'}
            if not reader.fieldnames:
                raise ValidationError("CSV file is empty.")
            
            missing_cols = required_cols - set(reader.fieldnames)
            if missing_cols:
                raise ValidationError(f"Missing required columns: {', '.join(missing_cols)}")
            
            rows = list(reader)
            if not rows:
                raise ValidationError("CSV file has no data rows.")
            
            # Validate data
            for idx, row in enumerate(rows, start=2):
                if not row['first_name'] or not row['last_name']:
                    raise ValidationError(f"Row {idx}: First and last name are required.")
                if not row['parent_phone']:
                    raise ValidationError(f"Row {idx}: Parent phone is required.")
                if row['gender'] not in ('M', 'F'):
                    raise ValidationError(f"Row {idx}: Gender must be M or F.")
        
        except UnicodeDecodeError:
            raise ValidationError("File must be UTF-8 encoded.")
        except Exception as e:
            raise ValidationError(f"Error reading CSV: {str(e)}")
        
        return file


class AdminMessageForm(forms.Form):
    """
    Admin message creation form for sending targeted in-app messages.
    Supports templates and free-form messages, with optional scheduling.
    """
    
    RECIPIENT_CHOICES = [
        ('all_teachers', 'All Teachers'),
        ('all_staff', 'All Support Staff'),
        ('all_staff_combined', 'All Teachers & Support Staff'),
        ('all_parents', 'All Parents'),
        ('class_specific', 'Parents of Specific Class'),
        ('individual', 'Individual User'),
    ]
    
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Message subject', 'class': 'form-input'})
    )
    recipient_type = forms.ChoiceField(
        choices=RECIPIENT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-input'}),
        label="Send to"
    )
    template = forms.ModelChoiceField(
        queryset=MessageTemplate.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-input'}),
        label="Use template (optional)"
    )
    body = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Message body (max 1000 chars)\nAvailable placeholders: {student_name}, {parent_name}, {class_name}, {teacher_name}',
            'rows': 6,
            'class': 'form-input',
            'maxlength': 1000
        })
    )
    target_class = forms.ModelChoiceField(
        queryset=ClassGrade.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-input'}),
        label="Select class (required for 'Parents of Specific Class')"
    )
    target_user = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-input'}),
        label="Select user (required for 'Individual User')"
    )
    scheduled_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-input'
        }),
        label="Schedule for later (optional, leaves blank for immediate)"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        recipient_type = cleaned_data.get('recipient_type')
        target_class = cleaned_data.get('target_class')
        target_user = cleaned_data.get('target_user')
        scheduled_at = cleaned_data.get('scheduled_at')
        
        # Validate class_specific requires target_class
        if recipient_type == 'class_specific' and not target_class:
            raise ValidationError("Select a class when sending to 'Parents of Specific Class'.")
        
        # Validate individual requires target_user
        if recipient_type == 'individual' and not target_user:
            raise ValidationError("Select a user when sending to 'Individual User'.")
        
        # Validate scheduled_at is in the future if provided
        if scheduled_at and scheduled_at <= timezone.now():
            raise ValidationError("Scheduled time must be in the future.")
        
        return cleaned_data


class StaffPasswordResetForm(forms.Form):
    """
    Form for admins to reset staff password and generate temporary password.
    """
    
    staff_identifier = forms.CharField(
        label="Staff Email or Employee ID",
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter email or employee ID',
            'class': 'form-input'
        })
    )
    
    def clean_staff_identifier(self):
        identifier = self.cleaned_data['staff_identifier'].strip().lower()
        
        # Try to find staff by email or employee ID
        user = CustomUser.objects.filter(
            email=identifier,
            role__in=('teacher', 'non_teaching_staff'),
            is_active=True
        ).first()
        
        if not user:
            # Try employee ID
            staff = StaffProfile.objects.filter(
                employee_id=identifier,
                user__is_active=True
            ).first()
            if staff:
                user = staff.user
        
        if not user:
            raise ValidationError("Staff member not found with that email or employee ID.")
        
        self.cleaned_data['_staff_user'] = user
        return identifier
