import re
from django import forms
from django.core.exceptions import ValidationError
from datetime import date


class TeacherRegistrationForm(forms.Form):
    """Form for teacher self-registration without email verification."""
    
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'First name'})
    )
    
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Last name'})
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email address'})
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Phone (optional)'})
    )
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
        required=True
    )
    
    password2 = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}),
        required=True
    )
    
    position = forms.CharField(
        max_length=100,
        required=True,
        initial='Teacher',
        widget=forms.TextInput(attrs={'placeholder': 'Position'})
    )
    
    date_joined = forms.DateField(
        required=True,
        initial=date.today,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    TEACHER_ADMIN_ROLE_CHOICES = [
        ('teacher', 'Class/Subject Teacher'),
        ('dos', 'Director of Studies'),
        ('department_head', 'Subject Department Head'),
        ('head_teacher', 'Head Teacher'),
        ('deputy_hm', 'Deputy Headmaster'),
    ]
    
    teacher_admin_role = forms.ChoiceField(
        required=False,
        choices=TEACHER_ADMIN_ROLE_CHOICES,
        initial='teacher',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Select administrative role if applicable. Leave as Teacher for regular class teachers.'
    )
    
    def clean_password1(self):
        """Validate password strength with separate errors for each rule."""
        password = self.cleaned_data.get('password1')
        
        if not password:
            raise ValidationError("Password is required.")
        
        # Check minimum length
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        
        # Check for at least one digit
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one digit.")
        
        # Check for at least one special character
        special_chars = r'[!@#$%^&*()_+\-]'
        if not re.search(special_chars, password):
            raise ValidationError(
                "Password must contain at least one special character from: ! @ # $ % ^ & * ( ) _ + -"
            )
        
        return password
    
    def clean(self):
        """Verify that password1 and password2 match."""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2:
            if password1 != password2:
                self.add_error('password2', 'Passwords do not match.')
        
        return cleaned_data


class AdminRegistrationForm(forms.Form):
    """Form for admin/staff self-registration without email verification."""
    
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'First name'})
    )
    
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Last name'})
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email address'})
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Phone (optional)'})
    )
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
        required=True
    )
    
    password2 = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}),
        required=True
    )
    
    position = forms.CharField(
        max_length=100,
        required=True,
        initial='Staff',
        widget=forms.TextInput(attrs={'placeholder': 'Position/Title'})
    )
    
    date_joined = forms.DateField(
        required=True,
        initial=date.today,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    def clean_password1(self):
        """Validate password strength with separate errors for each rule."""
        password = self.cleaned_data.get('password1')
        
        if not password:
            raise ValidationError("Password is required.")
        
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one digit.")
        
        special_chars = r'[!@#$%^&*()_+\-]'
        if not re.search(special_chars, password):
            raise ValidationError(
                "Password must contain at least one special character from: ! @ # $ % ^ & * ( ) _ + -"
            )
        
        return password
    
    def clean(self):
        """Verify that password1 and password2 match."""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2:
            if password1 != password2:
                self.add_error('password2', 'Passwords do not match.')
        
        return cleaned_data


class NonTeachingStaffRegistrationForm(forms.Form):
    """Form for non-teaching staff self-registration without email verification."""
    
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'First name'})
    )
    
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Last name'})
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email address'})
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Phone (optional)'})
    )
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
        required=True
    )
    
    password2 = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}),
        required=True
    )
    
    position = forms.CharField(
        max_length=100,
        required=True,
        initial='Support Staff',
        widget=forms.TextInput(attrs={'placeholder': 'Position/Title'})
    )
    
    date_joined = forms.DateField(
        required=True,
        initial=date.today,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    def clean_password1(self):
        """Validate password strength with separate errors for each rule."""
        password = self.cleaned_data.get('password1')
        
        if not password:
            raise ValidationError("Password is required.")
        
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one digit.")
        
        special_chars = r'[!@#$%^&*()_+\-]'
        if not re.search(special_chars, password):
            raise ValidationError(
                "Password must contain at least one special character from: ! @ # $ % ^ & * ( ) _ + -"
            )
        
        return password
    
    def clean(self):
        """Verify that password1 and password2 match."""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2:
            if password1 != password2:
                self.add_error('password2', 'Passwords do not match.')
        
        return cleaned_data


class ParentRegistrationForm(forms.Form):
    """Form for parent/guardian self-registration without email verification."""
    
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'First name'})
    )
    
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Last name'})
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email address'})
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Phone (optional)'})
    )
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
        required=True
    )
    
    password2 = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}),
        required=True
    )
    
    def clean_password1(self):
        """Validate password strength with separate errors for each rule."""
        password = self.cleaned_data.get('password1')
        
        if not password:
            raise ValidationError("Password is required.")
        
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one digit.")
        
        special_chars = r'[!@#$%^&*()_+\-]'
        if not re.search(special_chars, password):
            raise ValidationError(
                "Password must contain at least one special character from: ! @ # $ % ^ & * ( ) _ + -"
            )
        
        return password
    
    def clean(self):
        """Verify that password1 and password2 match."""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2:
            if password1 != password2:
                self.add_error('password2', 'Passwords do not match.')
        
        return cleaned_data


