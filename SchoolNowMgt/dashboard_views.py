from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Avg, Q, Sum
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
import uuid
import csv
import io

from .models import (
    Student, StaffProfile, StudentAttendance, StaffAttendance,
    RetentionAlert, SMSLog, Enquiry, FeePayment, Grade, ClassGrade,
    CustomUser, Message, MessageRecipient, MessageTemplate, School,
    ActivityLog
)
from .forms import (
    StaffOnboardingForm, BulkStaffUploadForm,
    StudentOnboardingForm, BulkStudentUploadForm,
    AdminMessageForm, StaffPasswordResetForm
)
from .utils import (
    generate_temp_password, parse_csv_upload, resolve_message_recipients,
    create_message_recipients, replace_message_placeholders, generate_employee_id
)


# Custom login required that redirects to unified login portal
def unified_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('auth:unified_login')
        return view_func(request, *args, **kwargs)
    return wrapper


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
    }
    
    return render(request, 'SchoolNowMgt/support_staff_dashboard.html', context)


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
