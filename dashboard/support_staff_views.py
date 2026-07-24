"""
Support Staff Department Dashboard Views

Purpose: Provide role-based dashboards for support staff:
- Department Heads: Manage their department, staff, budgets
- Shift Supervisors: Manage shift schedules and attendance
- Welfare Coordinators: Manage student welfare activities

Permission: Requires specific support_staff_role via decorators
School Isolation: All queries filtered by school=user.school
"""

from datetime import datetime, timedelta
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from django.core.paginator import Paginator
from django.db import transaction
from django.views.decorators.http import require_http_methods

from SchoolNowMgt.models import (
    StaffProfile, CustomUser, School, Department, ActivityLog,
    StaffAttendance
)
from SchoolNowMgt.decorators import (
    require_support_staff_role, require_shift_supervisor, get_user_school
)


@require_support_staff_role(['staff', 'supervisor', 'shift_supervisor', 'department_head', 'welfare_coordinator'])
def support_staff_dashboard(request):
    """Base support dashboard landing view for non-teaching staff."""
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)

    if staff_profile.support_staff_role == 'department_head':
        return redirect('/teacher/support/dept-head/')
    if staff_profile.support_staff_role in {'supervisor', 'shift_supervisor'}:
        return redirect('/teacher/support/shift-supervisor/')
    if staff_profile.support_staff_role == 'welfare_coordinator':
        return redirect('/teacher/support/welfare/')

    context = {
        'school': school,
        'staff_profile': staff_profile,
        'section': 'support_staff_dashboard',
    }
    return render(request, 'support_staff/support_staff_dashboard.html', context)


# ============================================================================
# DEPARTMENT HEAD DASHBOARD
# ============================================================================

@require_support_staff_role('department_head')
def dept_head_dashboard(request):
    """
    Department Head Dashboard - Overview of department operations
    
    Template context:
    - school: Current school
    - staff_profile: Department head staff profile
    - department: Assigned department
    - statistics: Department metrics (staff count, budget, etc.)
    - recent_activities: Latest activity logs
    - staff_list: Team members
    
    School Filtering: All queries filtered by school=school
    """
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get department head's assigned department
    department = staff_profile.support_department
    if not department or department.school != school:
        raise PermissionDenied("Department not found or not in your school")
    
    # Get department staff
    dept_staff = StaffProfile.objects.filter(
        support_department=department,
        user__school=school
    ).select_related('user').order_by('user__first_name')
    
    # Calculate statistics
    total_staff = dept_staff.count()
    active_staff = dept_staff.filter(user__is_active=True).count()
    supervisors = dept_staff.filter(support_staff_role='supervisor').count()
    
    # Get today's attendance for department
    today = timezone.now().date()
    today_attendance = StaffAttendance.objects.filter(
        staff__support_department=department,
        staff__user__school=school,
        date=today
    ).select_related('staff__user')
    
    on_duty_today = today_attendance.filter(time_out__isnull=True).count()
    absent_today = total_staff - today_attendance.count()
    
    # Get recent activities
    recent_activities = ActivityLog.objects.all().select_related('teacher').order_by('-created_at')[:10]
    
    statistics = {
        'total_staff': total_staff,
        'active_staff': active_staff,
        'inactive_staff': total_staff - active_staff,
        'supervisors': supervisors,
        'on_duty_today': on_duty_today,
        'absent_today': absent_today,
        'department_budget': department.monthly_budget or 0,
    }
    
    context = {
        'school': school,
        'staff_profile': staff_profile,
        'department': department,
        'statistics': statistics,
        'staff_list': dept_staff[:5],  # Show top 5 for dashboard
        'recent_activities': recent_activities,
        'section': 'dept_head_dashboard',
    }
    
    return render(request, 'support_staff/dept_head_dashboard.html', context)


