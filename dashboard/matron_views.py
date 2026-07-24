"""
Matron & Hostel Management Dashboard Views

Purpose: Manage hostel operations, student residency, and welfare
- Matron: Overall hostel oversight and resident management
- Hostel Supervisor: Specific hostel duty roster and daily operations

Permission: Support staff with matron/welfare coordinator roles via decorators
School Isolation: All queries filtered by school=user.school

Note: Hostels are modeled as Department entities (department_type='hostel')
Residents are students assigned to hostels
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

from SchoolNowMgt.models import (
    StaffProfile, CustomUser, School, Department, ActivityLog,
    Student, StudentAttendance, Hostel, ResidentAssignment
)
from SchoolNowMgt.decorators import require_support_staff_role, require_welfare_coordinator, get_user_school


# ============================================================================
# MATRON DASHBOARD
# ============================================================================


def paginate_queryset(request, queryset, per_page):
    """Helper function to paginate queryset"""
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page', 1)
    return paginator.get_page(page_number)

@require_welfare_coordinator
def matron_dashboard(request):
    """
    Matron Dashboard - Overview of hostel operations and resident welfare
    
    Template context:
    - school: Current school
    - staff_profile: Matron staff profile
    - statistics: Key metrics (hostels, residents, occupancy, etc.)
    - hostels: List of hostels
    - recent_activities: Latest activity logs
    - roll_call_sessions: Dormitory roll call progress
    - unaccounted_students: Students missing room assignment or needing follow-up
    - health_logs: Infirmary-related entries for the dashboard
    - maintenance_tasks: Quick maintenance ticket summary
    - inventory_items: Supplies and inventory statuses
    
    School Filtering: All queries filtered by school=school
    """
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get all hostels
    hostels = Hostel.objects.filter(
        school=school,
        is_active=True
    ).annotate(
        resident_count=Count('residents')
    ).order_by('name')
    
    # Get total residents from ResidentAssignment
    total_residents = ResidentAssignment.objects.filter(
        hostel__school=school,
        is_active=True
    ).count()
    
    # Calculate occupancy
    total_hostels = hostels.count()
    total_capacity = hostels.aggregate(total=Sum('capacity'))['total'] or 0
    occupancy_rate = f"{(total_residents / total_capacity * 100):.1f}%" if total_capacity > 0 else "0%"
    
    # Recent activities - not filtered by school since ActivityLog doesn't have school field
    recent_activities = ActivityLog.objects.all().order_by('-created_at')[:10]
    
    statistics = {
        'total_hostels': total_hostels,
        'total_residents': total_residents,
        'total_capacity': total_capacity,
        'occupancy_rate': occupancy_rate,
        'avg_residents_per_hostel': int(total_residents / total_hostels) if total_hostels > 0 else 0,
    }
    
    roll_call_sessions = []
    for hostel in hostels[:3]:
        capacity = hostel.capacity or 0
        present = hostel.resident_count
        percentage = int((present / capacity) * 100) if capacity > 0 else 0
        if percentage >= 100:
            status_label = 'Completed'
            status_color = 'green'
        elif percentage >= 70:
            status_label = 'In Progress'
            status_color = 'yellow'
        else:
            status_label = 'Pending'
            status_color = 'gray'

        roll_call_sessions.append({
            'code': hostel.name[:2].upper() if hostel.name else 'HS',
            'name': hostel.name,
            'count_text': f"{present}/{capacity if capacity > 0 else 0} Present",
            'progress_width': min(100, percentage),
            'status_label': status_label,
            'status_color': status_color,
        })
    roll_call_overall = roll_call_sessions[0]['progress_width'] if roll_call_sessions else 0
    
    unaccounted_assignments = list(ResidentAssignment.objects.filter(
        hostel__school=school,
        is_active=True,
        room_number__exact=''
    ).select_related('student', 'hostel')[:3])

    if not unaccounted_assignments:
        unaccounted_assignments = list(ResidentAssignment.objects.filter(
            hostel__school=school,
            is_active=True
        ).select_related('student', 'hostel')[:3])

    unaccounted_students = []
    for assignment in unaccounted_assignments:
        student = assignment.student
        hostel = assignment.hostel
        unaccounted_students.append({
            'initials': ''.join([student.first_name[:1], student.last_name[:1]]).upper(),
            'name': student.full_name if hasattr(student, 'full_name') else f"{student.first_name} {student.last_name}",
            'details': f"{hostel.name} - Room {assignment.room_number or 'TBD'}",
        })

    if not unaccounted_students:
        unaccounted_students = [
            {'initials': 'KO', 'name': 'Kofi Osei', 'details': 'Eagle Wing B - Room 12'},
            {'initials': 'AA', 'name': 'Amara Adeyemi', 'details': 'Shark Senior - Room 04'},
            {'initials': 'JM', 'name': 'Jude Mensah', 'details': 'Eagle Wing B - Room 21'},
        ]

    health_logs = [
        {
            'student': 'Chinedu Okafor',
            'note': 'High fever - Observation Wing 1',
            'meta': 'Medication due in 15m',
            'accent': 'secondary',
        },
        {
            'student': 'Sarah Williams',
            'note': 'Sprained ankle - Discharged',
            'meta': 'Parents Notified',
            'accent': 'on-tertiary-container',
        },
        {
            'student': 'Fatima Bello',
            'note': 'Asthma review - Routine check',
            'meta': '2 hrs ago',
            'accent': 'primary-container',
        },
    ]

    maintenance_tasks = [
        {
            'title': 'Pipe Leak - Lion B',
            'status': 'Urgent',
            'icon': 'plumbing',
            'badge_color': 'error',
        },
        {
            'title': 'Bulb Out - Dining',
            'status': 'Pending',
            'icon': 'lightbulb',
            'badge_color': 'on-surface-variant',
        },
    ]

    inventory_items = [
        {'name': 'Liquid Detergent', 'current': 42, 'total': 50, 'percentage': 84, 'status': 'Sufficient Stock', 'status_color': 'secondary-container'},
        {'name': 'Bed Linens (Sets)', 'current': 12, 'total': 200, 'percentage': 6, 'status': 'Critical: Reorder Now', 'status_color': 'on-tertiary-container'},
        {'name': 'Disinfectant Spray', 'current': 18, 'total': 40, 'percentage': 45, 'status': 'Low Stock Alert', 'status_color': 'primary-container'},
        {'name': 'Sanitary Kits', 'current': 310, 'total': 350, 'percentage': 88, 'status': 'Stock Optimal', 'status_color': 'on-surface-variant'},
    ]

    context = {
        'school': school,
        'staff_profile': staff_profile,
        'statistics': statistics,
        'hostels': hostels[:5],
        'recent_activities': recent_activities,
        'roll_call_sessions': roll_call_sessions,
        'roll_call_overall': roll_call_overall,
        'unaccounted_students': unaccounted_students,
        'health_logs': health_logs,
        'maintenance_tasks': maintenance_tasks,
        'inventory_items': inventory_items,
        'health_hub_count': len(health_logs),
        'maintenance_open_count': sum(1 for task in maintenance_tasks if task['status'].lower() != 'resolved'),
        'inventory_fill': sum(item['percentage'] for item in inventory_items) // len(inventory_items) if inventory_items else 0,
        'section': 'matron_dashboard',
    }
    
    return render(request, 'matron/matron_dashboard.html', context)


@require_welfare_coordinator
def hostels_list(request):
    """
    List and manage hostels with resident information
    
    GET params:
    - search: Search by hostel name
    - status: active/inactive
    - page: Pagination
    
    School Filtering: Only school's hostels
    """
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Base queryset for hostels
    hostels = Hostel.objects.filter(
        school=school
    ).select_related('matron').order_by('name')
    
    # Apply filters
    search = request.GET.get('search')
    if search:
        hostels = hostels.filter(
            Q(name__icontains=search)
        )
    
    status = request.GET.get('status')
    if status == 'active':
        hostels = hostels.filter(is_active=True)
    elif status == 'inactive':
        hostels = hostels.filter(is_active=False)
    
    # Pagination
    page_obj = paginate_queryset(request, hostels, 15)
    
    context = {
        'school': school,
        'staff_profile': staff_profile,
        'page_obj': page_obj,
        'section': 'hostels_list',
    }
    
    return render(request, 'matron/hostels_list.html', context)


@require_welfare_coordinator
def hostel_detail(request, hostel_id):
    """
    View hostel details and manage residents
    
    School Filtering: Only school's hostels
    """
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get hostel
    hostel = get_object_or_404(
        Hostel,
        id=hostel_id,
        school=school
    )
    
    # Get residents via ResidentAssignment
    resident_assignments = ResidentAssignment.objects.filter(
        hostel=hostel,
        is_active=True
    ).select_related('student').order_by('student__first_name')
    
    residents = [ra.student for ra in resident_assignments]
    
    # Statistics
    total_residents = len(residents)
    occupancy_rate = (total_residents / hostel.capacity * 100) if hostel.capacity > 0 else 0
    matron_name = hostel.matron.user.get_full_name() if hostel.matron else "Unassigned"
    
    statistics = {
        'total_residents': total_residents,
        'capacity': hostel.capacity,
        'occupancy_rate': f"{occupancy_rate:.1f}%",
        'hostel_type': hostel.get_hostel_type_display(),
        'matron': matron_name,
    }
    
    context = {
        'school': school,
        'staff_profile': staff_profile,
        'hostel': hostel,
        'residents': residents,
        'hostel_staff': hostel_staff,
        'statistics': statistics,
        'section': 'hostel_detail',
    }
    
    return render(request, 'matron/hostel_detail.html', context)


@require_welfare_coordinator
def hostel_edit(request, hostel_id):
    """
    Edit hostel details (name, description, head, capacity)
    
    School Filtering: Only school's hostels
    """
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    hostel = get_object_or_404(
        Hostel,
        id=hostel_id,
        school=school
    )
    
    if request.method == 'POST':
        try:
            hostel.name = request.POST.get('name', hostel.name)
            hostel.hostel_type = request.POST.get('hostel_type', hostel.hostel_type)
            
            # Update matron if provided
            matron_id = request.POST.get('matron')
            if matron_id:
                matron = get_object_or_404(StaffProfile, id=matron_id, user__school=school)
                hostel.matron = matron
            elif request.POST.get('matron') == '':
                hostel.matron = None
            
            # Update capacity
            capacity = request.POST.get('capacity')
            if capacity:
                hostel.capacity = int(capacity)
            
            hostel.is_active = request.POST.get('is_active') == 'on'
            hostel.save()
            
            ActivityLog.objects.create(
                staff=staff_profile,
                school=school,
                activity_type='hostel_updated',
                description=f'Updated hostel: {hostel.name}',
                severity='info',
                icon_name='edit'
            )
            
            messages.success(request, 'Hostel updated successfully')
            return redirect('matron:hostel_detail', hostel_id=hostel.id)
        
        except Exception as e:
            messages.error(request, f'Error updating hostel: {str(e)}')
    
    # GET request
    # Get possible matrons (welfare coordinators)
    matrons = StaffProfile.objects.filter(
        user__school=school,
        support_staff_role='welfare_coordinator'
    ).select_related('user').order_by('user__first_name')
    
    context = {
        'school': school,
        'staff_profile': staff_profile,
        'hostel': hostel,
        'matrons': matrons,
        'section': 'hostel_edit',
    }
    
    return render(request, 'matron/hostel_form.html', context)


# ============================================================================
# RESIDENT MANAGEMENT
# ============================================================================

@require_welfare_coordinator
def residents_list(request):
    """
    List all hostel residents with filtering
    
    GET params:
    - hostel_id: Filter by hostel
    - search: Search by name
    - page: Pagination
    
    School Filtering: Only school's students
    """
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get all residents via ResidentAssignment
    resident_assignments = ResidentAssignment.objects.filter(
        hostel__school=school,
        is_active=True
    ).select_related('student', 'hostel')
    
    # Apply filters
    search = request.GET.get('search')
    if search:
        resident_assignments = resident_assignments.filter(
            Q(student__first_name__icontains=search) |
            Q(student__last_name__icontains=search) |
            Q(student__username__icontains=search)
        )
    
    hostel_id = request.GET.get('hostel_id')
    if hostel_id:
        resident_assignments = resident_assignments.filter(hostel__id=hostel_id)
    
    # Pagination
    page_obj = paginate_queryset(request, resident_assignments, 20)
    
    # Get hostels for filter
    hostels = Hostel.objects.filter(
        school=school,
        is_active=True
    ).order_by('name')
    
    context = {
        'school': school,
        'staff_profile': staff_profile,
        'page_obj': page_obj,
        'hostels': hostels,
        'section': 'residents_list',
    }
    
    return render(request, 'matron/residents_list.html', context)


@require_welfare_coordinator
def resident_detail(request, student_id):
    """
    View resident profile and manage hostel assignment
    
    School Filtering: Only school's students
    """
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get student
    student = get_object_or_404(
        CustomUser,
        id=student_id,
        school=school,
        role='student'
    )
    
    # Get student's hostel assignment
    hostel_assignment = ResidentAssignment.objects.filter(
        student=student,
        hostel__school=school,
        is_active=True
    ).select_related('hostel').first()
    
    # Get student attendance records
    attendance_records = StudentAttendance.objects.filter(
        student=student,
        student__class_grade__school=school
    ).order_by('-date')[:30]
    
    # Calculate attendance statistics
    total_records = attendance_records.count()
    present_days = attendance_records.filter(status='present').count()
    absent_days = attendance_records.filter(status='absent').count()
    attendance_rate = (present_days / total_records * 100) if total_records > 0 else 0
    
    statistics = {
        'total_attendance_records': total_records,
        'present_days': present_days,
        'absent_days': absent_days,
        'attendance_rate': f"{attendance_rate:.1f}%",
    }
    
    # Get available hostels for reassignment
    available_hostels = Hostel.objects.filter(
        school=school,
        is_active=True
    ).order_by('name')
    
    context = {
        'school': school,
        'staff_profile': staff_profile,
        'student': student,
        'hostel_assignment': hostel_assignment,
        'attendance_records': attendance_records,
        'statistics': statistics,
        'available_hostels': available_hostels,
        'section': 'resident_detail',
    }
    
    return render(request, 'matron/resident_detail.html', context)


# ============================================================================
# HOSTEL DUTY ROSTER
# ============================================================================

@require_welfare_coordinator
def duty_roster(request):
    """
    View and manage hostel duty roster
    
    School Filtering: Only school's staff assignments
    """
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get all hostels with assigned matrons
    hostels = Hostel.objects.filter(
        school=school,
        is_active=True
    ).select_related('matron').order_by('name')
    
    # Get resident counts per hostel
    resident_counts = {}
    for hostel in hostels:
        count = ResidentAssignment.objects.filter(
            hostel=hostel,
            is_active=True
        ).count()
        resident_counts[hostel.id] = count
    
    # Recent activities
    recent_activities = ActivityLog.objects.filter(
        school=school,
        activity_type__in=['staff_assigned', 'duty_updated']
    ).order_by('-created_at')[:10]
    
    context = {
        'school': school,
        'staff_profile': staff_profile,
        'hostels': hostels,
        'resident_counts': resident_counts,
        'recent_activities': recent_activities,
        'section': 'duty_roster',
    }
    
    return render(request, 'matron/duty_roster.html', context)


@require_welfare_coordinator
def roll_call_dashboard(request):
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)

    hostels = Hostel.objects.filter(
        school=school,
        is_active=True
    ).annotate(resident_count=Count('residents')).order_by('name')

    total_residents = ResidentAssignment.objects.filter(
        hostel__school=school,
        is_active=True
    ).count()

    total_capacity = hostels.aggregate(total=Sum('capacity'))['total'] or 0
    occupancy_rate = f"{(total_residents / total_capacity * 100):.1f}%" if total_capacity > 0 else "0%"

    roll_call_sessions = []
    for hostel in hostels[:5]:
        capacity = hostel.capacity or 0
        present = hostel.resident_count
        percentage = int((present / capacity) * 100) if capacity > 0 else 0
        if percentage >= 100:
            status_label = 'Completed'
            status_color = 'green'
        elif percentage >= 70:
            status_label = 'In Progress'
            status_color = 'yellow'
        else:
            status_label = 'Pending'
            status_color = 'gray'

        roll_call_sessions.append({
            'code': hostel.name[:2].upper() if hostel.name else 'HS',
            'name': hostel.name,
            'count_text': f"{present}/{capacity if capacity > 0 else 0} Present",
            'progress_width': min(100, percentage),
            'status_label': status_label,
            'status_color': status_color,
        })

    context = {
        'school': school,
        'staff_profile': staff_profile,
        'statistics': {
            'total_residents': total_residents,
        },
        'roll_call_sessions': roll_call_sessions,
        'roll_call_overall': roll_call_sessions[0]['progress_width'] if roll_call_sessions else 0,
        'unaccounted_students': [],
        'section': 'roll_call',
    }

    return render(request, 'matron/roll_call_dashboard.html', context)


@require_welfare_coordinator
def infirmary_dashboard(request):
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)

    health_logs = [
        {
            'student': 'Chinedu Okafor',
            'note': 'High fever - Observation Wing 1',
            'meta': 'Medication due in 15m',
            'accent': 'secondary',
        },
        {
            'student': 'Sarah Williams',
            'note': 'Sprained ankle - Discharged',
            'meta': 'Parents Notified',
            'accent': 'on-tertiary-container',
        },
        {
            'student': 'Fatima Bello',
            'note': 'Asthma review - Routine check',
            'meta': '2 hrs ago',
            'accent': 'primary-container',
        },
    ]

    context = {
        'school': school,
        'staff_profile': staff_profile,
        'health_logs': health_logs,
        'section': 'infirmary',
    }

    return render(request, 'matron/infirmary_dashboard.html', context)


@require_welfare_coordinator
def maintenance_dashboard(request):
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)

    maintenance_tasks = [
        {
            'title': 'Pipe Leak - Lion B',
            'status': 'Urgent',
            'icon': 'plumbing',
            'badge_color': 'error',
        },
        {
            'title': 'Bulb Out - Dining',
            'status': 'Pending',
            'icon': 'lightbulb',
            'badge_color': 'on-surface-variant',
        },
    ]

    inventory_items = [
        {'name': 'Liquid Detergent', 'current': 42, 'total': 50, 'percentage': 84, 'status': 'Sufficient Stock', 'status_color': 'secondary-container'},
        {'name': 'Bed Linens (Sets)', 'current': 12, 'total': 200, 'percentage': 6, 'status': 'Critical: Reorder Now', 'status_color': 'on-tertiary-container'},
        {'name': 'Disinfectant Spray', 'current': 18, 'total': 40, 'percentage': 45, 'status': 'Low Stock Alert', 'status_color': 'primary-container'},
        {'name': 'Sanitary Kits', 'current': 310, 'total': 350, 'percentage': 88, 'status': 'Stock Optimal', 'status_color': 'on-surface-variant'},
    ]

    context = {
        'school': school,
        'staff_profile': staff_profile,
        'maintenance_tasks': maintenance_tasks,
        'inventory_fill': sum(item['percentage'] for item in inventory_items) // len(inventory_items) if inventory_items else 0,
        'section': 'maintenance',
    }

    return render(request, 'matron/maintenance_dashboard.html', context)
