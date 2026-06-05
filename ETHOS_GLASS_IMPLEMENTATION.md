# Ethos Glass Design System - Implementation Guide

## Overview

This document explains how to integrate the Ethos Glass design system dashboards into your Django school management system. The design includes role-specific dashboards for:

- **Admin Dashboard** - School administration and oversight
- **Parent Dashboard** - Student progress monitoring
- **Teacher Dashboard** - Lesson management and grading
- **Support Staff Dashboard** - Maintenance and facility management

## Files Created

### CSS Files
- `static/css/ethos-glass-theme.css` - Complete design system with glass morphism effects

### Templates
- `templates/SchoolNowMgt/base_ethos.html` - Base template with Ethos Glass configuration
- `templates/SchoolNowMgt/admin_dashboard.html` - Admin portal dashboard
- `templates/SchoolNowMgt/parent_dashboard.html` - Parent portal dashboard
- `templates/SchoolNowMgt/teacher_dashboard.html` - Teacher portal dashboard
- `templates/SchoolNowMgt/support_staff_dashboard.html` - Maintenance/Support staff dashboard

## Design System Features

### Color Palette
- **Primary**: #080b3a (Navy Blue)
- **Secondary**: #feb700 (Gold)
- **Surface**: #f8f9fc (Light Background)
- **Error**: #ba1a1a (Red)

### Typography
- **Display Large**: 36px, Hanken Grotesk, Weight 700
- **Headline Large**: 28px, Hanken Grotesk, Weight 600
- **Headline Medium**: 22px, Hanken Grotesk, Weight 600
- **Body Large**: 16px, Inter, Weight 400
- **Body Medium**: 14px, Inter, Weight 400
- **Label Medium**: 12px, Inter, Weight 600

### Key Components

#### Glass Cards
```html
<div class="glass-card rounded-3xl p-6">
    <!-- Content here -->
</div>
```

Features:
- 70% transparent white background
- 20px blur backdrop filter
- Smooth hover animations
- Responsive shadow effects

#### Navigation
- Sidebar with gradient background
- Active state highlighting with gold color
- Smooth hover transitions
- Icon support via Material Symbols

#### Progress Bars
```html
<div class="progress-bar">
    <div class="progress-bar-fill" style="width: 85%"></div>
</div>
```

#### Badges
```html
<span class="badge badge-primary">Label</span>
<span class="badge badge-secondary">Label</span>
<span class="badge badge-error">Label</span>
<span class="badge badge-success">Label</span>
```

#### Alerts
```html
<div class="alert alert-error rounded-2xl">
    <span class="material-symbols-outlined">alert_icon</span>
    <div>
        <p class="font-bold">Error Title</p>
        <p>Error description</p>
    </div>
</div>
```

## Django Views Integration

### Admin Dashboard View

```python
# dashboard/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from SchoolNowMgt.models import Student, Staff, Payment

def is_admin(user):
    return user.groups.filter(name='Admin').exists()

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    context = {
        'school_name': 'Your School',
        'total_students': Student.objects.count(),
        'student_growth': '+12%',
        'monthly_revenue': '142,500.00',
        'collected_amount': '128k',
        'outstanding_amount': '14.5k',
        'fee_collection_goal': 85,
        'alert_count': 3,
        'alerts': get_priority_alerts(),
        'recent_activities': get_recent_activities(),
    }
    return render(request, 'SchoolNowMgt/admin_dashboard.html', context)
```

### Parent Dashboard View

```python
@login_required
def parent_dashboard(request):
    parent = request.user.profile
    students = parent.children.all()
    selected_student = request.GET.get('student_id', students.first().id if students else None)
    
    student = Student.objects.get(id=selected_student)
    
    context = {
        'parent_name': parent.first_name,
        'students': students,
        'selected_student': selected_student,
        'selected_student_name': student.first_name,
        'gpa': '3.82',
        'subjects': [
            {'name': 'Advanced Mathematics', 'score': 92, 'icon': 'functions'},
            {'name': 'Physics & Chemistry', 'score': 88, 'icon': 'biotech'},
            {'name': 'Modern Literature', 'score': 76, 'icon': 'history_edu'},
        ],
        'attendance': 98.4,
        'assignments_completed': 24,
        'total_assignments': 26,
        'class_rank': '4th',
        'class_size': 32,
        'outstanding_balance': '₦452,000.00',
        'payment_status': 'Due in 4 days',
        'current_month': 'October',
        'current_year': 2023,
    }
    return render(request, 'SchoolNowMgt/parent_dashboard.html', context)
```

