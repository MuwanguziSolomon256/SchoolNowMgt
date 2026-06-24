from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.db import transaction, ProgrammingError
from django.utils import timezone

from SchoolNowMgt.models import CustomUser, School, StaffProfile
from .forms import UnifiedLoginForm, UnifiedRegistrationForm, ParentRegistrationForm
from SchoolNowMgt.registration.utils import generate_employee_id


def get_school_safe():
    """
    Safely get the first school from the database.
    Returns None if the table doesn't exist yet (during initial deployment).
    """
    try:
        return School.objects.first()
    except ProgrammingError:
        # School table doesn't exist yet - migrations haven't run
        return None


# ============================================================================
# UNIFIED AUTH FLOW - Login and Registration Combined
# ============================================================================

def unified_login(request):
    """
    UNIFIED LOGIN - Single page with role selector + login form.
    Combines role selection and credential entry in one flow.
    
    GET: Show unified login page with role selector and form
    POST: Validate role + email/password and authenticate
    """
    if request.user.is_authenticated:
        # Redirect authenticated users to their dashboard based on role + admin_role
        if request.user.is_superuser:
            return redirect('/admin/')
        elif request.user.role == 'teacher':
            # Check if teacher has an admin role
            try:
                staff_profile = request.user.staffprofile
                admin_role = staff_profile.teacher_admin_role
                
                # Redirect to admin dashboard based on admin role
                if admin_role == 'dos':
                    return redirect('/teacher/admin/dos/')
                elif admin_role == 'deputy_hm':
                    return redirect('/teacher/admin/deputy/')
                elif admin_role == 'head_teacher':
                    return redirect('/teacher/admin/head-teacher/')
                elif admin_role == 'department_head':
                    return redirect('/teacher/department/')
                else:
                    # Regular teacher
                    return redirect('/teacher/')
            except:
                # No staff profile, redirect to teacher dashboard
                return redirect('/teacher/')
        elif request.user.role == 'non_teaching_staff':
            # Check if support staff has an admin role
            try:
                staff_profile = request.user.staffprofile
                support_role = staff_profile.support_staff_role
                
                # Redirect to admin dashboard based on support staff role
                if support_role == 'welfare_coordinator':
                    return redirect('/teacher/matron/')
                elif support_role == 'supervisor':
                    return redirect('/teacher/support/shift-supervisor/')
                elif support_role == 'department_head':
                    return redirect('/teacher/support/dept-head/')
                else:
                    # Regular support staff
                    return redirect('/support/')
            except:
                # No staff profile, redirect to support dashboard
                return redirect('/support/')
        elif request.user.role == 'admin':
            return redirect('/admin/')
        elif request.user.role == 'parent':
            return redirect('/parent/')
        else:
            return redirect('/')
    
    if request.method == 'POST':
        # Get the selected role from form data
        role = request.POST.get('role', 'teacher')
        
        # Validate role
        valid_roles = ['teacher', 'admin', 'parent', 'non_teaching_staff']
        if role not in valid_roles:
            role = 'teacher'
        
        # Create form with selected role
        form = UnifiedLoginForm(request.POST, role=role)
        
        if form.is_valid():
            user = form.authenticated_user
            login(request, user)
            
            # Role-based redirect with admin role support
            if user.is_superuser:
                return redirect('/admin/')
            elif user.role == 'teacher':
                # Check if teacher has an admin role
                try:
                    staff_profile = user.staffprofile
                    admin_role = staff_profile.teacher_admin_role
                    
                    # Redirect to admin dashboard based on admin role
                    if admin_role == 'dos':
                        return redirect('/teacher/admin/dos/')
                    elif admin_role == 'deputy_hm':
                        return redirect('/teacher/admin/deputy/')
                    elif admin_role == 'head_teacher':
                        return redirect('/teacher/department/')
                    elif admin_role == 'department_head':
                        return redirect('/teacher/support/dept-head/')
                    else:
                        # Regular teacher (admin_role == 'teacher')
                        return redirect('/teacher/')
                except Exception as e:
                    # No staff profile, redirect to teacher dashboard
                    import sys
                    print(f"DEBUG: Exception in teacher redirect: {e}", file=sys.stderr)
                    return redirect('/teacher/')
            elif user.role == 'non_teaching_staff':
                # Check if support staff has an admin role
                try:
                    staff_profile = user.staffprofile
                    support_role = staff_profile.support_staff_role
                    
                    # Redirect to admin dashboard based on support staff role
                    if support_role == 'welfare_coordinator':
                        return redirect('/teacher/matron/')
                    elif support_role == 'supervisor':
                        return redirect('/teacher/support/shift-supervisor/')
                    elif support_role == 'department_head':
                        return redirect('/teacher/support/dept-head/')
                    else:
                        # Regular support staff
                        return redirect('/support/')
                except Exception as e:
                    import sys
                    print(f"DEBUG: Exception in non_teaching_staff redirect: {e}", file=sys.stderr)
                    return redirect('/support/')
            elif user.role == 'admin':
                return redirect('SchoolNowMgt:dashboard')
            elif user.role == 'parent':
                return redirect('SchoolNowMgt:parent_dashboard')
            else:
                return redirect('/')
        else:
            # Form has errors, re-render with submitted role
            context = {
                'form': form,
                'is_login': True,
            }
            return render(request, 'auth/unified_auth.html', context)
    else:
        # Default to 'teacher' role on GET request
        form = UnifiedLoginForm(role='teacher')
        context = {
            'form': form,
            'is_login': True,
        }
        return render(request, 'auth/unified_auth.html', context)


