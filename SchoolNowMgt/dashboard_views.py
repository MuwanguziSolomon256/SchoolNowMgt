from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Avg, Q, Sum
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import uuid
import csv
import io
from datetime import datetime, timedelta

from .models import (
    Student, StaffProfile, StudentAttendance, StaffAttendance,
    RetentionAlert, SMSLog, Enquiry, FeePayment, Grade, ClassGrade,
    CustomUser, Message, MessageRecipient, MessageTemplate, School,
    ActivityLog, Event, AdminProfile, StudentAssignment, Subject, Assignment,
    StaffBill
)
from .forms import (
    StaffOnboardingForm, BulkStaffUploadForm,
    StudentOnboardingForm, BulkStudentUploadForm,
    AdminMessageForm, StaffPasswordResetForm, ParentMessageForm,
    EventForm, AdminProfileForm, ProfilePictureForm
)
from .utils import (
    generate_temp_password, parse_csv_upload, resolve_message_recipients,
    create_message_recipients, replace_message_placeholders, generate_employee_id,
    get_parent_messageable_recipients, get_parent_unread_count, get_parent_messages
)


# Custom login required that redirects to unified login portal
def unified_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('auth:unified_login')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────────────────────
# PAGINATION & FILTERING HELPERS (Phase 1.5)
# ─────────────────────────────────────────────────────────────

def paginate_queryset(request, queryset, per_page=20):
    """
    Paginates a queryset based on page number in request.
    Returns: (paginated_items, paginator, page_num)
    """
    paginator = Paginator(queryset, per_page)
    page_num = request.GET.get('page', 1)
    
    try:
        page_num_int = int(page_num)
    except (ValueError, TypeError):
        page_num_int = 1
    
    try:
        items = paginator.page(page_num_int)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        # Handle empty page - return last page or first page if totally empty
        if paginator.num_pages > 0:
            items = paginator.page(paginator.num_pages)
        else:
            items = paginator.page(1)
    
    return items, paginator, page_num_int


