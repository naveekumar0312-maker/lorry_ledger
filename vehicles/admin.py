from django.contrib import admin
from .models import Vehicle, VehicleDocument

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle_number', 'vehicle_type', 'owner_name', 'status')
    search_fields = ('vehicle_number', 'owner_name')
    list_filter = ('status', 'vehicle_type')

@admin.register(VehicleDocument)
class VehicleDocumentAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'document_type', 'document_number', 'expiry_date', 'status', 'is_active')
    search_fields = ('document_number', 'vehicle__vehicle_number')
    list_filter = ('document_type', 'is_active')
    # Use raw_id_fields instead of autocomplete_fields to avoid needing search_fields on VehicleAdmin if it wasn't registered properly before
    raw_id_fields = ('vehicle',)
