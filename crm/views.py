from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from .decorators import role_required


def landing(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'crm/landing.html')


def portal_login(request, role):
    if request.user.is_authenticated:
        return redirect('home')
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        if user.role != role:
            form.add_error(None, 'This account cannot log in here. Please use the other login.')
        else:
            login(request, user)
            return redirect('home')
    return render(request, 'crm/login.html', {'form': form, 'role': role})


@login_required
def home(request):
    if request.user.role == 'ADMIN':
        return redirect('admin_dashboard')
    return redirect('staff_dashboard')


@role_required('ADMIN')
def admin_dashboard(request):
    return render(request, 'crm/admin_dashboard.html')


@role_required('STAFF')
def staff_dashboard(request):
    return render(request, 'crm/staff_dashboard.html')