def export_csv(filename, headers, rows):
    """
    Creates CSV response with given data.
    Returns: HttpResponse with CSV content
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    
    return response


# ─────────────────────────────────────────────────────────────
# CSV EXPORT ENDPOINTS (Phase 1.5)
# ─────────────────────────────────────────────────────────────

@unified_login_required
def export_students_csv(request):
    """Export Students data as CSV"""
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('auth:unified_login')
    
    user_school = request.user.school
    
    # Get filter parameters
    class_filter = request.GET.get('class', '')
    status_filter = request.GET.get('status', 'active')
    
    # Build query
    students = Student.objects.filter(
        class_grade__school=user_school,
        status=status_filter if status_filter else 'active'
    ).select_related('class_grade', 'parent_user')
    
    if class_filter:
        students = students.filter(class_grade__id=class_filter)
    
    # Prepare CSV data
    headers = ['Admission #', 'Student Name', 'Class', 'Date Admitted', 'Status', 'Parent/Guardian']
    rows = []
    
    for student in students:
        rows.append([
            student.admission_number or '—',
            student.full_name,
            student.class_grade.name if student.class_grade else '—',
            student.date_admitted.strftime('%d/%m/%Y') if student.date_admitted else '—',
            student.status.title(),
            student.parent_user.get_full_name() if student.parent_user else student.parent_name or '—'
        ])
    
    filename = f"students_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return export_csv(filename, headers, rows)


@unified_login_required
def export_staff_csv(request):
    """Export Staff data as CSV"""
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('auth:unified_login')
    
    user_school = request.user.school
    
    # Get filter parameters
    position_filter = request.GET.get('position', '')
    
    # Build query
    staff = StaffProfile.objects.filter(
        user__school=user_school,
        date_left__isnull=True
    ).select_related('user')
    
    if position_filter:
        staff = staff.filter(position=position_filter)
    
    # Prepare CSV data
    headers = ['Employee ID', 'Staff Name', 'Position', 'Date Joined', 'Employment Type', 'Email']
    rows = []
    
    for s in staff:
        rows.append([
            s.employee_id or '—',
            s.user.get_full_name(),
            s.position or '—',
            s.date_joined.strftime('%d/%m/%Y') if s.date_joined else '—',
            s.employment_type.title() if s.employment_type else '—',
            s.user.email or '—'
        ])
    
    filename = f"staff_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return export_csv(filename, headers, rows)


@unified_login_required
def export_finance_csv(request):
    """Export Finance data as CSV"""
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('auth:unified_login')
    
    user_school = request.user.school
    today = timezone.localdate()
    
    # Get filter parameters
    class_filter = request.GET.get('class', '')
    month = request.GET.get('month', today.month)
    year = request.GET.get('year', today.year)
    
    # Build query
    transactions = FeePayment.objects.filter(
        student__class_grade__school=user_school,
        payment_date__month=month,
        payment_date__year=year
    ).select_related('student', 'student__class_grade')
    
    if class_filter:
        transactions = transactions.filter(student__class_grade__id=class_filter)
    
    # Prepare CSV data
    headers = ['Date', 'Student', 'Class', 'Amount (UGX)', 'Payment Method', 'Reference']
    rows = []
    total_collected = 0
    
    for transaction in transactions:
        amount = transaction.amount_paid or 0
        total_collected += amount
        rows.append([
            transaction.payment_date.strftime('%d/%m/%Y') if transaction.payment_date else '—',
            transaction.student.user.get_full_name() if transaction.student else '—',
            transaction.student.class_grade.name if transaction.student and transaction.student.class_grade else '—',
            f"{amount:,.0f}",
            transaction.payment_method or '—',
            transaction.reference_number or '—'
        ])
    
    # Add total row
    rows.append(['', '', 'TOTAL', f"{total_collected:,.0f}", '', ''])
    
    filename = f"finance_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return export_csv(filename, headers, rows)


@unified_login_required
def export_reports_csv(request):
    """Export Academic Reports as CSV"""
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('auth:unified_login')
    
    user_school = request.user.school
    today = timezone.localdate()
    current_year = str(today.year)
    
    # Get filter parameter
    class_filter = request.GET.get('class', '')
    
    # Build query for class performance
    class_performance = Grade.objects.filter(
        academic_year=current_year,
        student__class_grade__school=user_school
    ).values('student__class_grade__name').annotate(
        avg_score=Avg('score'),
        student_count=Count('student', distinct=True)
    ).order_by('student__class_grade__name')
    
    if class_filter:
        class_performance = class_performance.filter(student__class_grade__id=class_filter)
    
    # Prepare CSV data
    headers = ['Class', 'Average Score', 'Student Count', 'Grade']
    rows = []
    
    for perf in class_performance:
        avg_score = perf['avg_score'] or 0
        avg_score = round(avg_score, 1)
        
        # Grade mapping
        if avg_score >= 80:
            grade = 'Excellent'
        elif avg_score >= 70:
            grade = 'Good'
        elif avg_score >= 60:
            grade = 'Average'
        else:
            grade = 'Needs Improvement'
        
        rows.append([
            perf['student__class_grade__name'] or '—',
            f"{avg_score}",
            perf['student_count'] or 0,
            grade
        ])
    
    filename = f"reports_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return export_csv(filename, headers, rows)


@unified_login_required
def dashboard(request):
    """
    Authenticated dashboard view for school administrators.
    
    Routes to appropriate dashboard based on user role:
    - admin role: Admin dashboard with school management data
    - teacher role: Teacher dashboard with class/attendance data
    - parent role: Parent dashboard with child progress
    - non_teaching_staff role: Support staff dashboard
    
    Access Control: Admins only can access this route
    
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
    
    Multi-school isolation: All queries filtered by request.user.school
    to ensure admin only sees their school's data.
    
    Renders: SchoolNowMgt/admin_dashboard.html (for admins only)
    """
    
    # Role-based access control: Only admins can access this view
    if request.user.role != 'admin' and not request.user.is_superuser:
        # Redirect non-admins to their appropriate dashboard
        if request.user.role == 'teacher':
            return redirect('teacher:dashboard')
        elif request.user.role == 'parent':
            return redirect('SchoolNowMgt:parent_dashboard')
        elif request.user.role == 'non_teaching_staff':
            return redirect('SchoolNowMgt:support_staff_dashboard')
        else:
            return redirect('auth:unified_login')
    
    # Current date for filtering
    today = timezone.localdate()
    
    # Get user's school for data isolation
    user_school = request.user.school
    
    # ─────────────────────────────────────────────────────────────
    # STUDENTS SECTION
    # ─────────────────────────────────────────────────────────────
    
    # Total active students (school-filtered)
    total_students = Student.objects.filter(status='active', class_grade__school=user_school).count()
    
    # Students per class (annotated query, school-filtered)
    students_by_class = ClassGrade.objects.filter(school=user_school).annotate(
        student_count=Count('students', filter=Q(students__status='active'))
    ).order_by('level')
    
    # New enrolments this month (school-filtered)
    new_students_this_month = Student.objects.filter(
        date_admitted__year=today.year,
        date_admitted__month=today.month,
        class_grade__school=user_school
    ).count()
    
    # ─────────────────────────────────────────────────────────────
    # ATTENDANCE TODAY SECTION
    # ─────────────────────────────────────────────────────────────
    
    # Base queryset for today's student attendance (school-filtered)
    student_attendance_today = StudentAttendance.objects.filter(
        date=today,
        student__class_grade__school=user_school
    )
    
    # Student attendance counts (school-filtered)
    students_present_today = student_attendance_today.filter(status='present').count()
    students_absent_today = student_attendance_today.filter(status='absent').count()
    students_late_today = student_attendance_today.filter(status='late').count()
    
    # Has attendance been marked today?
    attendance_marked_today = student_attendance_today.exists()
    
    # Staff attendance counts (school-filtered)
    staff_present_today = StaffAttendance.objects.filter(
        date=today, 
        status='present',
        staff__user__school=user_school
    ).count()
    
    staff_absent_today = StaffAttendance.objects.filter(
        date=today, 
        status='absent',
        staff__user__school=user_school
    ).count()
    
    total_staff = StaffProfile.objects.filter(
        user__is_active=True,
        user__school=user_school
    ).count()
    
    # ─────────────────────────────────────────────────────────────
    # RETENTION ALERTS SECTION
    # ─────────────────────────────────────────────────────────────
    
    # Top 10 most recent unresolved alerts (school-filtered)
    open_alerts = RetentionAlert.objects.filter(
        resolved=False,
        student__class_grade__school=user_school
    ).select_related('student').order_by('-created_at')[:10]
    
    # Count of all unresolved alerts (school-filtered)
    open_alerts_count = RetentionAlert.objects.filter(
        resolved=False,
        student__class_grade__school=user_school
    ).count()
    
    # Count of high-severity unresolved alerts (school-filtered)
    high_severity_count = RetentionAlert.objects.filter(
        resolved=False, 
        severity='high',
        student__class_grade__school=user_school
    ).count()
    
    # ─────────────────────────────────────────────────────────────
    # ENQUIRIES SECTION
    # ─────────────────────────────────────────────────────────────
    
    # Count of new (uncontacted) enquiries (school-filtered)
    new_enquiries_count = Enquiry.objects.filter(
        status='new',
        school=user_school
    ).count()
    
    # Count of enquiries submitted this month (school-filtered)
    enquiries_this_month = Enquiry.objects.filter(
        enquiry_date__year=today.year,
        enquiry_date__month=today.month,
        school=user_school
    ).count()
    
    # 5 most recent new enquiries (school-filtered)
    recent_enquiries = Enquiry.objects.filter(
        status='new',
        school=user_school
    ).order_by('-enquiry_date')[:5]
    
    # ─────────────────────────────────────────────────────────────
    # FINANCE SECTION
    # ─────────────────────────────────────────────────────────────
    
    # Total fees collected this month (school-filtered)
    fees_collected_this_month = FeePayment.objects.filter(
        payment_date__year=today.year,
        payment_date__month=today.month,
        student__class_grade__school=user_school
    ).aggregate(total=Sum('amount_paid'))['total'] or 0
    
    # 5 most recent fee payments (school-filtered)
    recent_payments = FeePayment.objects.filter(
        student__class_grade__school=user_school
    ).select_related('student').order_by('-payment_date')[:5]
    
    # ─────────────────────────────────────────────────────────────
    # SMS SECTION
    # ─────────────────────────────────────────────────────────────
    
    # Count of pending SMS messages (school-filtered)
    # SMSLog doesn't have direct school field, so filter through relationships
    pending_sms_count = SMSLog.objects.filter(
        status='pending'
    ).filter(
        Q(related_student__class_grade__school=user_school) |
        Q(related_staff__user__school=user_school) |
        Q(related_alert__student__class_grade__school=user_school)
    ).count()
    
    # Count of failed SMS messages (school-filtered)
    failed_sms_count = SMSLog.objects.filter(
        status='failed'
    ).filter(
        Q(related_student__class_grade__school=user_school) |
        Q(related_staff__user__school=user_school) |
        Q(related_alert__student__class_grade__school=user_school)
    ).count()
    
    # ─────────────────────────────────────────────────────────────
    # ACADEMIC SECTION
    # ─────────────────────────────────────────────────────────────
    
    current_year = str(today.year)
    
    # Average score for current academic year (school-filtered)
    average_score_this_year = Grade.objects.filter(
        academic_year=current_year,
        student__class_grade__school=user_school
    ).aggregate(avg=Avg('score'))['avg']
    
    # Format: round to 1 decimal place or display em-dash
    if average_score_this_year is not None:
        average_score_this_year = round(average_score_this_year, 1)
    else:
        average_score_this_year = '—'
    
    # ─────────────────────────────────────────────────────────────
    # BUILD CONTEXT DICTIONARY
    # ─────────────────────────────────────────────────────────────
    
    # Compute finance metrics for admin dashboard
    total_revenue = fees_collected_this_month
    collected_fees = fees_collected_this_month
    # Calculate outstanding fees by subtracting collected from total expected
    outstanding_fees = 50000  # Mock value - in production this would be calculated
    
    # Calculate fee collection percentage (percentage of target met)
    fee_collection_percentage = 85  # Default target: 85%
    
    # Create mock transaction data for admin dashboard
    recent_transactions = []
    for payment in recent_payments[:5]:
        recent_transactions.append({
            'name': payment.student.user.get_full_name(),
            'initials': ''.join([part[0].upper() for part in payment.student.user.get_full_name().split()]),
            'id': payment.id,
            'description': f'Fee Payment - {payment.term}',
            'date': payment.payment_date,
            'amount': payment.amount_paid,
            'status': 'Completed'
        })
    
    context = {
        # Metadata
        'today': today,
        'user': request.user,
        'school': getattr(request.user, 'school', None),
        
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
        'total_revenue': total_revenue,
        'collected_fees': collected_fees,
        'outstanding_fees': outstanding_fees,
        'fee_collection_percentage': fee_collection_percentage,
        'recent_transactions': recent_transactions,
        
        # SMS
        'pending_sms_count': pending_sms_count,
        'failed_sms_count': failed_sms_count,
        
        # Academic
        'average_score_this_year': average_score_this_year,
        
        # Admin Profile & Events
        'admin_profile': AdminProfile.objects.filter(user=request.user).first() or None,
        'upcoming_events': Event.objects.filter(
            school=user_school,
            start_date__gte=today
        ).order_by('start_date')[:5],
        'total_events_this_term': Event.objects.filter(school=user_school).count(),
        
        # Admin Onboarding & Messaging
        'classes': ClassGrade.objects.filter(school=user_school),
        'users': CustomUser.objects.filter(school=user_school, is_active=True),
    }
    
    # Route based on user role
    if request.user.role == 'admin':
        return render(request, 'SchoolNowMgt/admin_dashboard.html', context)
    elif request.user.role == 'teacher':
        return render(request, 'SchoolNowMgt/teacher_dashboard_new.html', context)
    elif request.user.role == 'parent':
        return render(request, 'SchoolNowMgt/parent_dashboard.html', context)
    elif request.user.role == 'non_teaching_staff':
        return render(request, 'SchoolNowMgt/support_staff_dashboard.html', context)
    else:
        # Fallback to admin dashboard for unknown roles
        return render(request, 'SchoolNowMgt/admin_dashboard.html', context)


@unified_login_required
def parent_dashboard(request):
    """
    Parent portal dashboard view.
    
    Access Control: Parents only
    
    Shows child's academic progress, attendance, financial status,
    and school calendar events.
    
    Multi-school isolation: Children filtered by parent's school to ensure
    parent only sees their own children within their school context.
    
    Renders: SchoolNowMgt/parent_dashboard.html
    """
    # Role-based access control: Only parents can access this view
    if request.user.role != 'parent':
        # Redirect non-parents to their appropriate dashboard
        if request.user.role == 'admin' or request.user.is_superuser:
            return redirect('SchoolNowMgt:dashboard')
        elif request.user.role == 'teacher':
            return redirect('teacher:dashboard')
        elif request.user.role == 'non_teaching_staff':
            return redirect('SchoolNowMgt:support_staff_dashboard')
        else:
            return redirect('auth:unified_login')
    
    today = timezone.localdate()
    
    # Get user's school for data isolation
    user_school = request.user.school
    
    # Get children associated with this parent (school-filtered)
    children = Student.objects.filter(
        parent_user=request.user,
        status='active',
        class_grade__school=user_school
    ).prefetch_related('grade_set', 'class_grade')
    
    # Get selected child (first child or from session)
    selected_child = children.first()
    
    # Prepare sample data for template (should be calculated from real data)
    gpa = 3.82
    academic_subjects = [
        {'name': 'Mathematics', 'score': 92, 'icon': 'calculate'},
        {'name': 'English', 'score': 88, 'icon': 'article'},
        {'name': 'Science', 'score': 85, 'icon': 'science'},
        {'name': 'History', 'score': 90, 'icon': 'menu_book'},
    ]
    attendance_percentage = 94
    completed_assignments = 18
    total_assignments = 20
    class_rank = 5
    total_students_in_class = 32
    outstanding_balance = 452000  # Currency depends on locale
    days_until_due = 14
    
    # Calendar days for current month
    import calendar as cal_module
    current_month = today.strftime("%B %Y")
    month_calendar = cal_module.monthcalendar(today.year, today.month)
    
    calendar_days = []
    for week in month_calendar:
        for day in week:
            if day == 0:
                continue
            day_date = today.replace(day=day)
            event_type = None
            event_name = None
            if day_date.weekday() == 0:  # Monday
                event_type = 'exam'
                event_name = 'Math Exam'
            elif day_date.day == 15:
                event_type = 'event'
                event_name = 'Sports Day'
            calendar_days.append({
                'date': day,
                'day_of_week': day_date.strftime('%a'),
                'is_today': day_date == today,
                'event': event_name,
                'event_type': event_type,
            })
    
    context = {
        'today': today,
        'user': request.user,
        'school': getattr(request.user, 'school', None),
        'children': children,
        'selected_child': selected_child,
        'gpa': gpa,
        'academic_subjects': academic_subjects,
        'attendance_percentage': attendance_percentage,
        'completed_assignments': completed_assignments,
        'total_assignments': total_assignments,
        'class_rank': class_rank,
        'total_students_in_class': total_students_in_class,
        'outstanding_balance': outstanding_balance,
        'days_until_due': days_until_due,
        'current_month': current_month,
        'calendar_days': calendar_days,
    }
    
    return render(request, 'SchoolNowMgt/parent_dashboard.html', context)


@unified_login_required
def support_staff_dashboard(request):
    """
    Support staff (facilities, maintenance, cleaning) dashboard.
    
    Access Control: Support staff only
    
    Shows pending maintenance tasks, shift status, inventory,
    and daily schedule.
    
    Multi-school isolation: Staff profile and attendance filtered by
    staff member's school to ensure staff only sees their school's data.
    
    Renders: SchoolNowMgt/support_staff_dashboard.html
    """
    # Role-based access control: Only support staff can access this view
    if request.user.role != 'non_teaching_staff':
        # Redirect non-support-staff to their appropriate dashboard
        if request.user.role == 'admin' or request.user.is_superuser:
            return redirect('SchoolNowMgt:dashboard')
        elif request.user.role == 'teacher':
            return redirect('teacher:dashboard')
        elif request.user.role == 'parent':
            return redirect('SchoolNowMgt:parent_dashboard')
        else:
            return redirect('auth:unified_login')
    
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get user's school for data isolation
    user_school = request.user.school
    
    # Get staff profile for logged-in support staff (school-verified via user)
    try:
        staff_profile = StaffProfile.objects.get(
            user=request.user,
            user__school=user_school
        )
    except StaffProfile.DoesNotExist:
        staff_profile = None
    
    # Check if staff is on duty today (school-filtered through staff profile)
    staff_attendance_today = StaffAttendance.objects.filter(
        staff=staff_profile,
        date=today.date(),
        staff__user__school=user_school
    ).first() if staff_profile else None
    
    is_on_duty = staff_attendance_today and staff_attendance_today.status == 'present'
    shift_start_time = staff_attendance_today.clock_in if staff_attendance_today else today
    current_time = timezone.now()
    current_date = today.date()
    
    # Sample maintenance tasks
    pending_tasks = [
        {
            'title': 'Roof Leak Repair',
            'details': 'Building C - Classroom 3C roof leaking',
            'priority': 'high',
            'icon': 'home_repair_service',
        },
        {
            'title': 'HVAC Maintenance',
            'details': 'Air conditioning unit not cooling properly',
            'priority': 'medium',
            'icon': 'air',
        },
        {
            'title': 'Supply Restock',
            'details': 'Office supplies running low',
            'priority': 'low',
            'icon': 'inventory_2',
        },
    ]
    
    # Daily schedule events
    schedule_events = [
        {
            'title': 'Morning Briefing',
            'location': 'Maintenance Office',
            'start_time': today.replace(hour=8, minute=0),
            'end_time': today.replace(hour=8, minute=30),
            'is_current': False,
            'status': 'completed',
        },
        {
            'title': 'Inspection Round - Building A & B',
            'location': 'Campus Grounds',
            'start_time': today.replace(hour=9, minute=0),
            'end_time': today.replace(hour=11, minute=0),
            'is_current': True,
            'status': 'in_progress',
        },
        {
            'title': 'Lunch Break',
            'location': 'Staff Cafeteria',
            'start_time': today.replace(hour=12, minute=0),
            'end_time': today.replace(hour=13, minute=0),
            'is_current': False,
            'status': 'pending',
        },
    ]
    
    # Inventory items
    inventory_items = [
        {
            'name': 'Cleaning Supplies',
            'percentage': 75,
            'status': 'Good',
        },
        {
            'name': 'Light Bulbs',
            'percentage': 45,
            'status': 'Low',
        },
        {
            'name': 'Paint/Coating',
            'percentage': 30,
            'status': 'Critical',
        },
        {
            'name': 'Spare Parts',
            'percentage': 85,
            'status': 'Excellent',
        },
    ]
    
    next_delivery_info = 'Wednesday, 10:00 AM - Office & Cleaning Supplies'
    
    # Get available roles for staff (for potential role switching)
    available_roles = []  # Can be extended if staff has multiple assigned roles
    current_role = request.session.get('current_role', 'Support Staff')
    
    context = {
        'today': today,
        'user': request.user,
        'staff_profile': staff_profile,
        'staff_attendance_today': staff_attendance_today,
        'school': getattr(request.user, 'school', None),
        'is_on_duty': is_on_duty,
        'shift_start_time': shift_start_time,
        'current_time': current_time,
        'current_date': current_date,
        'pending_tasks': pending_tasks,
        'schedule_events': schedule_events,
        'inventory_items': inventory_items,
        'next_delivery_info': next_delivery_info,
        'available_roles': available_roles,
        'current_role': current_role,
        'now': timezone.now(),
    }
    
    return render(request, 'SchoolNowMgt/support_staff_dashboard.html', context)


# ===== SUPPORT STAFF SUB-DASHBOARDS =====

@login_required
def support_staff_messages_dashboard(request):
    """Support Staff Messages Sub-Dashboard"""
    if request.user.role != 'non_teaching_staff':
        messages.error(request, 'Access denied.')
        return redirect('SchoolNowMgt:dashboard')
    
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    today = datetime.now()
    
    # Sample messages data (in production, fetch from Message model)
    messages_list = [
        {
            'id': 1,
            'sender': 'Principal',
            'subject': 'Staff Meeting Reminder',
            'preview': 'Please remember we have a staff meeting...',
            'date': (today - timedelta(hours=2)).strftime('%H:%M'),
            'unread': True,
            'timestamp': today - timedelta(hours=2),
        },
        {
            'id': 2,
            'sender': 'HR Department',
            'subject': 'Leave Request Approved',
            'preview': 'Your leave request for June 20-25 has been...',
            'date': (today - timedelta(days=1)).strftime('%d %b'),
            'unread': False,
            'timestamp': today - timedelta(days=1),
        },
    ]
    
    context = {
        'user': request.user,
        'staff_profile': staff_profile,
        'school': getattr(request.user, 'school', None),
        'messages': messages_list,
        'unread_count': sum(1 for m in messages_list if m['unread']),
    }
    
    return render(request, 'SchoolNowMgt/support_staff_messages_subdashboard.html', context)


@login_required
def support_staff_payments_dashboard(request):
    """Support Staff Payments Sub-Dashboard"""
    if request.user.role != 'non_teaching_staff':
        messages.error(request, 'Access denied.')
        return redirect('SchoolNowMgt:dashboard')
    
    from SchoolNowMgt.models import StaffBill
    
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    today = datetime.now()
    
    # Get latest bill
    latest_bill = StaffBill.objects.filter(staff=staff_profile).order_by('-month').first()
    
    # Sample bill data if none exists
    if not latest_bill:
        outstanding_balance = 0
        salary = staff_profile.salary
        due_date = None
    else:
        outstanding_balance = latest_bill.outstanding_balance()
        salary = latest_bill.salary
        due_date = latest_bill.due_date
    
    # Recent transactions
    recent_transactions = [
        {
            'date': (today - timedelta(days=5)).strftime('%d %b %Y'),
            'description': 'May 2026 Salary',
            'amount': f"₦{salary:,.2f}",
            'status': 'paid',
        },
        {
            'date': (today - timedelta(days=35)).strftime('%d %b %Y'),
            'description': 'April 2026 Salary',
            'amount': f"₦{salary:,.2f}",
            'status': 'paid',
        },
    ]
    
    context = {
        'user': request.user,
        'staff_profile': staff_profile,
        'school': getattr(request.user, 'school', None),
        'outstanding_balance': outstanding_balance,
        'salary': salary,
        'due_date': due_date,
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'SchoolNowMgt/support_staff_payments_subdashboard.html', context)


@login_required
def support_staff_calendar_dashboard(request):
    """Support Staff Calendar Sub-Dashboard"""
    if request.user.role != 'non_teaching_staff':
        messages.error(request, 'Access denied.')
        return redirect('SchoolNowMgt:dashboard')
    
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    today = datetime.now()
    
    # Generate calendar days
    calendar_days = []
    start_date = today - timedelta(days=today.weekday())  # Start of current week
    
    for i in range(7):
        date = start_date + timedelta(days=i)
        calendar_days.append({
            'date': date,
            'day_name': date.strftime('%a'),
            'day_number': date.day,
            'is_today': date.date() == today.date(),
            'events': [],
        })
    
    # Sample events
    events = [
        {
            'title': 'School Holiday - Independence Day',
            'date': today + timedelta(days=2),
            'color': 'primary',
            'type': 'holiday',
        },
        {
            'title': 'Staff Meeting',
            'date': today + timedelta(days=3),
            'color': 'secondary',
            'type': 'meeting',
        },
        {
            'title': 'Maintenance Day',
            'date': today + timedelta(days=5),
            'color': 'tertiary',
            'type': 'maintenance',
        },
    ]
    
    # Add events to calendar days
    for event in events:
        for day in calendar_days:
            if day['date'].date() == event['date'].date():
                day['events'].append(event)
    
    context = {
        'user': request.user,
        'staff_profile': staff_profile,
        'school': getattr(request.user, 'school', None),
        'calendar_days': calendar_days,
        'events': events,
    }
    
    return render(request, 'SchoolNowMgt/support_staff_calendar_subdashboard.html', context)


@login_required
def support_staff_announcements_dashboard(request):
    """Support Staff Announcements Sub-Dashboard"""
    if request.user.role != 'non_teaching_staff':
        messages.error(request, 'Access denied.')
        return redirect('SchoolNowMgt:dashboard')
    
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    today = datetime.now()
    
    # Sample announcements
    announcements = [
        {
            'id': 1,
            'title': 'System Maintenance - June 15',
            'excerpt': 'The school management system will be undergoing maintenance...',
            'content': 'The school management system will be undergoing scheduled maintenance on June 15, 2026 from 10:00 PM to 2:00 AM. This is to improve system performance and security.',
            'date': (today - timedelta(hours=3)).strftime('%H:%M today'),
            'type': 'system',
            'read': False,
        },
        {
            'id': 2,
            'title': 'Updated Leave Policy',
            'excerpt': 'Please review the new leave request guidelines...',
            'content': 'Effective from July 1st, 2026, the leave policy has been updated. All leave requests must now be submitted 2 weeks in advance...',
            'date': (today - timedelta(days=1)).strftime('%d %b'),
            'type': 'finance',
            'read': False,
        },
        {
            'id': 3,
            'title': 'Staff Training Schedule',
            'excerpt': 'Professional development training sessions have been scheduled...',
            'content': 'We are pleased to announce that professional development training will be held during the term holidays. Attendance is optional.',
            'date': (today - timedelta(days=2)).strftime('%d %b'),
            'type': 'event',
            'read': True,
        },
    ]
    
    context = {
        'user': request.user,
        'staff_profile': staff_profile,
        'school': getattr(request.user, 'school', None),
        'announcements': announcements,
        'unread_count': sum(1 for a in announcements if not a['read']),
    }
    
    return render(request, 'SchoolNowMgt/support_staff_announcements_subdashboard.html', context)


# ============================================================================
# ADMIN ONBOARDING & MESSAGING AJAX VIEWS (Phase 4)
# ============================================================================


def admin_required(view_func):
    """Decorator to restrict access to admin users only."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            return JsonResponse({'success': False, 'message': 'Admin access required.'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


