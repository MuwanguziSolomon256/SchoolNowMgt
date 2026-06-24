"""
Forms for Student-Parent Linking Workflow

Provides forms for admins to:
1. Link existing parents to students
2. Create and link new parents
3. Manage parent-student relationships
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import StudentParentRelationship, CustomUser, Student, School


class LinkExistingParentForm(forms.Form):
    """
    Form to search for and link an existing parent to a student.
    
    Usage: Admin searches by email or name, selects relationship type
    """
    
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-input',
            'placeholder': 'Search for student...'
        }),
        label='Student',
        help_text='Select the student to link parent to'
    )
    
    parent_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter parent email (e.g., parent@example.com)',
            'autocomplete': 'email'
        }),
        label='Parent Email',
        help_text='Email of the parent to link'
    )
    
    relationship_type = forms.ChoiceField(
        choices=StudentParentRelationship.RELATIONSHIP_TYPES,
        widget=forms.Select(attrs={
            'class': 'form-input'
        }),
        label='Relationship Type',
        help_text='How is this parent related to the student?'
    )
    
    is_primary_guardian = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox'
        }),
        label='Mark as Primary Guardian',
        help_text='Check if this is the primary guardian (e.g., main contact)'
    )
    
    def clean_parent_email(self):
        """Validate that parent exists with this email"""
        email = self.cleaned_data.get('parent_email', '').lower().strip()
        
        try:
            parent = CustomUser.objects.get(email=email, role='parent')
        except CustomUser.DoesNotExist:
            raise ValidationError(
                f"No parent account found with email '{email}'. "
                f"Please create the parent account first or use 'Create and Link' option."
            )
        
        return email
    
    def clean(self):
        """Validate relationship doesn't already exist"""
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        parent_email = cleaned_data.get('parent_email')
        school = cleaned_data.get('school')
        
        if student and parent_email:
            try:
                parent = CustomUser.objects.get(email=parent_email, role='parent')
                # Check if relationship already exists
                if StudentParentRelationship.objects.filter(
                    student=student,
                    parent=parent
                ).exists():
                    raise ValidationError(
                        f"This parent is already linked to {student.first_name} {student.last_name}."
                    )
            except CustomUser.DoesNotExist:
                pass  # Already handled in clean_parent_email
        
        return cleaned_data


class CreateAndLinkParentForm(forms.Form):
    """
    Form to create a new parent account and immediately link to student.
    
    Usage: Admin provides parent info, account is created with temp password,
    parent is sent invitation email
    """
    
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-input',
            'placeholder': 'Select student...'
        }),
        label='Student',
        help_text='Select the student this parent will be linked to'
    )
    
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'First name'
        }),
        label='Parent First Name'
    )
    
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Last name'
        }),
        label='Parent Last Name'
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Parent email',
            'autocomplete': 'email'
        }),
        label='Parent Email',
        help_text='Email used to log in'
    )
    
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Phone number (optional)',
            'type': 'tel'
        }),
        label='Phone Number (Optional)'
    )
    
    relationship_type = forms.ChoiceField(
        choices=StudentParentRelationship.RELATIONSHIP_TYPES,
        widget=forms.Select(attrs={
            'class': 'form-input'
        }),
        label='Relationship Type',
        help_text='How is this person related to the student?'
    )
    
    is_primary_guardian = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox'
        }),
        label='Mark as Primary Guardian',
        help_text='Check if this is the primary guardian'
    )
    
    send_invitation_email = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox'
        }),
        label='Send Invitation Email',
        help_text='Email parent with temporary password and login instructions'
    )
    
    def clean_email(self):
        """Check email is unique"""
        email = self.cleaned_data.get('email', '').lower().strip()
        
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError(
                f"An account with email '{email}' already exists. "
                f"Use 'Link Existing Parent' instead."
            )
        
        return email
    
    def clean_phone_number(self):
        """Optional validation of phone format"""
        phone = self.cleaned_data.get('phone_number', '').strip()
        
        if phone:
            # Very basic validation - just check for digits
            if not any(c.isdigit() for c in phone):
                raise ValidationError("Phone number must contain at least one digit.")
        
        return phone


class ManageParentRelationshipForm(forms.ModelForm):
    """
    Form to manage existing parent-student relationships.
    
    Usage: Edit relationship type, primary guardian status, activation
    """
    
    class Meta:
        model = StudentParentRelationship
        fields = ['relationship_type', 'is_primary_guardian', 'is_active']
        widgets = {
            'relationship_type': forms.Select(attrs={
                'class': 'form-input'
            }),
            'is_primary_guardian': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }
        labels = {
            'relationship_type': 'Relationship Type',
            'is_primary_guardian': 'Mark as Primary Guardian',
            'is_active': 'Active',
        }
        help_texts = {
            'relationship_type': 'How is this person related to the student?',
            'is_primary_guardian': 'Primary guardian is the main contact for the student',
            'is_active': 'Inactive relationships will be hidden from parent portal',
        }


class BulkLinkParentsForm(forms.Form):
    """
    Form for bulk linking of parents to students via CSV upload.
    
    CSV Format Expected:
    student_admission_number, parent_email, relationship_type, is_primary_guardian
    
    Usage: Upload CSV file with parent-student mappings
    """
    
    csv_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-input',
            'accept': '.csv'
        }),
        label='Upload CSV File',
        help_text='CSV file with columns: admission_number, parent_email, relationship_type, is_primary_guardian'
    )
    
    send_invitation_emails = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox'
        }),
        label='Send Invitation Emails',
        help_text='Send invitation emails to newly linked parents'
    )
    
    def clean_csv_file(self):
        """Validate CSV file format"""
        csv_file = self.cleaned_data.get('csv_file')
        
        if not csv_file:
            raise ValidationError("CSV file is required.")
        
        # Check file extension
        if not csv_file.name.endswith('.csv'):
            raise ValidationError("File must be a CSV (.csv) file.")
        
        # Check file size (max 5MB)
        if csv_file.size > 5 * 1024 * 1024:
            raise ValidationError("File size must be less than 5MB.")
        
        return csv_file
