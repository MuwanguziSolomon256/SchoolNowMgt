from django import forms
from django.contrib.auth import authenticate
from SchoolNowMgt.models import CustomUser


class RoleSelectionForm(forms.Form):
    """Form for selecting user role during login/registration."""
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('teacher', 'Teacher'),
        ('parent', 'Parent'),
        ('non_teaching_staff', 'Support Staff'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'role-selector'}),
        label='Select your role'
    )


class UnifiedLoginForm(forms.Form):
    """
    Unified login form that handles login for all user roles.
    First step: select role. Second step: provide email/password.
    """
    email = forms.EmailField(
        label='Email or Username',
        widget=forms.EmailInput(attrs={
            'placeholder': 'name@schoolnow.edu',
            'class': 'form-input'
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter your password',
            'class': 'form-input'
        })
    )
    role = forms.ChoiceField(
        choices=[
            ('admin', 'Administrator'),
            ('teacher', 'Teacher'),
            ('parent', 'Parent'),
            ('non_teaching_staff', 'Support Staff'),
        ],
        widget=forms.HiddenInput()
    )
    
    admin_role = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        help_text='Specific admin role (dos, deputy_hm, etc.)'
    )
    
    def __init__(self, *args, role=None, **kwargs):
        # Set initial role value if provided
        if role and 'initial' not in kwargs:
            kwargs['initial'] = kwargs.get('initial', {})
            kwargs['initial']['role'] = role
        
        super().__init__(*args, **kwargs)
        self.role = role
        self.user = None
        self.authenticated_user = None
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        role = self.role or cleaned_data.get('role')
        
        if not email or not password:
            return cleaned_data
        
        # Try to find user by email (case-insensitive)
        try:
            user = CustomUser.objects.get(email__iexact=email)
            self.user = user
        except CustomUser.DoesNotExist:
            raise forms.ValidationError(
                'No account found with this email address.'
            )
        except CustomUser.MultipleObjectsReturned:
            # Handle duplicate email accounts - try to find the active one with matching role
            users = CustomUser.objects.filter(email__iexact=email, role=role, is_active=True)
            if users.exists():
                user = users.first()
                self.user = user
            else:
                raise forms.ValidationError(
                    f'Multiple accounts found with this email. Please contact support.'
                )
        
        # Verify role matches
        if role and user.role != role:
            raise forms.ValidationError(
                f'This account is registered as a {user.get_role_display()}, not a {dict(self.fields["role"].choices)[role]}.'
            )
        
        # Verify admin role if specified
        admin_role = cleaned_data.get('admin_role')
        if admin_role:
            from SchoolNowMgt.models import StaffProfile
            try:
                staff_profile = StaffProfile.objects.get(user=user)
                if staff_profile.teacher_admin_role != admin_role:
                    raise forms.ValidationError(
                        f'This account is not assigned the {admin_role} role.'
                    )
            except StaffProfile.DoesNotExist:
                raise forms.ValidationError(
                    'This account does not have a staff profile. Please contact support.'
                )
        
        # Authenticate
        authenticated_user = authenticate(username=user.username, password=password)
        if authenticated_user is None:
            raise forms.ValidationError(
                'Invalid password. Please try again.'
            )
        
        self.authenticated_user = authenticated_user
        return cleaned_data


class UnifiedRegistrationForm(forms.Form):
    """
    Base unified registration form with role selection.
    Role-specific logic handled by subclasses or custom view logic.
    """
    role = forms.ChoiceField(
        choices=[
            ('admin', 'Administrator'),
            ('teacher', 'Teacher'),
            ('parent', 'Parent'),
            ('non_teaching_staff', 'Support Staff'),
        ],
        widget=forms.HiddenInput()
    )
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'First name',
            'class': 'form-input'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Last name',
            'class': 'form-input'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Email address',
            'class': 'form-input'
        })
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Create a password',
            'class': 'form-input'
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm password',
            'class': 'form-input'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'An account with this email address already exists.'
            )
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    'Passwords do not match. Please try again.'
                )
            if len(password1) < 8:
                raise forms.ValidationError(
                    'Password must be at least 8 characters long.'
                )
        
        return cleaned_data


class ParentRegistrationForm(UnifiedRegistrationForm):
    """
    Registration form specifically for parents.
    Parents have school=NULL and access multiple schools via StudentParentRelationship.
    """
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Phone number (optional)',
            'class': 'form-input'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set role to parent
        self.fields['role'].initial = 'parent'
        self.fields['role'].widget = forms.HiddenInput()
    
    def save(self, commit=True):
        """Create a parent user with school=NULL"""
        user = CustomUser.objects.create_user(
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            password=self.cleaned_data['password1'],
            role='parent',
            school=None,  # Parents don't have a school; they access via StudentParentRelationship
            phone=self.cleaned_data.get('phone', ''),
        )
        return user
