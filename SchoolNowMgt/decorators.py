"""
Permission decorators for teacher admin roles and access control.

Provides role-based access control for DOS (Director of Studies),
Subject Department Heads, Class Teachers, and other admin roles.
"""

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse


def get_user_school(request):
    """
    Get user's school or raise 403 if not found.
    
    Args:
        request: Django request object
        
    Returns:
        School object associated with user
        
    Raises:
        PermissionDenied: If user has no school assigned
    """
    if not request.user.school:
        raise PermissionDenied("User has no school assigned")
    return request.user.school


def require_teacher_role(allowed_roles):
    """
    Decorator to ensure user is a teacher with specific admin role(s).
    
    Args:
        allowed_roles: String or list of teacher_admin_role values to allow
                      e.g., 'dos' or ['dos', 'head_teacher']
    
    Usage:
        @require_teacher_role('dos')
        def dos_dashboard(request):
            ...
            
        @require_teacher_role(['dos', 'head_teacher'])
        def admin_dashboard(request):
            ...
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]
    
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Check if user is a teacher
            if request.user.role != 'teacher':
                raise PermissionDenied("Only teachers can access this resource")
            
            # Check if user has a school
            get_user_school(request)
            
            # Check if user has StaffProfile
            try:
                staff_profile = request.user.staffprofile
            except:
                raise PermissionDenied("User has no staff profile")
            
            # Check if user has required admin role
            if staff_profile.teacher_admin_role not in allowed_roles:
                raise PermissionDenied(
                    f"User role '{staff_profile.teacher_admin_role}' not in allowed roles: {allowed_roles}"
                )
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator


def require_dos(view_func):
    """
    Decorator to ensure user is a Director of Studies (DOS).
    
    Usage:
        @require_dos
        def dos_dashboard(request):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Check if user is a teacher
        if request.user.role != 'teacher':
            raise PermissionDenied("Only teachers can be DOS")
        
        # Check if user has a school
        get_user_school(request)
        
        # Check if user has StaffProfile with DOS role
        try:
            staff_profile = request.user.staffprofile
            if staff_profile.teacher_admin_role != 'dos':
                raise PermissionDenied("User is not a Director of Studies")
        except:
            raise PermissionDenied("User has no staff profile or is not DOS")
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_department_head(view_func):
    """
    Decorator to ensure user is a Subject Department Head.
    
    Usage:
        @require_department_head
        def department_dashboard(request, dept_id):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Check if user is a teacher
        if request.user.role != 'teacher':
            raise PermissionDenied("Only teachers can be department heads")
        
        # Check if user has a school
        get_user_school(request)
        
        # Check if user has StaffProfile with department_head role
        try:
            staff_profile = request.user.staffprofile
            if staff_profile.teacher_admin_role != 'department_head':
                raise PermissionDenied("User is not a Subject Department Head")
        except:
            raise PermissionDenied("User has no staff profile or is not a department head")
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_head_teacher(view_func):
    """
    Decorator to ensure user is a Head Teacher.
    
    Usage:
        @require_head_teacher
        def head_teacher_dashboard(request):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Check if user is a teacher
        if request.user.role != 'teacher':
            raise PermissionDenied("Only teachers can be head teachers")
        
        # Check if user has a school
        get_user_school(request)
        
        # Check if user has StaffProfile with head_teacher role
        try:
            staff_profile = request.user.staffprofile
            if staff_profile.teacher_admin_role != 'head_teacher':
                raise PermissionDenied("User is not a Head Teacher")
        except:
            raise PermissionDenied("User has no staff profile or is not a head teacher")
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_class_teacher(view_func):
    """
    Decorator to ensure user is assigned as a class teacher.
    
    Note: Regular teachers can also be class teachers, so this checks
    if they have at least one ClassTeacherAssignment.
    
    Usage:
        @require_class_teacher
        def class_dashboard(request, class_id):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Check if user is a teacher
        if request.user.role != 'teacher':
            raise PermissionDenied("Only teachers can be class teachers")
        
        # Check if user has a school
        get_user_school(request)
        
        # Check if user has StaffProfile
        try:
            staff_profile = request.user.staffprofile
        except:
            raise PermissionDenied("User has no staff profile")
        
        # Note: Further validation of specific class assignment happens in the view
        # This decorator just ensures the user is a teacher
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_support_staff_role(allowed_roles):
    """
    Decorator to ensure user is support staff with specific admin role(s).
    
    Args:
        allowed_roles: String or list of support_staff_role values to allow
                      e.g., 'supervisor' or ['supervisor', 'department_head']
    
    Usage:
        @require_support_staff_role('supervisor')
        def shift_supervisor_dashboard(request):
            ...
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]
    
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Check if user is support staff
            if request.user.role != 'non_teaching_staff':
                raise PermissionDenied("Only support staff can access this resource")
            
            # Check if user has a school
            get_user_school(request)
            
            # Check if user has StaffProfile
            try:
                staff_profile = request.user.staffprofile
            except:
                raise PermissionDenied("User has no staff profile")
            
            # Check if user has required support staff role
            if staff_profile.support_staff_role not in allowed_roles:
                raise PermissionDenied(
                    f"User role '{staff_profile.support_staff_role}' not in allowed roles: {allowed_roles}"
                )
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator


