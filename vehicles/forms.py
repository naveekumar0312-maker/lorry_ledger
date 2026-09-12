from django import forms
from .models import Vehicle, VehicleDocument

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['vehicle_number', 'vehicle_type', 'model', 'capacity_tons', 'owner_name', 'owner_phone', 'status', 'notes']

class VehicleDocumentForm(forms.ModelForm):
    class Meta:
        model = VehicleDocument
        fields = ['vehicle', 'document_type', 'document_number', 'issue_date', 'expiry_date', 'document_file', 'is_active']
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'vehicle': forms.Select(attrs={'class': 'form-select select2'}),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'document_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'document_file': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
