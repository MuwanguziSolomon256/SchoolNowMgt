from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.db import transaction, ProgrammingError
from django.contrib import messages

from SchoolNowMgt.models import CustomUser, StaffProfile, School
from SchoolNowMgt.registration.forms import (
    TeacherRegistrationForm,
    AdminRegistrationForm,
    NonTeachingStaffRegistrationForm,
    ParentRegistrationForm,
)
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


def register_teacher(request):
    """
    Teacher self-registration view.
    
    GET: Display the registration form.
    POST: Process registration, create CustomUser and StaffProfile in atomic transaction,
          log in user, and redirect to teacher dashboard.
    
    No login required. No email verification for MVP.
    """
    school = get_school_safe()
    
    if request.method == 'GET':
        form = TeacherRegistrationForm()
        return render(request, 'SchoolNowMgt/registration/register.html', {
            'form': form,
            'school': school,
        })
    
    elif request.method == 'POST':
        form = TeacherRegistrationForm(request.POST)
        
        if form.is_valid():
            # Check for duplicate email BEFORE creating the user
            email = form.cleaned_data['email'].lower()
            if CustomUser.objects.filter(email=email).exists():
                form.add_error('email', 'An account with this email already exists.')
                return render(request, 'SchoolNowMgt/registration/register.html', {
                    'form': form,
                    'school': school,
                })
            
            # Use atomic transaction to ensure both CustomUser and StaffProfile are created
            # or both fail together
            try:
                with transaction.atomic():
                    # Create CustomUser
                    user = CustomUser(
                        username=email,
                        email=email,
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        phone=form.cleaned_data.get('phone', ''),
                        role='teacher',
                        school=school,
                        is_active=True,
                    )
                    user.set_password(form.cleaned_data['password1'])
                    user.save()
                    
                    # Generate unique employee ID
                    employee_id = generate_employee_id(school)
                    
                    # Create StaffProfile
                    staff_profile = StaffProfile(
                        user=user,
                        employee_id=employee_id,
                        position=form.cleaned_data['position'],
                        date_joined=form.cleaned_data['date_joined'],
                        salary=0,  # Salary is set to 0 at registration. Admin must update this via the admin panel.
                        is_full_time=True,
                    )
                    staff_profile.save()
                    
                    # Log in the user
                    login(request, user)
                    
                    # Redirect to teacher dashboard
                    return redirect('teacher:dashboard')
            
            except Exception as e:
                # If anything goes wrong, the transaction will be rolled back
                messages.error(request, 'An error occurred during registration. Please try again.')
                return render(request, 'SchoolNowMgt/registration/register.html', {
                    'form': form,
                    'school': school,
                })
        
        else:
            # Form is invalid, re-render with errors
            return render(request, 'SchoolNowMgt/registration/register.html', {
                'form': form,
                'school': school,
            })


def register_admin(request):
    """
    Admin/Staff self-registration view.
    
    GET: Display the registration form.
    POST: Process registration, create CustomUser and StaffProfile in atomic transaction,
          log in user, and redirect to admin dashboard.
    
    No login required. No email verification for MVP.
    """
    school = get_school_safe()
    
    if request.method == 'GET':
        form = AdminRegistrationForm()
        return render(request, 'registration/register_admin.html', {
            'form': form,
            'school': school,
            'role_display': 'Admin/Staff',
        })
    
    elif request.method == 'POST':
        form = AdminRegistrationForm(request.POST)
        
        if form.is_valid():
            # Check for duplicate email BEFORE creating the user
            email = form.cleaned_data['email'].lower()
            if CustomUser.objects.filter(email=email).exists():
                form.add_error('email', 'An account with this email already exists.')
                return render(request, 'registration/register_admin.html', {
                    'form': form,
                    'school': school,
                    'role_display': 'Admin/Staff',
                })
            
            try:
                with transaction.atomic():
                    # Create CustomUser
                    user = CustomUser(
                        username=email,
                        email=email,
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        phone=form.cleaned_data.get('phone', ''),
                        role='admin',
                        school=school,
                        is_active=True,
                        is_staff=True,  # Admin users should be staff
                    )
                    user.set_password(form.cleaned_data['password1'])
                    user.save()
                    
                    # Generate unique employee ID
                    employee_id = generate_employee_id(school)
                    
                    # Create StaffProfile
                    staff_profile = StaffProfile(
                        user=user,
                        employee_id=employee_id,
                        position=form.cleaned_data['position'],
                        date_joined=form.cleaned_data['date_joined'],
                        salary=0,
                        is_full_time=True,
                    )
                    staff_profile.save()
                    
                    # Log in the user
                    login(request, user)
                    
                    # Redirect to admin dashboard
                    return redirect('SchoolNowMgt:dashboard')
            
            except Exception as e:
                messages.error(request, 'An error occurred during registration. Please try again.')
                return render(request, 'registration/register_admin.html', {
                    'form': form,
                    'school': school,
                    'role_display': 'Admin/Staff',
                })
        
        else:
            return render(request, 'registration/register_admin.html', {
                'form': form,
                'school': school,
                'role_display': 'Admin/Staff',
            })