class ParentLoginForm(forms.Form):
    """Login form for parents."""
    from django.contrib.auth import authenticate
    from SchoolNowMgt.models import CustomUser
    
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'autofocus': True})
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput()
    )

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.authenticated_user = None

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if not email or not password:
            return cleaned_data

        from django.contrib.auth import authenticate
        from SchoolNowMgt.models import CustomUser

        # Find user by email (case-insensitive)
        try:
            user = CustomUser.objects.get(email__iexact=email)
        except CustomUser.DoesNotExist:
            raise forms.ValidationError(
                "No account found with this email address."
            )

        # Check if user role is 'parent'
        if user.role != 'parent':
            raise forms.ValidationError(
                "This login is for parents only."
            )

        # Authenticate with username and password
        authenticated = authenticate(
            request=self.request,
            username=user.username,
            password=password
        )

        if authenticated is None:
            raise forms.ValidationError(
                "Incorrect password. Please try again."
            )

        # Store authenticated user
        self.authenticated_user = authenticated
        return cleaned_data


class SupportStaffLoginForm(forms.Form):
    """Login form for support staff."""
    
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'autofocus': True})
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput()
    )

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.authenticated_user = None

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if not email or not password:
            return cleaned_data

        from django.contrib.auth import authenticate
        from SchoolNowMgt.models import CustomUser

        # Find user by email (case-insensitive)
        try:
            user = CustomUser.objects.get(email__iexact=email)
        except CustomUser.DoesNotExist:
            raise forms.ValidationError(
                "No account found with this email address."
            )

        # Check if user role is 'non_teaching_staff'
        if user.role != 'non_teaching_staff':
            raise forms.ValidationError(
                "This login is for support staff only."
            )

        # Authenticate with username and password
        authenticated = authenticate(
            request=self.request,
            username=user.username,
            password=password
        )

        if authenticated is None:
            raise forms.ValidationError(
                "Incorrect password. Please try again."
            )

        # Store authenticated user
        self.authenticated_user = authenticated
        return cleaned_data


# ═════════════════════════════════════════════════════════════════════════════
# PASSWORD RESET FORMS
# ═════════════════════════════════════════════════════════════════════════════


class ParentPasswordResetForm(forms.Form):
    """Password reset form for parents - filters by parent role."""
    
    email = forms.EmailField(
        label='Email',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'placeholder': 'Enter your email address'
        })
    )
    
    def clean_email(self):
        """Validate that email belongs to a parent user."""
        from SchoolNowMgt.models import CustomUser
        
        email = self.cleaned_data.get('email')
        
        try:
            user = CustomUser.objects.get(email__iexact=email)
            if user.role != 'parent':
                raise forms.ValidationError(
                    "This email is not associated with a parent account."
                )
        except CustomUser.DoesNotExist:
            raise forms.ValidationError(
                "No account found with this email address."
            )
        
        return email


class SupportStaffPasswordResetForm(forms.Form):
    """Password reset form for support staff - filters by role."""
    
    email = forms.EmailField(
        label='Email',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'placeholder': 'Enter your email address'
        })
    )
    
    def clean_email(self):
        """Validate that email belongs to a support staff user."""
        from SchoolNowMgt.models import CustomUser
        
        email = self.cleaned_data.get('email')
        
        try:
            user = CustomUser.objects.get(email__iexact=email)
            if user.role != 'non_teaching_staff':
                raise forms.ValidationError(
                    "This email is not associated with a support staff account."
                )
        except CustomUser.DoesNotExist:
            raise forms.ValidationError(
                "No account found with this email address."
            )
        
        return email
