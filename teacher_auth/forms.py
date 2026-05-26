from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from SchoolNowMgt.models import CustomUser, School, StaffProfile


class TeacherRegistrationForm(forms.Form):
    """
    Registration form for teachers.
    Creates a CustomUser with role='teacher' and a StaffProfile.
    """
    first_name = forms.CharField(
        label='First Name',
        max_length=150,
        widget=forms.TextInput(attrs={'autofocus': True})
    )
    last_name = forms.CharField(
        label='Last Name',
        max_length=150
    )
    email = forms.EmailField(label='Email Address')
    phone = forms.CharField(
        label='Phone Number',
        max_length=20,
        required=False
    )
    school = forms.ModelChoiceField(
        queryset=School.objects.all(),
        label='School',
        empty_label='Select a school'
    )
    employee_id = forms.CharField(
        label='Employee ID',
        max_length=50,
        help_text='Your staff employee ID number'
    )
    position = forms.CharField(
        label='Position/Title',
        max_length=100,
        help_text='e.g., Class Teacher, Head Teacher, Subject Specialist'
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput()
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput()
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'An account with this email address already exists.'
            )
        return email

    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id')
        if StaffProfile.objects.filter(employee_id=employee_id).exists():
            raise forms.ValidationError(
                'This employee ID is already registered.'
            )
        return employee_id

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

    def save(self):
        """
        Create a CustomUser and StaffProfile.
        """
        cleaned_data = self.cleaned_data
        
        # Generate a unique username from email
        email = cleaned_data['email']
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # Create CustomUser
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=cleaned_data['password1'],
            first_name=cleaned_data['first_name'],
            last_name=cleaned_data['last_name'],
            phone=cleaned_data.get('phone', ''),
            role='teacher',
            school=cleaned_data['school'],
            is_active=True
        )

        # Create StaffProfile
        staff_profile = StaffProfile.objects.create(
            user=user,
            employee_id=cleaned_data['employee_id'],
            position=cleaned_data['position'],
            date_joined=timezone.now().date()
        )

        return user


class TeacherLoginForm(forms.Form):
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

        # Step 1: Find user by email (case-insensitive)
        try:
            user = CustomUser.objects.get(email__iexact=email)
        except CustomUser.DoesNotExist:
            raise forms.ValidationError(
                "No account found with this email address."
            )

        # Step 2: Check if user role is 'teacher'
        if user.role != 'teacher':
            raise forms.ValidationError(
                "This login is for teachers only. Use the admin panel "
                "if you are an administrator."
            )

        # Step 3: Authenticate with username and password
        authenticated = authenticate(
            request=self.request,
            username=user.username,
            password=password
        )

        if authenticated is None:
            raise forms.ValidationError(
                "Incorrect password. Please try again."
            )

        # Step 4: Store authenticated user
        self.authenticated_user = authenticated
        return cleaned_data