def unified_register(request):
    """
    UNIFIED REGISTRATION - Single page with role selector + registration form.
    
    GET: Show unified registration page
    POST: Validate and create user account
    """
    if request.user.is_authenticated:
        # Redirect authenticated users
        if request.user.is_superuser:
            return redirect('/admin/')
        elif request.user.role == 'teacher':
            return redirect('teacher:dashboard')
        elif request.user.role == 'parent':
            return redirect('SchoolNowMgt:parent_dashboard')
        else:
            return redirect('/')
    
    school = get_school_safe()
    
    if request.method == 'POST':
        role = request.POST.get('role', 'teacher')
        
        # Validate role
        valid_roles = ['teacher', 'admin', 'parent', 'non_teaching_staff']
        if role not in valid_roles:
            role = 'teacher'
        
        form = UnifiedRegistrationForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email'].lower()
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            password = form.cleaned_data['password1']
            
            # Create user based on role
            try:
                with transaction.atomic():
                    user = CustomUser(
                        username=email,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        role=role,
                        school=school,
                        is_active=True,
                    )
                    user.set_password(password)
                    user.save()
                    
                    # If teacher or support staff, create StaffProfile
                    if role in ['teacher', 'non_teaching_staff']:
                        employee_id = generate_employee_id(school)
                        staff_profile = StaffProfile(
                            user=user,
                            employee_id=employee_id,
                            position=role.replace('_', ' ').title(),
                            date_joined=timezone.now().date(),
                            salary=0,
                            is_full_time=True,
                        )
                        staff_profile.save()
                
                # Log in the user (OUTSIDE transaction to avoid session issues)
                # Set the backend attribute to avoid "multiple authentication backends" error
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                messages.success(request, f'Welcome {first_name}! Your account has been created.')
                
                # Role-based redirect
                if user.role == 'teacher':
                    return redirect('teacher:dashboard')
                elif user.role == 'parent':
                    return redirect('SchoolNowMgt:parent_dashboard')
                else:
                    return redirect('/')
            
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
                context = {
                    'form': form,
                    'is_login': False,
                }
                return render(request, 'auth/unified_auth.html', context)
        else:
            context = {
                'form': form,
                'is_login': False,
            }
            return render(request, 'auth/unified_auth.html', context)
    
    else:
        form = UnifiedRegistrationForm()
        context = {
            'form': form,
            'is_login': False,
        }
        return render(request, 'auth/unified_auth.html', context)


def login_role(request, role):
    """
    Route to unified login view.
    All roles now use the unified login page with role selector.
    """
    # Validate role
    valid_roles = ['teacher', 'admin', 'parent', 'non_teaching_staff']
    if role not in valid_roles:
        return redirect('auth:unified_login')
    
    # Redirect to unified login (unified page handles role selection)
    return redirect('auth:unified_login')


def register_role(request, role):
    """
    Route to unified registration view.
    All roles now use the unified registration page with role selector.
    """
    # Validate role
    valid_roles = ['teacher', 'admin', 'parent', 'non_teaching_staff']
    if role not in valid_roles:
        return redirect('auth:unified_register')
    
    # Redirect to unified register (unified page handles role selection)
    return redirect('auth:unified_register')


def parent_register(request):
    """
    Dedicated parent registration view.
    Parents register without a school - they access multiple schools via StudentParentRelationship.
    
    GET: Show parent registration form
    POST: Validate and create parent account
    """
    if request.user.is_authenticated:
        if request.user.role == 'parent':
            return redirect('parent_dashboard')
        else:
            return redirect('/')
    
    if request.method == 'POST':
        form = ParentRegistrationForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Use the form's save method to create user with school=NULL
                    user = form.save(commit=False)
                    user.username = form.cleaned_data['email'].lower()
                    user.set_password(form.cleaned_data['password1'])
                    user.save()
                
                # Log in the user
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                messages.success(
                    request, 
                    f"Welcome {form.cleaned_data['first_name']}! "
                    "Your parent account has been created. "
                    "Please wait for school administrators to link you with your children."
                )
                
                return redirect('parent_dashboard')
            
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
                context = {'form': form}
                return render(request, 'auth/parent_register.html', context)
        else:
            context = {'form': form}
            return render(request, 'auth/parent_register.html', context)
    
    else:
        form = ParentRegistrationForm()
        context = {'form': form}
        return render(request, 'auth/parent_register.html', context)


# Routers now redirect to unified views - all role-specific views removed
# to ensure a single unified auth experience across all user roles