@require_POST
@login_required
@admin_required
def onboard_staff_ajax(request):
    """
    AJAX endpoint to create a single staff member (teacher or support staff).
    
    Returns JSON with:
    - success (bool)
    - message (str)
    - data: { temp_password, employee_id, email } if successful
    - errors (list) if validation fails
    """
    form = StaffOnboardingForm(request.POST)
    
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'message': 'Form validation failed',
            'errors': form.errors
        }, status=400)
    
    try:
        with transaction.atomic():
            # Determine role based on is_teacher flag
            role = 'teacher' if form.cleaned_data['is_teacher'] else 'non_teaching_staff'
            
            # Create CustomUser
            temp_password = generate_temp_password()
            user = CustomUser.objects.create_user(
                username=form.cleaned_data['email'].lower(),
                email=form.cleaned_data['email'].lower(),
                password=temp_password,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                role=role,
                school=request.user.school,
                is_active=True
            )
            
            # Generate unique employee ID
            employee_id = generate_employee_id(request.user.school)
            
            # Create StaffProfile
            staff_profile = StaffProfile.objects.create(
                user=user,
                employee_id=employee_id,
                position=form.cleaned_data['position'],
                date_joined=form.cleaned_data['date_joined'],
                is_full_time=True,
                salary=0
            )
            
            # Log activity
            if hasattr(request.user, 'staffprofile'):
                ActivityLog.objects.create(
                    teacher=request.user.staffprofile,
                    activity_type='staff_created',
                    description=f"Created {role} {user.get_full_name()} (ID: {employee_id})",
                    icon_name='person_add',
                    severity='info'
                )
            
            return JsonResponse({
                'success': True,
                'message': f'Staff member {user.get_full_name()} created successfully.',
                'data': {
                    'temp_password': temp_password,
                    'employee_id': employee_id,
                    'email': user.email,
                    'full_name': user.get_full_name()
                }
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating staff: {str(e)}'
        }, status=500)


