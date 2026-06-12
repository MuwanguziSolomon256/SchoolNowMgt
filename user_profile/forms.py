from django import forms
from django.core.exceptions import ValidationError
from SchoolNowMgt.models import CustomUser, StaffProfile


class TeacherProfileForm(forms.ModelForm):
    """Form for editing teacher's basic profile information."""
    
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                'accept': 'image/jpeg,image/png',
            }
        ),
        help_text='Accepted formats: JPG, JPEG, PNG. Max size: 2 MB.'
    )
    
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone', 'profile_picture']
    
    def clean_profile_picture(self):
        """Validate profile picture file size (max 2 MB)."""
        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture:
            if profile_picture.size > 2 * 1024 * 1024:  # 2 MB in bytes
                raise ValidationError("Photo must be under 2 MB.")
        return profile_picture


class TeacherQualificationForm(forms.ModelForm):
    """Form for editing teacher's qualification information."""
    
    position = forms.CharField(
        required=True,
        disabled=True,
        help_text='Position is managed by administration.'
    )
    
    class Meta:
        model = StaffProfile
        fields = ['qualification', 'position']


class ParentProfileForm(forms.ModelForm):
    """Form for editing parent's basic profile information."""
    
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                'accept': 'image/jpeg,image/png',
            }
        ),
        help_text='Accepted formats: JPG, JPEG, PNG. Max size: 2 MB.'
    )
    
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'profile_picture']
    
    def clean_profile_picture(self):
        """Validate profile picture file size (max 2 MB)."""
        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture:
            if profile_picture.size > 2 * 1024 * 1024:  # 2 MB in bytes
                raise ValidationError("Photo must be under 2 MB.")
        return profile_picture
    
    def clean_email(self):
        """Validate that email is unique (excluding current user)."""
        email = self.cleaned_data.get('email')
        if email and CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This email address is already in use.")
        return email


class SupportStaffProfileForm(forms.ModelForm):
    """Form for editing support staff's basic profile information."""
    
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                'accept': 'image/jpeg,image/png',
            }
        ),
        help_text='Accepted formats: JPG, JPEG, PNG. Max size: 2 MB.'
    )
    
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone', 'profile_picture']
    
    def clean_profile_picture(self):
        """Validate profile picture file size (max 2 MB)."""
        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture:
            if profile_picture.size > 2 * 1024 * 1024:  # 2 MB in bytes
                raise ValidationError("Photo must be under 2 MB.")
        return profile_picture


class SupportStaffDetailsForm(forms.ModelForm):
    """Form for editing support staff's extended profile details including emergency contact and bank information."""
    
    class Meta:
        model = StaffProfile
        fields = ['emergency_contact_name', 'emergency_contact_phone', 'bank_account_number', 'bank_name', 'account_holder_name']
        widgets = {
            'emergency_contact_name': forms.TextInput(attrs={'placeholder': 'Full name of emergency contact'}),
            'emergency_contact_phone': forms.TextInput(attrs={'placeholder': 'Phone number'}),
            'bank_account_number': forms.TextInput(attrs={'placeholder': 'Account number'}),
            'bank_name': forms.TextInput(attrs={'placeholder': 'Name of bank'}),
            'account_holder_name': forms.TextInput(attrs={'placeholder': 'Account holder name'}),
        }
    
    def clean_emergency_contact_phone(self):
        """Validate emergency contact phone number format."""
        phone = self.cleaned_data.get('emergency_contact_phone')
        if phone and len(phone) < 10:
            raise ValidationError("Phone number must be at least 10 digits.")
        return phone
    
    def clean_bank_account_number(self):
        """Validate bank account number format."""
        account = self.cleaned_data.get('bank_account_number')
        if account and len(account) < 8:
            raise ValidationError("Bank account number must be at least 8 digits.")
        return account
