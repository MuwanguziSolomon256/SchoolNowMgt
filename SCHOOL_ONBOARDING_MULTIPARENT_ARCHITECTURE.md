# School Onboarding & Multi-School Parent Architecture

## SCHOOL ONBOARDING FLOW (Progressive Hierarchy)

### **Phase 1: Initial School Setup**
\`\`\`
NEW SCHOOL JOINS SYSTEM
    ↓
[System Admin] Creates School record
    ↓
[System Admin] Creates Headmaster (Admin) account for school
    ↓
Headmaster can now access: /admin/
\`\`\`

---

### **Phase 2: Headmaster Onboards DOS**
\`\`\`
Headmaster (Admin) navigates to:
  /admin/ → Users → Add User
  
Fills in:
  - Name
  - Email
  - Role: Teacher
  - School: [Auto-selected - their school]
  - Teacher Admin Role: Director of Studies (DOS)
  
Sends invitation link to DOS
  ↓
DOS creates account
  ↓
DOS can now access: /teacher/admin/dos/
\`\`\`

---

### **Phase 3: Headmaster Onboards Deputy HM**
\`\`\`
Headmaster navigates to:
  /admin/ → Users → Add User
  
Fills in:
  - Name
  - Email
  - Role: Teacher
  - School: [Auto-selected]
  - Teacher Admin Role: Deputy Headmaster
  
Sends invitation link to Deputy HM
  ↓
Deputy HM creates account
  ↓
Deputy HM can now access: /teacher/admin/deputy/
\`\`\`

---

### **Phase 4: DOS Onboards Teachers (Bottom-Up)**
\`\`\`
DOS navigates to:
  /teacher/admin/dos/ → Teachers → Add Teacher
  
Sends invitation
  ↓
Teacher creates account
  ↓
Teacher can access: /teacher/
\`\`\`

---

### **Phase 5: Deputy HM Onboards Support Staff**
\`\`\`
Deputy HM navigates to:
  /teacher/admin/deputy/ → Support Departments → Add Staff
  
Sends invitation
  ↓
Support Staff creates account
  ↓
Support Staff can access: /support/dashboard/
\`\`\`

---

### **Phase 6: Student Enrollment & Parent Linking**
\`\`\`
Admin/DOS navigates to:
  /school/students/ → Add Student
  
Fills in:
  - Name, DOB, Admission Number
  - Class: [Select class]
  - Parent(s): [Search/Add parents]
  - School: [Auto-selected]

If parent email in system → Link to existing parent account
If parent email NOT in system → Create invitation for parent
  ↓
Parent receives invitation: "You have been added as parent for [Child Name]"
  ↓
Parent creates account / Accepts linkage
  ↓
Parent can access: /parent/ (Multi-school dashboard)
\`\`\`

---

## PARENT WITH MULTIPLE SCHOOLS ARCHITECTURE

### **The Problem (Old Way)**
\`\`\`
Parent John Smith registered at School 1
    ↓
Can ONLY see children at School 1
    ↓
If his child Grace moves to School 2 → Parent needs NEW account
    ↓
❌ Broken experience
\`\`\`

### **The Solution (New Way)**

Parents have NO school FK:
\`\`\`python
class CustomUser(AbstractUser):
    role = CharField(choices=[...])
    school = ForeignKey(School, nullable=True)  # ← Nullable for parents!
    # Parents: school = None
    # Teachers: school = School instance
    # Admins: school = School instance
\`\`\`

---

## DATABASE MODELS NEEDED

### **1. Update CustomUser Model**
**File**: \`SchoolNowMgt/models.py\`  

\`\`\`python
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('teacher', 'Teacher'),
        ('non_teaching_staff', 'Non-Teaching Staff'),
        ('parent', 'Parent'),
    ]
    
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, db_index=True)
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='users',
        db_index=True,
        null=True,  # CHANGED: Now nullable for parents
        blank=True
    )
    phone = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True)
    is_active = models.BooleanField(default=True)
    
    objects = CustomUserManager()
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"
\`\`\`

### **2. NEW: StudentParentRelationship Model**
**File**: \`SchoolNowMgt/models.py\`  

\`\`\`python
class StudentParentRelationship(models.Model):
    """Links parents to students they oversee"""
    
    RELATIONSHIP_TYPES = [
        ('mother', 'Mother'),
        ('father', 'Father'),
        ('guardian', 'Guardian'),
        ('uncle', 'Uncle'),
        ('aunt', 'Aunt'),
        ('grandparent', 'Grandparent'),
        ('other', 'Other'),
    ]
    
    parent = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'parent'},
        related_name='parent_relationships'
    )
    student = models.ForeignKey(
        'Student',
        on_delete=models.CASCADE,
        related_name='parent_relationships'
    )
    relationship_type = models.CharField(
        max_length=20,
        choices=RELATIONSHIP_TYPES,
        default='parent'
    )
    is_primary_guardian = models.BooleanField(default=False)
    
    # Link to specific school for easy filtering
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        help_text="School where this student is enrolled"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    date_linked = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('parent', 'student', 'school')
        verbose_name_plural = 'Student Parent Relationships'
    
    def __str__(self):
        return f"{self.parent.get_full_name()} - {self.student.full_name} ({self.get_relationship_type_display()})"
\`\`\`

### **3. UPDATE: Student Model**
**File**: \`SchoolNowMgt/models.py\`  

Add to existing Student model:

\`\`\`python
# In existing Student model, add:

parents = models.ManyToManyField(
    CustomUser,
    through='StudentParentRelationship',
    related_name='children',
    limit_choices_to={'role': 'parent'},
    help_text="Parents/guardians of this student"
)
\`\`\`

---

## PARENT DASHBOARD - MULTI-SCHOOL VIEW

### **New Parent Dashboard Structure**

**URL**: `/parent/` (REDESIGNED for multi-school)

\`\`\`
┌─────────────────────────────────────────────────────────┐
│  Good Morning, John Smith                               │
│  You have children in 2 schools                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  SCHOOL 1: St. Mary's Primary School                    │
│  ┌───────────────────────────────────────────────────┐  │
│  │                                                   │  │
│  │  Children:                                        │  │
│  │  ○ Grace Smith (Primary 7)       [ VIEW ]         │  │
│  │  ○ James Smith (Primary 5)       [ VIEW ]         │  │
│  │                                                   │  │
│  │  Quick Stats:                                     │  │
│  │  - Grace: Average 82%, 15/20 attendance           │  │
│  │  - James: Average 76%, 18/20 attendance           │  │
│  │                                                   │  │
│  │  Pending for you:                                 │  │
│  │  - Math Assignment (Grace) - Due Tomorrow         │  │
│  │  - Biology Quiz (James) - Results Available       │  │
│  │                                                   │  │
│  │  [ GO TO SCHOOL DASHBOARD ]                       │  │
│  │                                                   │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  SCHOOL 2: Kampala International Academy               │
│  ┌───────────────────────────────────────────────────┐  │
│  │                                                   │  │
│  │  Children:                                        │  │
│  │  ○ Emma Smith (Form 2)           [ VIEW ]         │  │
│  │                                                   │  │
│  │  Quick Stats:                                     │  │
│  │  - Emma: Average 89%, 19/20 attendance            │  │
│  │                                                   │  │
│  │  Pending for you:                                 │  │
│  │  - Physics Lab Report - Due Friday                │  │
│  │  - School Fee Payment - Due by 30th               │  │
│  │                                                   │  │
│  │  [ GO TO SCHOOL DASHBOARD ]                       │  │
│  │                                                   │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
\`\`\`

---

## PARENT CHILD-SPECIFIC DASHBOARD

### **Per-School Child Dashboard**

**URL**: `/parent/school/<school_id>/child/<child_id>/`

Shows EVERYTHING about Grace RIGHT NOW (not end of term):

\`\`\`
ACADEMIC PERFORMANCE
- Current average: 82% (as of today)
- Subject-by-subject breakdown
- Trend: ↑ Up 5% from last month
- Class rank: 7/48

ATTENDANCE (Real-time)
- Today: Present ✓
- This week: 5/5 days
- This month: 18/20 days (90%)

ASSIGNMENTS & QUIZZES (Current + Past)
- Due Tomorrow: Math Problem Set (not submitted)
- Due Friday: English Essay (not submitted)
- Completed: Biology Quiz (18/20 = 90%) ✓
- This month: 12 assignments (11 on-time)

CONDUCT & BEHAVIOR
- Grade: A (Excellent)
- Incidents this term: 1 (late submission)
- Teacher comment: "Hardworking and respectful student"

FINANCIAL
- Balance: 500,000 UGX
- Last payment: 2,000,000 UGX (June 5)
- Due: Aug 31

COMMUNICATION
- Recent from Ms. Jane: "Grace's essay was excellent!"
- Recent from Mr. Kato: "Doing well in Math, needs more practice"
- [ SEND MESSAGE ]
\`\`\`

---

## PARENT VIEWS TO CREATE

### **1. Parent Overview Dashboard** (Multi-School)
**URL**: `/parent/`  
**View**: \`dashboard/parent_views.py\` → \`parent_overview_dashboard()\`

**Data to Show:**
- All schools where parent has children
- Quick stats per child per school
- Aggregated pending items
- Quick navigation to each school's dashboard

---

### **2. Parent School Dashboard** (Single School)
**URL**: `/parent/school/<school_id>/`  
**View**: \`dashboard/parent_views.py\` → \`parent_school_dashboard()\`

**Data to Show:**
- All children in THIS school
- School-specific announcements
- School calendar
- School fees status
- Quick access to each child's profile

---

### **3. Parent Child Profile** (Detailed)
**URL**: `/parent/school/<school_id>/child/<child_id>/`  
**View**: \`dashboard/parent_views.py\` → \`parent_child_profile()\`

**Sections:**
1. Academic Performance
2. Attendance
3. Assignments & Quizzes
4. Conduct & Behavior
5. Financial
6. Communication
7. Activities
8. Medical Info

---

## VIEW LOGIC FOR PARENTS

### **Get Parent's Schools (Multi-School)**
\`\`\`python
def get_parent_schools(parent_user):
    """Get all schools where parent has children"""
    schools = School.objects.filter(
        studentparentrelationship__parent=parent_user,
        studentparentrelationship__is_active=True
    ).distinct()
    return schools

# Returns: Schools where parent has ≥1 child enrolled
\`\`\`

### **Get Parent's Children in School (Per-School)**
\`\`\`python
def get_parent_children_in_school(parent_user, school):
    """Get all children of parent in specific school"""
    children = Student.objects.filter(
        parents=parent_user,
        school=school,
        parent_relationships__is_active=True
    ).select_related('class_grade').distinct()
    return children

# Returns: List of children enrolled in that school
\`\`\`

### **Child's Real-Time Data**
\`\`\`python
# For each child, fetch:
1. Latest grades (by subject, by term)
2. Today's attendance status
3. Pending assignments (due this week/month)
4. Recent quiz results
5. Conduct grade
6. Recent teacher comments
7. Outstanding fees
8. Recent communications

# All queryable by date range for trend analysis
\`\`\`

---

## PARENT REGISTRATION FLOW

### **Old Way (Before)**
\`\`\`
Parent registers
    ↓
Selects 1 School
    ↓
Account created for that 1 school only
\`\`\`

### **New Way (Now)**
\`\`\`
SCHOOL 1: Admin adds student "Grace"
    ↓
Admin links Grace to Parent: john@email.com
    ↓
System checks: Account exists?
    ├─ YES → Link child to existing parent account
    └─ NO → Send invitation to parent email
            ↓
            Parent clicks invite link
            ↓
            Parent creates account
            ↓
            Account created WITHOUT school FK
            ↓
            Parent linked to Grace via StudentParentRelationship
            ↓
            Parent can access: /parent/
            ↓
            Sees: School 1, Child: Grace

LATER - SCHOOL 2: Admin adds same child to another school
    ↓
Admin links same "Grace Smith" to same "John Smith" parent
    ↓
System updates StudentParentRelationship
    ↓
Parent logs into same account
    ↓
Now sees: School 1 (Grace), School 2 (Grace)
\`\`\`

---

## UPDATES NEEDED IN CODEBASE

### **1. Models** (\`SchoolNowMgt/models.py\`)
- [ ] Add \`StudentParentRelationship\` model
- [ ] Update \`CustomUser\` - Make \`school\` nullable for parents
- [ ] Update \`Student\` - Add \`parents\` ManyToMany field

### **2. Views** (\`dashboard/parent_views.py\` - NEW FILE)
- [ ] \`parent_overview_dashboard()\` - Multi-school view
- [ ] \`parent_school_dashboard()\` - Per-school view
- [ ] \`parent_child_profile()\` - Child detail view
- [ ] \`get_parent_schools()\` - Helper function
- [ ] \`get_parent_children_in_school()\` - Helper function

### **3. Templates** (Create new templates)
- [ ] \`parent/dashboard_overview.html\` - Multi-school dashboard
- [ ] \`parent/school_dashboard.html\` - Per-school view
- [ ] \`parent/child_profile.html\` - Child detail view

### **4. Registration** (\`registration/views.py\` - UPDATE)
- [ ] Update \`register_parent()\` - No school selection needed
- [ ] Update parent registration form
- [ ] Handle school linkage via StudentParentRelationship

### **5. Admin** (\`SchoolNowMgt/admin.py\` - UPDATE)
- [ ] Add \`StudentParentRelationship\` admin
- [ ] Update \`Student\` admin - Show parents inline
- [ ] Update \`CustomUser\` admin - Show schools for non-parents only

---

## REAL-TIME MONITORING FEATURES

Parent should see (not waiting until end of term):

✅ **Daily:**
- Child's attendance for today
- Any new assignments assigned
- New quiz results posted
- New teacher comments
- New messages from teachers

✅ **Weekly:**
- Assignment completion rate
- Weekly average performance
- Absence patterns
- Behavioral incidents

✅ **Monthly:**
- Monthly average grade
- Performance trends (up/down)
- Subject-wise progress
- Attendance trends
- Financial updates

✅ **Historical:**
- Full grade history with dates
- Assignment history (can review old work)
- Attendance full year view
- Conduct records
- All teacher comments

---

## KEY ARCHITECTURAL DECISIONS

1. **Parent has NO school** - Belongs to multiple schools via children
2. **Parent-Child relationship is per-school** - Tracked in \`StudentParentRelationship\`
3. **Parent dashboard aggregates** - Shows all schools on one page
4. **Real-time data** - Not just end-of-term
5. **School-specific context** - Parent sees children organized by school
6. **Multiple guardians possible** - A student can have mother, father, guardian, etc.

---

## MIGRATION STEPS

1. Create \`StudentParentRelationship\` model
2. Run: \`python manage.py makemigrations\`
3. Run: \`python manage.py migrate\`
4. Update CustomUser school field to nullable
5. Run: \`python manage.py makemigrations\`
6. Run: \`python manage.py migrate\`
7. Create parent views
8. Create parent templates
9. Update registration forms
10. Update admin

---

## NEXT STEPS

1. **Create StudentParentRelationship model**
2. **Make CustomUser.school nullable**
3. **Create parent overview dashboard**
4. **Create per-school dashboard**
5. **Create child profile dashboard**
6. **Test with sample parents & multiple schools**

**Ready to implement multi-school parent dashboard!**