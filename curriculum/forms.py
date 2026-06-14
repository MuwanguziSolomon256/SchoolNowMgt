"""
Forms for Uganda national curriculum grade entry.

Provides ModelForm for entering student grades with teacher-filtered queries.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from SchoolNowMgt.models import Grade, Student, Subject
from .uganda_constants import UGANDA_TERMS


class UgandaGradeEntryForm(forms.ModelForm):
    """
    ModelForm for entering student grades under Uganda national curriculum.
    
    Filters student and subject querysets by teacher when instantiated.
    Provides validation for numeric scores (0–100).
    """
    
    term = forms.ChoiceField(
        choices=UGANDA_TERMS,
        label='Term',
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    
    academic_year = forms.CharField(
        max_length=4,
        label='Academic Year',
        initial=str(timezone.now().year),
        widget=forms.TextInput(attrs={'class': 'form-input'})
    )
    
    score = forms.DecimalField(
        min_value=0,
        max_value=100,
        decimal_places=2,
        label='Score (0–100)',
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'step': '0.01',
            'min': '0',
            'max': '100'
        })
    )
    
    remarks = forms.CharField(
        required=False,
        label='Remarks',
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'rows': 3,
            'placeholder': 'Optional remarks or notes'
        })
    )
    
    class Meta:
        model = Grade
        fields = ['student', 'subject', 'term', 'academic_year', 'score', 'remarks']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-input'}),
            'subject': forms.Select(attrs={'class': 'form-input'}),
        }
    
    def __init__(self, *args, teacher=None, **kwargs):
        """
        Initialize form with optional teacher filtering.
        
        Args:
            teacher (StaffProfile, optional): Teacher whose students/subjects to filter.
                If provided, filters student queryset to only students in classes
                where this teacher is class_teacher, and subject queryset to only
                subjects the teacher teaches (via Timetable).
        """
        super().__init__(*args, **kwargs)
        
        if teacher:
            # Filter students: only active students in this teacher's classes
            self.fields['student'].queryset = Student.objects.filter(
                class_grade__class_teacher=teacher,
                status='active'
            ).order_by('class_grade__name', 'last_name')
            
            # Filter subjects: only subjects in this teacher's timetable
            subject_queryset = Subject.objects.filter(
                timetable_entries__teacher=teacher
            ).distinct()
            
            # Fallback to all subjects if teacher has no timetable entries
            if not subject_queryset.exists():
                subject_queryset = Subject.objects.all()
            
            self.fields['subject'].queryset = subject_queryset
    
    def clean_score(self):
        """Validate score is between 0 and 100."""
        score = self.cleaned_data.get('score')
        
        if score is not None:
            if score < 0 or score > 100:
                raise ValidationError("Score must be between 0 and 100.")
        
        return score


# ========================
# TEACHER SUB-DASHBOARD FORMS
# ========================

class GradeEntryForm(forms.Form):
    """
    Form for bulk grade entry - teacher selects class and subject, then enters grades.
    """
    class_grade = forms.ModelChoiceField(
        queryset=None,  # Set in __init__
        label='Class',
        widget=forms.Select(attrs={
            'class': 'form-input',
            'id': 'id_class_grade'
        })
    )
    
    subject = forms.ModelChoiceField(
        queryset=None,  # Set in __init__
        label='Subject',
        widget=forms.Select(attrs={
            'class': 'form-input',
            'id': 'id_subject'
        })
    )
    
    term = forms.ChoiceField(
        choices=UGANDA_TERMS,
        label='Term',
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    
    academic_year = forms.IntegerField(
        label='Academic Year',
        initial=timezone.now().year,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'min': '2000',
            'max': str(timezone.now().year + 5)
        })
    )
    
    csv_file = forms.FileField(
        required=False,
        label='Upload CSV (optional)',
        help_text='CSV format: StudentID, Score. One per line.',
        widget=forms.FileInput(attrs={'class': 'form-input', 'accept': '.csv'})
    )
    
    def __init__(self, *args, teacher=None, **kwargs):
        """Initialize with teacher's classes and subjects."""
        super().__init__(*args, **kwargs)
        
        if teacher:
            # Filter to teacher's classes
            self.fields['class_grade'].queryset = Subject.objects.filter(
                timetable_entries__teacher=teacher
            ).distinct()
            
            # Filter to teacher's subjects
            self.fields['subject'].queryset = Subject.objects.filter(
                timetable_entries__teacher=teacher
            ).distinct()