def register_non_teaching_staff(request):
    """
    Non-teaching staff self-registration view.
    
    GET: Display the registration form.
    POST: Process registration, create CustomUser and StaffProfile in atomic transaction,
          log in user, and redirect to dashboard.
    """
    school = get_school_safe()
    
    if request.method == 'GET':
        form = NonTeachingStaffRegistrationForm()
        return render(request, 'registration/register_staff.html', {
            'form': form,
            'school': school,
            'role_display': 'Non-Teaching Staff',
        })
    
    elif request.method == 'POST':
        form = NonTeachingStaffRegistrationForm(request.POST)
        
        if form.is_valid():
            # Check for duplicate email BEFORE creating the user
            email = form.cleaned_data['email'].lower()
            if CustomUser.objects.filter(email=email).exists():
                form.add_error('email', 'An account with this email already exists.')
                return render(request, 'registration/register_staff.html', {
                    'form': form,
                    'school': school,
                    'role_display': 'Non-Teaching Staff',
                })
            
            try:
                with transaction.atomic():
                    # Create CustomUser
                    user = CustomUser(
                        username=email,
                        email=email,
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        phone=form.cleaned_data.get('phone', ''),
                        role='non_teaching_staff',
                        school=school,
                        is_active=True,
                    )
                    user.set_password(form.cleaned_data['password1'])
                    user.save()
                    
                    # Generate unique employee ID
                    employee_id = generate_employee_id(school)
                    
                    # Create StaffProfile
                    staff_profile = StaffProfile(
                        user=user,
                        employee_id=employee_id,
                        position=form.cleaned_data['position'],
                        date_joined=form.cleaned_data['date_joined'],
                        salary=0,
                        is_full_time=True,
                    )
                    staff_profile.save()
                    
                    # Log in the user
                    login(request, user)
                    
                    # Redirect to admin dashboard (or a generic dashboard if available)
                    return redirect('SchoolNowMgt:dashboard')
            
            except Exception as e:
                messages.error(request, 'An error occurred during registration. Please try again.')
                return render(request, 'registration/register_staff.html', {
                    'form': form,
                    'school': school,
                    'role_display': 'Non-Teaching Staff',
                })
        
        else:
            return render(request, 'registration/register_staff.html', {
                'form': form,
                'school': school,
                'role_display': 'Non-Teaching Staff',
            })


def register_parent(request):
    """
    Parent/Guardian self-registration view.
    
    GET: Display the registration form.
    POST: Process registration, create CustomUser in atomic transaction,
          log in user, and redirect to dashboard.
    """
    school = get_school_safe()
    
    if request.method == 'GET':
        form = ParentRegistrationForm()
        return render(request, 'registration/register_parent.html', {
            'form': form,
            'school': school,
            'role_display': 'Parent/Guardian',
        })
    
    elif request.method == 'POST':
        form = ParentRegistrationForm(request.POST)
        
        if form.is_valid():
            # Check for duplicate email BEFORE creating the user
            email = form.cleaned_data['email'].lower()
            if CustomUser.objects.filter(email=email).exists():
                form.add_error('email', 'An account with this email already exists.')
                return render(request, 'registration/register_parent.html', {
                    'form': form,
                    'school': school,
                    'role_display': 'Parent/Guardian',
                })
            
            try:
                with transaction.atomic():
                    # Create CustomUser
                    user = CustomUser(
                        username=email,
                        email=email,
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        phone=form.cleaned_data.get('phone', ''),
                        role='parent',
                        school=school,
                        is_active=True,
                    )
                    user.set_password(form.cleaned_data['password1'])
                    user.save()
                    
                    # Log in the user
                    login(request, user)
                    
                    # Redirect to home for now (parent dashboard not yet implemented)
                    return redirect('home')
            
            except Exception as e:
                messages.error(request, 'An error occurred during registration. Please try again.')
                return render(request, 'registration/register_parent.html', {
                    'form': form,
                    'school': school,
                    'role_display': 'Parent/Guardian',
                })
        
        else:
            return render(request, 'registration/register_parent.html', {
                'form': form,
                'school': school,
                'role_display': 'Parent/Guardian',
            })
