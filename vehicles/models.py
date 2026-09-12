from django.db import models
from django.contrib.auth.models import User

class Vehicle(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('MAINTENANCE', 'Under Maintenance'),
    )

    vehicle_number = models.CharField(max_length=30, unique=True, db_index=True, help_text="e.g. TN 66 AY 1092")
    vehicle_type = models.CharField(max_length=50, default='Lorry')
    model = models.CharField(max_length=100, blank=True, null=True)
    capacity_tons = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    owner_name = models.CharField(max_length=150, default='Own Fleet')
    owner_phone = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', db_index=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_vehicles')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['vehicle_number']

    def __str__(self):
        return f"{self.vehicle_number} ({self.vehicle_type})"

class VehicleDocument(models.Model):
    DOCUMENT_TYPES = (
        ('Insurance', 'Insurance'),
        ('RC', 'RC / Registration Certificate'),
        ('FC', 'FC / Fitness Certificate'),
        ('Permit', 'Permit'),
        ('PUC', 'PUC / Pollution Certificate'),
        ('Road Tax', 'Road Tax'),
        ('National Permit', 'National Permit'),
        ('Driver Licence', 'Driver Licence'),
        ('Other', 'Other Vehicle Document'),
    )

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    document_number = models.CharField(max_length=100, blank=True, null=True)
    issue_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True, db_index=True)
    document_file = models.FileField(upload_to='vehicle_documents/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_active', 'expiry_date']

    def __str__(self):
        return f"{self.vehicle.vehicle_number} - {self.get_document_type_display()}"

    @property
    def status(self):
        from datetime import date
        if not self.expiry_date:
            return 'VALID'
        today = date.today()
        if self.expiry_date < today:
            return 'EXPIRED'
        elif (self.expiry_date - today).days <= 30:
            return 'EXPIRING SOON'
        return 'VALID'

    @property
    def days_remaining(self):
        from datetime import date
        if not self.expiry_date:
            return None
        today = date.today()
        delta = (self.expiry_date - today).days
        return delta if delta >= 0 else 0

class VehicleDocumentReminder(models.Model):
    document = models.ForeignKey(VehicleDocument, on_delete=models.CASCADE, related_name='reminders')
    reminder_type = models.IntegerField(help_text="Days left when reminder generated (e.g. 30, 15, 0)")
    is_notified = models.BooleanField(default=False, help_text="True if shown to user on screen")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('document', 'reminder_type')
        ordering = ['created_at']

    def __str__(self):
        return f"{self.document.vehicle.vehicle_number} - {self.document.get_document_type_display()} ({self.reminder_type} days)"

