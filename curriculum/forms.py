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
