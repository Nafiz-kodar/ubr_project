# myapp/models.py
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    USER_TYPES = (
        ('Owner', 'Owner'),
        ('Inspector', 'Inspector'),
        ('Admin', 'Admin'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # SQL: FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE                                                                 
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='Owner')
    # SQL: user_type VARCHAR(20) DEFAULT 'Owner' CHECK (user_type IN ('Owner', 'Inspector', 'Admin'))
    nid = models.CharField(max_length=50, blank=True, null=True)
    # SQL: nid VARCHAR(50) NULL
    phone = models.CharField(max_length=30, blank=True, null=True)
    # SQL: phone VARCHAR(30) NULL
    location = models.CharField(max_length=255, blank=True, null=True)
    # SQL: location VARCHAR(255) NULL
    is_approved = models.BooleanField(default=True)
    # SQL: is_approved BOOLEAN DEFAULT TRUE
    is_banned = models.BooleanField(default=False)
    # SQL: is_banned BOOLEAN DEFAULT FALSE

    #CREATE TABLE profile (
    #id SERIAL PRIMARY KEY,
    #user_id INTEGER UNIQUE REFERENCES auth_user(id) ON DELETE CASCADE,
    #user_type VARCHAR(20) DEFAULT 'Owner',
    #nid VARCHAR(50),
    #phone VARCHAR(30),
    #location VARCHAR(255),
    #is_approved BOOLEAN DEFAULT TRUE,
    #is_banned BOOLEAN DEFAULT FALSE
    #  );
    #Get all inspectors pending approval
    #SELECT u.username, p.phone
    #FROM profile p
    #JOIN auth_user u ON p.user_id = u.id
    #WHERE p.user_type='Inspector' AND p.is_approved=FALSE;
    
    # Get user profile by user_id
    # SELECT * FROM profile WHERE user_id = %s
    
    # Update profile information
    # UPDATE profile SET phone=%s, location=%s WHERE user_id=%s
    def __str__(self):
        # SQL: SELECT CONCAT(u.username, ' (', p.user_type, ')') FROM profile p JOIN auth_user u ON p.user_id = u.id WHERE p.id = %s
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
    # SQL: FOREIGN KEY (owner_id) REFERENCES auth_user(id) ON DELETE CASCADE
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_inspections')
    # SQL: FOREIGN KEY (inspector_id) REFERENCES auth_user(id) ON DELETE SET NULL
    req_type = models.CharField(max_length=30, choices=REQ_TYPES, default='New Construction')
    # SQL: req_type VARCHAR(30) DEFAULT 'New Construction' CHECK (req_type IN ('New Construction', 'Reinspection'))
    building_location = models.CharField(max_length=255)
    # SQL: building_location VARCHAR(255) NOT NULL
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # SQL: fee DECIMAL(10,2) DEFAULT 0
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    # SQL: status VARCHAR(20) DEFAULT 'Pending' CHECK (status IN ('Pending', 'Assigned', 'Approved', 'Rejected', 'Completed', 'Paid'))
    created_at = models.DateTimeField(auto_now_add=True)
    # SQL: created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    # CREATE TABLE inspection_request (
    #   id SERIAL PRIMARY KEY,
    #   owner_id INTEGER REFERENCES auth_user(id),
    #   inspector_id INTEGER REFERENCES auth_user(id),
    #   req_type VARCHAR(30),
    #   building_location VARCHAR(255),
    #   fee DECIMAL(10,2),
    #   status VARCHAR(20),
    #   created_at TIMESTAMP
    # );

    # Assign inspector to request
    # UPDATE inspection_request
    # SET inspector_id = 7, status = 'Assigned'
    # WHERE id = 12;

    # View owner's inspection requests
    # SELECT *
    # FROM inspection_request
    # WHERE owner_id = 3;
    
    # Get pending requests
    # SELECT * FROM inspection_request WHERE status = 'Pending'
    
    # Count requests by status
    # SELECT status, COUNT(*) FROM inspection_request GROUP BY status

    def __str__(self):
        return f"{self.owner.username} - {self.building_location} ({self.status})"
        # SQL: SELECT CONCAT(u.username, ' - ', building_location, ' (', status, ')') FROM inspection_request ir JOIN auth_user u ON ir.owner_id = u.id WHERE ir.id = %s


class InspectionReport(models.Model):
    inspection_request = models.OneToOneField(InspectionRequest, on_delete=models.CASCADE, related_name='report')
    # SQL: FOREIGN KEY (inspection_request_id) REFERENCES inspection_request(id) ON DELETE CASCADE UNIQUE
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reports')
    # SQL: FOREIGN KEY (inspector_id) REFERENCES auth_user(id) ON DELETE SET NULL
    inspection_date = models.DateTimeField(default=timezone.now)
    # SQL: inspection_date TIMESTAMP DEFAULT NOW()
    structural_evaluation = models.TextField(blank=True)
    # SQL: structural_evaluation TEXT NULL
    compliance_checklist = models.TextField(blank=True)
    # SQL: compliance_checklist TEXT NULL
    decision = models.CharField(max_length=20, choices=(('Approved','Approved'),('Rejected','Rejected')), blank=True)
    # SQL: decision VARCHAR(20) NULL CHECK (decision IN ('Approved', 'Rejected'))
    remarks = models.TextField(blank=True)
    # SQL: remarks TEXT NULL
    # CREATE TABLE inspection_report (
    #   id SERIAL PRIMARY KEY,
    #   inspection_request_id INTEGER UNIQUE REFERENCES inspection_request(id),
    #   inspector_id INTEGER REFERENCES auth_user(id),
    #   inspection_date TIMESTAMP,
    #   structural_evaluation TEXT,
    #   compliance_checklist TEXT,
    #   decision VARCHAR(20),
    #   remarks TEXT
    # );

    # Insert inspection report
    # INSERT INTO inspection_report
    # (inspection_request_id, inspector_id, decision, remarks)
    # VALUES (12, 7, 'Approved', 'All standards met');
    
    # Get report by request_id
    # SELECT * FROM inspection_report WHERE inspection_request_id = %s
    
    # Update report decision
    # UPDATE inspection_report SET decision=%s, remarks=%s WHERE id=%s

    def __str__(self):
        # SQL: SELECT CONCAT('Report for request #', inspection_request_id) FROM inspection_report WHERE id = %s 
        return f"Report for {self.inspection_request}"


class Complaint(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints_made')
     # SQL: FOREIGN KEY (reporter_id) REFERENCES auth_user(id) ON DELETE CASCADE
    against_inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='complaints_received')
    # SQL: FOREIGN KEY (against_inspector_id) REFERENCES auth_user(id) ON DELETE SET NULL
    message = models.TextField()
     # SQL: message TEXT NOT NULL
    admin_response = models.TextField(blank=True)
    # SQL: admin_response TEXT NULL
    
    resolved = models.BooleanField(default=False)
    # SQL: resolved BOOLEAN DEFAULT FALSE
    created_at = models.DateTimeField(auto_now_add=True)
    # SQL: created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    # CREATE TABLE complaint (
    #   id SERIAL PRIMARY KEY,
    #   reporter_id INTEGER REFERENCES auth_user(id),
    #   against_inspector_id INTEGER REFERENCES auth_user(id),
    #   message TEXT,
    #   admin_response TEXT,
    #   resolved BOOLEAN DEFAULT FALSE,
    #   created_at TIMESTAMP
    # );

    # Get unresolved complaints
    # SELECT *
    # FROM complaint
    # WHERE resolved = FALSE;
    
    # Create new complaint
    # INSERT INTO complaint (reporter_id, against_inspector_id, message) VALUES (%s, %s, %s)
    
    # Mark complaint as resolved
    # UPDATE complaint SET resolved=TRUE, admin_response=%s WHERE id=%s

    def __str__(self):
        # SQL: SELECT CONCAT('Complaint by user #', reporter_id, ' against inspector #', COALESCE(against_inspector_id::text, 'N/A')) FROM complaint WHERE id = %s
        return f"Complaint by {self.reporter.username} against {self.against_inspector.username if self.against_inspector else 'N/A'}"


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    # SQL: FOREIGN KEY (sender_id) REFERENCES auth_user(id) ON DELETE CASCADE
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    # SQL: FOREIGN KEY (recipient_id) REFERENCES auth_user(id) ON DELETE CASCADE
    subject = models.CharField(max_length=200, blank=True)
     # SQL: subject VARCHAR(200) NULL
    body = models.TextField()
    # SQL: body TEXT NOT NULL
    sent_at = models.DateTimeField(auto_now_add=True)
    # SQL: sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    is_read = models.BooleanField(default=False)
        # SQL: sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    
    is_read = models.BooleanField(default=False)
    # SQL: is_read BOOLEAN DEFAULT FALSE
    # CREATE TABLE message (
    #   id SERIAL PRIMARY KEY,
    #   sender_id INTEGER REFERENCES auth_user(id),
    #   recipient_id INTEGER REFERENCES auth_user(id),
    #   subject VARCHAR(200),
    #   body TEXT,
    #   sent_at TIMESTAMP,
    #   is_read BOOLEAN DEFAULT FALSE
    # );

    # Inbox messages
    # SELECT *
    # FROM message
    # WHERE recipient_id = 3
    # ORDER BY sent_at DESC;
    
    # Send new message
    # INSERT INTO message (sender_id, recipient_id, subject, body) VALUES (%s, %s, %s, %s)
    
    # Mark message as read
    # UPDATE message SET is_read=TRUE WHERE id=%s AND recipient_id=%s
    
    # Get unread count
    # SELECT COUNT(*) FROM message WHERE recipient_id=%s AND is_read=FALSE

    def __str__(self):
         # SQL: SELECT CONCAT('Message from user #', sender_id, ' to user #', recipient_id) FROM message WHERE id = %s
        return f"Message from {self.sender.username} to {self.recipient.username}"


class Payment(models.Model):
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
     # SQL: FOREIGN KEY (payer_id) REFERENCES auth_user(id) ON DELETE CASCADE
    inspection_request = models.ForeignKey(InspectionRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    # SQL: FOREIGN KEY (inspection_request_id) REFERENCES inspection_request(id) ON DELETE SET NULL
    amount = models.DecimalField(max_digits=10, decimal_places=2)
     # SQL: amount DECIMAL(10,2) NOT NULL
    created_at = models.DateTimeField(auto_now_add=True)
    # SQL: created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    # CREATE TABLE payment (
    #   id SERIAL PRIMARY KEY,
    #   payer_id INTEGER REFERENCES auth_user(id),
    #   inspection_request_id INTEGER REFERENCES inspection_request(id),
    #   amount DECIMAL(10,2),
    #   created_at TIMESTAMP
    # );

    # Insert payment
    # INSERT INTO payment (payer_id, inspection_request_id, amount)
    # VALUES (3, 12, 5000);
    
    # Get payments by user
    # SELECT * FROM payment WHERE payer_id=%s ORDER BY created_at DESC
    
    # Get total paid by user
    # SELECT SUM(amount) FROM payment WHERE payer_id=%s
    
    # Get payment by request
    # SELECT * FROM payment WHERE inspection_request_id=%s


    def __str__(self):
        # SQL: SELECT CONCAT('Payment of ', amount, ' by user #', payer_id) FROM payment WHERE id = %s
        return f"Payment {self.amount} by {self.payer.username}"


class AdminBalance(models.Model):
     # Single-row table to track demo admin balance
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # SQL: balance DECIMAL(12,2) DEFAULT 0
    # CREATE TABLE admin_balance (
    #   id SERIAL PRIMARY KEY,
    #   balance DECIMAL(12,2) DEFAULT 0
    # );

    # Update admin balance
    # UPDATE admin_balance
    # SET balance = balance + 5000
    # WHERE id = 1;
    
    # Get current balance
    # SELECT balance FROM admin_balance WHERE id=1
    
    # Initialize balance (first time)
    # INSERT INTO admin_balance (balance) VALUES (0)

    def __str__(self):
        # SQL: SELECT CONCAT('Admin Balance: ', balance) FROM admin_balance WHERE id = %s
        return f"Admin Balance: {self.balance}"


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **kwargs):
    # SQL equivalent for get_or_create:
    # BEGIN;
    # SELECT * FROM profile WHERE user_id = %s;
    # IF NOT FOUND THEN
    #   INSERT INTO profile (user_id, user_type) VALUES (%s, 'Owner');
    # END IF;
    # COMMIT;
    profile, _ = Profile.objects.get_or_create(user=instance)
    # If the User has admin/staff flags (e.g. created via createsuperuser),
    # ensure their Profile reflects that role so dashboard routing works.
    if instance.is_staff or instance.is_superuser:
        if profile.user_type != 'Admin':
            profile.user_type = 'Admin'
            profile.save()
