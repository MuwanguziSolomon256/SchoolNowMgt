from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Avg, Q, Sum

from .models import (
    Student, StaffProfile, StudentAttendance, StaffAttendance,
    RetentionAlert, SMSLog, Enquiry, FeePayment, Grade, ClassGrade
)


@login_required
def dashboard(request):
    """
    Authenticated dashboard view for school administrators.
    
    Computes 22 context variables covering:
    - Student enrollment and demographics
    - Attendance tracking (students and staff)
    - Retention alerts for at-risk students
    - Fee collection and payments
    - SMS delivery status
    - Academic performance metrics
    - New enquiries from prospective parents
    
    All queries are database-optimized: no N+1 queries, use of
    select_related() for ForeignKey relationships.
    
    Renders: SchoolNowMgt/dashboard.html
    """
    
    # Current date for filtering
    today = timezone.localdate()
    
    # ─────────────────────────────────────────────────────────────
    # STUDENTS SECTION
    # ─────────────────────────────────────────────────────────────
    
    # Total active students
    total_students = Student.objects.filter(status='active').count()
    
    # Students per class (annotated query)
    students_by_class = ClassGrade.objects.annotate(
        student_count=Count('students', filter=Q(students__status='active'))
    ).order_by('level')
    
    # New enrolments this month
    new_students_this_month = Student.objects.filter(
        date_admitted__year=today.year,
        date_admitted__month=today.month
    ).count()
    
    # ─────────────────────────────────────────────────────────────
    # ATTENDANCE TODAY SECTION
    # ─────────────────────────────────────────────────────────────
    
    # Base queryset for today's student attendance
    student_attendance_today = StudentAttendance.objects.filter(date=today)
    
    # Student attendance counts
    students_present_today = student_attendance_today.filter(status='present').count()
    students_absent_today = student_attendance_today.filter(status='absent').count()
    students_late_today = student_attendance_today.filter(status='late').count()
    
    # Has attendance been marked today?
    attendance_marked_today = student_attendance_today.exists()
    
    # Staff attendance counts
    staff_present_today = StaffAttendance.objects.filter(
        date=today, 
        status='present'
    ).count()
    
    staff_absent_today = StaffAttendance.objects.filter(
        date=today, 
        status='absent'
    ).count()
    
    total_staff = StaffProfile.objects.filter(
        user__is_active=True
    ).count()
    
    # ─────────────────────────────────────────────────────────────
    # RETENTION ALERTS SECTION
    # ─────────────────────────────────────────────────────────────
    
    # Top 10 most recent unresolved alerts
    open_alerts = RetentionAlert.objects.filter(resolved=False)\
        .select_related('student')\
        .order_by('-created_at')[:10]
    
    # Count of all unresolved alerts
    open_alerts_count = RetentionAlert.objects.filter(resolved=False).count()
    
    # Count of high-severity unresolved alerts
    high_severity_count = RetentionAlert.objects.filter(
        resolved=False, 
        severity='high'
    ).count()
    
    # ─────────────────────────────────────────────────────────────
    # ENQUIRIES SECTION
    # ─────────────────────────────────────────────────────────────
    
    # Count of new (uncontacted) enquiries
    new_enquiries_count = Enquiry.objects.filter(status='new').count()
    
    # Count of enquiries submitted this month
    enquiries_this_month = Enquiry.objects.filter(
        enquiry_date__year=today.year,
        enquiry_date__month=today.month
    ).count()
    
    # 5 most recent new enquiries
    recent_enquiries = Enquiry.objects.filter(status='new')\
        .order_by('-enquiry_date')[:5]
    
    # ─────────────────────────────────────────────────────────────
    # FINANCE SECTION
    # ─────────────────────────────────────────────────────────────
    
    # Total fees collected this month
    fees_collected_this_month = FeePayment.objects.filter(
        payment_date__year=today.year,
        payment_date__month=today.month
    ).aggregate(total=Sum('amount_paid'))['total'] or 0
    
    # 5 most recent fee payments
    recent_payments = FeePayment.objects.select_related('student')\
        .order_by('-payment_date')[:5]
    
    # ─────────────────────────────────────────────────────────────
    # SMS SECTION
    # ─────────────────────────────────────────────────────────────
    
    # Count of pending SMS messages
    pending_sms_count = SMSLog.objects.filter(status='pending').count()
    
    # Count of failed SMS messages
    failed_sms_count = SMSLog.objects.filter(status='failed').count()
    
    # ─────────────────────────────────────────────────────────────
    # ACADEMIC SECTION
    # ─────────────────────────────────────────────────────────────
    
    current_year = str(today.year)
    
    # Average score for current academic year
    average_score_this_year = Grade.objects.filter(
        academic_year=current_year
    ).aggregate(avg=Avg('score'))['avg']
    
    # Format: round to 1 decimal place or display em-dash
    if average_score_this_year is not None:
        average_score_this_year = round(average_score_this_year, 1)
    else:
        average_score_this_year = '—'
    
    # ─────────────────────────────────────────────────────────────
    # BUILD CONTEXT DICTIONARY
    # ─────────────────────────────────────────────────────────────
    
    context = {
        # Metadata
        'today': today,
        'user': request.user,
        
        # Students
        'total_students': total_students,
        'students_by_class': students_by_class,
        'new_students_this_month': new_students_this_month,
        
        # Attendance
        'students_present_today': students_present_today,
        'students_absent_today': students_absent_today,
        'students_late_today': students_late_today,
        'attendance_marked_today': attendance_marked_today,
        'staff_present_today': staff_present_today,
        'staff_absent_today': staff_absent_today,
        'total_staff': total_staff,
        
        # Retention
        'open_alerts': open_alerts,
        'open_alerts_count': open_alerts_count,
        'high_severity_count': high_severity_count,
        
        # Enquiries
        'new_enquiries_count': new_enquiries_count,
        'enquiries_this_month': enquiries_this_month,
        'recent_enquiries': recent_enquiries,
        
        # Finance
        'fees_collected_this_month': fees_collected_this_month,
        'recent_payments': recent_payments,
        
        # SMS
        'pending_sms_count': pending_sms_count,
        'failed_sms_count': failed_sms_count,
        
        # Academic
        'average_score_this_year': average_score_this_year,
    }
    
    return render(request, 'SchoolNowMgt/dashboard.html', context)
