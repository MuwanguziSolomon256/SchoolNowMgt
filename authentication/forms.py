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
    
    def __init__(self, *args, role=None, **kwargs):
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
        
        # Verify role matches
        if role and user.role != role:
            raise forms.ValidationError(
                f'This account is registered as a {user.get_role_display()}, not a {dict(self.fields["role"].choices)[role]}.'
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
