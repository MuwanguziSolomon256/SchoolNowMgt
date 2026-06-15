"""
Admin views for shift management and reporting.

Provides admin dashboard for real-time teacher shift status,
historical shift data, manual editing capabilities, and reporting.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.db.models import Q, Count, Sum, Avg, F, ExpressionWrapper, fields
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime, timedelta, time
import csv

from SchoolNowMgt.models import (
    TeacherAttendance, BreakSession, StaffProfile, CustomUser, School
)


def admin_required(view_func):
    """Decorator to ensure only admin users can access views."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('auth:unified_login')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@admin_required
def shift_dashboard(request):
    """
    Main admin shift dashboard showing real-time status of all teachers.
    
    Context:
        - active_teachers: Teachers currently on duty
        - on_break_teachers: Teachers currently on break
        - clocked_out_teachers: Teachers who have clocked out today
        - not_clocked_in: Teachers who haven't clocked in yet
        - total_teachers: Total teachers in the school
        - school: User's school
    """
    school = request.user.school
    today = timezone.now().date()
    
    # Get all teachers in the school
    all_teachers = StaffProfile.objects.filter(
        user__role='teacher',
        user__school=school
    ).select_related('user').prefetch_related('teacher_attendance_records')
    
    # Get today's attendance records
    today_attendance = TeacherAttendance.objects.filter(
        staff__user__school=school,
        date=today
    ).select_related('staff__user').prefetch_related('break_sessions')
    
    # Categorize teachers
    active_teachers = []
    on_break_teachers = []
    clocked_out_teachers = []
    
    for attendance in today_attendance:
        if attendance.time_in and not attendance.time_out:
            # Currently on duty
            active_teachers.append({
                'attendance': attendance,
                'teacher': attendance.staff,
                'shift_elapsed': calculate_elapsed_time(attendance.date, attendance.time_in),
                'break_count': attendance.break_count,
                'is_on_break': BreakSession.objects.filter(
                    teacher_attendance=attendance,
                    break_out_time__isnull=True
                ).exists()
            })
        elif attendance.time_out:
            # Clocked out
            clocked_out_teachers.append({
                'attendance': attendance,
                'teacher': attendance.staff,
                'shift_duration': attendance.get_shift_hours(),
                'break_count': attendance.break_count,
            })
    
    # Check for on break
    on_break_teachers = [t for t in active_teachers if t['is_on_break']]
    active_teachers = [t for t in active_teachers if not t['is_on_break']]
    
    # Teachers not clocked in
    clocked_in_ids = set(today_attendance.values_list('staff_id', flat=True))
    not_clocked_in = all_teachers.exclude(id__in=clocked_in_ids)
    
    context = {
        'school': school,
        'today': today,
        'active_teachers': active_teachers,
        'on_break_teachers': on_break_teachers,
        'clocked_out_teachers': clocked_out_teachers,
        'not_clocked_in': not_clocked_in,
        'total_teachers': all_teachers.count(),
        'current_time': timezone.now().time(),
    }
    
    return render(request, 'admin/shift_dashboard.html', context)


@login_required
@admin_required
def shift_history(request):
    """
    Historical view of teacher shifts with filtering and search.
    
    Allows admin to:
    - View past shift records
    - Filter by date range, teacher, school
    - Edit shift times
    - Export shift data to CSV
    
    Query params:
        - teacher: Filter by teacher ID
        - date_from: Start date (YYYY-MM-DD)
        - date_to: End date (YYYY-MM-DD)
        - status: Filter by attendance status
        - search: Search teacher name/employee ID
        - page: Pagination
    """
    school = request.user.school
    
    # Base queryset
    shifts = TeacherAttendance.objects.filter(
        staff__user__school=school
    ).select_related(
        'staff__user', 'marked_by'
    ).prefetch_related(
        'break_sessions'
    ).order_by('-date', '-created_at')
    
    # Apply filters
    teacher_id = request.GET.get('teacher')
    if teacher_id:
        shifts = shifts.filter(staff_id=teacher_id)
    
    date_from = request.GET.get('date_from')
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            shifts = shifts.filter(date__gte=date_from)
        except ValueError:
            pass
    
    date_to = request.GET.get('date_to')
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            shifts = shifts.filter(date__lte=date_to)
        except ValueError:
            pass
    
    status = request.GET.get('status')
    if status:
        shifts = shifts.filter(status=status)
    
    search = request.GET.get('search')
    if search:
        shifts = shifts.filter(
            Q(staff__user__first_name__icontains=search) |
            Q(staff__user__last_name__icontains=search) |
            Q(staff__employee_id__icontains=search)
        )
    
    # Check for export request
    if request.GET.get('export') == 'csv':
        return export_shift_data_csv(shifts)
    
    # Pagination
    paginator = Paginator(shifts, 30)
    page_num = request.GET.get('page', 1)
    try:
        shifts_page = paginator.page(page_num)
    except (EmptyPage, PageNotAnInteger):
        shifts_page = paginator.page(1)
    
    # Get all teachers for filter dropdown
    all_teachers = StaffProfile.objects.filter(
        user__role='teacher',
        user__school=school
    ).select_related('user').order_by('user__last_name', 'user__first_name')
    
    context = {
        'shifts': shifts_page,
        'all_teachers': all_teachers,
        'school': school,
        'filter_teacher': teacher_id,
        'filter_date_from': date_from,
        'filter_date_to': date_to,
        'filter_status': status,
        'search_query': search,
        'total_shifts': paginator.count,
    }
    
    return render(request, 'admin/shift_history.html', context)


