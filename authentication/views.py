from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.db import transaction, ProgrammingError
from django.utils import timezone

from SchoolNowMgt.models import CustomUser, School, StaffProfile
from .forms import UnifiedLoginForm, UnifiedRegistrationForm
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
        # Redirect authenticated users to their dashboard or admin
        if request.user.is_superuser:
            return redirect('/admin/')
        elif request.user.role == 'teacher':
            return redirect('teacher:dashboard')
        elif request.user.role == 'admin':
            return redirect('SchoolNowMgt:dashboard')
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
            
            # Role-based redirect
            if user.is_superuser:
                return redirect('/admin/')
            elif user.role == 'teacher':
                return redirect('teacher:dashboard')
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
# Routers now redirect to unified views - all role-specific views removed
# to ensure a single unified auth experience across all user roles
