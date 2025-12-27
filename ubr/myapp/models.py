# myapp/models.py
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    USER_TYPES = (
        ('Owner', 'Owner'),
        ('Inspector', 'Inspector'),
        ('Admin', 'Admin'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='Owner')
    nid = models.CharField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    is_approved = models.BooleanField(default=True)  # Inspectors require admin approval
    is_banned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} ({self.user_type})"


class InspectionRequest(models.Model):
    REQ_TYPES = (
        ('New Construction', 'New Construction'),
        ('Reinspection', 'Reinspection'),
    )
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Assigned', 'Assigned'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
        ('Paid', 'Paid'),
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owner_requests')
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_inspections')
    req_type = models.CharField(max_length=30, choices=REQ_TYPES, default='New Construction')
    building_location = models.CharField(max_length=255)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.owner.username} - {self.building_location} ({self.status})"


class InspectionReport(models.Model):
    inspection_request = models.OneToOneField(InspectionRequest, on_delete=models.CASCADE, related_name='report')
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reports')
    inspection_date = models.DateTimeField(default=timezone.now)
    structural_evaluation = models.TextField(blank=True)
    compliance_checklist = models.TextField(blank=True)
    decision = models.CharField(max_length=20, choices=(('Approved','Approved'),('Rejected','Rejected')), blank=True)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"Report for {self.inspection_request}"


class Complaint(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints_made')
    against_inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='complaints_received')
    message = models.TextField()
    admin_response = models.TextField(blank=True)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Complaint by {self.reporter.username} against {self.against_inspector.username if self.against_inspector else 'N/A'}"


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.username} to {self.recipient.username}"


class Payment(models.Model):
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    inspection_request = models.ForeignKey(InspectionRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.amount} by {self.payer.username}"


class AdminBalance(models.Model):
    # Single-row table to track demo admin balance
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"Admin Balance: {self.balance}"


# Ensure a Profile exists for every User. This creates a Profile when a User
# is created and also ensures one exists if the signal fires for an existing
# user without a Profile (get_or_create is idempotent).
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **kwargs):
    profile, _ = Profile.objects.get_or_create(user=instance)
    # If the User has admin/staff flags (e.g. created via createsuperuser),
    # ensure their Profile reflects that role so dashboard routing works.
    if instance.is_staff or instance.is_superuser:
        if profile.user_type != 'Admin':
            profile.user_type = 'Admin'
            profile.save()
