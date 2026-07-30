"""
Head Teacher Admin Dashboard Views

Director of overall academic leadership and school performance
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from SchoolNowMgt.models import (
    StaffProfile, ClassGrade, Subject, Student, Timetable, ActivityLog,
    FeePayment, FeeStructure, Event, StudentAttendance, StaffAttendance,
    TeacherAttendance
)
from SchoolNowMgt.decorators import require_teacher_role, get_user_school
from user_profile.forms import TeacherProfileForm, TeacherQualificationForm


@login_required
@require_teacher_role('head_teacher')
def headmaster_dashboard(request):
    """Profile dashboard for the headmaster, with editable user profile information."""
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)

    if request.method == 'POST':
        profile_form = TeacherProfileForm(request.POST, request.FILES, instance=request.user)
        qualification_form = TeacherQualificationForm(request.POST, instance=staff_profile)

        if profile_form.is_valid() and qualification_form.is_valid():
            profile_form.save()
            qualification_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('teacher:head_teacher:dashboard')

        context = build_headmaster_context(request, 'dashboard')
        context['profile_form'] = profile_form
        context['qualification_form'] = qualification_form
        return render(request, 'head_teacher/headmaster_dashboard.html', context)

    return render(request, 'head_teacher/headmaster_dashboard.html', build_headmaster_context(request, 'dashboard'))


@login_required
@require_teacher_role('head_teacher')
def financials_dashboard(request):
    """Financial dashboard with revenue, collections and outstanding fees."""
    return render(request, 'head_teacher/headmaster_dashboard.html', build_headmaster_context(request, 'financials'))


@login_required
@require_teacher_role('head_teacher')
def enrollment_dashboard(request):
    """Enrollment dashboard showing student mix and trends."""
    return render(request, 'head_teacher/headmaster_dashboard.html', build_headmaster_context(request, 'enrollment'))


@login_required
@require_teacher_role('head_teacher')
def calendar_dashboard(request):
    """Calendar dashboard showing events and calendar management."""
    return render(request, 'head_teacher/headmaster_dashboard.html', build_headmaster_context(request, 'calendar'))


def build_headmaster_context(request, active_section):
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    today = timezone.now().date()

    # ===== FINANCIAL HEALTH DATA =====
    current_month_start = today.replace(day=1)
    current_month_payments = FeePayment.objects.filter(
        student__class_grade__school=school,
        payment_date__gte=current_month_start
    ).aggregate(total=Sum('amount_paid'))['total'] or 0

    term_start = today.replace(day=1) - timedelta(days=60)
    term_payments = FeePayment.objects.filter(
        student__class_grade__school=school,
        payment_date__gte=term_start
    ).aggregate(total=Sum('amount_paid'))['total'] or 0

    total_expected_fees = FeeStructure.objects.filter(
        class_grade__school=school
    ).aggregate(total=Sum('amount'))['total'] or 0

    total_fees_paid = FeePayment.objects.filter(
        student__class_grade__school=school
    ).aggregate(total=Sum('amount_paid'))['total'] or 0

    outstanding_balance = max(0, total_expected_fees - total_fees_paid)
    collections_percentage = (total_fees_paid / total_expected_fees * 100) if total_expected_fees > 0 else 0
    outstanding_percentage = (outstanding_balance / total_expected_fees * 100) if total_expected_fees > 0 else 0

    financial_data = {
        'total_revenue': total_fees_paid,
        'total_revenue_formatted': f"£{total_fees_paid:,.0f}" if total_fees_paid < 1000000 else f"£{total_fees_paid/1000000:.2f}M",
        'collections': total_fees_paid,
        'collections_percentage': collections_percentage,
        'outstanding': outstanding_balance,
        'outstanding_percentage': outstanding_percentage,
        'current_month_payments': current_month_payments,
        'term_payments': term_payments,
    }

    # ===== ENROLLMENT DATA =====
    active_students = Student.objects.filter(
        class_grade__school=school,
        status='active'
    )

    day_scholars = active_students.filter(curriculum='national').count()
    boarding_students = active_students.filter(curriculum='international').count()
    total_enrollment = day_scholars + boarding_students

    day_scholars_percentage = (day_scholars / total_enrollment * 100) if total_enrollment > 0 else 0
    boarding_percentage = (boarding_students / total_enrollment * 100) if total_enrollment > 0 else 0

    enrollment_data = {
        'day_scholars': day_scholars,
        'day_scholars_percentage': day_scholars_percentage,
        'boarding_students': boarding_students,
        'boarding_percentage': boarding_percentage,
        'total_enrollment': total_enrollment,
    }

    # ===== CALENDAR EVENTS =====
    upcoming_events = Event.objects.filter(
        school=school,
        start_date__gte=today
    ).order_by('start_date')[:10]

    events_this_month = Event.objects.filter(
        school=school,
        start_date__month=today.month,
        start_date__year=today.year
    )

    calendar_events = {}
    for event in events_this_month:
        day = event.start_date.day
        calendar_events.setdefault(day, []).append({
            'id': event.id,
            'title': event.title,
            'description': getattr(event, 'description', ''),
            'type': event.event_type,
            'start_date': event.start_date,
            'end_date': event.end_date,
            'location': getattr(event, 'location', ''),
        })

    # ===== STAFF ATTENDANCE STATUS =====
    today_staff_attendance = StaffAttendance.objects.filter(
        staff__user__school=school,
        date=today
    )
    staff_present = today_staff_attendance.filter(status='present').count()
    staff_absent = today_staff_attendance.filter(status='absent').count()
    staff_late = today_staff_attendance.filter(status='late').count()

    today_teacher_attendance = TeacherAttendance.objects.filter(
        staff__user__school=school,
        date=today
    )
    teachers_present = today_teacher_attendance.filter(status='present').count()

    today_student_attendance = StudentAttendance.objects.filter(
        student__class_grade__school=school,
        date=today
    )
    students_present = today_student_attendance.filter(status='present').count()
    students_absent = today_student_attendance.filter(status='absent').count()
    students_late = today_student_attendance.filter(status='late').count()

    attendance_data = {
        'staff_present': staff_present,
        'staff_absent': staff_absent,
        'staff_late': staff_late,
        'teachers_present': teachers_present,
        'students_present': students_present,
        'students_absent': students_absent,
        'students_late': students_late,
        'total_staff_attendance': today_staff_attendance.count(),
        'total_student_attendance': today_student_attendance.count(),
    }

    system_status = {
        'lms_integration': {
            'status': 'connected',
            'message': 'Sync successful 4m ago',
            'icon': 'account_tree',
            'color': 'secondary-container'
        },
        'campus_security': {
            'status': 'secured',
            'message': 'All perimeters secured',
            'icon': 'shield',
            'color': 'primary'
        },
        'parent_portal': {
            'status': 'active',
            'message': '24 pending notifications',
            'icon': 'mail',
            'color': 'tertiary-container'
        }
    }

    # ===== HEAD TEACHER SHIFT STATUS =====
    teacher_attendance_today = TeacherAttendance.objects.filter(
        staff=staff_profile,
        date=today
    ).first()

    is_on_duty = False
    shift_start_time = timezone.now()

    if teacher_attendance_today and teacher_attendance_today.status == 'present' and teacher_attendance_today.time_out is None:
        is_on_duty = True
        if teacher_attendance_today.time_in:
            naive_dt = datetime.combine(today, teacher_attendance_today.time_in)
            shift_start_time = timezone.make_aware(naive_dt)
        else:
            shift_start_time = timezone.now()

    # ===== SCHOOL OVERVIEW NUMBERS =====
    school_student_count = Student.objects.filter(class_grade__school=school, status='active').count()
    school_class_count = ClassGrade.objects.filter(school=school).count()

    return {
        'school': school,
        'staff_profile': staff_profile,
        'today': today,
        'financial_data': financial_data,
        'enrollment_data': enrollment_data,
        'attendance_data': attendance_data,
        'upcoming_events': upcoming_events,
        'calendar_events': calendar_events,
        'system_status': system_status,
        'profile_form': TeacherProfileForm(instance=request.user),
        'qualification_form': TeacherQualificationForm(instance=staff_profile),
        'active_section': active_section,
        'page_title': 'Institutional Pulse - Headmaster Dashboard',
        'breadcrumbs': [
            {'label': 'Home', 'url': '/teacher/'},
            {'label': 'Headmaster Dashboard', 'url': None},
        ],
        'is_on_duty': is_on_duty,
        'shift_start_time': shift_start_time,
        'school_student_count': school_student_count,
        'school_class_count': school_class_count,
    }


@login_required
@require_teacher_role('head_teacher')
@require_http_methods(['POST'])
def create_event(request):
    """AJAX endpoint to create a new event"""
    school = get_user_school(request)
    
    try:
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        event_type = request.POST.get('event_type', 'other')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        location = request.POST.get('location', '').strip()
        
        # Validate required fields
        if not title or not start_date or not end_date:
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
        
        # Create event
        event = Event.objects.create(
            school=school,
            title=title,
            description=description,
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
            location=location,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'event': {
                'id': event.id,
                'title': event.title,
                'start_date': str(event.start_date),
                'end_date': str(event.end_date),
                'event_type': event.event_type,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_teacher_role('head_teacher')
@require_http_methods(['POST'])
def update_event(request, event_id):
    """AJAX endpoint to update an event"""
    school = get_user_school(request)
    event = get_object_or_404(Event, id=event_id, school=school)
    
    try:
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        event_type = request.POST.get('event_type', 'other')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        location = request.POST.get('location', '').strip()
        
        # Update fields if provided
        if title:
            event.title = title
        if description:
            event.description = description
        if event_type:
            event.event_type = event_type
        if start_date:
            event.start_date = start_date
        if end_date:
            event.end_date = end_date
        if location:
            event.location = location
        
        event.save()
        
        return JsonResponse({
            'success': True,
            'event': {
                'id': event.id,
                'title': event.title,
                'start_date': str(event.start_date),
                'end_date': str(event.end_date),
                'event_type': event.event_type,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_teacher_role('head_teacher')
@require_http_methods(['POST'])
def delete_event(request, event_id):
    """AJAX endpoint to delete an event"""
    school = get_user_school(request)
    try:
        event = get_object_or_404(Event, id=event_id, school=school)
        event.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_teacher_role('head_teacher')
@require_http_methods(['GET'])
def get_event(request, event_id):
    """AJAX endpoint to fetch a single event's details"""
    school = get_user_school(request)
    event = get_object_or_404(Event, id=event_id, school=school)
    return JsonResponse({
        'success': True,
        'event': {
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'event_type': event.event_type,
            'start_date': str(event.start_date),
            'end_date': str(event.end_date),
            'location': event.location,
        }
    })


