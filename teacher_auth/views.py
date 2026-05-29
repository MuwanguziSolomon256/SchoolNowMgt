from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib import messages
from .forms import TeacherLoginForm, TeacherRegistrationForm
from SchoolNowMgt.models import (
    StaffProfile, Timetable, Student, ClassGrade,
    StudentAttendance, RetentionAlert, Grade
)


def teacher_register(request):
    """
    Teacher registration view.
    Creates a new teacher account and associated staff profile.
    """
    # Redirect if already logged in as teacher
    if request.user.is_authenticated and request.user.role == 'teacher':
        return redirect('teacher:dashboard')

    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(
                    request,
                    'Registration successful! You can now log in with your email and password.'
                )
                return redirect('teacher:login')
            except Exception as e:
                messages.error(
                    request,
                    f'Registration failed: {str(e)}'
                )
    else:
        form = TeacherRegistrationForm()

    context = {'form': form}
    return render(request, 'teacher/register.html', context)


def teacher_login(request):
    """
    Teacher login view.
    """
    # Redirect if already logged in as teacher
    if request.user.is_authenticated and request.user.role == 'teacher':
        return redirect('teacher:dashboard')

    if request.method == 'POST':
        form = TeacherLoginForm(request=request, data=request.POST)
        if form.is_valid():
            login(request, form.authenticated_user)

            # Safe redirect logic
            next_url = request.GET.get('next', '')
            if (next_url.startswith('/') and 
                not next_url.startswith('//') and 
                ' ' not in next_url):
                return redirect(next_url)
            else:
                return redirect('teacher:dashboard')
    else:
        form = TeacherLoginForm()

    context = {'form': form}
    return render(request, 'teacher/login.html', context)


@login_required(login_url='teacher:login')
@require_POST
def teacher_logout(request):
    """
    Teacher logout view. POST only.
    """
    logout(request)
    return redirect('teacher:login')


@login_required(login_url='teacher:login')
def teacher_dashboard(request):
    """
    Teacher dashboard view.
    
    Displays:
    - Welcome banner (first login only)
    - Today's schedule
    - My students and classes
    - Attendance overview (my classes)
    - At-risk students (my classes)
    - Recent grades entered by this teacher
    """
    # Verify logged-in user is a teacher
    if request.user.role != 'teacher':
        return redirect('teacher:login')
    
    # Fetch StaffProfile or redirect to profile setup
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    # Get today's date
    today = timezone.localtime()
    current_time = timezone.now()
    
    # Determine first login (banner display logic)
    is_first_login = (
        request.user.last_login is None or 
        request.user.date_joined.date() == today.date()
    )
    
    # Convert today to lowercase day name (e.g., "monday")
    day_of_week = today.strftime('%A').lower()
    
    # ===== TODAY'S SCHEDULE =====
    todays_classes = Timetable.objects.filter(
        teacher=staff,
        day_of_week=day_of_week
    ).select_related('subject', 'class_grade').order_by('start_time')
    
    # Get current lesson (first class today)
    current_lesson = todays_classes.first()
    
    # ===== MY STUDENTS =====
    my_student_count = Student.objects.filter(
        class_grade__class_teacher=staff,
        status='active'
    ).count()
    
    my_students = Student.objects.filter(
        class_grade__class_teacher=staff,
        status='active'
    )[:4]
    
    my_classes = ClassGrade.objects.filter(
        class_teacher=staff
    ).annotate(
        student_count=Count('students', filter=Q(students__status='active'))
    )
    
    # ===== ATTENDANCE — MY CLASSES TODAY =====
    attendance_marked_today = StudentAttendance.objects.filter(
        student__class_grade__class_teacher=staff,
        date=today.date()
    ).exists()
    
    present_today = StudentAttendance.objects.filter(
        student__class_grade__class_teacher=staff,
        date=today.date(),
        status='present'
    ).count()
    
    absent_today = StudentAttendance.objects.filter(
        student__class_grade__class_teacher=staff,
        date=today.date(),
        status='absent'
    ).count()
    
    # ===== AT-RISK STUDENTS (MY CLASSES ONLY) =====
    at_risk_alerts = RetentionAlert.objects.filter(
        student__class_grade__class_teacher=staff,
        resolved=False
    ).select_related('student').order_by('-created_at')[:5]
    
    at_risk_count = RetentionAlert.objects.filter(
        student__class_grade__class_teacher=staff,
        resolved=False
    ).count()
    
    # ===== RECENT GRADES (ENTERED BY THIS TEACHER) =====
    recent_grades = Grade.objects.filter(
        recorded_by=request.user
    ).select_related('student', 'subject').order_by('-created_at')[:5]
    
    # ===== TASK PRIORITY WIDGET =====
    priority_tasks = [
        {'title': 'Mark Attendance', 'subject': 'Daily Task', 'due_date': 'Today', 'priority': 'high', 'completed': attendance_marked_today},
        {'title': 'Input Grades', 'subject': 'Assessment', 'due_date': 'Tomorrow', 'priority': 'high', 'completed': False},
        {'title': 'Review At-Risk Students', 'subject': 'Monitoring', 'due_date': 'This Week', 'priority': 'medium', 'completed': False},
    ]
    
    # ===== RECENT ACTIVITY =====
    recent_activity = [
        {'title': 'Student submitted assignment', 'type': 'submission', 'time_ago': '2 hours ago'},
        {'title': 'Grade entered for Math test', 'type': 'grade', 'time_ago': '4 hours ago'},
        {'title': 'Alert: Low attendance in Class 2B', 'type': 'alert', 'time_ago': '1 day ago'},
    ]
    
    # ===== PERFORMANCE STATS =====
    performance_stats = [
        {'height': 60},
        {'height': 75},
        {'height': 85},
        {'height': 95},
        {'height': 70},
    ]
    performance_metric = "18% average"
    
    # Build context
    context = {
        'today': today,
        'current_time': current_time,
        'is_first_login': is_first_login,
        'employee_id': staff.employee_id,
        'todays_classes': todays_classes,
        'current_lesson': current_lesson if current_lesson else {'subject': 'No Lesson', 'description': 'No active lesson at this time'},
        'my_student_count': my_student_count,
        'students': my_students,
        'my_classes': my_classes,
        'attendance_marked_today': attendance_marked_today,
        'present_today': present_today,
        'absent_today': absent_today,
        'at_risk_alerts': at_risk_alerts,
        'at_risk_count': at_risk_count,
        'recent_grades': recent_grades,
        'priority_tasks': priority_tasks,
        'recent_activity': recent_activity,
        'performance_stats': performance_stats,
        'performance_metric': performance_metric,
    }
    
    return render(request, 'teacher/dashboard_new.html', context)
