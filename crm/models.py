from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

phone_validator = RegexValidator(
    r'^\d{10}$', 'Enter a valid 10-digit phone number.'
)

class User(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('STAFF', 'Staff'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='STAFF')
    daily_target = models.IntegerField(default=100)


class Lead(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('CALLED', 'Called'),
        ('INTERESTED', 'Interested'),
        ('NOT_INTERESTED', 'Not Interested'),
        ('FOLLOW_UP', 'Follow-up'),
    ]
    name = models.CharField(max_length=100, unique=True, validators=[phone_validator])
    phone = models.CharField(max_length=15, unique=True)
    loan_type = models.CharField(max_length=50, blank=True)
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='leads'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    remarks = models.TextField(blank=True)
    assigned_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.phone})"


class CallLog(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='calls')
    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calls')
    outcome = models.CharField(max_length=20, choices=Lead.STATUS_CHOICES)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.staff} called {self.lead} on {self.created_at:%d-%m-%Y}"


class FollowUp(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='followups')
    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followups')
    follow_up_date = models.DateField()
    done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lead} on {self.follow_up_date}"

class LoanApplication(models.Model):
    STATUS_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('DISBURSED', 'Disbursed'),
        ('CLOSED', 'Closed'),
        ('REJECTED', 'Rejected'),
    ]
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='applications')
    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    bank_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUBMITTED')
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.lead.name} - {self.bank_name} ({self.status})"