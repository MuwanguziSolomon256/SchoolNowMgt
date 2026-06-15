"""
Views for international curriculum grade entry.

Provides teacher grade entry form for Cambridge IGCSE and IB systems,
with update_or_create logic and recent grades display.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from SchoolNowMgt.models import StaffProfile, Grade
from .international_forms import InternationalGradeEntryForm


@login_required
def enter_grade_international(request):
    """
    Grade entry view for international curriculum (IGCSE and IB).
    
    GET: Display form and recent grades entered by teacher.
    POST: Validate and save/update grade using update_or_create.
    
    Requires: User must be authenticated (login_required).
    Teacher filtering: Uses StaffProfile to filter students/subjects.
    
    Grade storage: Computed grade band is stored in the remarks field as a
    structured prefix: "[IGCSE] Grade: A*." or "[IB] Grade: 7." to maintain
    compatibility with the shared Grade model.
    """
    # Fetch teacher's StaffProfile
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    if request.method == 'GET':
        # Display form and recent grades
        form = InternationalGradeEntryForm(teacher=staff)
        
        recent_grades = Grade.objects.filter(
            recorded_by=request.user,
            curriculum='international'
        ).select_related('student', 'subject').order_by('-created_at')[:10]
        
        context = {
            'form': form,
            'recent_grades': recent_grades,
            'curriculum_type': 'International Curriculum',
        }
        return render(request, 'teacher/grade_entry_international.html', context)
    
    elif request.method == 'POST':
        # Process form submission
        form = InternationalGradeEntryForm(request.POST, teacher=staff)
        
        if form.is_valid():
            # Extract data
            cd = form.cleaned_data
            score_value = cd.get('score') or 0
            computed_grade = cd.get('computed_grade', '')
            curriculum_type_upper = cd.get('curriculum_type', '').upper()
            
            # Store computed grade in remarks with curriculum type prefix
            remarks_prefix = (
                f"[{curriculum_type_upper}] Grade: {computed_grade}. "
            )
            full_remarks = remarks_prefix + cd.get('remarks', '')
            
            # Update or create grade (prevents duplicates)
            Grade.objects.update_or_create(
                student=cd['student'],
                subject=cd['subject'],
                curriculum='international',
                semester=cd['semester'],
                academic_year=cd['academic_year'],
                defaults={
                    'score': score_value,
                    'remarks': full_remarks,
                    'recorded_by': request.user,
                }
            )
            
            # Success message
            messages.success(
                request,
                f"Grade saved: {cd['student'].full_name} — "
                f"{cd['subject']} — {computed_grade} "
                f"({cd['curriculum_type'].upper()})"
            )
            
            # Redirect (PRG pattern)
            return redirect('teacher:enter_grade_international')
        
        else:
            # Re-render form with errors
            recent_grades = Grade.objects.filter(
                recorded_by=request.user,
                curriculum='international'
            ).select_related('student', 'subject').order_by('-created_at')[:10]
            
            context = {
                'form': form,
                'recent_grades': recent_grades,
                'curriculum_type': 'International Curriculum',
            }
            return render(request, 'teacher/grade_entry_international.html', context)
