from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomFieldDefinition

@login_required
def custom_field_list(request):
    if request.method == 'POST':
        field_name = request.POST.get('field_name', '').strip()
        field_type = request.POST.get('field_type', 'TEXT')
        options = request.POST.get('options', '').strip()
        is_required = request.POST.get('is_required') == 'on'
        
        if field_name:
            if CustomFieldDefinition.objects.filter(field_name=field_name, user=request.user).exists():
                messages.error(request, f"Custom field '{field_name}' already exists.")
            else:
                CustomFieldDefinition.objects.create(user=request.user, 
                    field_name=field_name,
                    field_type=field_type,
                    options=options,
                    is_required=is_required
                )
                messages.success(request, f"Custom field '{field_name}' defined successfully.")
        return redirect('custom_fields:list')
        
    custom_fields = CustomFieldDefinition.objects.filter(user=request.user)
    return render(request, 'custom_fields/list.html', {'custom_fields': custom_fields})

@login_required
def custom_field_toggle(request, pk):
    field_def = get_object_or_404(CustomFieldDefinition, pk=pk, user=request.user)
    field_def.is_active = not field_def.is_active
    field_def.save()
    messages.info(request, f"Custom field '{field_def.field_name}' updated.")
    return redirect('custom_fields:list')
