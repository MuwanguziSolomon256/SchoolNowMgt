"""
Subject Department Head Dashboard Views
Handles department overview, teacher management, subject management, and performance tracking
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Count, Q, Avg
from django.utils import timezone
from django.contrib import messages

from SchoolNowMgt.decorators import require_teacher_role, get_user_school
from SchoolNowMgt.models import (
    CustomUser, StaffProfile, Subject, ClassGrade, Timetable, 
    Grade, StudentAttendance, ActivityLog, School, Department
)


def paginate_queryset(request, queryset, per_page=15):
    """Helper function to paginate querysets"""
    paginator = Paginator(queryset, per_page)
    page_num = request.GET.get('page', 1)
    try:
        page = paginator.page(page_num)
    except PageNotAnInteger:
        page = paginator.page(1)
        page_num = 1
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
        page_num = paginator.num_pages
    return page, paginator, page_num


@login_required
@require_teacher_role('department_head')
def dept_dashboard(request):
    """Subject Department Head Dashboard - Overview"""
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get all subjects for this school
    subjects = Subject.objects.all()[:20]
    
    # Get teachers in this school
    department_teachers = StaffProfile.objects.filter(
        user__school=school,
        subjects__in=subjects
    ).distinct()
    
    # Get classes in school
    classes = ClassGrade.objects.filter(
        school=school
    ).select_related('class_grade_level', 'class_stream').distinct()
    
    # Statistics
    total_subjects = subjects.count()
    total_teachers = department_teachers.count()
    total_classes = classes.count()
    
    # Average student performance (from grades)
    avg_performance = Grade.objects.filter(
        score__isnull=False
    ).aggregate(avg=Avg('score'))['avg'] or 0
    avg_performance = round(avg_performance, 1)
    
    # Recent activities - not filtered by school since ActivityLog doesn't have school field
    recent_activities = ActivityLog.objects.filter(
        activity_type__in=['subject_updated', 'grade_entered', 'assignment_created']
    ).order_by('-created_at')[:5]
    
    # Get current semester/term for display
    today = timezone.now().date()
    
    context = {
        'today': today,
        'school': school,
        'staff_profile': staff_profile,
        'subjects': subjects[:8],
        'total_subjects': total_subjects,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'avg_performance': avg_performance,
        'recent_activities': recent_activities,
        'department_teachers': department_teachers,
    }
    
    return render(request, 'subject_dept/dept_dashboard.html', context)


@login_required
@require_teacher_role('department_head')
def teachers_list(request):
    """List all teachers in department"""
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get department subjects (all subjects, no school/department_head filter available)
    subjects = Subject.objects.all()
    
    # Get teachers
    teachers = StaffProfile.objects.filter(
        user__school=school
    ).select_related('user').distinct()
    
    # Search filter
    search_term = request.GET.get('search', '')
    if search_term:
        teachers = teachers.filter(
            Q(user__first_name__icontains=search_term) |
            Q(user__last_name__icontains=search_term) |
            Q(employee_id__icontains=search_term)
        )
    
    # Status filter
    status = request.GET.get('status', '')
    if status == 'active':
        teachers = teachers.filter(user__is_active=True)
    elif status == 'inactive':
        teachers = teachers.filter(user__is_active=False)
    
    # Pagination
    page, paginator, page_num = paginate_queryset(request, teachers, per_page=15)
    
    context = {
        'page_obj': page,
        'paginator': paginator,
        'page_num': page_num,
        'search_term': search_term,
        'status': status,
    }
    
    return render(request, 'subject_dept/teachers_list.html', context)


@login_required
@require_teacher_role('department_head')
def teacher_detail(request, teacher_id):
    """View teacher profile and teaching load"""
    school = get_user_school(request)
    staff_profile = get_object_or_404(
        StaffProfile,
        user=request.user,
        user__school=school
    )
    
    # Verify teacher is in department
    teacher = get_object_or_404(StaffProfile, id=teacher_id, user__school=school)
    
    # Get teacher's subjects
    subjects = Subject.objects.filter(
        school=school,
        staff__in=[teacher]
    )
    
    # Get teacher's classes
    classes = ClassGrade.objects.filter(
        school=school,
        subject__in=subjects
    ).select_related('class_grade_level', 'class_stream')
    
    # Get teacher's timetable
    timetable = Timetable.objects.filter(
        school=school,
        staff=teacher
    ).select_related('subject', 'class_grade').order_by('day', 'start_time')
    
    # Performance stats
    grades_entered = Grade.objects.filter(
        recorded_by__user__id=teacher.user.id,
        school=school
    ).count()
    
    context = {
        'teacher': teacher,
        'subjects': subjects,
        'classes': classes,
        'timetable': timetable,
        'grades_entered': grades_entered,
    }
    
    return render(request, 'subject_dept/teacher_detail.html', context)


@login_required
@require_teacher_role('department_head')
def subjects_list(request):
    """List all subjects in department"""
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get department subjects (all subjects)
    subjects = Subject.objects.all()
    
    # Search filter
    search_term = request.GET.get('search', '')
    if search_term:
        subjects = subjects.filter(
            Q(name__icontains=search_term) |
            Q(code__icontains=search_term)
        )
    
    # Pagination
    page, paginator, page_num = paginate_queryset(request, subjects, per_page=15)
    
    context = {
        'page_obj': page,
        'paginator': paginator,
        'page_num': page_num,
        'search_term': search_term,
    }
    
    return render(request, 'subject_dept/subjects_list.html', context)


@login_required
@require_teacher_role('department_head')
def subject_detail(request, subject_id):
    """View subject details and classes"""
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get subject by ID (Note: Subject doesn't have school/department_head fields)
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Get classes for this subject
    classes = ClassGrade.objects.filter(
        school=school,
        subject=subject
    ).select_related('class_grade_level', 'class_stream')
    
    # Get teachers teaching this subject
    # Note: StaffProfile has many-to-many 'subjects' relationship, filter by that
    teachers = StaffProfile.objects.filter(
        user__school=school,
        subjects=subject
    ).select_related('user').distinct()
    
    # Get grades for this subject
    grades = Grade.objects.filter(
        subject=subject,
        school=school
    ).select_related('student', 'recorded_by__user')[:10]
    
    # Performance metrics
    avg_score = Grade.objects.filter(
        subject=subject,
        school=school,
        grade_point__isnull=False
    ).aggregate(avg=Avg('grade_point'))['avg'] or 0
    avg_score = round(avg_score, 1)
    
    context = {
        'subject': subject,
        'classes': classes,
        'teachers': teachers,
        'grades': grades,
        'avg_score': avg_score,
    }
    
    return render(request, 'subject_dept/subject_detail.html', context)


@login_required
@require_teacher_role('department_head')
def classes_list(request):
    """List all classes assigned to department subjects"""
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get department subjects (all subjects)
    subjects = Subject.objects.all()
    
    # Get classes
    classes = ClassGrade.objects.filter(
        school=school
    ).select_related('class_grade_level', 'class_stream', 'subject').distinct()
    
    # Search filter
    search_term = request.GET.get('search', '')
    if search_term:
        classes = classes.filter(
            Q(class_grade_level__level_name__icontains=search_term) |
            Q(class_stream__stream_name__icontains=search_term)
        )
    
    # Grade filter
    grade_filter = request.GET.get('grade', '')
    if grade_filter:
        classes = classes.filter(class_grade_level__id=grade_filter)
    
    # Pagination
    page, paginator, page_num = paginate_queryset(request, classes, per_page=15)
    
    # Get all grades for filter dropdown
    all_grades = ClassGrade.objects.filter(school=school).select_related(
        'class_grade_level'
    ).distinct('class_grade_level').order_by('class_grade_level__order')
    
    context = {
        'page_obj': page,
        'paginator': paginator,
        'page_num': page_num,
        'search_term': search_term,
        'grade_filter': grade_filter,
        'all_grades': all_grades,
    }
    
    return render(request, 'subject_dept/classes_list.html', context)


@login_required
@require_teacher_role('department_head')
def timetable_overview(request):
    """View department timetable"""
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get department subjects (all subjects)
    subjects = Subject.objects.all()
    
    # Get timetable for department subjects
    timetable = Timetable.objects.filter(
        school=school,
        subject__in=subjects
    ).select_related('subject', 'class_grade', 'staff').order_by('day', 'start_time')
    
    # Group by day
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    timetable_by_day = {}
    for day in days_order:
        timetable_by_day[day] = [t for t in timetable if t.day == day]
    
    context = {
        'timetable_by_day': timetable_by_day,
        'all_timetable': timetable,
    }
    
    return render(request, 'subject_dept/timetable_overview.html', context)


@login_required
@require_teacher_role('department_head')
def performance_report(request):
    """Department performance metrics"""
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get department subjects (all subjects)
    subjects = Subject.objects.all()
    
    # Subject performance
    subject_performance = []
    for subject in subjects:
        avg_score = Grade.objects.filter(
            subject=subject,
            school=school,
            grade_point__isnull=False
        ).aggregate(avg=Avg('grade_point'))['avg'] or 0
        
        grades_count = Grade.objects.filter(
            subject=subject,
            school=school
        ).count()
        
        subject_performance.append({
            'subject': subject,
            'avg_score': round(avg_score, 1),
            'grades_count': grades_count,
        })
    
    # Sort by performance
    subject_performance.sort(key=lambda x: x['avg_score'], reverse=True)
    
    # Class-wise performance
    classes = ClassGrade.objects.filter(
        school=school,
        subject__in=subjects
    ).distinct()
    
    class_performance = []
    for cls in classes:
        avg_score = Grade.objects.filter(
            class_grade=cls,
            school=school,
            grade_point__isnull=False
        ).aggregate(avg=Avg('grade_point'))['avg'] or 0
        
        class_performance.append({
            'class': cls,
            'avg_score': round(avg_score, 1),
        })
    
    # Overall metrics
    total_students = StudentAttendance.objects.filter(
        school=school
    ).values('student').distinct().count()
    
    context = {
        'subject_performance': subject_performance,
        'class_performance': class_performance,
        'total_students': total_students,
    }
    
    return render(request, 'subject_dept/performance_report.html', context)
