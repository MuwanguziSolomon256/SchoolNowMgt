# Complete Administrative Roles & Department Implementation Guide

**Project**: School Management System (Multi-School)  
**Date Started**: June 18, 2026  
**Status**: Design Complete - Ready for Implementation  

---

## TABLE OF CONTENTS
1. [System Overview](#system-overview)
2. [Database Models](#database-models)
3. [User Roles & Hierarchy](#user-roles--hierarchy)
4. [Admin-Teacher Dashboards](#admin-teacher-dashboards)
5. [Support Staff Departments](#support-staff-departments)
6. [Teacher Departments](#teacher-departments)
7. [URL Routes](#url-routes)
8. [Permission & Access Control](#permission--access-control)
9. [Implementation Checklist](#implementation-checklist)

---

## SYSTEM OVERVIEW

### **Three Organizational Hierarchies**

\`\`\`
HIERARCHY 1: HEADMASTER (Full Control)
└── Admin Dashboard (/admin/)
    └── Access to everything

HIERARCHY 2: TEACHING STAFF (DOS manages)
└── Director of Studies (DOS) - Teacher with admin role
    ├── Subject Department Heads (Teachers)
    ├── Class Teachers (Teachers)
    └── Regular Teachers

HIERARCHY 3: NON-TEACHING STAFF (Deputy HM manages)
└── Deputy Headmaster (General Duties) - Teacher with admin role
    ├── Support Department Heads (Non-teaching staff)
    ├── Matrons (Non-teaching staff)
    ├── Shift Supervisors (Non-teaching staff)
    └── Regular Support Staff
\`\`\`

---

## DATABASE MODELS

### **PHASE 1: Core Models (Required)**

#### 1. Department Model (Support Staff)
**File**: \`SchoolNowMgt/models.py\`  
**Purpose**: Non-teaching support staff departments

\`\`\`python
class Department(models.Model):
    """Non-teaching staff departments per school"""
    DEPARTMENT_TYPES = [
        ('security', 'Security (Askaris)'),
        ('matron', 'Matrons/Hostels'),
        ('catering', 'Kitchen/Catering'),
        ('cleaning', 'Cleaning/Housekeeping'),
        ('maintenance', 'Maintenance & Grounds'),
        ('health', 'Health & Wellness'),
        ('welfare', 'Welfare & Counseling'),
        ('transport', 'Transport & Drivers'),
        ('library', 'Library'),
        ('laboratory', 'Laboratory'),
        ('it', 'IT & Computer'),
        ('reception', 'Reception & Admin'),
        ('facilities', 'Facilities Management'),
        ('sports', 'Sports & Recreation'),
        ('other', 'Other'),
    ]
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='support_departments')
    name = models.CharField(max_length=100)
    department_type = models.CharField(max_length=20, choices=DEPARTMENT_TYPES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # Department Head (Senior non-teaching staff member)
    head_of_department = models.ForeignKey(
        'StaffProfile',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='heads_support_department',
        limit_choices_to={'user__role': 'non_teaching_staff'}
    )
    
    # Budget for department operations
    monthly_budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Monthly budget allocation in local currency"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('school', 'department_type')
        verbose_name_plural = 'Support Departments'
    
    def __str__(self):
        return f"{self.name} ({self.school.name})"
\`\`\`

---

#### 2. Hostel Model (For Matrons)
**File**: \`SchoolNowMgt/models.py\`  
**Purpose**: Hostel/Dormitory assignments for matrons

\`\`\`python
class Hostel(models.Model):
    """Hostel/Dormitory for boarding schools with assigned matron"""
    HOSTEL_TYPES = [
        ('boys', 'Boys Hostel'),
        ('girls', 'Girls Hostel'),
        ('mixed', 'Mixed Hostel'),
    ]
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='hostels')
    name = models.CharField(max_length=100)  # e.g., "Boys Hostel A", "Girls Hostel B"
    hostel_type = models.CharField(max_length=20, choices=HOSTEL_TYPES)
    capacity = models.IntegerField()
    
    # Assigned Matron (One matron per hostel)
    matron = models.OneToOneField(
        'StaffProfile',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='manages_hostel',
        limit_choices_to={
            'user__role': 'non_teaching_staff',
            'support_department__department_type': 'matron'
        }
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('school', 'name')
    
    def __str__(self):
        return f"{self.name} (Capacity: {self.capacity})"
\`\`\`

---

#### 3. TeacherDepartment Model (Subject Departments)
**File**: \`SchoolNowMgt/models.py\`  
**Purpose**: Subject/Academic departments managed by DOS

\`\`\`python
class TeacherDepartment(models.Model):
    """Subject/Academic departments managed by DOS"""
    DEPARTMENT_TYPES = [
        ('mathematics', 'Mathematics'),
        ('science', 'Science'),
        ('languages', 'Languages'),
        ('social_studies', 'Social Studies'),
        ('technology', 'Technology & ICT'),
        ('pe_sports', 'Physical Education & Sports'),
        ('arts_music', 'Arts & Music'),
        ('humanities', 'Humanities'),
        ('vocational', 'Vocational Studies'),
        ('other', 'Other'),
    ]
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='teacher_departments')
    name = models.CharField(max_length=100)
    department_type = models.CharField(max_length=20, choices=DEPARTMENT_TYPES)
    description = models.TextField(blank=True)
    
    # Department Head (Teacher only)
    head_of_department = models.ForeignKey(
        'StaffProfile',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='heads_teacher_department',
        limit_choices_to={'user__role': 'teacher'}
    )
    
    # Budget for resources
    annual_budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('school', 'department_type')
        verbose_name_plural = 'Teacher Departments'
    
    def __str__(self):
        return f"{self.name} ({self.school.name})"
\`\`\`

---

#### 4. ClassTeacherAssignment Model
**File**: \`SchoolNowMgt/models.py\`  
**Purpose**: Assign teachers to classes for pastoral care

\`\`\`python
class ClassTeacherAssignment(models.Model):
    """Links a teacher to a class as the class teacher"""
    
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    class_grade = models.ForeignKey(
        ClassGrade,
        on_delete=models.CASCADE,
        related_name='class_teacher_assignments'
    )
    teacher = models.ForeignKey(
        'StaffProfile',
        on_delete=models.PROTECT,
        related_name='class_teacher_assignments',
        limit_choices_to={'user__role': 'teacher'}
    )
    
    # Academic year (e.g., "2024-2025")
    academic_year = models.CharField(max_length=9)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    assigned_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('school', 'class_grade', 'academic_year')
        # One class teacher per class per academic year
    
    def __str__(self):
        return f"{self.teacher.user.get_full_name()} - {self.class_grade.name} ({self.academic_year})"
\`\`\`

---

#### 5. Update StaffProfile Model
**File**: \`SchoolNowMgt/models.py\`  
**Purpose**: Add administrative role fields

\`\`\`python
# IN EXISTING StaffProfile MODEL - ADD THESE FIELDS:

class StaffProfile(models.Model):
    # ... existing fields ...
    
    # ===== NEW FIELDS FOR TEACHERS =====
    teacher_department = models.ForeignKey(
        'TeacherDepartment',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='teacher_members',
        help_text="Subject department this teacher belongs to"
    )
    
    TEACHER_ADMIN_ROLE_CHOICES = [
        ('teacher', 'Class/Subject Teacher'),
        ('dos', 'Director of Studies'),
        ('department_head', 'Subject Department Head'),
        ('head_teacher', 'Head Teacher'),
    ]
    
    teacher_admin_role = models.CharField(
        max_length=50,
        choices=TEACHER_ADMIN_ROLE_CHOICES,
        default='teacher',
        help_text="Administrative role if teacher has one"
    )
    
    # ===== NEW FIELDS FOR SUPPORT STAFF =====
    support_department = models.ForeignKey(
        'Department',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='support_staff_members',
        help_text="Department for non-teaching staff"
    )
    
    SUPPORT_STAFF_ROLE_CHOICES = [
        ('staff', 'Regular Staff Member'),
        ('supervisor', 'Shift Supervisor'),
        ('department_head', 'Department Head'),
        ('welfare_coordinator', 'Welfare Coordinator'),
    ]
    
    support_staff_role = models.CharField(
        max_length=50,
        choices=SUPPORT_STAFF_ROLE_CHOICES,
        default='staff',
        help_text="Administrative role within support staff"
    )
    
    # For shift supervisors: who they report to
    assigned_shift_supervisor = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='supervised_staff',
        limit_choices_to={'support_staff_role': 'supervisor'},
        help_text="Supervisor this staff member reports to"
    )
\`\`\`

---

## URL ROUTES

### **Director of Studies (DOS) URLs**
\`\`\`
/teacher/admin/dos/                           → Main DOS dashboard
/teacher/admin/dos/timetable/                 → Timetable management
/teacher/admin/dos/timetable/create/          → Create new timetable entry
/teacher/admin/dos/class-teachers/            → Class teacher assignments
/teacher/admin/dos/departments/               → Subject departments overview
/teacher/admin/dos/curriculum/                → Curriculum management
/teacher/admin/dos/reports/                   → Reports
\`\`\`

### **Deputy Headmaster URLs**
\`\`\`
/teacher/admin/deputy/                        → Main Deputy HM dashboard
/teacher/admin/deputy/staff/                  → All support staff overview
/teacher/admin/deputy/departments/            → All support departments
/teacher/admin/deputy/shifts/                 → Shift management
/teacher/admin/deputy/facilities/             → Facilities & maintenance
/teacher/admin/deputy/hostels/                → Hostels overview (if boarding)
\`\`\`

### **Subject Department Head URLs**
\`\`\`
/teacher/department/<dept_id>/                → Department dashboard
/teacher/department/<dept_id>/team/           → Team members
/teacher/department/<dept_id>/performance/    → Academic performance
/teacher/department/<dept_id>/resources/      → Resources & budget
\`\`\`

### **Support Staff Department Head URLs**
\`\`\`
/support/department/<dept_id>/                → Department dashboard
/support/department/<dept_id>/team/           → My team
/support/department/<dept_id>/shifts/         → Shift management
/support/department/<dept_id>/budget/         → Budget tracking
\`\`\`

### **Matron URLs**
\`\`\`
/support/hostel/<hostel_id>/                  → Matron dashboard
/support/hostel/<hostel_id>/students/         → Student check-in/out
/support/hostel/<hostel_id>/rooms/            → Room assignments
/support/hostel/<hostel_id>/health/           → Health issues
\`\`\`

---

## IMPLEMENTATION CHECKLIST

### **PHASE 1: Database & Models (Week 1)**
- [ ] Create migration: Add Department model
- [ ] Create migration: Add Hostel model
- [ ] Create migration: Add TeacherDepartment model
- [ ] Create migration: Add ClassTeacherAssignment model
- [ ] Create migration: Update StaffProfile with new fields
- [ ] Update admin.py with new model admins
- [ ] Test model relationships and constraints

### **PHASE 2: Authentication & Decorators (Week 1-2)**
- [ ] Create decorators.py with all permission decorators
- [ ] Update registration/login flows to support new roles
- [ ] Create fixtures with sample data
- [ ] Test authentication for each role

### **PHASE 3: DOS Dashboard (Week 2-3)**
- [ ] Create dashboard/dos_views.py
- [ ] Create templates for DOS dashboard
- [ ] Implement timetable CRUD views
- [ ] Implement class teacher assignment views
- [ ] Add URL routes
- [ ] Test end-to-end

### **PHASE 4: Deputy HM Dashboard (Week 3-4)**
- [ ] Create dashboard/deputy_hm_views.py
- [ ] Create templates
- [ ] Implement views for all sections
- [ ] Add URL routes
- [ ] Test end-to-end

### **PHASE 5: Support Staff Department Dashboards (Week 4-5)**
- [ ] Create SchoolNowMgt/support_department_views.py
- [ ] Create templates
- [ ] Implement views
- [ ] Add URL routes

### **PHASE 6: Matron & Hostel Dashboards (Week 5-6)**
- [ ] Create SchoolNowMgt/matron_views.py
- [ ] Create templates
- [ ] Implement views
- [ ] Add URL routes

### **PHASE 7: Subject Department Dashboards (Week 6-7)**
- [ ] Create dashboard/department_views.py (for teachers)
- [ ] Create templates
- [ ] Implement views
- [ ] Add URL routes

### **PHASE 8: Class Teacher Dashboards (Week 7)**
- [ ] Create dashboard/class_teacher_views.py
- [ ] Create templates
- [ ] Implement views
- [ ] Add URL routes

### **PHASE 9: Integration & Testing (Week 8)**
- [ ] End-to-end testing
- [ ] Permission tests
- [ ] Performance testing

### **PHASE 10: Documentation & Deployment (Week 9)**
- [ ] Update admin documentation
- [ ] Create user guides
- [ ] Deploy to staging
- [ ] Deploy to production

---

## PERMISSION DECORATORS

**File**: Create \`SchoolNowMgt/decorators.py\`

\`\`\`python
from functools import wraps
from django.shortcuts import redirect

def require_dos(view_func):
    """Ensure user is Director of Studies"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'teacher':
            return redirect('teacher:login')
        try:
            staff = request.user.staffprofile
            if staff.teacher_admin_role != 'dos':
                return redirect('teacher:dashboard')
        except:
            return redirect('teacher:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

def require_deputy_hm(view_func):
    """Ensure user is Deputy Headmaster"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'teacher':
            return redirect('teacher:login')
        try:
            staff = request.user.staffprofile
            if staff.teacher_admin_role != 'deputy_hm':
                return redirect('teacher:dashboard')
        except:
            return redirect('teacher:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

def require_support_dept_head(view_func):
    """Ensure user is support department head"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'non_teaching_staff':
            return redirect('teacher:login')
        try:
            staff = request.user.staffprofile
            if staff.support_staff_role != 'department_head':
                return redirect('support:dashboard')
        except:
            return redirect('support:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
\`\`\`

---

## COMMON IMPLEMENTATION ERRORS TO AVOID

1. ❌ Confusing Teacher models with Support Staff models
2. ❌ Allowing Deputy HM to manage teachers (DOS only)
3. ❌ Not enforcing unique constraints
4. ❌ Not checking permissions in views
5. ❌ Creating admin access for non-admin users
6. ❌ Mixing teacher and support staff dashboards
7. ❌ Not filtering data by school in multi-school system
8. ❌ Not handling budget calculations correctly

---

## TESTING SCENARIOS

### **Test Case 1: DOS Workflow**
1. Login as DOS
2. View timetable
3. Create new timetable entry
4. Assign class teacher
5. View subject departments
6. ✓ Should NOT see finance, support staff

### **Test Case 2: Deputy HM Workflow**
1. Login as Deputy HM
2. View all support departments
3. Check shift status
4. Approve staff break
5. View hostels (if boarding)
6. ✓ Should NOT see finance, teacher grading

### **Test Case 3: Permission Denial**
1. Login as Teacher
2. Try to access /teacher/admin/dos/ (should redirect)
3. Login as Support Staff
4. Try to access /teacher/admin/deputy/ (should redirect)

---

## NEXT STEPS

1. **Save this document** and refer to it for implementation
2. **Follow the PHASE breakdown** in implementation checklist
3. **Start with PHASE 1** (Database models)
4. **Test each phase** before moving to next
5. **Maintain design consistency** with existing system

---

**Ready to implement? Start with database migrations!**