@login_required
@admin_required
@require_POST
def edit_shift_times(request, attendance_id):
    """
    AJAX endpoint to edit teacher shift times.
    
    Admin can manually adjust:
    - time_in
    - time_out
    - break_count (optional)
    
    Request body:
        {
            'time_in': 'HH:MM',
            'time_out': 'HH:MM',
            'reason': str  # Reason for modification
        }
    
    Returns:
        {
            'success': bool,
            'message': str,
            'updated_shift': {...} (on success)
        }
    """
    import json
    
    try:
        attendance = TeacherAttendance.objects.get(
            id=attendance_id,
            staff__user__school=request.user.school
        )
    except TeacherAttendance.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Shift record not found'}, status=404)
    
    try:
        body = json.loads(request.body)
        time_in_str = body.get('time_in')
        time_out_str = body.get('time_out')
        reason = body.get('reason', '')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid request body'}, status=400)
    
    # Validate and parse times
    try:
        if time_in_str:
            time_in = datetime.strptime(time_in_str, '%H:%M').time()
        else:
            time_in = attendance.time_in
        
        if time_out_str:
            time_out = datetime.strptime(time_out_str, '%H:%M').time()
        else:
            time_out = attendance.time_out
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid time format. Use HH:MM'}, status=400)
    
    # Validate logic: time_in must be before time_out
    if time_in and time_out and time_in >= time_out:
        return JsonResponse({
            'success': False,
            'error': 'Clock in time must be before clock out time'
        }, status=400)
    
    try:
        # Update shift times
        attendance.time_in = time_in
        attendance.time_out = time_out
        
        # Add reason to notes
        if reason:
            attendance.reason = (attendance.reason or '') + f"\n[ADMIN EDIT] {reason}"
        
        attendance.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Shift times updated successfully',
            'updated_shift': {
                'id': attendance.id,
                'date': attendance.date.isoformat(),
                'time_in': time_in.strftime('%H:%M') if time_in else None,
                'time_out': time_out.strftime('%H:%M') if time_out else None,
                'shift_duration': attendance.get_shift_hours(),
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to update shift: {str(e)}'
        }, status=500)


@login_required
@admin_required
def shift_report(request):
    """
    Generate shift reports with analytics.
    
    Available reports:
    - Daily summary: Date → Teachers, hours worked, avg shift time
    - Weekly summary: Week → Aggregated data
    - Monthly summary: Month → Aggregated data
    - Punctuality: Late arrivals, early departures
    - Break analysis: Excessive breaks, patterns
    
    Query params:
        - report_type: 'daily', 'weekly', 'monthly', 'punctuality', 'breaks'
        - date_from, date_to: Date range
        - teacher: Specific teacher (optional)
        - export: 'csv', 'json' (optional)
    """
    school = request.user.school
    report_type = request.GET.get('report_type', 'daily')
    date_from_str = request.GET.get('date_from')
    date_to_str = request.GET.get('date_to')
    
    # Parse dates
    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except ValueError:
            date_from = timezone.now().date() - timedelta(days=30)
    else:
        date_from = timezone.now().date() - timedelta(days=30)
    
    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            date_to = timezone.now().date()
    else:
        date_to = timezone.now().date()
    
    # Base queryset
    shifts = TeacherAttendance.objects.filter(
        staff__user__school=school,
        date__gte=date_from,
        date__lte=date_to
    ).select_related('staff__user')
    
    # Filter by teacher if specified
    teacher_id = request.GET.get('teacher')
    if teacher_id:
        shifts = shifts.filter(staff_id=teacher_id)
    
    # Generate report data based on type
    if report_type == 'daily':
        report_data = generate_daily_report(shifts)
    elif report_type == 'weekly':
        report_data = generate_weekly_report(shifts)
    elif report_type == 'monthly':
        report_data = generate_monthly_report(shifts)
    elif report_type == 'punctuality':
        report_data = generate_punctuality_report(shifts)
    elif report_type == 'breaks':
        report_data = generate_break_analysis_report(shifts)
    else:
        report_data = generate_daily_report(shifts)
    
    # Handle export
    if request.GET.get('export') == 'csv':
        return export_report_csv(report_data, report_type)
    
    context = {
        'report_type': report_type,
        'report_data': report_data,
        'date_from': date_from,
        'date_to': date_to,
        'school': school,
    }
    
    return render(request, 'admin/shift_report.html', context)


# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def calculate_elapsed_time(date, start_time):
    """Calculate elapsed time from start_time until now."""
    start_datetime = datetime.combine(date, start_time)
    current_datetime = datetime.combine(
        timezone.now().date(),
        timezone.now().time()
    )
    delta = current_datetime - start_datetime
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}h {minutes}m"


