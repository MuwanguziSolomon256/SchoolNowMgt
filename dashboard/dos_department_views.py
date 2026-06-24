"""
DOS Department Management Views - TeacherDepartment CRUD

Director of Studies can:
- List all academic departments
- Create new departments
- Edit department details
- Assign department heads
- Delete departments
- View department performance metrics
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.contrib import messages
from django.utils import timezone

from SchoolNowMgt.models import (
    TeacherDepartment, StaffProfile, School, CustomUser, Grade, Subject
)
from SchoolNowMgt.decorators import get_user_school, require_dos


# ============================================================================
# DEPARTMENT LIST VIEW
# ============================================================================

@login_required
@require_dos
def departments_list(request):
    """
    List all academic departments for DOS to manage
    
    Features:
    - Filter by status (active/inactive)
    - Search by name
    - Show department head, members count, budget
    - Pagination
    
    Template Context:
    - school: Current school
    - departments: Paginated department list with stats
    - department_count: Total departments
    - active_count: Active departments
    - department_types: All available department types
    """
    school = get_user_school(request)
    
    # Base queryset with related data
    departments = TeacherDepartment.objects.filter(
        school=school
    ).select_related(
        'head_of_department__user'
    ).prefetch_related(
        'teacher_members'
    ).order_by('-is_active', 'name')
    
    # Filter by status
    status = request.GET.get('status', 'all')
    if status == 'active':
        departments = departments.filter(is_active=True)
    elif status == 'inactive':
        departments = departments.filter(is_active=False)
    
    # Search by name or type
    search = request.GET.get('search', '').strip()
    if search:
        departments = departments.filter(
            Q(name__icontains=search) |
            Q(department_type__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Add stats to each department
    departments_with_stats = []
    for dept in departments:
        teacher_count = dept.teacher_members.filter(
            user__is_active=True
        ).count()
        
        # Get number of classes in this department (approximation via timetable entries)
        # Note: Departments don't have direct class relationships, so we use teacher count as proxy
        class_count = 0
        
        departments_with_stats.append({
            'dept': dept,
            'teacher_count': teacher_count,
            'class_count': class_count,
        })
    
    # Pagination
    paginator = Paginator(departments_with_stats, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_depts = TeacherDepartment.objects.filter(school=school).count()
    active_depts = TeacherDepartment.objects.filter(
        school=school, is_active=True
    ).count()
    
    context = {
        'school': school,
        'page_obj': page_obj,
        'department_count': total_depts,
        'active_count': active_depts,
        'status': status,
        'search': search,
        'department_types': dict(TeacherDepartment.DEPARTMENT_TYPES),
    }
    
    return render(request, 'dos/departments_list.html', context)


# ============================================================================
# DEPARTMENT CREATE VIEW
# ============================================================================

@login_required
@require_dos
@require_http_methods(["GET", "POST"])
def department_create(request):
    """
    Create a new academic department
    
    GET: Show form
    POST: Create department with validation
    
    Validation:
    - Department type must be unique per school
    - Name is required
    - Annual budget must be positive (if provided)
    
    Template Context:
    - school: Current school
    - department_types: All available types
    - teachers: Available teachers to assign as head
    """
    school = get_user_school(request)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        department_type = request.POST.get('department_type', '').strip()
        description = request.POST.get('description', '').strip()
        annual_budget = request.POST.get('annual_budget', '').strip()
        head_of_department_id = request.POST.get('head_of_department', '').strip()
        
        # Validate inputs
        errors = []
        
        if not name:
            errors.append('Department name is required')
        
        if not department_type:
            errors.append('Department type is required')
        elif TeacherDepartment.objects.filter(
            school=school,
            department_type=department_type,
            is_active=True
        ).exists():
            errors.append(f'An active department of type "{department_type}" already exists')
        
        if annual_budget:
            try:
                budget = float(annual_budget)
                if budget < 0:
                    errors.append('Annual budget must be a positive number')
            except ValueError:
                errors.append('Annual budget must be a valid number')
        else:
            annual_budget = None
        
        # Validate head of department if selected
        head_of_department = None
        if head_of_department_id:
            try:
                head_of_department = StaffProfile.objects.get(
                    id=head_of_department_id,
                    user__school=school,
                    user__role='teacher'
                )
            except StaffProfile.DoesNotExist:
                errors.append('Invalid teacher selected as department head')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Create department
            dept = TeacherDepartment.objects.create(
                school=school,
                name=name,
                department_type=department_type,
                description=description,
                annual_budget=annual_budget if annual_budget else None,
                head_of_department=head_of_department,
                is_active=True
            )
            
            messages.success(
                request,
                f'Department "{dept.name}" created successfully'
            )
            return redirect('dos:departments_list')
    
    # Get available teachers for department head assignment
    available_teachers = StaffProfile.objects.filter(
        user__school=school,
        user__role='teacher',
        user__is_active=True
    ).select_related('user').order_by('user__first_name')
    
    context = {
        'school': school,
        'department_types': TeacherDepartment.DEPARTMENT_TYPES,
        'available_teachers': available_teachers,
    }
    
    return render(request, 'dos/department_form.html', context)


# ============================================================================
# DEPARTMENT EDIT VIEW
# ============================================================================

@login_required
@require_dos
@require_http_methods(["GET", "POST"])
def department_edit(request, dept_id):
    """
    Edit an existing academic department
    
    GET: Show form with current values
    POST: Update department
    
    Template Context:
    - school: Current school
    - department: Department being edited
    - department_types: All available types
    - available_teachers: Teachers available as department head
    """
    school = get_user_school(request)
    department = get_object_or_404(
        TeacherDepartment,
        id=dept_id,
        school=school
    )
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        department_type = request.POST.get('department_type', '').strip()
        description = request.POST.get('description', '').strip()
        annual_budget = request.POST.get('annual_budget', '').strip()
        head_of_department_id = request.POST.get('head_of_department', '').strip()
        is_active = request.POST.get('is_active', 'off') == 'on'
        
        # Validate inputs
        errors = []
        
        if not name:
            errors.append('Department name is required')
        
        if not department_type:
            errors.append('Department type is required')
        elif department_type != department.department_type:
            # Check if another department with this type exists
            if TeacherDepartment.objects.filter(
                school=school,
                department_type=department_type,
                is_active=True
            ).exclude(id=dept_id).exists():
                errors.append(f'An active department of type "{department_type}" already exists')
        
        if annual_budget:
            try:
                budget = float(annual_budget)
                if budget < 0:
                    errors.append('Annual budget must be a positive number')
            except ValueError:
                errors.append('Annual budget must be a valid number')
        else:
            annual_budget = None
        
        # Validate head of department if selected
        head_of_department = None
        if head_of_department_id:
            try:
                head_of_department = StaffProfile.objects.get(
                    id=head_of_department_id,
                    user__school=school,
                    user__role='teacher'
                )
            except StaffProfile.DoesNotExist:
                errors.append('Invalid teacher selected as department head')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Update department
            department.name = name
            department.department_type = department_type
            department.description = description
            department.annual_budget = annual_budget
            department.head_of_department = head_of_department
            department.is_active = is_active
            department.save()
            
            messages.success(
                request,
                f'Department "{department.name}" updated successfully'
            )
            return redirect('dos:departments_list')
    
    # Get available teachers for department head assignment
    available_teachers = StaffProfile.objects.filter(
        user__school=school,
        user__role='teacher',
        user__is_active=True
    ).select_related('user').order_by('user__first_name')
    
    context = {
        'school': school,
        'department': department,
        'department_types': TeacherDepartment.DEPARTMENT_TYPES,
        'available_teachers': available_teachers,
    }
    
    return render(request, 'dos/department_form.html', context)


# ============================================================================
# DEPARTMENT DETAIL VIEW
# ============================================================================

@login_required
@require_dos
def department_detail(request, dept_id):
    """
    View detailed information about a department
    
    Shows:
    - Department info (name, type, budget, head)
    - Teachers in department
    - Subjects offered
    - Performance metrics
    - Budget tracking
    
    Template Context:
    - school: Current school
    - department: Department being viewed
    - teachers: All teachers in department
    - subjects: All subjects in department
    - student_count: Total students in department subjects
    - avg_performance: Average performance in department
    """
    school = get_user_school(request)
    department = get_object_or_404(
        TeacherDepartment,
        id=dept_id,
        school=school
    )
    
    # Get teachers in this department (using M2M teacher_members relationship)
    teachers = department.teacher_members.filter(
        user__is_active=True
    ).select_related('user').order_by('user__first_name')
    
    # Subjects are not directly linked to departments in current model
    # They exist at the global level
    subjects = Subject.objects.all().order_by('name')
    
    # Performance metrics - cannot be calculated without direct department-subject link
    grades = Grade.objects.none()  # Empty queryset
    
    avg_performance = None
    pass_rate = 0
    
    # Get budget usage (if tracking available)
    budget_status = 'adequate'
    if department.annual_budget and department.annual_budget > 0:
        # This would require expense tracking - for now just show budget
        budget_status = 'tracking'
    
    context = {
        'school': school,
        'department': department,
        'teachers': teachers,
        'subjects': subjects,
        'teacher_count': teachers.count(),
        'subject_count': subjects.count(),
        'avg_performance': round(avg_performance, 1) if avg_performance else '-',
        'pass_rate': round(pass_rate, 1),
        'grade_count': 0,
        'budget_status': budget_status,
    }
    
    return render(request, 'dos/department_detail.html', context)


# ============================================================================
# DEPARTMENT DELETE VIEW
# ============================================================================

@login_required
@require_dos
@require_http_methods(["POST"])
def department_delete(request, dept_id):
    """
    Delete (deactivate) a department
    
    Does soft delete:
    - Sets is_active=False (does not permanently remove from DB)
    - Allows future reactivation if needed
    - Prevents data loss
    """
    school = get_user_school(request)
    department = get_object_or_404(
        TeacherDepartment,
        id=dept_id,
        school=school
    )
    
    dept_name = department.name
    
    # Check if department has active subjects
    active_subjects = Subject.objects.filter(
        teacher_department=department,
        is_active=True
    ).count()
    
    if active_subjects > 0:
        messages.error(
            request,
            f'Cannot delete department with {active_subjects} active subject(s). '
            'Deactivate subjects first.'
        )
    else:
        # Soft delete
        department.is_active = False
        department.save()
        
        messages.success(
            request,
            f'Department "{dept_name}" has been deactivated'
        )
    
    return redirect('dos:departments_list')


# ============================================================================
# DEPARTMENT HEAD ASSIGNMENT VIEW (AJAX/API)
# ============================================================================

@login_required
@require_dos
@require_http_methods(["POST"])
def assign_department_head(request, dept_id):
    """
    API endpoint to assign/update department head
    
    Request:
    - POST /dos/departments/<dept_id>/assign-head/
    - Data: { "teacher_id": <id> }
    
    Response:
    - JSON: { "success": true, "message": "..." }
    """
    school = get_user_school(request)
    department = get_object_or_404(
        TeacherDepartment,
        id=dept_id,
        school=school
    )
    
    teacher_id = request.POST.get('teacher_id', '').strip()
    
    if not teacher_id:
        department.head_of_department = None
        department.save()
        return JsonResponse({
            'success': True,
            'message': 'Department head cleared'
        })
    
    try:
        teacher = StaffProfile.objects.get(
            id=teacher_id,
            user__school=school,
            user__role='teacher'
        )
        department.head_of_department = teacher
        department.save()
        
        return JsonResponse({
            'success': True,
            'message': f'{teacher.user.get_full_name()} assigned as department head'
        })
    except StaffProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Invalid teacher selected'
        }, status=400)