class TeacherMessageForm(forms.Form):
    """
    Form for teachers to send messages to parents, colleagues, or admin.
    """
    RECIPIENT_TYPE_CHOICES = [
        ('class_announcement', 'Class Announcement (All parents in class)'),
        ('individual_parent', 'Individual Parent'),
        ('specific_teacher', 'Colleague (Teacher)'),
        ('admin', 'Admin/School Management'),
    ]
    
    recipient_type = forms.ChoiceField(
        choices=RECIPIENT_TYPE_CHOICES,
        label='Send To',
        widget=forms.Select(attrs={
            'class': 'form-input',
            'id': 'id_recipient_type'
        })
    )
    
    target_class = forms.ModelChoiceField(
        queryset=None,  # Set in __init__
        required=False,
        label='Select Class',
        widget=forms.Select(attrs={
            'class': 'form-input',
            'id': 'id_target_class',
            'style': 'display:none;'
        })
    )
    
    target_user = forms.ModelChoiceField(
        queryset=None,  # Set in __init__
        required=False,
        label='Select Recipient',
        widget=forms.Select(attrs={
            'class': 'form-input',
            'id': 'id_target_user',
            'style': 'display:none;'
        })
    )
    
    subject = forms.CharField(
        max_length=200,
        label='Subject',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Message subject'
        })
    )
    
    body = forms.CharField(
        max_length=2000,
        min_length=5,
        label='Message',
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'rows': 5,
            'placeholder': 'Type your message here...'
        })
    )
    
    def __init__(self, *args, teacher=None, **kwargs):
        """Initialize with teacher's classes and potential recipients."""
        super().__init__(*args, **kwargs)
        
        if teacher:
            # Set class queryset for announcements
            from SchoolNowMgt.models import ClassGrade, StaffProfile
            staff = StaffProfile.objects.filter(user=teacher).first()
            if staff:
                self.fields['target_class'].queryset = ClassGrade.objects.filter(
                    school=teacher.school
                )
            
            # Set user queryset for individual messages
            from SchoolNowMgt.models import CustomUser
            self.fields['target_user'].queryset = CustomUser.objects.filter(
                school=teacher.school
            ).exclude(id=teacher.id)


class AttendanceMarkingForm(forms.Form):
    """
    Form for marking attendance - dynamically generates checkbox fields per student.
    """
    class_grade = forms.ModelChoiceField(
        queryset=None,  # Set in __init__
        label='Class',
        widget=forms.Select(attrs={
            'class': 'form-input',
            'id': 'id_class_grade'
        })
    )
    
    def __init__(self, *args, class_grade=None, **kwargs):
        """Initialize with students from the selected class."""
        super().__init__(*args, **kwargs)
        
        if class_grade:
            # Get all active students in the class
            students = Student.objects.filter(
                class_grade=class_grade,
                status='active'
            ).order_by('first_name', 'last_name')
            
            # Create checkbox field for each student
            for student in students:
                field_name = f'student_{student.id}'
                self.fields[field_name] = forms.ChoiceField(
                    choices=[
                        ('present', 'Present'),
                        ('absent', 'Absent'),
                        ('late', 'Late'),
                    ],
                    label=student.get_full_name(),
                    initial='present',
                    widget=forms.RadioSelect(attrs={
                        'class': 'attendance-radio',
                    })
                )
