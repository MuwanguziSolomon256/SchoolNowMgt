"""
Views for Uganda national curriculum grade entry.

Provides teacher grade entry form with update_or_create logic.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from SchoolNowMgt.models import StaffProfile, Grade
from .forms import UgandaGradeEntryForm
from .uganda_constants import get_letter_grade


@login_required
def enter_grade_uganda(request):
    """
    Grade entry view for Uganda national curriculum.
    
    GET: Display form and recent grades entered by teacher.
    POST: Validate and save/update grade using update_or_create.
    
    Requires: User must be authenticated (login_required).
    Teacher filtering: Uses StaffProfile to filter students/subjects.
    """
    # Fetch teacher's StaffProfile
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    if request.method == 'GET':
        # Display form and recent grades
        form = UgandaGradeEntryForm(teacher=staff)
        
        recent_grades = Grade.objects.filter(
            recorded_by=request.user
        ).select_related('student', 'subject').order_by('-created_at')[:10]
        
        context = {
            'form': form,
            'recent_grades': recent_grades,
            'curriculum_type': 'Uganda National Curriculum',
        }
        return render(request, 'teacher/grade_entry_uganda.html', context)
    
    elif request.method == 'POST':
        # Process form submission
        form = UgandaGradeEntryForm(request.POST, teacher=staff)
        
        if form.is_valid():
            # Extract data
            grade_obj = form.save(commit=False)
            
            # Use update_or_create to prevent duplicates
            Grade.objects.update_or_create(
                student=grade_obj.student,
                subject=grade_obj.subject,
                term=grade_obj.term,
                academic_year=grade_obj.academic_year,
                defaults={
                    'score': grade_obj.score,
                    'remarks': grade_obj.remarks,
                    'recorded_by': request.user,
                }
            )
            
            # Success message with letter grade
            letter_grade = get_letter_grade(grade_obj.score)
            messages.success(
                request,
                f"Grade saved: {grade_obj.student.full_name} — "
                f"{grade_obj.subject} — {grade_obj.score}/100 ({letter_grade})"
            )
            
            # Redirect (PRG pattern)
            return redirect('teacher:enter_grade_uganda')
        
        else:
            # Re-render form with errors
            recent_grades = Grade.objects.filter(
                recorded_by=request.user
            ).select_related('student', 'subject').order_by('-created_at')[:10]
            
            context = {
                'form': form,
                'recent_grades': recent_grades,
                'curriculum_type': 'Uganda National Curriculum',
            }
            return render(request, 'teacher/grade_entry_uganda.html', context)
