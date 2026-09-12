from django.db import models
from django.contrib.auth.models import User

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50) # e.g. CREATE, UPDATE, ARCHIVE, DELETE
    model_name = models.CharField(max_length=50) # e.g. Trip, Vehicle, Driver
    object_id = models.CharField(max_length=50)
    details = models.JSONField(blank=True, null=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        user_str = self.user.username if self.user else "System"
        return f"[{self.timestamp}] {user_str} {self.action} {self.model_name} #{self.object_id}"
