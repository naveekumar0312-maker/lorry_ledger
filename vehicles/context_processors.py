from vehicles.models import VehicleDocumentReminder

def unshown_reminders(request):
    """
    Injects a list of unshown Vehicle Document Reminders into the context.
    We return a serialized structure so JavaScript can easily consume it.
    """
    if not request.user.is_authenticated:
        return {}
        
    reminders_qs = VehicleDocumentReminder.objects.filter(
        is_notified=False
    ).select_related('document__vehicle')[:5]
    
    reminders_list = []
    for r in reminders_qs:
        # Determine Severity
        days = r.reminder_type
        if days > 15:
            severity = 'info'
            title = 'Vehicle Document Reminder'
            icon = '🔔'
        elif days > 7:
            severity = 'warning'
            title = 'Expiring Soon'
            icon = '🟡'
        elif days > 3:
            severity = 'warning'
            title = 'Important Reminder'
            icon = '🟠'
        elif days > 0:
            severity = 'danger'
            title = 'Urgent Reminder'
            icon = '🚨'
        else:
            severity = 'danger'
            title = 'Document Expired'
            icon = '🔴'
            
        reminders_list.append({
            'id': r.id,
            'vehicle': r.document.vehicle.vehicle_number,
            'document_type': r.document.get_document_type_display(),
            'document_number': r.document.document_number or 'N/A',
            'expiry_date': r.document.expiry_date.strftime('%d %b %Y') if r.document.expiry_date else 'N/A',
            'days_remaining': days,
            'severity': severity,
            'title': title,
            'icon': icon
        })
        
    if not reminders_list:
        return {}

    import json
    return {
        'popup_reminders': json.dumps(reminders_list)
    }
