from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from .decorators import role_required
import csv
import re
from datetime import date
from django.contrib import messages
from .models import Lead, User


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

@role_required('ADMIN')
def upload_leads(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        text = request.FILES['csv_file'].read().decode('utf-8-sig')
        lines = [line for line in text.splitlines() if line.strip()]
        reader = csv.DictReader(lines)
        reader.fieldnames = [f.strip().lower() for f in (reader.fieldnames or [])]
        added = skipped = 0
        for row in reader:
            name = (row.get('name') or '').strip()
            phone = (row.get('phone') or '').strip()
            loan_type = (row.get('loan_type') or '').strip()
            if not name or not re.fullmatch(r'\d{10}', phone):
                skipped += 1
                continue
            _, created = Lead.objects.get_or_create(
                phone=phone,
                defaults={'name': name, 'loan_type': loan_type},
            )
            if created:
                added += 1
            else:
                skipped += 1
        messages.success(request, f'{added} leads added, {skipped} skipped (invalid or duplicate).')
        return redirect('upload_leads')
    unassigned = Lead.objects.filter(assigned_to__isnull=True).count()
    return render(request, 'crm/upload_leads.html', {'unassigned': unassigned})

@role_required('ADMIN')
def distribute_leads(request):
    if request.method == 'POST':
        staff = list(User.objects.filter(role='STAFF', is_active=True))
        leads = Lead.objects.filter(assigned_to__isnull=True)
        if not staff:
            messages.error(request, 'No active staff to assign leads to.')
        else:
            count = 0
            for i, lead in enumerate(leads):
                lead.assigned_to = staff[i % len(staff)]
                lead.assigned_date = date.today()
                lead.save()
                count += 1
            messages.success(request, f'{count} leads distributed among {len(staff)} staff.')
    return redirect('upload_leads')