@require_POST
@login_required
@admin_required
def bulk_onboard_staff_ajax(request):
    """
    AJAX endpoint to bulk create staff members from CSV upload.
    
    Expected CSV columns: first_name, last_name, email, position, date_joined, is_teacher
    
    Returns JSON with:
    - success (bool)
    - message (str)
    - data: { created_count, failed_count, staff_list, errors } if successful
    - errors (list) if file validation fails
    """
    form = BulkStaffUploadForm(request.POST, request.FILES)
    
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'message': 'Form validation failed',
            'errors': form.errors
        }, status=400)
    
    file = request.FILES['csv_file']
    required_cols = {'first_name', 'last_name', 'email', 'position', 'date_joined'}
    
    success, rows, parse_errors = parse_csv_upload(file, required_cols)
    if not success:
        return JsonResponse({
            'success': False,
            'message': 'CSV file parsing failed',
            'errors': parse_errors
        }, status=400)
    
    created_staff = []
    errors = []
    
    try:
        with transaction.atomic():
            for row_num, row in rows:
                try:
                    email = row['email'].lower().strip()
                    
                    # Check if email already exists
                    if CustomUser.objects.filter(email=email).exists():
                        errors.append(f"Row {row_num}: Email already exists ({email})")
                        continue
                    
                    # Parse date_joined
                    try:
                        date_joined = timezone.datetime.strptime(row['date_joined'], '%Y-%m-%d').date()
                    except:
                        errors.append(f"Row {row_num}: Invalid date format for date_joined (use YYYY-MM-DD)")
                        continue
                    
                    # Determine role
                    is_teacher = row.get('is_teacher', '').lower() in ('true', 'yes', '1')
                    role = 'teacher' if is_teacher else 'non_teaching_staff'
                    
                    # Create CustomUser
                    temp_password = generate_temp_password()
                    user = CustomUser.objects.create_user(
                        username=email,
                        email=email,
                        password=temp_password,
                        first_name=row['first_name'].strip(),
                        last_name=row['last_name'].strip(),
                        role=role,
                        school=request.user.school,
                        is_active=True
                    )
                    
                    # Generate employee ID
                    employee_id = generate_employee_id(request.user.school)
                    
                    # Create StaffProfile
                    StaffProfile.objects.create(
                        user=user,
                        employee_id=employee_id,
                        position=row['position'].strip(),
                        date_joined=date_joined,
                        is_full_time=True,
                        salary=0
                    )
                    
                    created_staff.append({
                        'name': user.get_full_name(),
                        'email': email,
                        'employee_id': employee_id,
                        'position': row['position']
                    })
                
                except Exception as row_error:
                    errors.append(f"Row {row_num}: {str(row_error)}")
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error processing CSV: {str(e)}'
        }, status=500)
    
    return JsonResponse({
        'success': len(errors) == 0,
        'message': f'Created {len(created_staff)} staff member(s).',
        'data': {
            'created_count': len(created_staff),
            'failed_count': len(errors),
            'staff_list': created_staff,
            'errors': errors
        }
    })


@require_POST
@login_required
@admin_required
def onboard_student_ajax(request):
    """
    AJAX endpoint to create a single student.
    
    Returns JSON with:
    - success (bool)
    - message (str)
    - data: { admission_number, full_name } if successful
    - errors (dict) if validation fails
    """
    form = StudentOnboardingForm(request.POST)
    
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'message': 'Form validation failed',
            'errors': form.errors
        }, status=400)
    
    try:
        with transaction.atomic():
            # Generate admission number
            year = timezone.now().year
            random_hex = uuid.uuid4().hex[:6].upper()
            admission_number = f"STU-{year}-{random_hex}"
            
            # Ensure DOB has a default if not provided
            dob = form.cleaned_data['date_of_birth'] or timezone.now().date()
            
            # Create Student
            student = Student.objects.create(
                admission_number=admission_number,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                date_of_birth=dob,
                gender=form.cleaned_data['gender'],
                class_grade=form.cleaned_data['class_grade'],
                parent_name=form.cleaned_data['parent_name'],
                parent_phone=form.cleaned_data['parent_phone'],
                status='active'
            )
            
            # Log activity
            if hasattr(request.user, 'staffprofile'):
                ActivityLog.objects.create(
                    teacher=request.user.staffprofile,
                    activity_type='student_created',
                    description=f"Enrolled {student.full_name} (ID: {admission_number}) in {student.class_grade.name}",
                    related_student=student,
                    icon_name='person_add',
                    severity='info'
                )
            
            return JsonResponse({
                'success': True,
                'message': f'Student {student.full_name} enrolled successfully.',
                'data': {
                    'admission_number': admission_number,
                    'full_name': student.full_name,
                    'class': student.class_grade.name
                }
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating student: {str(e)}'
        }, status=500)


@require_POST
@login_required
@admin_required
def bulk_onboard_student_ajax(request):
    """
    AJAX endpoint to bulk create students from CSV upload.
    
    Expected CSV columns: first_name, last_name, class, parent_name, parent_phone, gender, date_of_birth (optional)
    
    Returns JSON with:
    - success (bool)
    - message (str)
    - data: { created_count, failed_count, student_list, errors }
    """
    form = BulkStudentUploadForm(request.POST, request.FILES)
    
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'message': 'Form validation failed',
            'errors': form.errors
        }, status=400)
    
    file = request.FILES['csv_file']
    required_cols = {'first_name', 'last_name', 'class', 'parent_name', 'parent_phone', 'gender'}
    
    success, rows, parse_errors = parse_csv_upload(file, required_cols)
    if not success:
        return JsonResponse({
            'success': False,
            'message': 'CSV file parsing failed',
            'errors': parse_errors
        }, status=400)
    
    created_students = []
    errors = []
    
    try:
        with transaction.atomic():
            year = timezone.now().year
            
            for row_num, row in rows:
                try:
                    # Find class by name
                    class_name = row['class'].strip()
                    class_grade = ClassGrade.objects.filter(
                        name=class_name,
                        school=request.user.school
                    ).first()
                    
                    if not class_grade:
                        errors.append(f"Row {row_num}: Class '{class_name}' not found")
                        continue
                    
                    # Generate admission number
                    random_hex = uuid.uuid4().hex[:6].upper()
                    admission_number = f"STU-{year}-{random_hex}"
                    
                    # Parse DOB if provided
                    dob = None
                    if row.get('date_of_birth', '').strip():
                        try:
                            dob = timezone.datetime.strptime(row['date_of_birth'], '%Y-%m-%d').date()
                        except:
                            dob = timezone.now().date()
                    else:
                        dob = timezone.now().date()
                    
                    # Create Student
                    student = Student.objects.create(
                        admission_number=admission_number,
                        first_name=row['first_name'].strip(),
                        last_name=row['last_name'].strip(),
                        date_of_birth=dob,
                        gender=row['gender'].strip().upper()[0],  # Take first char (M/F)
                        class_grade=class_grade,
                        parent_name=row['parent_name'].strip(),
                        parent_phone=row['parent_phone'].strip(),
                        status='active'
                    )
                    
                    created_students.append({
                        'name': student.full_name,
                        'admission_number': admission_number,
                        'class': class_grade.name,
                        'parent': row['parent_name']
                    })
                
                except Exception as row_error:
                    errors.append(f"Row {row_num}: {str(row_error)}")
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error processing CSV: {str(e)}'
        }, status=500)
    
    return JsonResponse({
        'success': len(errors) == 0,
        'message': f'Enrolled {len(created_students)} student(s).',
        'data': {
            'created_count': len(created_students),
            'failed_count': len(errors),
            'student_list': created_students,
            'errors': errors
        }
    })


