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
