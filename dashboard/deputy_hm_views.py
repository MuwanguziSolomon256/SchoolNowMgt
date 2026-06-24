"""
Deputy Headmaster Dashboard Views

Purpose: Manage non-teaching support staff, departments, shifts, and facilities

Permission: Requires Deputy HM role via @require_deputy_hm decorator
(Deputy HM has teacher role but with support_staff_role management capabilities)
School Isolation: All queries filtered by school=user.school
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction

from SchoolNowMgt.models import (
    StaffProfile, CustomUser, School, Department, ActivityLog,
    StudentAttendance, StaffAttendance, TeacherAttendance
)
from SchoolNowMgt.decorators import require_deputy_hm, get_user_school


# ============================================================================
# DEPUTY HEADMASTER MAIN DASHBOARD
# ============================================================================

@require_deputy_hm
def deputy_hm_dashboard(request):
    """
    Deputy Headmaster Dashboard - Overview of support staff and operations
    
    Template context:
    - school: Current school
    - staff_profile: Deputy HM staff profile
    - statistics: Key metrics (staff count, departments, shifts, etc.)
    - recent_activities: Latest activity logs
    - pending_tasks: Staff assignments, department heads needed, etc.
    
    School Filtering: All queries filtered by school=school
    """
    school = get_user_school(request)
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    # Get all support staff for the school
    all_support_staff = StaffProfile.objects.filter(
        user__school=school,
        user__role='non_teaching_staff'
    ).select_related('user', 'support_department')
    
    # Get departments
    departments = Department.objects.filter(
        school=school,
        is_active=True
    )
    
    # Calculate statistics
    statistics = {
        'total_support_staff': all_support_staff.count(),
        'total_departments': departments.count(),
        'departments_with_heads': departments.filter(
            head_of_department__isnull=False
        ).count(),
        'departments_without_heads': departments.filter(
            head_of_department__isnull=True
        ).count(),
        'active_shifts': 0,  # Will calculate if shift data exists
    }
    
    # Get staff by department
    staff_by_department = {}
    for dept in departments:
        count = all_support_staff.filter(support_department=dept).count()
        staff_by_department[dept.name] = count
    
    # Get recent activity logs
    recent_activities = ActivityLog.objects.filter(
        teacher=staff
    ).order_by('-created_at')[:10]
    
    # Get departments without head
    departments_without_head = departments.filter(head_of_department__isnull=True)
    
    # Get staff without department assignment
    staff_without_dept = all_support_staff.filter(support_department__isnull=True)
    
    context = {
        'school': school,
        'staff_profile': staff,
        'statistics': statistics,
        'staff_by_department': staff_by_department,
        'recent_activities': recent_activities,
        'departments_without_head': departments_without_head,
        'staff_without_dept': staff_without_dept,
        'total_staff': all_support_staff.count(),
        'section': 'deputy_hm_dashboard',
    }
    
    # Log activity
    ActivityLog.objects.create(
        teacher=staff,
        activity_type='dashboard_visit',
        description='Accessed Deputy HM Dashboard',
        severity='info',
        icon_name='dashboard'
    )
    
    return render(request, 'deputy_hm/deputy_hm_dashboard.html', context)


# ============================================================================
# SUPPORT STAFF MANAGEMENT
# ============================================================================

@require_deputy_hm
def support_staff_list(request):
    """
    List all support staff with filtering options
    
    GET params:
    - department_id: Filter by department
    - role: Filter by support staff role
    - status: active/inactive
    - search: Search by name or ID
    - page: Pagination
    
    School Filtering: All staff filtered by school
    """
    school = get_user_school(request)
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    # Base queryset
    support_staff = StaffProfile.objects.filter(
        user__school=school,
        user__role='non_teaching_staff'
    ).select_related('user', 'support_department').order_by('user__first_name')
    
    # Apply filters
    department_id = request.GET.get('department_id')
    if department_id:
        support_staff = support_staff.filter(support_department_id=department_id)
    
    role = request.GET.get('role')
    if role:
        support_staff = support_staff.filter(support_staff_role=role)
    
    status = request.GET.get('status')
    if status == 'active':
        support_staff = support_staff.filter(user__is_active=True)
    elif status == 'inactive':
        support_staff = support_staff.filter(user__is_active=False)
    
    search = request.GET.get('search')
    if search:
        support_staff = support_staff.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__username__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(support_staff, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    departments = Department.objects.filter(school=school, is_active=True)
    role_choices = StaffProfile.SUPPORT_STAFF_ROLE_CHOICES
    
    context = {
        'school': school,
        'staff_profile': staff,
        'page_obj': page_obj,
        'support_staff': page_obj.object_list,
        'departments': departments,
        'role_choices': role_choices,
        'selected_department': department_id,
        'selected_role': role,
        'selected_status': status,
        'search_query': search,
        'section': 'support_staff_list',
    }
    
    return render(request, 'deputy_hm/support_staff_list.html', context)


@require_deputy_hm
@require_http_methods(['GET', 'POST'])
def support_staff_edit(request, staff_id):
    """
    Edit support staff assignment and role
    
    POST params:
    - department_id: Department assignment
    - support_staff_role: Role (staff, supervisor, department_head, welfare_coordinator)
    - is_active: Active status
    
    School Filtering: Only school's staff can be edited
    """
    school = get_user_school(request)
    admin_staff = get_object_or_404(StaffProfile, user=request.user)
    
    support_staff = get_object_or_404(
        StaffProfile,
        id=staff_id,
        user__school=school,
        user__role='non_teaching_staff'
    )
    
    if request.method == 'POST':
        try:
            department_id = request.POST.get('department_id')
            role = request.POST.get('support_staff_role')
            is_active = request.POST.get('is_active') == 'on'
            
            if department_id:
                dept = get_object_or_404(Department, id=department_id, school=school)
                support_staff.support_department = dept
            
            if role in dict(StaffProfile.SUPPORT_STAFF_ROLE_CHOICES):
                support_staff.support_staff_role = role
            
            support_staff.user.is_active = is_active
            support_staff.user.save()
            support_staff.save()
            
            ActivityLog.objects.create(
                teacher=admin_staff,
                activity_type='staff_updated',
                description=f'Updated support staff: {support_staff.user.get_full_name()}',
                severity='info',
                icon_name='edit'
            )
            
            messages.success(request, 'Support staff updated successfully')
            return redirect('deputy_hm:support_staff_list')
        
        except Exception as e:
            messages.error(request, f'Error updating staff: {str(e)}')
    
    # GET request
    departments = Department.objects.filter(school=school, is_active=True)
    role_choices = StaffProfile.SUPPORT_STAFF_ROLE_CHOICES
    
    context = {
        'school': school,
        'staff_profile': admin_staff,
        'support_staff': support_staff,
        'departments': departments,
        'role_choices': role_choices,
        'section': 'support_staff_edit',
    }
    
    return render(request, 'deputy_hm/support_staff_form.html', context)


# ============================================================================
# DEPARTMENTS MANAGEMENT (Support Staff)
# ============================================================================

@require_deputy_hm
def departments_list(request):
    """
    List all support staff departments
    
    GET params:
    - department_type: Filter by type
    - status: active/inactive
    - page: Pagination
    
    School Filtering: All departments filtered by school
    """
    school = get_user_school(request)
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    # Base queryset
    departments = Department.objects.filter(
        school=school
    ).select_related('head_of_department').order_by('name')
    
    # Apply filters
    dept_type = request.GET.get('department_type')
    if dept_type:
        departments = departments.filter(department_type=dept_type)
    
    status = request.GET.get('status')
    if status == 'active':
        departments = departments.filter(is_active=True)
    elif status == 'inactive':
        departments = departments.filter(is_active=False)
    else:
        # Default to active
        departments = departments.filter(is_active=True)
    
    # Pagination
    paginator = Paginator(departments, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get department type choices
    dept_type_choices = Department.DEPARTMENT_TYPES
    
    context = {
        'school': school,
        'staff_profile': staff,
        'page_obj': page_obj,
        'departments': page_obj.object_list,
        'dept_type_choices': dept_type_choices,
        'selected_type': dept_type,
        'selected_status': status or 'active',
        'section': 'departments_list',
    }
    
    return render(request, 'deputy_hm/departments_list.html', context)


@require_deputy_hm
@require_http_methods(['GET', 'POST'])
def department_edit(request, department_id):
    """
    Edit department details
    
    POST params:
    - name: Department name
    - department_type: Type choice
    - description: Department description
    - head_of_department: Staff member ID to assign as head
    - monthly_budget: Budget allocation
    
    School Filtering: Only school's departments can be edited
    """
    school = get_user_school(request)
    admin_staff = get_object_or_404(StaffProfile, user=request.user)
    
    department = get_object_or_404(Department, id=department_id, school=school)
    
    if request.method == 'POST':
        try:
            department.name = request.POST.get('name')
            department.description = request.POST.get('description')
            
            monthly_budget = request.POST.get('monthly_budget')
            if monthly_budget:
                department.monthly_budget = Decimal(monthly_budget)
            
            head_id = request.POST.get('head_of_department')
            if head_id:
                head = get_object_or_404(
                    StaffProfile,
                    id=head_id,
                    user__school=school,
                    user__role='non_teaching_staff'
                )
                department.head_of_department = head
            else:
                department.head_of_department = None
            
            department.is_active = request.POST.get('is_active') == 'on'
            department.save()
            
            ActivityLog.objects.create(
                teacher=admin_staff,
                activity_type='department_updated',
                description=f'Updated department: {department.name}',
                severity='info',
                icon_name='edit'
            )
            
            messages.success(request, 'Department updated successfully')
            return redirect('deputy_hm:departments_list')
        
        except Exception as e:
            messages.error(request, f'Error updating department: {str(e)}')
    
    # GET request
    department_heads = StaffProfile.objects.filter(
        user__school=school,
        user__role='non_teaching_staff'
    ).select_related('user')
    
    dept_type_choices = Department.DEPARTMENT_TYPES
    
    context = {
        'school': school,
        'staff_profile': admin_staff,
        'department': department,
        'department_heads': department_heads,
        'dept_type_choices': dept_type_choices,
        'section': 'department_edit',
    }
    
    return render(request, 'deputy_hm/department_form.html', context)


@require_deputy_hm
@require_http_methods(['GET', 'POST'])
def department_create(request):
    """
    Create a new support staff department
    
    POST params:
    - name: Department name (required, unique per school)
    - department_type: Type choice (required)
    - description: Department description
    - head_of_department: Staff member ID to assign as head
    - monthly_budget: Budget allocation
    
    Validation:
    - Department type must be unique per school
    - Monthly budget must be positive if provided
    - Head must be non_teaching_staff role
    
    School Filtering: New department assigned to current school
    """
    school = get_user_school(request)
    admin_staff = get_object_or_404(StaffProfile, user=request.user)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            dept_type = request.POST.get('department_type')
            description = request.POST.get('description', '').strip()
            
            # Validation
            if not name:
                messages.error(request, 'Department name is required')
                return redirect('deputy_hm:department_create')
            
            if not dept_type:
                messages.error(request, 'Department type is required')
                return redirect('deputy_hm:department_create')
            
            # Check if type already exists in this school
            if Department.objects.filter(school=school, department_type=dept_type).exists():
                messages.error(request, f'Department type "{dept_type}" already exists in your school')
                return redirect('deputy_hm:department_create')
            
            # Create department
            department = Department(
                school=school,
                name=name,
                department_type=dept_type,
                description=description,
                is_active=True
            )
            
            # Handle optional budget
            monthly_budget = request.POST.get('monthly_budget')
            if monthly_budget:
                try:
                    budget = Decimal(monthly_budget)
                    if budget < 0:
                        messages.error(request, 'Monthly budget must be positive')
                        return redirect('deputy_hm:department_create')
                    department.monthly_budget = budget
                except (ValueError, Decimal.InvalidOperation):
                    messages.error(request, 'Invalid budget amount')
                    return redirect('deputy_hm:department_create')
            
            # Handle optional head assignment
            head_id = request.POST.get('head_of_department')
            if head_id:
                try:
                    head = StaffProfile.objects.get(
                        id=head_id,
                        user__school=school,
                        user__role='non_teaching_staff'
                    )
                    department.head_of_department = head
                except StaffProfile.DoesNotExist:
                    messages.error(request, 'Invalid department head selection')
                    return redirect('deputy_hm:department_create')
            
            department.save()
            
            ActivityLog.objects.create(
                teacher=admin_staff,
                activity_type='department_created',
                description=f'Created support department: {department.name}',
                severity='info',
                icon_name='add'
            )
            
            messages.success(request, f'Department "{department.name}" created successfully')
            return redirect('deputy_hm:departments_list')
        
        except Exception as e:
            messages.error(request, f'Error creating department: {str(e)}')
            return redirect('deputy_hm:department_create')
    
    # GET request
    department_heads = StaffProfile.objects.filter(
        user__school=school,
        user__role='non_teaching_staff'
    ).select_related('user')
    
    dept_type_choices = Department.DEPARTMENT_TYPES
    
    context = {
        'school': school,
        'staff_profile': admin_staff,
        'department': None,  # No department for create
        'department_heads': department_heads,
        'dept_type_choices': dept_type_choices,
        'section': 'department_create',
        'is_create': True,
    }
    
    return render(request, 'deputy_hm/department_form.html', context)


@require_deputy_hm
@require_http_methods(['GET'])
def department_detail(request, department_id):
    """
    View department details with related information
    
    Displays:
    - Department info (name, type, description, budget)
    - Department head details
    - Staff members assigned to department
    - Department statistics
    
    School Filtering: Only school's departments can be viewed
    """
    school = get_user_school(request)
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    department = get_object_or_404(
        Department,
        id=department_id,
        school=school
    )
    
    # Get related staff members in this department
    department_staff = StaffProfile.objects.filter(
        department=department,
        user__school=school
    ).select_related('user').order_by('user__first_name')
    
    context = {
        'school': school,
        'staff_profile': staff,
        'department': department,
        'department_staff': department_staff,
        'staff_count': department_staff.count(),
        'section': 'department_detail',
    }
    
    return render(request, 'deputy_hm/department_detail.html', context)


@require_deputy_hm
@require_http_methods(['POST'])
def department_delete(request, department_id):
    """
    Delete a support department (soft delete via is_active=False)
    
    Prevents deletion if:
    - Department has active staff assignments (can reassign first)
    
    School Filtering: Only school's departments can be deleted
    """
    school = get_user_school(request)
    admin_staff = get_object_or_404(StaffProfile, user=request.user)
    
    department = get_object_or_404(
        Department,
        id=department_id,
        school=school
    )
    
    try:
        # Check for active staff assignments
        active_staff = StaffProfile.objects.filter(
            department=department,
            user__school=school
        ).count()
        
        if active_staff > 0:
            messages.error(
                request,
                f'Cannot delete department with {active_staff} active staff member(s). '
                'Please reassign staff first.'
            )
            return redirect('deputy_hm:department_detail', department_id=department.id)
        
        # Soft delete
        department.is_active = False
        department.save()
        
        ActivityLog.objects.create(
            teacher=admin_staff,
            activity_type='department_deleted',
            description=f'Deleted support department: {department.name}',
            severity='warning',
            icon_name='delete'
        )
        
        messages.success(request, 'Department deleted successfully')
        return redirect('deputy_hm:departments_list')
    
    except Exception as e:
        messages.error(request, f'Error deleting department: {str(e)}')
        return redirect('deputy_hm:department_detail', department_id=department.id)


# ============================================================================
# HOSTEL MANAGEMENT
# ============================================================================

@require_deputy_hm
@require_http_methods(['GET'])
def hostels_list(request):
    """
    List all hostels in the school
    
    GET params:
    - hostel_type: Filter by type (boys/girls/mixed)
    - status: active/inactive
    - page: Pagination
    
    School Filtering: All hostels filtered by school
    """
    school = get_user_school(request)
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    # Import Hostel model
    from SchoolNowMgt.models import Hostel
    
    # Base queryset
    hostels = Hostel.objects.filter(
        school=school
    ).select_related('matron__user').order_by('name')
    
    # Apply filters
    hostel_type = request.GET.get('hostel_type')
    if hostel_type:
        hostels = hostels.filter(hostel_type=hostel_type)
    
    status = request.GET.get('status')
    if status == 'active':
        hostels = hostels.filter(is_active=True)
    elif status == 'inactive':
        hostels = hostels.filter(is_active=False)
    else:
        # Default to active
        hostels = hostels.filter(is_active=True)
    
    # Pagination
    paginator = Paginator(hostels, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Calculate stats for each hostel
    hostel_stats = []
    for hostel in page_obj.object_list:
        from SchoolNowMgt.models import ResidentAssignment
        residents = ResidentAssignment.objects.filter(
            hostel=hostel,
            status='active'
        ).count()
        hostel_stats.append({
            'hostel': hostel,
            'current_residents': residents,
            'occupancy_percentage': (residents / hostel.capacity * 100) if hostel.capacity > 0 else 0
        })
    
    # Get hostel type choices
    hostel_type_choices = Hostel.HOSTEL_TYPES
    
    context = {
        'school': school,
        'staff_profile': staff,
        'page_obj': page_obj,
        'hostel_stats': hostel_stats,
        'hostel_type_choices': hostel_type_choices,
        'selected_type': hostel_type,
        'selected_status': status or 'active',
        'section': 'hostels_list',
    }
    
    return render(request, 'deputy_hm/hostels_list.html', context)


@require_deputy_hm
@require_http_methods(['GET', 'POST'])
def hostel_create(request):
    """
    Create a new hostel
    
    POST params:
    - name: Hostel name (required, unique per school)
    - hostel_type: Type choice (boys/girls/mixed, required)
    - capacity: Maximum residents (required, must be positive)
    - matron: Staff ID to assign as matron (optional)
    
    Validation:
    - Hostel name must be unique per school
    - Capacity must be positive integer
    - Matron must be welfare_coordinator role if provided
    
    School Filtering: New hostel assigned to current school
    """
    school = get_user_school(request)
    admin_staff = get_object_or_404(StaffProfile, user=request.user)
    
    from SchoolNowMgt.models import Hostel
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            hostel_type = request.POST.get('hostel_type')
            capacity = request.POST.get('capacity')
            
            # Validation
            if not name:
                messages.error(request, 'Hostel name is required')
                return redirect('deputy_hm:hostel_create')
            
            if not hostel_type:
                messages.error(request, 'Hostel type is required')
                return redirect('deputy_hm:hostel_create')
            
            if not capacity:
                messages.error(request, 'Capacity is required')
                return redirect('deputy_hm:hostel_create')
            
            try:
                capacity = int(capacity)
                if capacity <= 0:
                    messages.error(request, 'Capacity must be a positive number')
                    return redirect('deputy_hm:hostel_create')
            except ValueError:
                messages.error(request, 'Invalid capacity value')
                return redirect('deputy_hm:hostel_create')
            
            # Check if name already exists in this school
            if Hostel.objects.filter(school=school, name=name).exists():
                messages.error(request, f'Hostel "{name}" already exists in your school')
                return redirect('deputy_hm:hostel_create')
            
            # Create hostel
            hostel = Hostel(
                school=school,
                name=name,
                hostel_type=hostel_type,
                capacity=capacity,
                is_active=True
            )
            
            # Handle optional matron assignment
            matron_id = request.POST.get('matron')
            if matron_id:
                try:
                    matron = StaffProfile.objects.get(
                        id=matron_id,
                        user__school=school,
                        user__role='non_teaching_staff',
                        support_staff_role='welfare_coordinator'
                    )
                    hostel.matron = matron
                except StaffProfile.DoesNotExist:
                    messages.error(request, 'Invalid matron selection')
                    return redirect('deputy_hm:hostel_create')
            
            hostel.save()
            
            ActivityLog.objects.create(
                teacher=admin_staff,
                activity_type='hostel_created',
                description=f'Created hostel: {hostel.name} (Capacity: {capacity})',
                severity='info',
                icon_name='add'
            )
            
            messages.success(request, f'Hostel "{hostel.name}" created successfully')
            return redirect('deputy_hm:hostels_list')
        
        except Exception as e:
            messages.error(request, f'Error creating hostel: {str(e)}')
            return redirect('deputy_hm:hostel_create')
    
    # GET request
    # Get available matrons (welfare_coordinator role)
    matrons = StaffProfile.objects.filter(
        user__school=school,
        user__role='non_teaching_staff',
        support_staff_role='welfare_coordinator'
    ).select_related('user')
    
    hostel_type_choices = Hostel.HOSTEL_TYPES
    
    context = {
        'school': school,
        'staff_profile': admin_staff,
        'hostel': None,
        'matrons': matrons,
        'hostel_type_choices': hostel_type_choices,
        'section': 'hostel_create',
        'is_create': True,
    }
    
    return render(request, 'deputy_hm/hostel_form.html', context)


@require_deputy_hm
@require_http_methods(['GET', 'POST'])
def hostel_edit(request, hostel_id):
    """
    Edit hostel details
    
    POST params:
    - name: Hostel name
    - capacity: Maximum residents
    - matron: Staff ID to assign as matron
    - is_active: Active status
    
    School Filtering: Only school's hostels can be edited
    """
    school = get_user_school(request)
    admin_staff = get_object_or_404(StaffProfile, user=request.user)
    
    from SchoolNowMgt.models import Hostel
    
    hostel = get_object_or_404(Hostel, id=hostel_id, school=school)
    
    if request.method == 'POST':
        try:
            hostel.name = request.POST.get('name', hostel.name)
            
            capacity = request.POST.get('capacity')
            if capacity:
                try:
                    capacity = int(capacity)
                    if capacity <= 0:
                        messages.error(request, 'Capacity must be a positive number')
                        return redirect('deputy_hm:hostel_edit', hostel_id=hostel.id)
                    hostel.capacity = capacity
                except ValueError:
                    messages.error(request, 'Invalid capacity value')
                    return redirect('deputy_hm:hostel_edit', hostel_id=hostel.id)
            
            matron_id = request.POST.get('matron')
            if matron_id:
                try:
                    matron = StaffProfile.objects.get(
                        id=matron_id,
                        user__school=school,
                        user__role='non_teaching_staff',
                        support_staff_role='welfare_coordinator'
                    )
                    hostel.matron = matron
                except StaffProfile.DoesNotExist:
                    messages.error(request, 'Invalid matron selection')
                    return redirect('deputy_hm:hostel_edit', hostel_id=hostel.id)
            else:
                hostel.matron = None
            
            hostel.is_active = request.POST.get('is_active') == 'on'
            hostel.save()
            
            ActivityLog.objects.create(
                teacher=admin_staff,
                activity_type='hostel_updated',
                description=f'Updated hostel: {hostel.name}',
                severity='info',
                icon_name='edit'
            )
            
            messages.success(request, 'Hostel updated successfully')
            return redirect('deputy_hm:hostels_list')
        
        except Exception as e:
            messages.error(request, f'Error updating hostel: {str(e)}')
    
    # GET request
    matrons = StaffProfile.objects.filter(
        user__school=school,
        user__role='non_teaching_staff',
        support_staff_role='welfare_coordinator'
    ).select_related('user')
    
    hostel_type_choices = Hostel.HOSTEL_TYPES
    
    context = {
        'school': school,
        'staff_profile': admin_staff,
        'hostel': hostel,
        'matrons': matrons,
        'hostel_type_choices': hostel_type_choices,
        'section': 'hostel_edit',
        'is_create': False,
    }
    
    return render(request, 'deputy_hm/hostel_form.html', context)


@require_deputy_hm
@require_http_methods(['GET'])
def hostel_detail(request, hostel_id):
    """
    View hostel details with residents and matron information
    
    Displays:
    - Hostel info (name, type, capacity)
    - Current occupancy
    - Assigned matron details
    - Current residents list
    - Available beds
    
    School Filtering: Only school's hostels can be viewed
    """
    school = get_user_school(request)
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    from SchoolNowMgt.models import Hostel, ResidentAssignment
    
    hostel = get_object_or_404(Hostel, id=hostel_id, school=school)
    
    # Get current residents
    residents = ResidentAssignment.objects.filter(
        hostel=hostel,
        status='active'
    ).select_related('student__user').order_by('student__user__first_name')
    
    occupancy = residents.count()
    available_beds = hostel.capacity - occupancy
    occupancy_percentage = (occupancy / hostel.capacity * 100) if hostel.capacity > 0 else 0
    
    context = {
        'school': school,
        'staff_profile': staff,
        'hostel': hostel,
        'residents': residents,
        'occupancy': occupancy,
        'available_beds': available_beds,
        'occupancy_percentage': occupancy_percentage,
        'section': 'hostel_detail',
    }
    
    return render(request, 'deputy_hm/hostel_detail.html', context)


@require_deputy_hm
@require_http_methods(['POST'])
def hostel_delete(request, hostel_id):
    """
    Delete a hostel (soft delete via is_active=False)
    
    Prevents deletion if:
    - Hostel has active resident assignments
    
    School Filtering: Only school's hostels can be deleted
    """
    school = get_user_school(request)
    admin_staff = get_object_or_404(StaffProfile, user=request.user)
    
    from SchoolNowMgt.models import Hostel, ResidentAssignment
    
    hostel = get_object_or_404(Hostel, id=hostel_id, school=school)
    
    try:
        # Check for active residents
        active_residents = ResidentAssignment.objects.filter(
            hostel=hostel,
            status='active'
        ).count()
        
        if active_residents > 0:
            messages.error(
                request,
                f'Cannot delete hostel with {active_residents} active resident(s). '
                'Please transfer residents first.'
            )
            return redirect('deputy_hm:hostel_detail', hostel_id=hostel.id)
        
        # Soft delete
        hostel.is_active = False
        hostel.save()
        
        ActivityLog.objects.create(
            teacher=admin_staff,
            activity_type='hostel_deleted',
            description=f'Deleted hostel: {hostel.name}',
            severity='warning',
            icon_name='delete'
        )
        
        messages.success(request, 'Hostel deleted successfully')
        return redirect('deputy_hm:hostels_list')
    
    except Exception as e:
        messages.error(request, f'Error deleting hostel: {str(e)}')
        return redirect('deputy_hm:hostel_detail', hostel_id=hostel.id)


@require_deputy_hm
def shift_overview(request):
    """
    Overview of staff shifts and attendance
    
    Shows:
    - Staff on duty today
    - Staff attendance records
    - Shift patterns
    - Clock in/out times
    
    School Filtering: Only school's shift data shown
    """
    school = get_user_school(request)
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    # Get today's attendance for support staff
    today = timezone.now().date()
    
    # Get all support staff
    all_support_staff = StaffProfile.objects.filter(
        user__school=school,
        user__role='non_teaching_staff',
        user__is_active=True
    ).select_related('user', 'support_department')
    
    # Try to get attendance records (may not exist for all staff)
    try:
        today_attendance = StaffAttendance.objects.filter(
            staff__in=all_support_staff,
            date=today
        ).select_related('staff').order_by('-clock_in_time')
    except:
        today_attendance = []
    
    # Get this week's attendance summary
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    try:
        week_attendance = StaffAttendance.objects.filter(
            staff__in=all_support_staff,
            date__range=[week_start, week_end]
        ).order_by('-date')
    except:
        week_attendance = []
    
    # Calculate statistics
    statistics = {
        'total_staff': all_support_staff.count(),
        'on_duty_today': len(today_attendance),
        'absent_today': all_support_staff.count() - len(today_attendance),
    }
    
    context = {
        'school': school,
        'staff_profile': staff,
        'today': today,
        'today_attendance': today_attendance,
        'week_attendance': week_attendance,
        'statistics': statistics,
        'section': 'shift_overview',
    }
    
    return render(request, 'deputy_hm/shift_overview.html', context)


# ============================================================================
# FACILITIES & MAINTENANCE
# ============================================================================

@require_deputy_hm
def facilities_overview(request):
    """
    Overview of facilities and maintenance status
    
    Shows:
    - Maintenance department
    - Cleaning/housekeeping status
    - Facilities availability
    - Budget tracking
    
    School Filtering: School-level facilities only
    """
    school = get_user_school(request)
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    # Get facility-related departments
    facility_depts = Department.objects.filter(
        school=school,
        department_type__in=[
            'maintenance', 'cleaning', 'facilities', 'catering'
        ]
    ).select_related('head_of_department')
    
    # Calculate total budget for facilities
    total_facility_budget = facility_depts.aggregate(
        total=Sum('monthly_budget')
    )['total'] or 0
    
    # Get staff in facility departments
    facility_staff = StaffProfile.objects.filter(
        user__school=school,
        user__role='non_teaching_staff',
        support_department__in=facility_depts
    ).count()
    
    statistics = {
        'total_facility_depts': facility_depts.count(),
        'facility_staff': facility_staff,
        'total_budget': total_facility_budget,
        'avg_budget_per_dept': (
            total_facility_budget / facility_depts.count()
            if facility_depts.count() > 0 else 0
        ),
    }
    
    context = {
        'school': school,
        'staff_profile': staff,
        'facility_depts': facility_depts,
        'statistics': statistics,
        'section': 'facilities_overview',
    }
    
    return render(request, 'deputy_hm/facilities_overview.html', context)


# ============================================================================
# BUDGET TRACKING
# ============================================================================

@require_deputy_hm
def budget_overview(request):
    """
    Budget overview for all support departments
    
    Shows:
    - Total allocated budget
    - Budget by department
    - Budget utilization
    
    School Filtering: School-level budgets only
    """
    school = get_user_school(request)
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    # Get all departments with budgets
    departments = Department.objects.filter(
        school=school,
        is_active=True
    ).order_by('-monthly_budget')
    
    # Calculate budget statistics
    total_budget = departments.aggregate(
        total=Sum('monthly_budget')
    )['total'] or 0
    
    depts_with_budget = departments.exclude(monthly_budget__isnull=True).count()
    depts_without_budget = departments.filter(monthly_budget__isnull=True).count()
    
    # Prepare department budget data
    dept_budget_data = []
    for dept in departments:
        if dept.monthly_budget:
            dept_budget_data.append({
                'department': dept,
                'budget': dept.monthly_budget,
                'percentage': (dept.monthly_budget / total_budget * 100) if total_budget > 0 else 0,
            })
    
    statistics = {
        'total_budget': total_budget,
        'depts_with_budget': depts_with_budget,
        'depts_without_budget': depts_without_budget,
        'avg_budget': (
            total_budget / depts_with_budget
            if depts_with_budget > 0 else 0
        ),
    }
    
    context = {
        'school': school,
        'staff_profile': staff,
        'dept_budget_data': dept_budget_data,
        'statistics': statistics,
        'section': 'budget_overview',
    }
    
    return render(request, 'deputy_hm/budget_overview.html', context)