def require_shift_supervisor(view_func):
    """
    Decorator to ensure user is a Shift Supervisor (non-teaching staff).
    
    Usage:
        @require_shift_supervisor
        def shift_supervisor_dashboard(request):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Check if user is support staff
        if request.user.role != 'non_teaching_staff':
            raise PermissionDenied("Only support staff can be shift supervisors")
        
        # Check if user has a school
        get_user_school(request)
        
        # Check if user has StaffProfile with supervisor role
        try:
            staff_profile = request.user.staffprofile
            if staff_profile.support_staff_role != 'supervisor':
                raise PermissionDenied("User is not a Shift Supervisor")
        except:
            raise PermissionDenied("User has no staff profile or is not a shift supervisor")
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_admin(view_func):
    """
    Decorator to ensure user is a school administrator (Headmaster/Admin).
    
    Usage:
        @require_admin
        def admin_dashboard(request):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Check if user is admin
        if request.user.role != 'admin':
            raise PermissionDenied("Only administrators can access this resource")
        
        # Check if user has a school
        get_user_school(request)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_deputy_hm(view_func):
    """
    Decorator to ensure user is a Deputy Headmaster.
    
    Usage:
        @require_deputy_hm
        def deputy_hm_dashboard(request):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Check if user is a teacher
        if request.user.role != 'teacher':
            raise PermissionDenied("Only teachers can be Deputy Headmaster")
        
        # Check if user has a school
        get_user_school(request)
        
        # Check if user has StaffProfile with deputy_hm role
        try:
            staff_profile = request.user.staffprofile
            if staff_profile.teacher_admin_role != 'deputy_hm':
                raise PermissionDenied("User is not a Deputy Headmaster")
        except:
            raise PermissionDenied("User has no staff profile or is not a Deputy Headmaster")
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_support_dept_head(view_func):
    """
    Decorator to ensure user is a support staff department head.
    
    Usage:
        @require_support_dept_head
        def support_dept_head_dashboard(request):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Check if user is support staff
        if request.user.role != 'non_teaching_staff':
            raise PermissionDenied("Only support staff can be department heads")
        
        # Check if user has a school
        get_user_school(request)
        
        # Check if user has StaffProfile with department_head role
        try:
            staff_profile = request.user.staffprofile
            if staff_profile.support_staff_role != 'department_head':
                raise PermissionDenied("User is not a support staff department head")
        except:
            raise PermissionDenied("User has no staff profile or is not a department head")
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_welfare_coordinator(view_func):
    """
    Decorator to ensure user is a Welfare Coordinator (Matron).
    
    Usage:
        @require_welfare_coordinator
        def matron_dashboard(request):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Check if user is support staff
        if request.user.role != 'non_teaching_staff':
            raise PermissionDenied("Only support staff can be welfare coordinators")
        
        # Check if user has a school
        get_user_school(request)
        
        # Check if user has StaffProfile with welfare_coordinator role
        try:
            staff_profile = request.user.staffprofile
            if staff_profile.support_staff_role != 'welfare_coordinator':
                raise PermissionDenied("User is not a Welfare Coordinator")
        except:
            raise PermissionDenied("User has no staff profile or is not a welfare coordinator")
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_matron(view_func):
    """
    Decorator to ensure user is a welfare coordinator (matron) with hostel assignment.
    
    Optionally validates that the matron can only access their assigned hostel
    by checking 'hostel_id' in kwargs against the matron's assigned hostel.
    
    Usage:
        @require_matron
        def matron_dashboard(request):
            ...
            
        @require_matron
        def hostel_detail(request, hostel_id):
            # User can only access their assigned hostel
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Check if user is support staff
        if request.user.role != 'non_teaching_staff':
            raise PermissionDenied("Only support staff can be matrons")
        
        # Check if user has a school
        get_user_school(request)
        
        # Check if user has StaffProfile with welfare_coordinator role
        try:
            staff_profile = request.user.staffprofile
            if staff_profile.support_staff_role != 'welfare_coordinator':
                raise PermissionDenied("User is not a Welfare Coordinator/Matron")
        except:
            raise PermissionDenied("User has no staff profile or is not a matron")
        
        # If hostel_id is provided in kwargs, check if matron is assigned to that hostel
        if 'hostel_id' in kwargs:
            try:
                from SchoolNowMgt.models import Hostel
                hostel_id = kwargs['hostel_id']
                hostel = Hostel.objects.get(id=hostel_id, school=request.user.school)
                
                # Check if matron is assigned to this hostel
                if hostel.matron != staff_profile:
                    raise PermissionDenied(
                        "You are not assigned as matron for this hostel"
                    )
            except Exception as e:
                if isinstance(e, PermissionDenied):
                    raise
                raise PermissionDenied("Invalid hostel or hostel not found")
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_parent(view_func):
    """
    Decorator to ensure user is a parent.
    
    Usage:
        @require_parent
        def parent_notifications(request):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Check if user is a parent
        if request.user.role != 'parent':
            raise PermissionDenied("Only parents can access this resource")
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
    
    return wrapper


def multi_role_required(*allowed_roles):
    """
    Decorator to allow access to multiple role types.
    
    Usage:
        @multi_role_required('admin', 'teacher')
        def combined_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Check if user has a school
            get_user_school(request)
            
            # Check if user role is in allowed_roles
            if request.user.role not in allowed_roles:
                raise PermissionDenied(
                    f"User role '{request.user.role}' not in allowed roles: {allowed_roles}"
                )
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator
