"""
Student-Parent Linking Views

Provides admin workflows for:
1. Linking existing parents to students
2. Creating and linking new parents
3. Managing parent-student relationships
4. Bulk importing parent-student mappings
5. Sending invitation emails to parents
"""

import csv
import io
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Q
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse

from SchoolNowMgt.models import (
    CustomUser, Student, StudentParentRelationship, School, ActivityLog, StaffProfile
)
from SchoolNowMgt.decorators import require_admin, get_user_school
from SchoolNowMgt.parent_linking_forms import (
    LinkExistingParentForm, CreateAndLinkParentForm,
    ManageParentRelationshipForm, BulkLinkParentsForm
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_temp_password(length=12):
    """Generate a temporary password for new parent accounts"""
    import secrets
    import string
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


def send_parent_invitation_email(parent, temp_password, student=None):
    """
    Send invitation email to newly created parent account.
    
    Includes:
    - Temporary password
    - Login URL
    - Student name(s) they're linked to
    - Instructions to change password on first login
    """
    try:
        subject = f"Welcome to {settings.SCHOOL_NAME} Parent Portal"
        
        context = {
            'parent_name': parent.get_full_name() or parent.email,
            'parent_email': parent.email,
            'temp_password': temp_password,
            'login_url': f"{settings.SITE_URL}/auth/login/",
            'student_name': student.get_full_name() if student else "Your child",
            'school_name': settings.SCHOOL_NAME,
        }
        
        html_message = render_to_string('emails/parent_invitation.html', context)
        plain_message = render_to_string('emails/parent_invitation.txt', context)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[parent.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return True, "Invitation email sent successfully"
    
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"


def record_linking_activity(staff, school, parent, student, action='linked'):
    """Record parent-student linking activity in activity log"""
    try:
        ActivityLog.objects.create(
            staff=staff,
            school=school,
            activity_type='parent_student_linked',
            description=f"Parent {parent.email} {action} to student {student.get_full_name()}",
            severity='info',
            icon_name='link'
        )
    except Exception as e:
        print(f"Error recording activity: {e}")


# ============================================================================
# LINK EXISTING PARENT
# ============================================================================

@login_required
@require_admin
def link_existing_parent(request, student_id=None):
    """
    Link an existing parent account to a student.
    
    GET: Show form to search and link parent
    POST: Create relationship and send confirmation
    
    URL params:
    - student_id: Pre-fill student in form
    
    Context:
    - school: User's school
    - form: LinkExistingParentForm instance
    - student: Pre-selected student (if provided)
    """
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Pre-fill student if provided
    initial = {}
    if student_id:
        try:
            student = get_object_or_404(Student, id=student_id, school=school)
            initial['student'] = student
        except:
            pass
    
    if request.method == 'POST':
        form = LinkExistingParentForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Get parent by email
                    parent = CustomUser.objects.get(
                        email=form.cleaned_data['parent_email'].lower(),
                        role='parent'
                    )
                    
                    student = form.cleaned_data['student']
                    school_obj = student.school or school
                    
                    # Check if relationship already exists
                    if StudentParentRelationship.objects.filter(
                        parent=parent,
                        student=student,
                        school=school_obj
                    ).exists():
                        messages.warning(
                            request,
                            f"{parent.get_full_name()} is already linked to {student.get_full_name()}"
                        )
                    else:
                        # Create relationship
                        relationship = StudentParentRelationship.objects.create(
                            parent=parent,
                            student=student,
                            school=school_obj,
                            relationship_type=form.cleaned_data['relationship_type'],
                            is_primary_guardian=form.cleaned_data['is_primary_guardian']
                        )
                        
                        # Record activity
                        record_linking_activity(staff_profile, school, parent, student, 'linked')
                        
                        messages.success(
                            request,
                            f"✓ {parent.get_full_name()} successfully linked to {student.get_full_name()}"
                        )
            
            except CustomUser.DoesNotExist:
                messages.error(
                    request,
                    f"Parent with email '{form.cleaned_data['parent_email']}' not found"
                )
            except Exception as e:
                messages.error(request, f"Error linking parent: {str(e)}")
            
            return redirect('admin:link_existing_parent')
    
    else:
        form = LinkExistingParentForm(initial=initial)
    
    # Get all students for form
    students = Student.objects.filter(school=school).order_by('first_name')
    form.fields['student'].queryset = students
    
    context = {
        'school': school,
        'form': form,
        'section': 'link_existing_parent',
    }
    
    return render(request, 'admin/link_existing_parent.html', context)


# ============================================================================
# CREATE AND LINK NEW PARENT
# ============================================================================

@login_required
@require_admin
def create_and_link_parent(request, student_id=None):
    """
    Create a new parent account and immediately link to student.
    
    GET: Show form to enter parent details
    POST: Create account, link to student, send invitation email
    
    URL params:
    - student_id: Pre-fill student in form
    
    Process:
    1. Validate form data
    2. Create CustomUser with role='parent', school=NULL
    3. Create StudentParentRelationship
    4. Send invitation email with temp password
    5. Record activity
    
    Context:
    - school: User's school
    - form: CreateAndLinkParentForm instance
    - student: Pre-selected student (if provided)
    - temp_password_display: Show temp password to admin (for manual sharing if email fails)
    """
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Pre-fill student if provided
    initial = {}
    if student_id:
        try:
            student = get_object_or_404(Student, id=student_id, school=school)
            initial['student'] = student
        except:
            pass
    
    temp_password_display = None
    
    if request.method == 'POST':
        form = CreateAndLinkParentForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Generate temp password
                    temp_password = generate_temp_password()
                    
                    # Create parent account (school=NULL)
                    parent = CustomUser.objects.create_user(
                        username=form.cleaned_data['email'].lower(),
                        email=form.cleaned_data['email'].lower(),
                        first_name=form.cleaned_data['first_name'].strip(),
                        last_name=form.cleaned_data['last_name'].strip(),
                        role='parent',
                        school=None,  # Parents have no school
                        is_active=True
                    )
                    
                    # Set temporary password
                    parent.set_password(temp_password)
                    parent.save()
                    
                    student = form.cleaned_data['student']
                    school_obj = student.school or school
                    
                    # Create relationship
                    relationship = StudentParentRelationship.objects.create(
                        parent=parent,
                        student=student,
                        school=school_obj,
                        relationship_type=form.cleaned_data['relationship_type'],
                        is_primary_guardian=form.cleaned_data['is_primary_guardian']
                    )
                    
                    # Record activity
                    record_linking_activity(staff_profile, school, parent, student, 'created and linked')
                    
                    # Send invitation email if requested
                    email_sent = False
                    if form.cleaned_data['send_invitation_email']:
                        success, msg = send_parent_invitation_email(parent, temp_password, student)
                        email_sent = success
                        if not success:
                            messages.warning(request, f"Account created but {msg}")
                    
                    if email_sent:
                        messages.success(
                            request,
                            f"✓ Parent account '{parent.email}' created and linked to {student.get_full_name()}. "
                            f"Invitation email sent."
                        )
                    else:
                        # Store temp password for admin to share if email failed
                        temp_password_display = temp_password
                        messages.success(
                            request,
                            f"✓ Parent account created and linked. "
                            f"Temporary password: {temp_password}"
                        )
            
            except Exception as e:
                messages.error(request, f"Error creating parent account: {str(e)}")
            
            if temp_password_display is None:
                return redirect('admin:create_and_link_parent')
    
    else:
        form = CreateAndLinkParentForm(initial=initial)
    
    # Get all students for form
    students = Student.objects.filter(school=school).order_by('first_name')
    form.fields['student'].queryset = students
    
    context = {
        'school': school,
        'form': form,
        'temp_password_display': temp_password_display,
        'section': 'create_and_link_parent',
    }
    
    return render(request, 'admin/create_and_link_parent.html', context)


# ============================================================================
# MANAGE PARENT-STUDENT RELATIONSHIPS
# ============================================================================

@login_required
@require_admin
def manage_parent_relationships(request, student_id=None):
    """
    List and manage all parent-student relationships.
    
    GET: Show list of relationships, filter by student
    POST (via AJAX): Edit relationship or remove
    
    Filtering:
    - student_id: Show relationships for specific student
    - search: Search by parent/student name
    
    Actions:
    - Edit relationship type or primary guardian status
    - Deactivate relationship
    - Reactivate relationship
    
    Context:
    - school: User's school
    - relationships: Paginated list of StudentParentRelationship
    - students: For filtering dropdown
    """
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Get relationships for school
    relationships = StudentParentRelationship.objects.filter(
        school=school
    ).select_related('parent', 'student').order_by('-date_linked')
    
    # Filter by student if provided
    if student_id:
        try:
            student = get_object_or_404(Student, id=student_id, school=school)
            relationships = relationships.filter(student=student)
        except:
            pass
    
    # Search filter
    search = request.GET.get('search', '').strip()
    if search:
        relationships = relationships.filter(
            Q(parent__first_name__icontains=search) |
            Q(parent__last_name__icontains=search) |
            Q(parent__email__icontains=search) |
            Q(student__first_name__icontains=search) |
            Q(student__last_name__icontains=search)
        )
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(relationships, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get all students for filter
    students = Student.objects.filter(school=school).order_by('first_name')
    
    context = {
        'school': school,
        'page_obj': page_obj,
        'students': students,
        'search': search,
        'section': 'manage_parent_relationships',
    }
    
    return render(request, 'admin/manage_parent_relationships.html', context)


@login_required
@require_admin
def edit_parent_relationship(request, relationship_id):
    """
    Edit an existing parent-student relationship (AJAX).
    
    Allows:
    - Change relationship type (mother/father/guardian/etc)
    - Toggle primary guardian status
    - Deactivate/reactivate relationship
    
    Returns:
    - JSON response with success status
    """
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    relationship = get_object_or_404(
        StudentParentRelationship,
        id=relationship_id,
        school=school
    )
    
    if request.method == 'POST':
        form = ManageParentRelationshipForm(request.POST, instance=relationship)
        
        if form.is_valid():
            try:
                form.save()
                
                # Record activity
                record_linking_activity(
                    staff_profile, school,
                    relationship.parent,
                    relationship.student,
                    'relationship updated'
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Relationship updated successfully'
                })
            
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error updating relationship: {str(e)}'
                })
        
        else:
            return JsonResponse({
                'success': False,
                'message': 'Form validation failed',
                'errors': form.errors
            })
    
    # GET: Return edit form
    form = ManageParentRelationshipForm(instance=relationship)
    
    return render(request, 'admin/edit_parent_relationship_form.html', {
        'form': form,
        'relationship': relationship,
    })


# ============================================================================
# BULK IMPORT PARENT-STUDENT MAPPINGS
# ============================================================================

@login_required
@require_admin
def bulk_link_parents(request):
    """
    Bulk link parents to students via CSV upload.
    
    CSV Format:
    admission_number, parent_email, relationship_type, is_primary_guardian
    
    Example:
    STU001, parent1@example.com, mother, true
    STU001, parent2@example.com, father, false
    STU002, parent3@example.com, guardian, true
    
    Process:
    1. Parse CSV file
    2. For each row:
       - Find student by admission number
       - Find/create parent by email
       - Create relationship
    3. Send invitation emails if requested
    4. Return report with success/failure count
    
    Context:
    - school: User's school
    - form: BulkLinkParentsForm instance
    - import_report: Results of import (if POST)
    """
    school = get_user_school(request)
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    import_report = None
    
    if request.method == 'POST':
        form = BulkLinkParentsForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                csv_file = request.FILES['csv_file']
                decoded_file = csv_file.read().decode('utf-8')
                csv_reader = csv.DictReader(io.StringIO(decoded_file))
                
                success_count = 0
                error_count = 0
                errors = []
                
                with transaction.atomic():
                    for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (skip header)
                        try:
                            admission_number = row.get('admission_number', '').strip()
                            parent_email = row.get('parent_email', '').lower().strip()
                            relationship_type = row.get('relationship_type', 'parent').strip()
                            is_primary = row.get('is_primary_guardian', 'false').lower() == 'true'
                            
                            # Validate required fields
                            if not admission_number or not parent_email:
                                raise ValueError("Missing admission_number or parent_email")
                            
                            # Find student
                            student = Student.objects.get(
                                admission_number=admission_number,
                                school=school
                            )
                            
                            # Find or create parent
                            parent, created = CustomUser.objects.get_or_create(
                                email=parent_email,
                                defaults={
                                    'username': parent_email,
                                    'role': 'parent',
                                    'school': None,
                                    'first_name': row.get('parent_first_name', 'Parent'),
                                    'last_name': row.get('parent_last_name', 'Parent'),
                                }
                            )
                            
                            if parent.role != 'parent':
                                raise ValueError(f"User {parent_email} is not a parent account")
                            
                            # Create relationship
                            relationship, created = StudentParentRelationship.objects.get_or_create(
                                parent=parent,
                                student=student,
                                school=school,
                                defaults={
                                    'relationship_type': relationship_type,
                                    'is_primary_guardian': is_primary,
                                }
                            )
                            
                            # Send invitation if new account and requested
                            if created and form.cleaned_data['send_invitation_emails']:
                                temp_password = generate_temp_password()
                                parent.set_password(temp_password)
                                parent.save()
                                send_parent_invitation_email(parent, temp_password, student)
                            
                            success_count += 1
                        
                        except Exception as e:
                            error_count += 1
                            errors.append(f"Row {row_num}: {str(e)}")
                
                # Record activity
                record_linking_activity(
                    staff_profile, school,
                    CustomUser(email='bulk_import'),
                    None,
                    f'bulk imported {success_count} relationships'
                )
                
                import_report = {
                    'success_count': success_count,
                    'error_count': error_count,
                    'errors': errors[:10],  # Show first 10 errors
                    'total_errors': len(errors),
                }
                
                if error_count == 0:
                    messages.success(
                        request,
                        f"✓ Successfully linked {success_count} parent-student relationships"
                    )
                else:
                    messages.warning(
                        request,
                        f"Completed with {success_count} success and {error_count} errors. "
                        f"See details below."
                    )
            
            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")
    
    else:
        form = BulkLinkParentsForm()
    
    context = {
        'school': school,
        'form': form,
        'import_report': import_report,
        'section': 'bulk_link_parents',
    }
    
    return render(request, 'admin/bulk_link_parents.html', context)


# ============================================================================
# AJAX ENDPOINTS
# ============================================================================

@login_required
@require_admin
def get_students_ajax(request):
    """
    AJAX endpoint to get students for a school.
    
    GET params:
    - search: Search term for student name
    - school_id: School ID (optional)
    
    Returns:
    - JSON list of students: [{'id': 1, 'name': 'John Doe', ...}, ...]
    """
    school = get_user_school(request)
    search = request.GET.get('search', '').strip()
    
    students = Student.objects.filter(school=school).order_by('first_name')
    
    if search:
        students = students.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(admission_number__icontains=search)
        )
    
    data = [
        {
            'id': s.id,
            'name': f"{s.get_full_name()} ({s.admission_number})",
            'admission_number': s.admission_number,
        }
        for s in students[:20]  # Limit to first 20
    ]
    
    return JsonResponse({'students': data})
