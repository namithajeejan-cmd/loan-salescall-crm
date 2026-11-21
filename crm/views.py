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


@role_required('ADMIN')
def admin_dashboard(request):
    return render(request, 'crm/admin_dashboard.html')


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