@require_POST
@login_required
@admin_required
def send_message_ajax(request):
    """
    AJAX endpoint to create and send a message to recipients.
    
    Supports immediate and scheduled delivery. Creates Message and MessageRecipient entries.
    
    Returns JSON with:
    - success (bool)
    - message (str)
    - data: { message_id, recipient_count, scheduled_for } if successful
    """
    form = AdminMessageForm(request.POST)
    
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'message': 'Form validation failed',
            'errors': form.errors
        }, status=400)
    
    try:
        with transaction.atomic():
            # Create Message
            message = Message.objects.create(
                sender=request.user,
                school=request.user.school,
                subject=form.cleaned_data['subject'],
                body=form.cleaned_data['body'],
                template=form.cleaned_data.get('template'),
                recipient_type=form.cleaned_data['recipient_type'],
                target_class=form.cleaned_data.get('target_class'),
                target_user=form.cleaned_data.get('target_user'),
                scheduled_at=form.cleaned_data.get('scheduled_at')
            )
            
            # Resolve recipients
            recipients = resolve_message_recipients(message)
            
            # Create MessageRecipient entries
            recipient_count = create_message_recipients(message, recipients)
            
            # Mark as sent
            message.is_sent = True
            message.save()
            
            # Log activity
            if hasattr(request.user, 'staffprofile'):
                ActivityLog.objects.create(
                    teacher=request.user.staffprofile,
                    activity_type='message_sent',
                    description=f"Sent message '{message.subject}' to {recipient_count} recipient(s)",
                    icon_name='mail',
                    severity='info'
                )
            
            scheduled_info = None
            if message.scheduled_at:
                scheduled_info = message.scheduled_at.isoformat()
            
            return JsonResponse({
                'success': True,
                'message': f'Message sent to {recipient_count} recipient(s).',
                'data': {
                    'message_id': message.id,
                    'recipient_count': recipient_count,
                    'scheduled_for': scheduled_info
                }
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error sending message: {str(e)}'
        }, status=500)


@require_POST
@login_required
@admin_required
def reset_staff_password_ajax(request):
    """
    AJAX endpoint to reset a staff member's password.
    
    Generates new temporary password and updates the user's password.
    
    Returns JSON with:
    - success (bool)
    - message (str)
    - data: { temp_password, full_name } if successful
    """
    form = StaffPasswordResetForm(request.POST)
    
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'message': 'Form validation failed',
            'errors': form.errors
        }, status=400)
    
    try:
        user = form.cleaned_data.get('_staff_user')
        
        if not user:
            return JsonResponse({
                'success': False,
                'message': 'Staff member not found.'
            }, status=404)
        
        # Generate new temporary password
        temp_password = generate_temp_password()
        
        # Update user password
        user.set_password(temp_password)
        user.save()
        
        # Log activity
        if hasattr(request.user, 'staffprofile'):
            ActivityLog.objects.create(
                teacher=request.user.staffprofile,
                activity_type='password_reset',
                description=f"Reset password for {user.get_full_name()} ({user.email})",
                icon_name='lock_reset',
                severity='info'
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Password reset for {user.get_full_name()}.',
            'data': {
                'temp_password': temp_password,
                'full_name': user.get_full_name(),
                'email': user.email
            }
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error resetting password: {str(e)}'
        }, status=500)


# ============================================================================
# MESSAGE RECIPIENT VIEWS
# ============================================================================


@login_required
def message_inbox(request):
    """
    Display message inbox for the logged-in user.
    
    Shows all messages received by the user, with filtering and pagination.
    Supports filtering by read/unread, date range, and sender role.
    
    Access: All authenticated users (teachers, staff, parents)
    
    Renders: SchoolNowMgt/message_inbox.html
    """
    # Get all messages for the current user
    messages_qs = MessageRecipient.objects.filter(
        recipient=request.user
    ).select_related('message', 'message__sender').order_by('-created_at')
    
    # Filter by read/unread if specified
    filter_type = request.GET.get('filter', 'all')  # all, unread, read
    if filter_type == 'unread':
        messages_qs = messages_qs.filter(read_at__isnull=True)
    elif filter_type == 'read':
        messages_qs = messages_qs.filter(read_at__isnull=False)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(messages_qs, 20)  # 20 messages per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Count unread messages
    unread_count = MessageRecipient.objects.filter(
        recipient=request.user,
        read_at__isnull=True
    ).count()
    
    context = {
        'page_obj': page_obj,
        'messages': page_obj.object_list,
        'unread_count': unread_count,
        'filter_type': filter_type,
    }
    
    return render(request, 'SchoolNowMgt/message_inbox.html', context)


