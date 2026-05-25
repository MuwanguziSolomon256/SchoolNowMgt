from django import forms
from django.core.exceptions import ValidationError
from .models import Enquiry, StudentAttendance, ClassGrade


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
