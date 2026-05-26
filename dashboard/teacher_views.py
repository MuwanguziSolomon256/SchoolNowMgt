from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q
from SchoolNowMgt.models import (
    StaffProfile, Timetable, Student, ClassGrade,
    StudentAttendance, RetentionAlert, Grade
)


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
    today = timezone.localdate()
    
    # Determine first login (banner display logic)
    is_first_login = (
        request.user.last_login is None or 
        request.user.date_joined.date() == today
    )
    
    # Convert today to lowercase day name (e.g., "monday")
    day_of_week = today.strftime('%A').lower()
    
    # ===== TODAY'S SCHEDULE =====
    todays_classes = Timetable.objects.filter(
        teacher=staff,
        day_of_week=day_of_week
    ).select_related('subject', 'class_grade').order_by('start_time')
    
    # ===== MY STUDENTS =====
    my_student_count = Student.objects.filter(
        class_grade__class_teacher=staff,
        status='active'
    ).count()
    
    my_classes = ClassGrade.objects.filter(
        class_teacher=staff
    ).annotate(
        student_count=Count('students', filter=Q(students__status='active'))
    )
    
    # ===== ATTENDANCE — MY CLASSES TODAY =====
    attendance_marked_today = StudentAttendance.objects.filter(
        student__class_grade__class_teacher=staff,
        date=today
    ).exists()
    
    present_today = StudentAttendance.objects.filter(
        student__class_grade__class_teacher=staff,
        date=today,
        status='present'
    ).count()
    
    absent_today = StudentAttendance.objects.filter(
        student__class_grade__class_teacher=staff,
        date=today,
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
    
    # Build context
    context = {
        'today': today,
        'is_first_login': is_first_login,
        'employee_id': staff.employee_id,
        'todays_classes': todays_classes,
        'my_student_count': my_student_count,
        'my_classes': my_classes,
        'attendance_marked_today': attendance_marked_today,
        'present_today': present_today,
        'absent_today': absent_today,
        'at_risk_alerts': at_risk_alerts,
        'at_risk_count': at_risk_count,
        'recent_grades': recent_grades,
    }
    
    return render(request, 'teacher/dashboard.html', context)