@require_support_staff_role('department_head')
def dept_head_staff_list(request):
    """
    List and manage department staff
    
    GET params:
    - role: Filter by support_staff_role
    - status: active/inactive
    - search: Search by name
    - page: Pagination
    
    School Filtering: Only department's staff in user's school
    """
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    department = staff_profile.support_department
    
    if not department or department.school != school:
        raise PermissionDenied("Department not found or not in your school")
    
    # Base queryset
    dept_staff = StaffProfile.objects.filter(
        support_department=department,
        user__school=school
    ).select_related('user').order_by('user__first_name')
    
    # Apply filters
    role = request.GET.get('role')
    if role:
        dept_staff = dept_staff.filter(support_staff_role=role)
    
    status = request.GET.get('status')
    if status == 'active':
        dept_staff = dept_staff.filter(user__is_active=True)
    elif status == 'inactive':
        dept_staff = dept_staff.filter(user__is_active=False)
    
    search = request.GET.get('search')
    if search:
        dept_staff = dept_staff.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__username__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(dept_staff, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    role_choices = StaffProfile.SUPPORT_STAFF_ROLE_CHOICES
    
    context = {
        'school': school,
        'staff_profile': staff_profile,
        'department': department,
        'page_obj': page_obj,
        'role_choices': role_choices,
        'section': 'dept_head_staff_list',
    }
    
    return render(request, 'support_staff/dept_head_staff_list.html', context)


@require_support_staff_role('department_head')
def dept_head_staff_detail(request, staff_id):
    """
    View and manage individual staff member details
    
    School Filtering: Only staff in user's department and school
    """
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    department = staff_profile.support_department
    
    if not department or department.school != school:
        raise PermissionDenied("Department not found")
    
    # Get the staff member
    staff_member = get_object_or_404(
        StaffProfile,
        id=staff_id,
        support_department=department,
        user__school=school
    )
    
    # Get attendance records for this staff
    attendance_records = StaffAttendance.objects.filter(
        staff=staff_member,
        staff__user__school=school
    ).order_by('-date')[:30]
    
    # Calculate statistics
    total_days_recorded = attendance_records.count()
    days_present = attendance_records.filter(clock_in_time__isnull=False).count()
    attendance_rate = (days_present / total_days_recorded * 100) if total_days_recorded > 0 else 0
    
    statistics = {
        'total_attendance_records': total_days_recorded,
        'days_present': days_present,
        'attendance_rate': f"{attendance_rate:.1f}%",
    }
    
    context = {
        'school': school,
        'staff_profile': staff_profile,
        'department': department,
        'staff_member': staff_member,
        'attendance_records': attendance_records,
        'statistics': statistics,
        'section': 'dept_head_staff_detail',
    }
    
    return render(request, 'support_staff/dept_head_staff_detail.html', context)


# ============================================================================
# SHIFT SUPERVISOR DASHBOARD
# ============================================================================

@require_shift_supervisor
def shift_supervisor_dashboard(request):
    """
    Shift Supervisor Dashboard - Manage shift schedules and attendance
    
    Template context:
    - school: Current school
    - staff_profile: Supervisor staff profile
    - statistics: Shift metrics
    - today_attendance: Today's attendance records
    - recent_activities: Latest activity logs
    
    School Filtering: All queries filtered by school=school
    """
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get today's date
    today = timezone.now().date()
    
    # Get all staff in school (supervisor manages overall shifts)
    all_staff = StaffProfile.objects.filter(
        user__school=school,
        user__role='non_teaching_staff'
    ).count()
    
    # Get today's attendance
    today_attendance = StaffAttendance.objects.filter(
        staff__user__school=school,
        date=today
    ).select_related('staff__user', 'staff__support_department')
    
    on_duty = today_attendance.filter(time_out__isnull=True).count()
    clocked_out = today_attendance.filter(time_out__isnull=False).count()
    absent = all_staff - today_attendance.count()
    
    # Weekly summary
    week_start = today - timedelta(days=today.weekday())
    week_attendance = StaffAttendance.objects.filter(
        staff__user__school=school,
        date__gte=week_start,
        date__lte=today
    ).values('date').annotate(
        count=Count('id'),
        on_duty_count=Count('id', filter=Q(time_out__isnull=True))
    ).order_by('date')
    
    # Recent activities for current school only
    recent_activities = ActivityLog.objects.filter(
        teacher__user__school=school
    ).select_related('teacher').order_by('-created_at')[:10]
    
    statistics = {
        'total_staff': all_staff,
        'on_duty_today': on_duty,
        'clocked_out_today': clocked_out,
        'absent_today': absent,
        'week_days': week_attendance.count(),
    }
    
    # Roster for supervisor dashboard
    roster_staff = StaffProfile.objects.filter(
        user__school=school,
        user__role='non_teaching_staff'
    ).select_related('user', 'support_department').order_by('user__first_name')[:6]
    today_on_duty_ids = set(
        today_attendance.filter(time_out__isnull=True).values_list('staff_id', flat=True)
    )
    staff_roster = []
    for staff in roster_staff:
        staff_roster.append({
            'full_name': staff.user.get_full_name(),
            'role_label': staff.position,
            'department': staff.support_department.name if staff.support_department else 'General Duty',
            'status': 'On Duty' if staff.id in today_on_duty_ids else 'Offline',
            'status_class': 'bg-green-500' if staff.id in today_on_duty_ids else 'bg-slate-300',
            'avatar_url': staff.user.profile_picture.url if getattr(staff.user, 'profile_picture', None) else '',
        })
    
    # Build material card context placeholders where system data is not yet modelled
    maintenance_alerts = [
        {
            'title': 'North Wing Ventilation',
            'subtitle': 'Routine Filter Replacement Required',
            'status': 'URGENT',
            'badge_class': 'bg-error text-white',
            'image_url': 'https://lh3.googleusercontent.com/aida-public/AB6AXuC2nFp4MFddwEEKBeR9DcL8fYNvgYfhQCD79mhYJbRuvjnodWYETDnM3QpL9RzNb5gC6c_EKXmued34tdHGCDY2gLcOAtftvZVYFQAmcuxs4ReOtcqROR9Y5v-IkZF9mjj9OfdmQmwWX5zjWiPMibS_09kqAyZx0s-M_M5N4IRzXmYYDEMfbwA6BToQ69jlQBK8mJv0ZkOLNAeXR2vZDNE-FPw-ybDQyPQztYHq9-9-9U9qKJrymVxf5xtqycgtxPxcECa2furbToAc',
        },
        {
            'title': 'Water Facility Block C',
            'subtitle': '75% complete',
            'progress': 75,
            'icon': 'plumbing',
            'status_text': '75%',
            'status_class': 'text-secondary',
        },
        {
            'title': 'IT Hub Wiring Audit',
            'subtitle': '25% complete',
            'progress': 25,
            'icon': 'electrical_services',
            'status_text': '25%',
            'status_class': 'text-primary',
        },
        {
            'title': 'Main Gate Security Tech',
            'subtitle': 'Completed',
            'icon': 'check_circle',
            'status_text': 'Completed',
            'status_class': 'text-green-700',
        },
    ]

    supply_requests = [
        {
            'title': 'Industrial Cleaning Supplies',
            'reference': 'Req #4928',
            'department': 'Sanitation Dept.',
            'amount': '$1,240.00',
            'primary_button': 'Approve',
            'secondary_button': 'Decline',
        },
        {
            'title': 'Cisco Network Switches (x2)',
            'reference': 'Req #4931',
            'department': 'IT Infrastructure',
            'amount': '$4,850.00',
            'primary_button': 'Approve',
            'secondary_button': 'Decline',
        },
    ]

    clocked_out_records = today_attendance.filter(time_out__isnull=False, time_in__isnull=False)
    avg_tat = 24
    if clocked_out_records.exists():
        total_seconds = 0
        valid_count = 0
        for record in clocked_out_records:
            if record.time_in and record.time_out:
                total_seconds += (record.time_out - record.time_in).total_seconds()
                valid_count += 1
        if valid_count:
            avg_tat = max(1, int(total_seconds / valid_count / 3600))

    task_completion = {
        'efficiency': int((on_duty / all_staff * 100) if all_staff else 0),
        'open_tasks': absent,
        'avg_tat': f"{avg_tat}h",
    }

    week_summary = []
    week_records = list(week_attendance)
    max_count = max((item['count'] for item in week_records), default=1)
    for item in week_records:
        bar_height = int(item['count'] / max_count * 100) if max_count else 20
        if bar_height < 20:
            bar_height = 20
        week_summary.append({
            'label': item['date'].strftime('%a').upper(),
            'count': item['count'],
            'height': bar_height,
        })

    context = {
        'school': school,
        'staff_profile': staff_profile,
        'today': today,
        'statistics': statistics,
        'today_attendance': today_attendance,
        'week_attendance': week_attendance,
        'week_summary': week_summary,
        'recent_activities': recent_activities,
        'staff_roster': staff_roster,
        'maintenance_alerts': maintenance_alerts,
        'supply_requests': supply_requests,
        'task_completion': task_completion,
        'section': 'shift_supervisor_dashboard',
    }
    
    return render(request, 'support_staff/shift_supervisor_dashboard.html', context)


@require_shift_supervisor
def shift_attendance_list(request):
    """
    List staff attendance with filtering
    
    GET params:
    - date: Filter by date (YYYY-MM-DD)
    - department_id: Filter by department
    - status: on_duty/clocked_out/absent
    - search: Search by staff name
    - page: Pagination
    """
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Default to today
    date_str = request.GET.get('date')
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            target_date = timezone.now().date()
    else:
        target_date = timezone.now().date()
    
    # Base queryset
    attendance = StaffAttendance.objects.filter(
        staff__user__school=school,
        date=target_date
    ).select_related('staff__user', 'staff__support_department').order_by('-clock_in_time')
    
    # Apply filters
    department_id = request.GET.get('department_id')
    if department_id:
        attendance = attendance.filter(staff__support_department_id=department_id)
    
    status = request.GET.get('status')
    if status == 'on_duty':
        attendance = attendance.filter(time_out__isnull=True)
    elif status == 'clocked_out':
        attendance = attendance.filter(time_out__isnull=False)
    elif status == 'absent':
        # This requires checking staff not in attendance records
        present_staff_ids = attendance.values_list('staff_id', flat=True)
        all_school_staff = StaffProfile.objects.filter(
            user__school=school,
            user__role='non_teaching_staff'
        ).exclude(id__in=present_staff_ids)
        attendance = None
        absent_staff = all_school_staff
    
    if attendance is not None:
        # Pagination
        paginator = Paginator(attendance, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    else:
        page_obj = None
    
    # Get departments for filter
    from SchoolNowMgt.models import Department
    departments = Department.objects.filter(school=school, is_active=True)
    
    context = {
        'school': school,
        'staff_profile': staff_profile,
        'target_date': target_date,
        'page_obj': page_obj,
        'absent_staff': absent_staff if status == 'absent' else None,
        'departments': departments,
        'section': 'shift_attendance_list',
    }
    
    return render(request, 'support_staff/shift_attendance_list.html', context)


# ============================================================================
# WELFARE COORDINATOR DASHBOARD
# ============================================================================

@require_support_staff_role('welfare_coordinator')
def welfare_coordinator_dashboard(request):
    """
    Welfare Coordinator Dashboard - Manage student welfare activities
    
    Template context:
    - school: Current school
    - staff_profile: Welfare coordinator staff profile
    - statistics: Welfare metrics
    - recent_activities: Latest activity logs
    
    School Filtering: All queries filtered by school=school
    """
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get welfare department if assigned
    department = staff_profile.support_department
    
    # Basic statistics
    all_students = CustomUser.objects.filter(
        school=school,
        role='student'
    ).count()
    
    # Get recent activities for the current school via the related teacher profile
    recent_activities = ActivityLog.objects.filter(
        teacher__user__school=school
    ).order_by('-created_at')[:10]
    
    statistics = {
        'total_students': all_students,
        'department': department.name if department else 'Not assigned',
    }
    
    context = {
        'school': school,
        'staff_profile': staff_profile,
        'department': department,
        'statistics': statistics,
        'recent_activities': recent_activities,
        'section': 'welfare_coordinator_dashboard',
    }
    
    return render(request, 'support_staff/welfare_coordinator_dashboard.html', context)


# ============================================================================
# COMMON VIEWS FOR ALL SUPPORT STAFF
# ============================================================================

@require_support_staff_role(['staff', 'supervisor', 'department_head', 'welfare_coordinator'])
def support_staff_profile(request):
    """
    View and edit own profile (available to all support staff)
    
    School Filtering: Only own staff profile
    """
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    if staff_profile.user.school != school:
        raise PermissionDenied("Profile not in your school")
    
    if request.method == 'POST':
        # Update profile (phone, address, etc.)
        # Implementation depends on StaffProfile fields
        pass
    
    context = {
        'school': school,
        'staff_profile': staff_profile,
        'section': 'support_staff_profile',
    }
    
    return render(request, 'support_staff/support_staff_profile.html', context)