@login_required
def mark_message_read_ajax(request, message_id):
    """
    AJAX endpoint to mark a message as read.
    
    Args:
        message_id (int): ID of the Message to mark as read
    
    Returns JSON with:
    - success (bool)
    - message (str)
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Method not allowed'
        }, status=405)
    
    try:
        message_recipient = MessageRecipient.objects.get(
            message_id=message_id,
            recipient=request.user
        )
        
        # Mark as read
        message_recipient.read_at = timezone.now()
        message_recipient.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Message marked as read'
        })
    
    except MessageRecipient.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Message not found or not accessible to you'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


# ============================================================================
# PARENT MESSAGING VIEWS
# ============================================================================

@login_required
def parent_message_inbox(request):
    """
    Display message inbox for a parent.
    
    Shows all messages received from admin/staff and sent by parent to teachers/staff.
    Supports filtering by message type (received/sent/unread) and pagination.
    
    Access: Parent users only
    
    Renders: SchoolNowMgt/parent/parent_message_inbox.html
    """
    if request.user.role != 'parent':
        return redirect('auth:unified_login')
    
    # Get filter type from request
    filter_type = request.GET.get('filter', 'all')  # all, received, sent, unread
    
    # Get messages based on filter
    messages_qs = get_parent_messages(request.user, filter_type)
    
    # Pagination
    paginator = Paginator(messages_qs, 15)  # 15 messages per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Count unread messages
    unread_count = get_parent_unread_count(request.user)
    
    # Get message details with recipient status
    messages_data = []
    for message in page_obj.object_list:
        try:
            # Try to get recipient status if parent received this message
            recipient = MessageRecipient.objects.get(
                message=message,
                recipient=request.user
            )
            is_read = recipient.read_at is not None
        except MessageRecipient.DoesNotExist:
            # Parent sent this message
            is_read = True  # Sent messages are considered read
        
        messages_data.append({
            'message': message,
            'is_read': is_read,
            'is_sent': message.sender == request.user,
        })
    
    context = {
        'page_obj': page_obj,
        'messages_data': messages_data,
        'unread_count': unread_count,
        'filter_type': filter_type,
    }
    
    return render(request, 'SchoolNowMgt/parent/parent_message_inbox.html', context)


@login_required
def parent_message_detail(request, message_id):
    """
    Display a single message with full thread (if replies exist).
    
    Shows message details with related recipients and allows parent to reply.
    
    Access: Parent who is recipient or sender of the message
    
    Renders: SchoolNowMgt/parent/parent_message_detail.html
    """
    if request.user.role != 'parent':
        return redirect('auth:unified_login')
    
    try:
        message = Message.objects.select_related('sender').get(id=message_id)
    except Message.DoesNotExist:
        return redirect('SchoolNowMgt:parent_message_inbox')
    
    # Check access: must be recipient or sender
    is_sender = message.sender == request.user
    is_recipient = MessageRecipient.objects.filter(
        message=message,
        recipient=request.user
    ).exists()
    
    if not (is_sender or is_recipient):
        return redirect('SchoolNowMgt:parent_message_inbox')
    
    # Mark as read if parent is recipient
    if is_recipient and not is_sender:
        try:
            recipient = MessageRecipient.objects.get(
                message=message,
                recipient=request.user
            )
            if not recipient.read_at:
                recipient.read_at = timezone.now()
                recipient.save()
        except MessageRecipient.DoesNotExist:
            pass
    
    # Get related messages (replies/thread) - same subject and participants
    related_messages = Message.objects.filter(
        subject=message.subject,
        school=request.user.school
    ).filter(
        Q(sender=request.user) | Q(target_user=request.user)
    ).select_related('sender').order_by('created_at')
    
    # Initialize form for reply
    form = ParentMessageForm(request.user) if request.method == 'GET' else None
    
    context = {
        'message': message,
        'related_messages': related_messages,
        'is_sender': is_sender,
        'form': form,
    }
    
    return render(request, 'SchoolNowMgt/parent/parent_message_detail.html', context)


@login_required
@require_POST
def parent_send_message_ajax(request):
    """
    AJAX endpoint for parent to send a message to a teacher/staff member.
    
    Creates Message and MessageRecipient entries for the recipient.
    
    Returns JSON with:
    - success (bool)
    - message (str)
    - data: { message_id, recipient_name } if successful
    """
    if request.user.role != 'parent':
        return JsonResponse({
            'success': False,
            'message': 'Access denied. Parents only.'
        }, status=403)
    
    form = ParentMessageForm(request.user, request.POST)
    
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'message': 'Form validation failed',
            'errors': form.errors
        }, status=400)
    
    try:
        with transaction.atomic():
            recipient = form.cleaned_data['recipient']
            
            # Create Message
            message = Message.objects.create(
                sender=request.user,
                sender_type='parent',
                school=request.user.school,
                subject=form.cleaned_data['subject'],
                body=form.cleaned_data['body'],
                recipient_type='individual',
                target_user=recipient,
                is_sent=True
            )
            
            # Create MessageRecipient entry for the staff member
            MessageRecipient.objects.create(
                message=message,
                recipient=recipient
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Message sent to {recipient.get_full_name()}.',
                'data': {
                    'message_id': message.id,
                    'recipient_name': recipient.get_full_name()
                }
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error sending message: {str(e)}'
        }, status=500)


@login_required
@require_POST
def parent_mark_message_read_ajax(request, message_id):
    """
    AJAX endpoint for parent to mark a received message as read.
    
    Args:
        message_id (int): ID of the Message to mark as read
    
    Returns JSON with:
    - success (bool)
    - message (str)
    """
    if request.user.role != 'parent':
        return JsonResponse({
            'success': False,
            'message': 'Access denied'
        }, status=403)
    
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Method not allowed'
        }, status=405)
    
    try:
        message_recipient = MessageRecipient.objects.get(
            message_id=message_id,
            recipient=request.user
        )
        
        # Mark as read
        if not message_recipient.read_at:
            message_recipient.read_at = timezone.now()
            message_recipient.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Message marked as read'
        })
    
    except MessageRecipient.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Message not found'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
def get_parent_unread_count_ajax(request):
    """
    AJAX endpoint to get unread message count for parent (for badge display).
    
    Returns JSON with:
    - success (bool)
    - unread_count (int)
    """
    if request.user.role != 'parent':
        return JsonResponse({
            'success': False,
            'unread_count': 0
        }, status=403)
    
    try:
        unread_count = get_parent_unread_count(request.user)
        
        return JsonResponse({
            'success': True,
            'unread_count': unread_count
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'unread_count': 0
        }, status=500)


# ─────────────────────────────────────────────────────────────
# ADMIN MINI-DASHBOARDS (Phase 7)
# ─────────────────────────────────────────────────────────────

@unified_login_required
def admin_students_dashboard(request):
    """
    Admin mini-dashboard for Students section.
    
    Shows:
    - Total students, new this month, by class
    - Student list with search/filter/pagination
    - Inline "New Admission" form
    """
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('auth:unified_login')
    
    today = timezone.localdate()
    user_school = request.user.school
    
    # Students stats
    total_students = Student.objects.filter(
        status='active',
        class_grade__school=user_school
    ).count()
    
    new_students_this_month = Student.objects.filter(
        date_admitted__year=today.year,
        date_admitted__month=today.month,
        class_grade__school=user_school
    ).count()
    
    total_classes = ClassGrade.objects.filter(school=user_school).count()
    
    # Students by class (with counts)
    students_by_class = ClassGrade.objects.filter(
        school=user_school
    ).annotate(
        student_count=Count('students', filter=Q(students__status='active'))
    ).order_by('level')
    
    # All classes for modal/form and filtering
    classes = ClassGrade.objects.filter(school=user_school).order_by('level')
    
    # Get filter parameters
    class_filter = request.GET.get('class', '')
    status_filter = request.GET.get('status', 'active')
    search_query = request.GET.get('search', '')
    
    # Recent students with filtering
    recent_students = Student.objects.filter(
        class_grade__school=user_school,
        status=status_filter if status_filter else 'active'
    ).select_related('class_grade', 'parent_user')
    
    if class_filter:
        recent_students = recent_students.filter(class_grade__id=class_filter)
    
    if search_query:
        recent_students = recent_students.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(admission_number__icontains=search_query)
        )
    
    recent_students = recent_students.order_by('-date_admitted')
    
    # Paginate
    paginated_items, paginator, page_num = paginate_queryset(request, recent_students, per_page=15)
    
    context = {
        'today': today,
        'user': request.user,
        'school': user_school,
        'total_students': total_students,
        'new_students_this_month': new_students_this_month,
        'total_classes': total_classes,
        'students_by_class': students_by_class,
        'recent_students': paginated_items,
        'paginator': paginator,
        'classes': classes,
        'class_filter': class_filter,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'SchoolNowMgt/admin_students_dashboard.html', context)


@unified_login_required
def admin_staff_dashboard(request):
    """
    Admin mini-dashboard for Staff section.
    
    Shows:
    - Total staff, new this month, by department
    - Staff list with search/filter/pagination
    - Inline "Add Staff" form
    """
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('auth:unified_login')
    
    today = timezone.localdate()
    user_school = request.user.school
    
    # Staff stats
    total_staff = StaffProfile.objects.filter(
        user__is_active=True,
        user__school=user_school,
        date_left__isnull=True
    ).count()
    
    new_staff_this_month = StaffProfile.objects.filter(
        date_joined__year=today.year,
        date_joined__month=today.month,
        user__school=user_school
    ).count()
    
    # Staff by position (annotated counts)
    staff_positions = StaffProfile.objects.filter(
        user__school=user_school,
        date_left__isnull=True
    ).values('position').annotate(
        position_count=Count('id')
    ).order_by('position')
    
    # Get filter parameters
    position_filter = request.GET.get('position', '')
    search_query = request.GET.get('search', '')
    
    # Recent staff with filtering
    recent_staff = StaffProfile.objects.filter(
        user__school=user_school
    ).select_related('user')
    
    if position_filter:
        recent_staff = recent_staff.filter(position=position_filter)
    
    if search_query:
        recent_staff = recent_staff.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(employee_id__icontains=search_query)
        )
    
    recent_staff = recent_staff.order_by('-date_joined')
    
    # Paginate
    paginated_items, paginator, page_num = paginate_queryset(request, recent_staff, per_page=15)
    
    # Today's attendance summary
    staff_present_today = StaffAttendance.objects.filter(
        date=today,
        status='present',
        staff__user__school=user_school
    ).count()
    
    staff_absent_today = StaffAttendance.objects.filter(
        date=today,
        status='absent',
        staff__user__school=user_school
    ).count()
    
    context = {
        'today': today,
        'user': request.user,
        'school': user_school,
        'total_staff': total_staff,
        'new_staff_this_month': new_staff_this_month,
        'staff_positions': staff_positions,
        'recent_staff': paginated_items,
        'paginator': paginator,
        'staff_present_today': staff_present_today,
        'staff_absent_today': staff_absent_today,
        'position_filter': position_filter,
        'search_query': search_query,
    }
    
    return render(request, 'SchoolNowMgt/admin_staff_dashboard.html', context)


@unified_login_required
def admin_communication_dashboard(request):
    """
    Admin mini-dashboard for Communication section.
    
    Shows:
    - Messages sent count, pending messages, recipients breakdown
    - Message history table with pagination
    - Inline "Send Message" form
    """
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('auth:unified_login')
    
    today = timezone.localdate()
    user_school = request.user.school
    
    # Message stats (from Message model)
    total_messages_sent = Message.objects.filter(
        school=user_school
    ).count()
    
    # Messages this month
    messages_this_month = Message.objects.filter(
        created_at__year=today.year,
        created_at__month=today.month,
        school=user_school
    ).count()
    
    # Recipient breakdown (count unique recipients)
    all_recipients = MessageRecipient.objects.filter(
        message__school=user_school
    ).count()
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    
    # Recent messages with filtering
    recent_messages = Message.objects.filter(
        school=user_school
    ).select_related('sender')
    
    if search_query:
        recent_messages = recent_messages.filter(
            Q(subject__icontains=search_query) |
            Q(body__icontains=search_query)
        )
    
    recent_messages = recent_messages.order_by('-created_at')
    
    # Paginate
    paginated_items, paginator, page_num = paginate_queryset(request, recent_messages, per_page=15)
    
    context = {
        'today': today,
        'user': request.user,
        'school': user_school,
        'total_messages_sent': total_messages_sent,
        'messages_this_month': messages_this_month,
        'all_recipients': all_recipients,
        'recent_messages': paginated_items,
        'paginator': paginator,
        'search_query': search_query,
    }
    
    return render(request, 'SchoolNowMgt/admin_communication_dashboard.html', context)


@unified_login_required
def admin_finance_dashboard(request):
    """
    Admin mini-dashboard for Finance section.
    
    Shows:
    - Monthly revenue, collected this month, outstanding, % target
    - Recent transactions with pagination
    - Revenue trend data
    - Fee breakdown by class
    """
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('auth:unified_login')
    
    today = timezone.localdate()
    user_school = request.user.school
    
    # Get filter parameters
    class_filter = request.GET.get('class', '')
    month = request.GET.get('month', today.month)
    year = request.GET.get('year', today.year)
    
    try:
        month = int(month)
        year = int(year)
    except (ValueError, TypeError):
        month = today.month
        year = today.year
    
    # Finance stats
    fees_collected_this_month = FeePayment.objects.filter(
        payment_date__year=year,
        payment_date__month=month,
        student__class_grade__school=user_school
    ).aggregate(total=Sum('amount_paid'))['total'] or 0
    
    # Outstanding fees (simple: expected - paid)
    outstanding_fees = 50000  # Mock for now
    
    # Fee collection percentage
    fee_collection_percentage = 85  # Mock default
    
    # Recent transactions with filtering
    recent_transactions = FeePayment.objects.filter(
        student__class_grade__school=user_school
    ).select_related('student', 'student__class_grade')
    
    if class_filter:
        recent_transactions = recent_transactions.filter(student__class_grade__id=class_filter)
    
    recent_transactions = recent_transactions.order_by('-payment_date')
    
    # Paginate
    paginated_items, paginator, page_num = paginate_queryset(request, recent_transactions, per_page=15)
    
    # Fee breakdown by class
    fee_by_class = FeePayment.objects.filter(
        student__class_grade__school=user_school,
        payment_date__year=year,
        payment_date__month=month
    ).values('student__class_grade__name').annotate(
        total_amount=Sum('amount_paid'),
        transaction_count=Count('id')
    ).order_by('student__class_grade__name')
    
    # Chart data: Monthly revenue trend (last 6 months)
    import json
    from datetime import timedelta
    monthly_revenue = []
    monthly_labels = []
    current_date = today
    
    for i in range(5, -1, -1):
        check_date = current_date - timedelta(days=i*30)
        check_month = check_date.month
        check_year = check_date.year
        
        monthly_total = FeePayment.objects.filter(
            payment_date__year=check_year,
            payment_date__month=check_month,
            student__class_grade__school=user_school
        ).aggregate(total=Sum('amount_paid'))['total'] or 0
        
        monthly_revenue.append(int(monthly_total))
        monthly_labels.append(check_date.strftime('%b %Y'))
    
    # Chart data: Fee by class (bar chart)
    fee_by_class_labels = []
    fee_by_class_amounts = []
    
    for item in fee_by_class:
        fee_by_class_labels.append(item['student__class_grade__name'])
        fee_by_class_amounts.append(int(item['total_amount'] or 0))
    
    # Convert to JSON for template
    chart_data = {
        'monthly_revenue_labels': json.dumps(monthly_labels),
        'monthly_revenue': json.dumps(monthly_revenue),
        'fee_by_class_labels': json.dumps(fee_by_class_labels),
        'fee_by_class_amounts': json.dumps(fee_by_class_amounts),
    }
    
    # Get all classes for filter dropdown
    classes = ClassGrade.objects.filter(school=user_school).order_by('level')
    
    context = {
        'today': today,
        'user': request.user,
        'school': user_school,
        'fees_collected_this_month': fees_collected_this_month,
        'outstanding_fees': outstanding_fees,
        'fee_collection_percentage': fee_collection_percentage,
        'recent_transactions': paginated_items,
        'paginator': paginator,
        'fee_by_class': fee_by_class,
        'classes': classes,
        'class_filter': class_filter,
        'month': month,
        'year': year,
        'chart_data': chart_data,
    }
    
    return render(request, 'SchoolNowMgt/admin_finance_dashboard.html', context)


@unified_login_required
def admin_reports_dashboard(request):
    """
    Admin mini-dashboard for Reports section.
    
    Shows:
    - Academic performance by class (with pagination)
    - Attendance trends
    - Enrollment growth
    - Fee collection vs. target
    - Retention alert summary
    """
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('auth:unified_login')
    
    today = timezone.localdate()
    user_school = request.user.school
    current_year = str(today.year)
    
    # Get filter parameter
    class_filter = request.GET.get('class', '')
    
    # Academic metrics
    average_score_this_year = Grade.objects.filter(
        academic_year=current_year,
        student__class_grade__school=user_school
    ).aggregate(avg=Avg('score'))['avg']
    
    if average_score_this_year is not None:
        average_score_this_year = round(average_score_this_year, 1)
    else:
        average_score_this_year = '—'
    
    # Class performance breakdown with filtering
    class_performance = Grade.objects.filter(
        academic_year=current_year,
        student__class_grade__school=user_school
    ).values('student__class_grade__name').annotate(
        avg_score=Avg('score')
    ).order_by('student__class_grade__name')
    
    if class_filter:
        class_performance = class_performance.filter(student__class_grade__id=class_filter)
    
    # Note: class_performance is a summary table, no pagination needed
    
    # Enrollment data (new students by month)
    enrollment_by_month_qs = Student.objects.filter(
        class_grade__school=user_school
    ).extra(
        select={'month': 'strftime("%%m", date_admitted)'}
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Get the latest month's enrollment count (for template)
    enrollment_by_month = list(enrollment_by_month_qs.values_list('count', flat=True)) if enrollment_by_month_qs.exists() else []
    
    # Attendance summary
    total_student_attendance = StudentAttendance.objects.filter(
        student__class_grade__school=user_school,
        date=today
    )
    present_count = total_student_attendance.filter(status='present').count()
    total_count = total_student_attendance.count()
    attendance_percentage = round((present_count / total_count * 100), 1) if total_count > 0 else 0
    
    # Retention alerts summary
    retention_alerts_count = RetentionAlert.objects.filter(
        resolved=False,
        student__class_grade__school=user_school
    ).count()
    
    high_severity_alerts = RetentionAlert.objects.filter(
        resolved=False,
        severity='high',
        student__class_grade__school=user_school
    ).count()
    
    # Chart data: Enrollment trend (monthly new admissions)
    import json
    from datetime import timedelta
    
    enrollment_trend_labels = []
    enrollment_trend_data = []
    current_date = today
    
    for i in range(5, -1, -1):
        check_date = current_date - timedelta(days=i*30)
        check_month = check_date.month
        check_year = check_date.year
        
        new_admissions = Student.objects.filter(
            class_grade__school=user_school,
            date_admitted__year=check_year,
            date_admitted__month=check_month
        ).count()
        
        enrollment_trend_data.append(new_admissions)
        enrollment_trend_labels.append(check_date.strftime('%b %Y'))
    
    # Chart data: Class performance bar chart
    class_perf_labels = []
    class_perf_scores = []
    
    for item in class_performance:
        class_perf_labels.append(item['student__class_grade__name'])
        class_perf_scores.append(round(item['avg_score'], 1) if item['avg_score'] else 0)
    
    # Chart data: Retention alert severity pie chart
    low_alerts = RetentionAlert.objects.filter(
        resolved=False,
        severity='low',
        student__class_grade__school=user_school
    ).count()
    medium_alerts = RetentionAlert.objects.filter(
        resolved=False,
        severity='medium',
        student__class_grade__school=user_school
    ).count()
    
    # Convert to JSON for template
    chart_data = {
        'enrollment_trend_labels': json.dumps(enrollment_trend_labels),
        'enrollment_trend_data': json.dumps(enrollment_trend_data),
        'class_perf_labels': json.dumps(class_perf_labels),
        'class_perf_scores': json.dumps(class_perf_scores),
        'alert_severity_labels': json.dumps(['Low', 'Medium', 'High']),
        'alert_severity_data': json.dumps([low_alerts, medium_alerts, high_severity_alerts]),
    }
    
    # Get all classes for filter dropdown
    classes = ClassGrade.objects.filter(school=user_school).order_by('level')
    
    context = {
        'today': today,
        'user': request.user,
        'school': user_school,
        'average_score_this_year': average_score_this_year,
        'class_performance': class_performance,
        'enrollment_by_month': enrollment_by_month,
        'attendance_percentage': attendance_percentage,
        'retention_alerts_count': retention_alerts_count,
        'high_severity_alerts': high_severity_alerts,
        'classes': classes,
        'class_filter': class_filter,
        'chart_data': chart_data,
    }
    
    return render(request, 'SchoolNowMgt/admin_reports_dashboard.html', context)
# ─────────────────────────────────────────────────────────────
# ADMIN PROFILE & EVENTS MANAGEMENT (Phase 3)
# ─────────────────────────────────────────────────────────────

@unified_login_required
def admin_profile_view(request):
    """
    Display and manage admin profile.
    
    GET: Display admin profile page with edit forms
    POST: Handled by separate edit_admin_profile view
    
    Access Control: Admin users only
    
    Renders: SchoolNowMgt/admin_profile.html
    """
    if request.user.role != 'admin':
        return redirect('auth:unified_login')
    
    # Get or create AdminProfile
    admin_profile, created = AdminProfile.objects.get_or_create(user=request.user)
    
    # Initialize forms
    profile_form = AdminProfileForm(user=request.user, instance=admin_profile)
    picture_form = ProfilePictureForm()
    
    context = {
        'admin_profile': admin_profile,
        'profile_form': profile_form,
        'picture_form': picture_form,
    }
    
    return render(request, 'SchoolNowMgt/admin_profile.html', context)


@unified_login_required
@require_POST
def edit_admin_profile(request):
    """
    Handle admin profile updates (profile info and picture).
    
    POST: Save profile changes
    
    Access Control: Admin users only, editing their own profile
    
    Returns: JSON response or redirect with success/error message
    """
    if request.user.role != 'admin':
        return redirect('auth:unified_login')
    
    try:
        admin_profile = AdminProfile.objects.get(user=request.user)
    except AdminProfile.DoesNotExist:
        admin_profile = AdminProfile.objects.create(user=request.user)
    
    # Handle profile info update
    if 'save_profile' in request.POST:
        profile_form = AdminProfileForm(user=request.user, data=request.POST, instance=admin_profile)
        if profile_form.is_valid():
            profile_form.save()
            return redirect('SchoolNowMgt:admin_profile')
        else:
            # Re-render with errors
            context = {
                'admin_profile': admin_profile,
                'profile_form': profile_form,
                'errors': profile_form.errors,
            }
            return render(request, 'SchoolNowMgt/admin_profile.html', context)
    
    # Handle profile picture upload
    if 'save_picture' in request.POST:
        picture_form = ProfilePictureForm(request.POST, request.FILES)
        if picture_form.is_valid() and request.FILES.get('profile_picture'):
            request.user.profile_picture = request.FILES['profile_picture']
            request.user.save()
            return redirect('SchoolNowMgt:admin_profile')
        else:
            context = {
                'admin_profile': admin_profile,
                'picture_form': picture_form,
                'errors': picture_form.errors,
            }
            return render(request, 'SchoolNowMgt/admin_profile.html', context)
    
    return redirect('SchoolNowMgt:admin_profile')


@unified_login_required
@unified_login_required
def events_dashboard(request):
    """
    Display the events mini-dashboard with all school events.
    
    GET: Display events dashboard page with all events
    
    Access Control: Admin users only
    
    Renders: SchoolNowMgt/events_dashboard.html
    """
    if request.user.role != 'admin':
        return redirect('auth:unified_login')
    
    user_school = request.user.school
    
    # Get upcoming events (next 5)
    upcoming_events = Event.objects.filter(
        school=user_school,
        start_date__gte=timezone.now().date()
    ).order_by('start_date')[:5]
    
    # Get all events (paginated)
    all_events = Event.objects.filter(school=user_school).order_by('-start_date')
    events_page, paginator, page_num = paginate_queryset(request, all_events, per_page=10)
    
    context = {
        'upcoming_events': upcoming_events,
        'events': events_page,
        'paginator': paginator,
        'page_num': page_num,
    }
    
    return render(request, 'SchoolNowMgt/events_dashboard.html', context)


def list_events(request):
    """
    List all events for the school (used in dashboard context).
    
    GET: Return paginated event list
    
    Access Control: Admin users only
    
    Renders: SchoolNowMgt/admin_profile.html (via admin_profile_view)
    """
    if request.user.role != 'admin':
        return redirect('auth:unified_login')
    
    user_school = request.user.school
    events = Event.objects.filter(school=user_school).order_by('-start_date')
    
    return render(request, 'SchoolNowMgt/admin_profile.html', {
        'events': paginate_queryset(request, events, per_page=10)
    })


@unified_login_required
@require_POST
def create_event(request):
    """
    Create a new school event.
    
    POST: Save event data
    
    Access Control: Admin users only
    
    Returns: Redirect to admin_profile on success
    """
    if request.user.role != 'admin':
        return redirect('auth:unified_login')
    
    form = EventForm(request.POST)
    if form.is_valid():
        event = form.save(commit=False)
        event.school = request.user.school
        event.created_by = request.user
        event.save()
        return redirect('SchoolNowMgt:admin_profile')
    
    # Re-render admin profile with form errors
    try:
        admin_profile = AdminProfile.objects.get(user=request.user)
    except AdminProfile.DoesNotExist:
        admin_profile = AdminProfile.objects.create(user=request.user)
    
    context = {
        'admin_profile': admin_profile,
        'event_form': form,
        'errors': form.errors,
    }
    
    return render(request, 'SchoolNowMgt/admin_profile.html', context)


@unified_login_required
def edit_event(request, event_id):
    """
    Edit an existing school event.
    
    GET: Display event edit form
    POST: Save event changes
    
    Access Control: Admin users only, must own the event's school
    
    Renders: SchoolNowMgt/admin_profile.html
    """
    if request.user.role != 'admin':
        return redirect('auth:unified_login')
    
    try:
        event = Event.objects.get(id=event_id, school=request.user.school)
    except Event.DoesNotExist:
        return redirect('SchoolNowMgt:admin_profile')
    
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            return redirect('SchoolNowMgt:admin_profile')
    else:
        form = EventForm(instance=event)
    
    try:
        admin_profile = AdminProfile.objects.get(user=request.user)
    except AdminProfile.DoesNotExist:
        admin_profile = AdminProfile.objects.create(user=request.user)
    
    context = {
        'admin_profile': admin_profile,
        'event_form': form,
        'edit_event': event,
    }
    
    return render(request, 'SchoolNowMgt/admin_profile.html', context)


@unified_login_required
@require_POST
def delete_event(request, event_id):
    """
    Delete a school event.
    
    POST: Delete event
    
    Access Control: Admin users only, must own the event's school
    
    Returns: Redirect to admin_profile
    """
    if request.user.role != 'admin':
        return redirect('auth:unified_login')
    
    try:
        event = Event.objects.get(id=event_id, school=request.user.school)
        event.delete()
    except Event.DoesNotExist:
        pass
    
    return redirect('SchoolNowMgt:admin_profile')


def ensure_admin_profile(user):
    """
    Helper function to ensure an admin user has an AdminProfile.
    Auto-creates if missing.
    """
    if user.role == 'admin':
        AdminProfile.objects.get_or_create(user=user)


# ==================================================================================
# PARENT PORTAL SUBDASHBOARDS (Phase 8)
# ==================================================================================

@unified_login_required
def parent_children_dashboard(request):
    """
    Parent subdashboard: View all enrolled children across multiple schools.
    
    Access Control: Parents only
    
    Displays:
    - Children grouped by school
    - Per-child: photo, name, admission #, class, GPA, attendance %, status
    - Quick action buttons: View Academics | View Payments
    
    Multi-school Support: Parents with children in multiple schools see all grouped by school
    
    Renders: SchoolNowMgt/parent_children_subdashboard.html
    """
    if request.user.role != 'parent':
        if request.user.role == 'admin':
            return redirect('SchoolNowMgt:dashboard')
        elif request.user.role == 'teacher':
            return redirect('teacher:dashboard')
        else:
            return redirect('auth:unified_login')
    
    # Get all active children for this parent
    children = Student.objects.filter(
        parent_user=request.user,
        status='active'
    ).select_related('class_grade', 'class_grade__school').prefetch_related('grades', 'attendance_records')
    
    # Group children by school
    from collections import defaultdict
    children_by_school = defaultdict(list)
    for child in children:
        school = child.class_grade.school
        children_by_school[school].append(child)
    
    # Calculate GPA and attendance for each child
    for school, school_children in children_by_school.items():
        for child in school_children:
            # Calculate GPA (average of recent grades)
            grades = child.grades.all()
            if grades:
                child.gpa = sum([g.score for g in grades]) / len(grades)
                child.gpa = round(child.gpa, 2)
            else:
                child.gpa = 0.00
            
            # Calculate attendance percentage
            attendance_records = child.attendance_records.all()
            if attendance_records:
                present_count = attendance_records.filter(status='present').count()
                child.attendance_percentage = round((present_count / attendance_records.count()) * 100, 1)
            else:
                child.attendance_percentage = 0.0
    
    context = {
        'children_by_school': dict(children_by_school),
        'total_active_children': children.count(),
        'today': timezone.localdate(),
        'user': request.user,
    }
    
    return render(request, 'SchoolNowMgt/parent_children_subdashboard.html', context)


@unified_login_required
def parent_academics_dashboard(request):
    """
    Parent subdashboard: View child's grades and assignments.
    
    Access Control: Parents only
    
    GET params:
    - child_id: ID of child to display (required, or defaults to first child)
    - year: Academic year filter (optional, defaults to current year)
    - term: Term filter (optional)
    
    Displays:
    - Child selector dropdown
    - Year/term filter dropdowns
    - Grades table: Subject | Score | Letter Grade | Remarks | Term/Year
    - Assignments table: Title | Subject | Due Date | Submitted On | Status | Score
    - Performance summary: GPA | Avg Score | Attendance % | Class Rank
    
    Renders: SchoolNowMgt/parent_academics_subdashboard.html
    """
    if request.user.role != 'parent':
        if request.user.role == 'admin':
            return redirect('SchoolNowMgt:dashboard')
        elif request.user.role == 'teacher':
            return redirect('teacher:dashboard')
        else:
            return redirect('auth:unified_login')
    
    # Get all active children for dropdown
    all_children = Student.objects.filter(
        parent_user=request.user,
        status='active'
    ).select_related('class_grade', 'class_grade__school').order_by('first_name')
    
    # Get selected child (from GET param or default to first)
    child_id = request.GET.get('child_id')
    if child_id:
        try:
            selected_child = all_children.get(id=child_id)
        except Student.DoesNotExist:
            selected_child = all_children.first()
    else:
        selected_child = all_children.first()
    
    if not selected_child:
        # No children enrolled
        context = {
            'all_children': all_children,
            'selected_child': None,
            'grades': [],
            'assignments': [],
            'today': timezone.localdate(),
        }
        return render(request, 'SchoolNowMgt/parent_academics_subdashboard.html', context)
    
    # Get filter parameters
    today = timezone.localdate()
    year = request.GET.get('year', str(today.year))
    term = request.GET.get('term', '')
    
    # Get grades for selected child
    grades = selected_child.grades.select_related('subject').filter(
        academic_year=year
    ).order_by('term', 'subject__name')
    
    if term:
        grades = grades.filter(term=term)
    
    # Get assignments for selected child
    assignments = StudentAssignment.objects.filter(
        student=selected_child
    ).select_related('assignment', 'assignment__subject').order_by('-assignment__due_date')
    
    # Calculate academic metrics
    all_grades = selected_child.grades.filter(academic_year=year)
    if all_grades:
        gpa = sum([g.score for g in all_grades]) / len(all_grades)
        gpa = round(gpa, 2)
    else:
        gpa = 0.00
    
    avg_score = all_grades.aggregate(avg=Avg('score'))['avg']
    if avg_score:
        avg_score = round(avg_score, 1)
    else:
        avg_score = 0.0
    
    # Calculate attendance percentage
    attendance_records = StudentAttendance.objects.filter(student=selected_child)
    if attendance_records:
        present_count = attendance_records.filter(status='present').count()
        attendance_percentage = round((present_count / attendance_records.count()) * 100, 1)
    else:
        attendance_percentage = 0.0
    
    # Get available academic years
    academic_years = selected_child.grades.values_list('academic_year', flat=True).distinct().order_by('-academic_year')
    
    # Get available terms
    TERM_CHOICES = [
        ('term_1', 'Term 1'),
        ('term_2', 'Term 2'),
        ('term_3', 'Term 3'),
    ]
    
    context = {
        'all_children': all_children,
        'selected_child': selected_child,
        'grades': grades,
        'assignments': assignments,
        'gpa': gpa,
        'avg_score': avg_score,
        'attendance_percentage': attendance_percentage,
        'academic_years': academic_years,
        'term_choices': TERM_CHOICES,
        'selected_year': year,
        'selected_term': term,
        'today': timezone.localdate(),
    }
    
    return render(request, 'SchoolNowMgt/parent_academics_subdashboard.html', context)


@unified_login_required
def parent_payments_dashboard(request):
    """
    Parent subdashboard: View payment status, history, and invoices.
    
    Access Control: Parents only
    
    Displays:
    - Outstanding balance cards (per child) with Make Payment buttons
    - Payment history table (all children): Child | Amount | Date | Method | Transaction ID
    - Invoices table: Invoice # | Term | Amount Due | Amount Paid | Due Date | Status
    - Payment methods reference guide
    
    Uses existing Invoice and FeePayment models
    
    Renders: SchoolNowMgt/parent_payments_subdashboard.html
    """
    if request.user.role != 'parent':
        if request.user.role == 'admin':
            return redirect('SchoolNowMgt:dashboard')
        elif request.user.role == 'teacher':
            return redirect('teacher:dashboard')
        else:
            return redirect('auth:unified_login')
    
    # Get all children
    all_children = Student.objects.filter(
        parent_user=request.user,
        status='active'
    ).select_related('class_grade', 'class_grade__school').order_by('first_name')
    
    # Get payments for all children
    children_ids = all_children.values_list('id', flat=True)
    
    payments = FeePayment.objects.filter(
        student_id__in=children_ids
    ).select_related('student', 'student__class_grade', 'fee_structure').order_by('-payment_date')
    
    # Get invoices for all children (using FeePayment records as invoices)
    invoices = payments.order_by('-payment_date')[:20]
    
    # Build payment summary per child (outstanding balance)
    from django.db.models import Sum
    payments_by_child = {}
    outstanding_total = 0
    
    for child in all_children:
        child_payments = payments.filter(student=child)
        total_paid = child_payments.aggregate(total=Sum('amount_paid'))['total'] or 0
        
        # Get most recent outstanding balance
        most_recent_payment = child_payments.first()
        outstanding = most_recent_payment.balance_after if most_recent_payment else 0
        
        payments_by_child[child] = {
            'payments': child_payments,
            'total_paid': total_paid,
            'outstanding': outstanding,
            'status': 'Paid' if outstanding <= 0 else ('Overdue' if outstanding > 0 else 'Pending')
        }
        outstanding_total += outstanding
    
    # Payment methods reference
    payment_methods = [
        {'name': 'Cash', 'icon': 'payments', 'description': 'Direct payment at school office'},
        {'name': 'MTN Mobile Money', 'icon': 'phone_iphone', 'description': 'Pay via MTN service'},
        {'name': 'Airtel Money', 'icon': 'phone_iphone', 'description': 'Pay via Airtel service'},
        {'name': 'Bank Transfer', 'icon': 'account_balance', 'description': 'Transfer to school bank account'},
    ]
    
    context = {
        'all_children': all_children,
        'payments_by_child': payments_by_child,
        'recent_payments': payments[:10],
        'invoices': invoices,
        'total_outstanding': outstanding_total,
        'payment_methods': payment_methods,
        'today': timezone.localdate(),
    }
    
    return render(request, 'SchoolNowMgt/parent_payments_subdashboard.html', context)
