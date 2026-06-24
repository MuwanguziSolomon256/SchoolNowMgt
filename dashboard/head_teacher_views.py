"""
Head Teacher Admin Dashboard Views

Director of overall academic leadership and school performance
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from SchoolNowMgt.models import StaffProfile, ClassGrade, Subject, Student, Timetable, ActivityLog
from SchoolNowMgt.decorators import require_teacher_role, get_user_school


@login_required
@require_teacher_role('head_teacher')
def head_teacher_dashboard(request):
    """Head Teacher Dashboard - Overall academic leadership"""
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get all classes in school
    classes = ClassGrade.objects.filter(school=school).count()
    
    # Get all subjects (not filtered by school as Subject doesn't have school FK)
    subjects = Subject.objects.all().count()
    
    # Get all students in school
    students = Student.objects.filter(
        class_grade__school=school
    ).distinct().count()
    
    # Get all timetable entries in school
    timetable_entries = Timetable.objects.filter(
        class_grade__school=school
    ).count()
    
    # Get recent activities
    recent_activities = ActivityLog.objects.all().select_related('teacher').order_by('-created_at')[:10]
    
    context = {
        'school': school,
        'staff_profile': staff_profile,
        'statistics': {
            'classes': classes,
            'subjects': subjects,
            'students': students,
            'timetable_entries': timetable_entries,
        },
        'recent_activities': recent_activities,
        'page_title': 'Head Teacher Dashboard',
        'breadcrumbs': [
            {'label': 'Home', 'url': '/teacher/'},
            {'label': 'Head Teacher Dashboard', 'url': None},
        ]
    }
    
    return render(request, 'head_teacher/head_teacher_dashboard.html', context)


@login_required
@require_teacher_role('head_teacher')
def academic_performance(request):
    """Overall academic performance report"""
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get class performance metrics
    classes = ClassGrade.objects.filter(school=school).prefetch_related('subject_set')
    
    # Calculate statistics per class
    class_stats = []
    for cls in classes:
        students_count = Student.objects.filter(class_grade=cls).count()
        class_stats.append({
            'class': cls,
            'students': students_count,
        })
    
    context = {
        'school': school,
        'staff_profile': staff_profile,
        'class_statistics': class_stats,
        'page_title': 'Academic Performance',
    }
    
    return render(request, 'head_teacher/academic_performance.html', context)


@login_required
@require_teacher_role('head_teacher')
def staff_oversight(request):
    """Oversight of all teaching staff"""
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get all staff members in school
    staff_list = StaffProfile.objects.filter(
        user__role='teacher',
        user__school=school
    ).select_related('user')
    
    context = {
        'school': school,
        'staff_profile': staff_profile,
        'staff_list': staff_list,
        'page_title': 'Staff Oversight',
    }
    
    return render(request, 'head_teacher/staff_oversight.html', context)


@login_required
@require_teacher_role('head_teacher')
def school_timetable(request):
    """Overall school timetable view"""
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get all timetable entries
    timetables = Timetable.objects.filter(
        school=school
    ).select_related('class_grade', 'subject', 'teacher')
    
    context = {
        'school': school,
        'staff_profile': staff_profile,
        'timetables': timetables,
        'page_title': 'School Timetable',
    }
    
    return render(request, 'head_teacher/school_timetable.html', context)