### Teacher Dashboard View

```python
@login_required
def teacher_dashboard(request):
    teacher = request.user.profile
    current_lesson = 'Advanced Astrophysics'
    current_class = teacher.classes.first()
    
    context = {
        'teacher_name': teacher.first_name,
        'current_lesson': current_lesson,
        'lesson_description': 'Unit 4: Galactic Evolution and Dark Matter Distribution.',
        'class_students': current_class.students.all()[:5] if current_class else [],
        'priority_tasks': get_teacher_tasks(),
        'current_month': 'October',
        'current_year': 2023,
    }
    return render(request, 'SchoolNowMgt/teacher_dashboard.html', context)
```

### Support Staff Dashboard View

```python
@login_required
def support_dashboard(request):
    staff = request.user.profile
    
    context = {
        'staff_name': staff.first_name,
        'current_date': 'Monday, October 23, 2023',
        'pending_tasks': get_pending_maintenance(),
        'daily_schedule': get_daily_schedule(),
        'inventory_items': get_inventory_status(),
        'delivery_schedule': 'Plumbing & Hardware supplies arriving tomorrow at 10:00 AM.',
        'work_orders': get_recent_work_orders(),
    }
    return render(request, 'SchoolNowMgt/support_staff_dashboard.html', context)
```

## URL Configuration

Add these to your `urls.py`:

```python
# schoolmgmt_project/urls.py
from django.urls import path
from dashboard import views

urlpatterns = [
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/parent/', views.parent_dashboard, name='parent_dashboard'),
    path('dashboard/teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('dashboard/support/', views.support_dashboard, name='support_dashboard'),
]
```

## Customization

### Modifying Colors
Edit `static/css/ethos-glass-theme.css`:

```css
:root {
  --primary: #080b3a;
  --secondary: #feb700;
  --surface: #f8f9fc;
  /* ... */
}
```

### Changing Border Radius
All cards use `rounded-3xl` (1.5rem). Modify by changing the class on glass-card divs.

### Animation Speed
Glass card animations are 0.3s by default. Adjust in CSS:

```css
.glass-card {
  transition: all 0.3s cubic-bezier(0.22, 1, 0.36, 1);
}
```

### Responsive Behavior
- Sidebar hides on mobile (< 768px)
- Grid layouts adjust from 2 columns to single column
- Font sizes remain consistent across devices

## Browser Support

- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support (including blur effects)
- Mobile Safari: Full support

## Performance Considerations

1. **Glass Effects**: Uses CSS backdrop-filter (hardware-accelerated)
2. **Animations**: Uses CSS transitions (no JavaScript overhead)
3. **Image Loading**: Use placeholder images or optimize existing ones
4. **Icon Library**: Material Symbols Outlined (loaded via CDN)

## Accessibility

- All navigation items have proper labels
- Color contrast meets WCAG AA standards
- Icons paired with text labels
- Semantic HTML structure
- Keyboard navigation support

## Common Customizations

### Add Your Logo
```html
<h1 class="font-headline-lg text-headline-lg font-black text-secondary-container">
    Your School Name
</h1>
```

### Change Active Navigation Item
Add `active` class to the nav item:
```html
<div class="nav-item active"><!-- item --></div>
```

### Modify Card Grid Layout
Change `col-span-*` classes:
```html
<!-- Default: 4 columns -->
<div class="col-span-4 glass-card"><!-- content --></div>
<!-- Change to 3 columns -->
<div class="col-span-3 glass-card"><!-- content --></div>
```

## Troubleshooting

### Glass Effect Not Showing
- Ensure CSS file is loaded: Check Network tab in DevTools
- Browser support: backdrop-filter requires modern browser
- Check z-index conflicts

### Icons Not Displaying
- Verify Material Symbols font is loaded
- Check icon name spelling
- Ensure `<span class="material-symbols-outlined">` is used

### Layout Issues
- Clear browser cache
- Check viewport meta tag is present
- Verify Tailwind CSS is compiled

## Support & Resources

- **Design System**: Ethos Glass DESIGN.md reference
- **Tailwind CSS**: https://tailwindcss.com
- **Material Symbols**: https://fonts.google.com/icons
- **CSS Backdrop Filter**: https://developer.mozilla.org/en-US/docs/Web/CSS/backdrop-filter

## Future Enhancements

- Dark mode support
- Mobile app integration
- Real-time data updates
- Export/Print functionality
- Advanced filtering options
- Dashboard customization
- Theme switching