def generate_daily_report(shifts):
    """Generate daily shift summary report."""
    report = []
    
    dates = sorted(set(shifts.values_list('date', flat=True)))
    
    for date in dates:
        day_shifts = shifts.filter(date=date)
        
        worked_count = day_shifts.filter(time_in__isnull=False).count()
        absent_count = day_shifts.filter(status='absent').count()
        
        total_minutes = 0
        total_breaks = 0
        for shift in day_shifts.filter(time_in__isnull=False, time_out__isnull=False):
            duration = shift.get_shift_duration()
            if duration:
                total_minutes += duration
            total_breaks += shift.break_count
        
        avg_hours = (total_minutes / worked_count / 60) if worked_count > 0 else 0
        
        report.append({
            'date': date,
            'teachers_worked': worked_count,
            'teachers_absent': absent_count,
            'total_hours': total_minutes / 60,
            'avg_hours_per_teacher': avg_hours,
            'total_breaks': total_breaks,
        })
    
    return report


def generate_weekly_report(shifts):
    """Generate weekly shift summary report."""
    report = []
    
    current_date = shifts.aggregate(min_date=Count('date'))
    # Implementation: group by week
    return report


def generate_monthly_report(shifts):
    """Generate monthly shift summary report."""
    return generate_daily_report(shifts)  # For now, similar to daily


def generate_punctuality_report(shifts):
    """Generate punctuality report (late arrivals, early departures)."""
    report = []
    
    # Assuming work starts at 8:00 AM
    WORK_START_TIME = time(8, 0)
    WORK_END_TIME = time(16, 30)
    
    for shift in shifts.filter(time_in__isnull=False):
        if shift.time_in > WORK_START_TIME:
            minutes_late = int((datetime.combine(shift.date, shift.time_in) -
                               datetime.combine(shift.date, WORK_START_TIME)).total_seconds() / 60)
            report.append({
                'teacher': shift.staff.user.get_full_name(),
                'date': shift.date,
                'type': 'late_arrival',
                'time': shift.time_in,
                'minutes_late': minutes_late,
            })
        
        if shift.time_out and shift.time_out < WORK_END_TIME:
            minutes_early = int((datetime.combine(shift.date, WORK_END_TIME) -
                                datetime.combine(shift.date, shift.time_out)).total_seconds() / 60)
            report.append({
                'teacher': shift.staff.user.get_full_name(),
                'date': shift.date,
                'type': 'early_departure',
                'time': shift.time_out,
                'minutes_early': minutes_early,
            })
    
    return report


def generate_break_analysis_report(shifts):
    """Generate report analyzing break patterns."""
    report = []
    
    for shift in shifts:
        if shift.break_count > 3:
            report.append({
                'teacher': shift.staff.user.get_full_name(),
                'date': shift.date,
                'type': 'excessive_breaks',
                'break_count': shift.break_count,
            })
        
        if shift.total_break_duration > 120:  # More than 2 hours
            report.append({
                'teacher': shift.staff.user.get_full_name(),
                'date': shift.date,
                'type': 'excessive_break_time',
                'total_break_mins': shift.total_break_duration,
            })
    
    return report


def export_shift_data_csv(shifts):
    """Export shift data to CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="shift_data.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Teacher Name', 'Employee ID', 'Date', 'Status',
        'Clock In', 'Clock Out', 'Breaks', 'Total Hours'
    ])
    
    for shift in shifts:
        shift_hours = shift.get_shift_duration() / 60 if shift.get_shift_duration() else 0
        writer.writerow([
            shift.staff.user.get_full_name(),
            shift.staff.employee_id,
            shift.date.isoformat(),
            shift.status,
            shift.time_in.strftime('%H:%M') if shift.time_in else '',
            shift.time_out.strftime('%H:%M') if shift.time_out else '',
            shift.break_count,
            f"{shift_hours:.1f}h"
        ])
    
    return response


def export_report_csv(report_data, report_type):
    """Export report to CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="shift_report_{report_type}.csv"'
    
    writer = csv.writer(response)
    
    if report_type in ('daily', 'monthly'):
        writer.writerow(['Date', 'Teachers Worked', 'Teachers Absent', 'Total Hours', 'Avg Hours/Teacher'])
        for row in report_data:
            writer.writerow([
                row['date'], row['teachers_worked'], row['teachers_absent'],
                f"{row['total_hours']:.1f}", f"{row['avg_hours_per_teacher']:.1f}"
            ])
    elif report_type == 'punctuality':
        writer.writerow(['Teacher', 'Date', 'Type', 'Time', 'Minutes'])
        for row in report_data:
            writer.writerow([
                row['teacher'], row['date'], row['type'],
                row['time'], row.get('minutes_late', row.get('minutes_early', ''))
            ])
    elif report_type == 'breaks':
        writer.writerow(['Teacher', 'Date', 'Issue', 'Details'])
        for row in report_data:
            details = row.get('break_count', row.get('total_break_mins', ''))
            writer.writerow([row['teacher'], row['date'], row['type'], details])
    
    return response
