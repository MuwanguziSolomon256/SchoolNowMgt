"""
Class Teacher Dashboard Views
Handles class management, student tracking, grade management, and parent communication
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Count, Q, Avg
from django.utils import timezone
from django.contrib import messages

from SchoolNowMgt.decorators import require_teacher_role, get_user_school
from SchoolNowMgt.models import (
    CustomUser, StaffProfile, ClassGrade, Student, Grade, StudentAttendance,
    ActivityLog, Timetable, Subject, Message
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
@require_teacher_role('class_teacher')
def class_dashboard(request):
    """Class Teacher Dashboard - Overview"""
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get classes where user is class_teacher
    classes = ClassGrade.objects.filter(
        school=school,
        class_teacher=staff_profile
    ).select_related('class_grade_level', 'class_stream')
    
    if not classes.exists():
        # If no class assigned, show empty state
        context = {'today': timezone.now().date(), 'no_class': True}
        return render(request, 'class_teacher/class_dashboard.html', context)
    
    # Use the first class (or could allow selection)
    my_class = classes.first()
    
    # Get students in class
    students = Student.objects.filter(
        school=school,
        class_grade=my_class,
        is_active=True
    ).select_related('user').order_by('user__last_name', 'user__first_name')
    
    total_students = students.count()
    
    # Attendance today
    today = timezone.now().date()
    attendance_today = StudentAttendance.objects.filter(
        student__in=students,
        date=today,
        school=school
    ).values('status').annotate(count=Count('status'))
    
    attendance_dict = {item['status']: item['count'] for item in attendance_today}
    present_today = attendance_dict.get('present', 0)
    absent_today = attendance_dict.get('absent', 0)
    
    # Average class performance
    avg_performance = Grade.objects.filter(
        student__in=students,
        school=school,
        grade_point__isnull=False
    ).aggregate(avg=Avg('grade_point'))['avg'] or 0
    avg_performance = round(avg_performance, 1)
    
    # Recent grades entered
    recent_grades = Grade.objects.filter(
        student__in=students,
        school=school
    ).select_related('student', 'subject', 'recorded_by__user').order_by('-created_at')[:5]
    
    # Class timetable
    timetable = Timetable.objects.filter(
        school=school,
        class_grade=my_class
    ).select_related('subject', 'staff').order_by('day', 'start_time')
    
    # Recent activities
    recent_activities = ActivityLog.objects.filter(
        school=school,
        activity_type__in=['grade_entered', 'attendance_marked', 'assignment_created']
    ).order_by('-created_at')[:5]
    
    context = {
        'today': today,
        'school': school,
        'staff_profile': staff_profile,
        'my_class': my_class,
        'total_students': total_students,
        'present_today': present_today,
        'absent_today': absent_today,
        'avg_performance': avg_performance,
        'recent_grades': recent_grades,
        'timetable': timetable,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'class_teacher/class_dashboard.html', context)


@login_required
@require_teacher_role('class_teacher')
def students_list(request):
    """List all students in class"""
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get user's class
    my_class = ClassGrade.objects.filter(
        school=school,
        class_teacher=staff_profile
    ).first()
    
    if not my_class:
        return render(request, 'class_teacher/students_list.html', {'no_class': True})
    
    # Get students
    students = Student.objects.filter(
        school=school,
        class_grade=my_class,
        is_active=True
    ).select_related('user')
    
    # Search filter
    search_term = request.GET.get('search', '')
    if search_term:
        students = students.filter(
            Q(user__first_name__icontains=search_term) |
            Q(user__last_name__icontains=search_term) |
            Q(user__email__icontains=search_term)
        )
    
    # Status filter
    status = request.GET.get('status', '')
    if status == 'present':
        today = timezone.now().date()
        present_students = StudentAttendance.objects.filter(
            date=today,
            status='present',
            school=school
        ).values_list('student_id', flat=True)
        students = students.filter(user_id__in=present_students)
    
    # Pagination
    page, paginator, page_num = paginate_queryset(request, students, per_page=20)
    
    context = {
        'page_obj': page,
        'paginator': paginator,
        'page_num': page_num,
        'search_term': search_term,
        'status': status,
        'my_class': my_class,
    }
    
    return render(request, 'class_teacher/students_list.html', context)


@login_required
@require_teacher_role('class_teacher')
def student_detail(request, student_id):
    """View student profile and performance"""
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Verify student is in class teacher's class
    my_class = ClassGrade.objects.filter(
        school=school,
        class_teacher=staff_profile
    ).first()
    
    student = get_object_or_404(
        Student,
        id=student_id,
        school=school,
        class_grade=my_class
    )
    
    # Get student's grades
    grades = Grade.objects.filter(
        student=student,
        school=school
    ).select_related('subject', 'recorded_by__user').order_by('-created_at')
    
    # Get student's attendance
    attendance = StudentAttendance.objects.filter(
        student=student,
        school=school
    ).order_by('-date')[:10]
    
    # Calculate statistics
    total_grades = grades.count()
    avg_score = grades.filter(
        grade_point__isnull=False
    ).aggregate(avg=Avg('grade_point'))['avg'] or 0
    avg_score = round(avg_score, 1)
    
    total_attendance = attendance.count()
    present_count = attendance.filter(status='present').count()
    attendance_rate = (present_count / total_attendance * 100) if total_attendance > 0 else 0
    attendance_rate = round(attendance_rate, 1)
    
    context = {
        'student': student,
        'my_class': my_class,
        'grades': grades,
        'attendance': attendance,
        'total_grades': total_grades,
        'avg_score': avg_score,
        'attendance_rate': attendance_rate,
    }
    
    return render(request, 'class_teacher/student_detail.html', context)


@login_required
@require_teacher_role('class_teacher')
def grades_management(request):
    """Manage class grades"""
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get user's class
    my_class = ClassGrade.objects.filter(
        school=school,
        class_teacher=staff_profile
    ).first()
    
    if not my_class:
        return render(request, 'class_teacher/grades_management.html', {'no_class': True})
    
    # Get students
    students = Student.objects.filter(
        school=school,
        class_grade=my_class,
        is_active=True
    ).select_related('user').order_by('user__last_name', 'user__first_name')
    
    # Get subjects for class
    subjects = Subject.objects.filter(
        school=school,
        classgrade=my_class
    )
    
    # Get grades
    grades = Grade.objects.filter(
        student__in=students,
        school=school
    ).select_related('student', 'subject')
    
    # Subject filter
    subject_filter = request.GET.get('subject', '')
    if subject_filter:
        grades = grades.filter(subject_id=subject_filter)
    
    # Pagination
    page, paginator, page_num = paginate_queryset(request, grades, per_page=20)
    
    context = {
        'page_obj': page,
        'paginator': paginator,
        'page_num': page_num,
        'my_class': my_class,
        'students': students,
        'subjects': subjects,
        'subject_filter': subject_filter,
    }
    
    return render(request, 'class_teacher/grades_management.html', context)


@login_required
@require_teacher_role('class_teacher')
def attendance_management(request):
    """Manage class attendance"""
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get user's class
    my_class = ClassGrade.objects.filter(
        school=school,
        class_teacher=staff_profile
    ).first()
    
    if not my_class:
        return render(request, 'class_teacher/attendance_management.html', {'no_class': True})
    
    # Get students
    students = Student.objects.filter(
        school=school,
        class_grade=my_class,
        is_active=True
    ).select_related('user').order_by('user__last_name', 'user__first_name')
    
    # Get attendance records
    attendance = StudentAttendance.objects.filter(
        student__in=students,
        school=school
    ).select_related('student').order_by('-date')
    
    # Date filter
    date_filter = request.GET.get('date', '')
    if date_filter:
        attendance = attendance.filter(date=date_filter)
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        attendance = attendance.filter(status=status_filter)
    
    # Pagination
    page, paginator, page_num = paginate_queryset(request, attendance, per_page=20)
    
    context = {
        'page_obj': page,
        'paginator': paginator,
        'page_num': page_num,
        'my_class': my_class,
        'students': students,
        'date_filter': date_filter,
        'status_filter': status_filter,
    }
    
    return render(request, 'class_teacher/attendance_management.html', context)


@login_required
@require_teacher_role('class_teacher')
def class_performance(request):
    """Class performance report"""
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get user's class
    my_class = ClassGrade.objects.filter(
        school=school,
        class_teacher=staff_profile
    ).first()
    
    if not my_class:
        return render(request, 'class_teacher/class_performance.html', {'no_class': True})
    
    # Get students
    students = Student.objects.filter(
        school=school,
        class_grade=my_class,
        is_active=True
    ).select_related('user')
    
    # Subject performance
    subjects = Subject.objects.filter(school=school, classgrade=my_class)
    
    subject_performance = []
    for subject in subjects:
        avg_score = Grade.objects.filter(
            student__in=students,
            subject=subject,
            school=school,
            grade_point__isnull=False
        ).aggregate(avg=Avg('grade_point'))['avg'] or 0
        
        grades_count = Grade.objects.filter(
            student__in=students,
            subject=subject,
            school=school
        ).count()
        
        subject_performance.append({
            'subject': subject,
            'avg_score': round(avg_score, 1),
            'grades_count': grades_count,
        })
    
    # Overall class statistics
    total_grades = Grade.objects.filter(
        student__in=students,
        school=school
    ).count()
    
    overall_avg = Grade.objects.filter(
        student__in=students,
        school=school,
        grade_point__isnull=False
    ).aggregate(avg=Avg('grade_point'))['avg'] or 0
    overall_avg = round(overall_avg, 1)
    
    # Attendance summary
    today = timezone.now().date()
    attendance_marked_today = StudentAttendance.objects.filter(
        student__in=students,
        date=today,
        school=school
    ).exists()
    
    context = {
        'my_class': my_class,
        'subject_performance': subject_performance,
        'total_grades': total_grades,
        'overall_avg': overall_avg,
        'attendance_marked_today': attendance_marked_today,
        'total_students': students.count(),
    }
    
    return render(request, 'class_teacher/class_performance.html', context)


@login_required
@require_teacher_role('class_teacher')
def parent_communications(request):
    """View parent communications"""
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get user's class
    my_class = ClassGrade.objects.filter(
        school=school,
        class_teacher=staff_profile
    ).first()
    
    if not my_class:
        return render(request, 'class_teacher/parent_communications.html', {'no_class': True})
    
    # Get students in class
    students = Student.objects.filter(
        school=school,
        class_grade=my_class,
        is_active=True
    ).select_related('user')
    
    # Get parents of students
    parent_ids = CustomUser.objects.filter(
        role='parent'
    ).values_list('id', flat=True)
    
    # Get messages
    messages_list = Message.objects.filter(
        Q(sender_id__in=parent_ids, receiver=staff_profile.user) |
        Q(sender=staff_profile.user, receiver_id__in=parent_ids)
    ).select_related('sender', 'receiver').order_by('-created_at')
    
    # Search filter
    search_term = request.GET.get('search', '')
    if search_term:
        messages_list = messages_list.filter(
            Q(content__icontains=search_term) |
            Q(subject__icontains=search_term)
        )
    
    # Pagination
    page, paginator, page_num = paginate_queryset(request, messages_list, per_page=15)
    
    context = {
        'page_obj': page,
        'paginator': paginator,
        'page_num': page_num,
        'my_class': my_class,
        'search_term': search_term,
    }
    
    return render(request, 'class_teacher/parent_communications.html', context)
