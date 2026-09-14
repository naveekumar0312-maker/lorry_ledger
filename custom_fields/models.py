from django.db import models
from django.contrib.auth.models import User

class CustomFieldDefinition(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='custom_fields')
    TYPE_CHOICES = (
        ('TEXT', 'Text'),
        ('NUMBER', 'Number'),
        ('DECIMAL', 'Decimal'),
        ('DATE', 'Date'),
        ('CURRENCY', 'Currency'),
        ('DROPDOWN', 'Dropdown List'),
        ('BOOLEAN', 'Yes / No'),
    )

    field_name = models.CharField(max_length=100, unique=True)
    field_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='TEXT')
    options = models.TextField(blank=True, null=True, help_text="Comma-separated values for dropdown options")
    is_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.field_name} ({self.field_type})"

class CustomFieldValue(models.Model):
    trip = models.ForeignKey('trips.Trip', on_delete=models.CASCADE, related_name='custom_values')
    field_def = models.ForeignKey(CustomFieldDefinition, on_delete=models.CASCADE, related_name='values')
    field_value = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('trip', 'field_def')

    def __str__(self):
        return f"{self.field_def.field_name}: {self.field_value}"