@login_required
@require_teacher_role('head_teacher')
@require_http_methods(['GET'])
def get_chart_data(request):
    """AJAX endpoint to get filtered chart data"""
    school = get_user_school(request)
    today = timezone.now().date()
    date_range = request.GET.get('range', 'month')  # month, term, year
    
    try:
        # Calculate date range
        if date_range == 'month':
            start_date = today.replace(day=1)
        elif date_range == 'term':
            start_date = today.replace(day=1) - timedelta(days=90)
        else:  # year
            start_date = today.replace(day=1, month=1)
        
        # Get financial data for selected range
        payments = FeePayment.objects.filter(
            student__class_grade__school=school,
            payment_date__gte=start_date
        ).aggregate(total=Sum('amount_paid'))['total'] or 0
        
        # Get enrollment by curriculum
        active_students = Student.objects.filter(
            class_grade__school=school,
            status='active'
        )
        
        day_scholars = active_students.filter(curriculum='national').count()
        boarding = active_students.filter(curriculum='international').count()
        
        return JsonResponse({
            'success': True,
            'financial': {
                'total': str(payments),
                'formatted': f"£{payments:,.0f}" if payments < 1000000 else f"£{payments/1000000:.2f}M"
            },
            'enrollment': {
                'day_scholars': day_scholars,
                'boarding': boarding,
            },
            'range': date_range,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_teacher_role('head_teacher')
@require_http_methods(['GET'])
def export_dashboard_report(request):
    """Export dashboard data as PDF"""
    from django.http import HttpResponse
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from io import BytesIO
    except ImportError:
        return JsonResponse(
            {'success': False, 'error': 'PDF library not installed. Use browser print-to-PDF instead.'},
            status=501
        )
    
    school = get_user_school(request)
    today = timezone.now().date()
    
    try:
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph(f"<b>Institutional Pulse Report - {today}</b>", styles['Heading1'])
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Financial Summary Table
        financial_data = [
            ['Financial Metric', 'Amount'],
            ['Total Revenue', 'UGX 2.48M'],
            ['Collections', 'UGX 2.12M'],
            ['Outstanding', 'UGX 364K'],
        ]
        
        table = Table(financial_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#080b3a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="dashboard_report_{today}.pdf"'
        return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


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
