"""
Forms for international curriculum grade entry.

Provides Form (not ModelForm) for entering student grades with support for
Cambridge IGCSE and IB grading systems, teacher-filtered queries, and
dual grade entry modes (percentage or direct grade band).
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from SchoolNowMgt.models import Student, Subject
from .international_constants import (
    INTERNATIONAL_TERMS,
    IGCSE_GRADE_BANDS,
    IB_GRADE_BANDS,
    percentage_to_igcse,
    percentage_to_ib,
)


CURRICULUM_TYPE_CHOICES = [
    ('igcse', 'Cambridge IGCSE'),
    ('ib',    'IB Primary Years / MYP'),
]


class InternationalGradeEntryForm(forms.Form):
    """
    Form for entering international curriculum grades.
    
    Supports:
    - Dual curriculum systems: Cambridge IGCSE and IB
    - Two semester system (semester_1, semester_2)
    - Percentage score entry (0–100) with automatic grade band conversion
    - Direct grade band entry (IGCSE: A*–U, IB: 7–1)
    - Teacher-filtered student and subject querysets
    
    Validation ensures that at least one grade method is provided (score or
    direct grade), and automatically computes the grade band from percentage
    if provided.
    """
    
    curriculum_type = forms.ChoiceField(
        choices=CURRICULUM_TYPE_CHOICES,
        label='Curriculum Type',
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        label='Student',
        widget=forms.Select(attrs={'class': 'form-input'}),
        empty_label='— Select student —'
    )
    
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        label='Subject',
        widget=forms.Select(attrs={'class': 'form-input'}),
        empty_label='— Select subject —'
    )
    
    semester = forms.ChoiceField(
        choices=INTERNATIONAL_TERMS,
        label='Semester',
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
        required=False,
        label='Score (0–100)',
        help_text='Enter percentage. Grade band will be calculated automatically.',
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'step': '0.01',
            'min': '0',
            'max': '100',
            'placeholder': '0–100'
        })
    )
    
    direct_grade_igcse = forms.ChoiceField(
        choices=IGCSE_GRADE_BANDS,
        required=False,
        label='Or enter IGCSE grade directly',
        widget=forms.Select(attrs={
            'class': 'form-input',
        })
    )
    
    direct_grade_ib = forms.ChoiceField(
        choices=IB_GRADE_BANDS,
        required=False,
        label='Or enter IB grade directly',
        widget=forms.Select(attrs={
            'class': 'form-input',
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
    
    def __init__(self, *args, teacher=None, **kwargs):
        """
        Initialize form with optional teacher filtering.
        
        Args:
            teacher (StaffProfile, optional): Teacher whose students/subjects to filter.
                If provided, filters student queryset to only active students in
                this teacher's international curriculum classes, and subject queryset
                to only international subjects the teacher teaches (via Timetable).
        """
        super().__init__(*args, **kwargs)
        
        if teacher:
            # Filter students: only active students in international curriculum classes
            self.fields['student'].queryset = Student.objects.filter(
                class_grade__class_teacher=teacher,
                class_grade__curriculum='international',
                curriculum='international',
                status='active'
            ).order_by('class_grade__name', 'last_name')
            
            # Filter subjects: only international curriculum subjects taught by this teacher
            subject_queryset = Subject.objects.filter(
                timetable_entries__teacher=teacher,
                timetable_entries__curriculum='international',
                curriculum='international'
            ).distinct()
            
            # Fallback to all international subjects if teacher has no timetable entries
            if not subject_queryset.exists():
                subject_queryset = Subject.objects.filter(curriculum='international')
            
            self.fields['subject'].queryset = subject_queryset
    
    def clean(self):
        """
        Validate grade entry and compute grade band from score if provided.
        
        Ensures:
        - At least one grade method (score or direct grade) is provided.
        - If score is provided, automatically computes grade band based on
          curriculum type.
        - If direct grade is provided without score, uses that grade.
        - Stores computed grade in cleaned_data['computed_grade'] for later use.
        
        Raises:
            ValidationError: If no grade method is provided.
        """
        cleaned_data = super().clean()
        
        score = cleaned_data.get('score')
        direct_grade_igcse = cleaned_data.get('direct_grade_igcse')
        direct_grade_ib = cleaned_data.get('direct_grade_ib')
        curriculum_type = cleaned_data.get('curriculum_type')
        
        # Validate: at least one grade method is provided
        if not score and not direct_grade_igcse and not direct_grade_ib:
            raise ValidationError(
                "Enter either a percentage score or a grade band."
            )
        
        # Compute grade from score if provided
        if score is not None:
            if curriculum_type == 'igcse':
                cleaned_data['computed_grade'] = percentage_to_igcse(float(score))
            elif curriculum_type == 'ib':
                cleaned_data['computed_grade'] = percentage_to_ib(float(score))
        # Otherwise, use direct grade entry
        elif curriculum_type == 'igcse' and direct_grade_igcse:
            cleaned_data['computed_grade'] = direct_grade_igcse
        elif curriculum_type == 'ib' and direct_grade_ib:
            cleaned_data['computed_grade'] = direct_grade_ib
        
        return cleaned_data
