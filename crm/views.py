from decimal import Decimal, InvalidOperation
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from .decorators import role_required
import csv
import re
from datetime import date
from django.contrib import messages
from .models import Lead, User, CallLog, FollowUp, LoanApplication
from django.shortcuts import get_object_or_404
from django.utils import timezone

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




@role_required('STAFF')
def staff_dashboard(request):
    leads = Lead.objects.filter(assigned_to=request.user).order_by('status', 'name')
    calls_today = CallLog.objects.filter(
        staff=request.user, created_at__date=timezone.localdate()
    ).count()
    target = request.user.daily_target
    percent = min(100, int(calls_today * 100 / target)) if target else 0
    followups = FollowUp.objects.filter(
        staff=request.user, done=False, follow_up_date__lte=timezone.localdate()
    ).select_related('lead').order_by('follow_up_date')
    return render(request, 'crm/staff_dashboard.html', {
        'leads': leads,
        'calls_today': calls_today,
        'target': target,
        'percent': percent,
        'followups': followups,
    })

@role_required('STAFF')
def update_call(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id, assigned_to=request.user)
    choices = [c for c in Lead.STATUS_CHOICES if c[0] != 'NEW']
    if request.method == 'POST':
        outcome = request.POST.get('outcome')
        remarks = request.POST.get('remarks', '').strip()
        date_text = request.POST.get('follow_up_date', '').strip()
        follow_date = None
        if date_text:
            try:
                follow_date = date.fromisoformat(date_text)
            except ValueError:
                messages.error(request, 'Invalid follow-up date.')
                return render(request, 'crm/update_call.html', {'lead': lead, 'choices': choices})
        if outcome not in [c[0] for c in choices]:
            messages.error(request, 'Please choose a call outcome.')
        elif outcome == 'FOLLOW_UP' and not follow_date:
            messages.error(request, 'Please choose a follow-up date.')
        else:
            CallLog.objects.create(lead=lead, staff=request.user,
                                   outcome=outcome, remarks=remarks)
            lead.status = outcome
            lead.remarks = remarks
            lead.save()
            # this call completes any earlier pending follow-ups for this lead
            FollowUp.objects.filter(lead=lead, done=False).update(done=True)
            if follow_date and outcome != 'NOT_INTERESTED':
                FollowUp.objects.create(lead=lead, staff=request.user,
                                        follow_up_date=follow_date)
            messages.success(request, f'Call saved for {lead.name}.')
            return redirect('staff_dashboard')
    return render(request, 'crm/update_call.html', {'lead': lead, 'choices': choices})

@role_required('STAFF')
def create_application(request, lead_id):
    # only the owner's Interested leads can become applications
    lead = get_object_or_404(Lead, id=lead_id, assigned_to=request.user, status='INTERESTED')
    if request.method == 'POST':
        bank_name = request.POST.get('bank_name', '').strip()
        try:
            amount = Decimal(request.POST.get('amount', ''))
        except InvalidOperation:
            amount = None
        if not bank_name:
            messages.error(request, 'Please enter the bank name.')
        elif amount is None or amount <= 0:
            messages.error(request, 'Please enter a valid loan amount.')
        else:
            LoanApplication.objects.create(
                lead=lead, staff=request.user, bank_name=bank_name,
                amount=amount, remarks=request.POST.get('remarks', '').strip(),
            )
            messages.success(request, f'Application created for {lead.name}.')
            return redirect('my_applications')
    return render(request, 'crm/create_application.html', {'lead': lead})


@role_required('STAFF')
def my_applications(request):
    apps = LoanApplication.objects.filter(staff=request.user).select_related('lead').order_by('-created_at')
    return render(request, 'crm/my_applications.html', {'apps': apps})

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


@role_required('ADMIN')
def admin_dashboard(request):
    today = timezone.localdate()
    staff_rows = []
    for s in User.objects.filter(role='STAFF', is_active=True):
        staff_rows.append({
            'name': s.username,
            'calls': CallLog.objects.filter(staff=s, created_at__date=today).count(),
            'target': s.daily_target,
            'leads': Lead.objects.filter(assigned_to=s).count(),
            'interested': Lead.objects.filter(assigned_to=s, status='INTERESTED').count(),
        })
    context = {
        'total_leads': Lead.objects.count(),
        'unassigned': Lead.objects.filter(assigned_to__isnull=True).count(),
        'calls_today': CallLog.objects.filter(created_at__date=today).count(),
        'interested': Lead.objects.filter(status='INTERESTED').count(),
        'applications': LoanApplication.objects.count(),
        'staff_rows': staff_rows,
    }
    return render(request, 'crm/admin_dashboard.html', context)


@role_required('ADMIN')
def applications_list(request):
    apps = LoanApplication.objects.select_related('lead', 'staff').order_by('-updated_at')
    return render(request, 'crm/applications_list.html', {'apps': apps})


@role_required('ADMIN')
def update_application(request, app_id):
    app = get_object_or_404(LoanApplication, id=app_id)
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in [c[0] for c in LoanApplication.STATUS_CHOICES]:
            app.status = status
            app.remarks = request.POST.get('remarks', '').strip()
            app.save()
            messages.success(request, 'Application updated.')
            return redirect('applications_list')
        messages.error(request, 'Invalid status.')
    return render(request, 'crm/update_application.html',
                  {'app': app, 'statuses': LoanApplication.STATUS_CHOICES})


@role_required('ADMIN')
def staff_list(request):
    staff = User.objects.filter(role='STAFF').order_by('username')
    return render(request, 'crm/staff_list.html', {'staff': staff})


@role_required('ADMIN')
def add_staff(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        try:
            target = int(request.POST.get('daily_target') or 100)
        except ValueError:
            target = 0
        if not username or len(password) < 6:
            messages.error(request, 'Enter a username and a password of at least 6 characters.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'That username already exists.')
        elif target < 1:
            messages.error(request, 'Daily target must be at least 1.')
        else:
            User.objects.create_user(username=username, password=password,
                                     role='STAFF', daily_target=target)
            messages.success(request, f'Staff {username} added.')
            return redirect('staff_list')
    return render(request, 'crm/add_staff.html')


@role_required('ADMIN')
def toggle_staff(request, user_id):
    if request.method == 'POST':
        s = get_object_or_404(User, id=user_id, role='STAFF')
        s.is_active = not s.is_active
        s.save()
        messages.success(request, f'{s.username} is now {"active" if s.is_active else "inactive"}.')
    return redirect('staff_list')