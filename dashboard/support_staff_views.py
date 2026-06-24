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
    ).select_related('staff__user')
    
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
    
    # Recent activities
    recent_activities = ActivityLog.objects.all().select_related('teacher').order_by('-created_at')[:10]
    
    statistics = {
        'total_staff': all_staff,
        'on_duty_today': on_duty,
        'clocked_out_today': clocked_out,
        'absent_today': absent,
        'week_days': week_attendance.count(),
    }
    
    context = {
        'school': school,
        'staff_profile': staff_profile,
        'statistics': statistics,
        'today_attendance': today_attendance,
        'week_attendance': week_attendance,
        'recent_activities': recent_activities,
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
    
    # Get recent activities
    recent_activities = ActivityLog.objects.filter(
        school=school
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
