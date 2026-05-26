from django.shortcuts import render, redirect
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from teacher_auth.forms import TeacherLoginForm


def teacher_login(request):
    """
    Teacher login view.
    """
    # Redirect if already logged in as teacher
    if request.user.is_authenticated and request.user.role == 'teacher':
        return redirect('teacher:dashboard')

    if request.method == 'POST':
        form = TeacherLoginForm(request=request, data=request.POST)
        if form.is_valid():
            login(request, form.authenticated_user)

            # Safe redirect logic
            next_url = request.GET.get('next', '')
            if (next_url.startswith('/') and 
                not next_url.startswith('//') and 
                ' ' not in next_url):
                return redirect(next_url)
            else:
                return redirect('teacher:dashboard')
    else:
        form = TeacherLoginForm()

    context = {'form': form}
    return render(request, 'teacher/login.html', context)


@login_required(login_url='teacher:login')
@require_POST
def teacher_logout(request):
    """
    Teacher logout view. POST only.
    """
    logout(request)
    return redirect('teacher:login')
