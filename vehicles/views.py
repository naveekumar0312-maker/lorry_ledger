from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models.deletion import ProtectedError
from .models import Vehicle

@login_required
def vehicle_list(request):
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    
    vehicles = Vehicle.objects.filter(created_by=request.user)
    if search_query:
        vehicles = vehicles.filter(vehicle_number__icontains=search_query) | vehicles.filter(owner_name__icontains=search_query) | vehicles.filter(model__icontains=search_query)
    if status_filter:
        vehicles = vehicles.filter(status=status_filter)
        
    paginator = Paginator(vehicles, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'vehicles/list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
    })

@login_required
def vehicle_create(request):
    if request.method == 'POST':
        vehicle_number = request.POST.get('vehicle_number', '').strip().upper()
        vehicle_type = request.POST.get('vehicle_type', 'Lorry').strip()
        model = request.POST.get('model', '').strip()
        capacity_tons = request.POST.get('capacity_tons') or None
        owner_name = request.POST.get('owner_name', 'Own Fleet').strip()
        owner_phone = request.POST.get('owner_phone', '').strip()
        status = request.POST.get('status', 'ACTIVE')
        notes = request.POST.get('notes', '').strip()
        
        if Vehicle.objects.filter(vehicle_number=vehicle_number, created_by=request.user).exists():
            messages.error(request, f"Vehicle with registration number '{vehicle_number}' already exists.")
            return render(request, 'vehicles/form.html', {'post_data': request.POST})
            
        Vehicle.objects.create(
            vehicle_number=vehicle_number,
            vehicle_type=vehicle_type,
            model=model,
            capacity_tons=capacity_tons,
            owner_name=owner_name,
            owner_phone=owner_phone,
            status=status,
            notes=notes,
            created_by=request.user
        )
        messages.success(request, f"Vehicle {vehicle_number} created successfully.")
        return redirect('vehicles:list')
        
    return render(request, 'vehicles/form.html', {'post_data': {}})

@login_required
def vehicle_edit(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk, created_by=request.user)
    if request.method == 'POST':
        vehicle_number = request.POST.get('vehicle_number', '').strip().upper()
        vehicle.vehicle_type = request.POST.get('vehicle_type', 'Lorry').strip()
        vehicle.model = request.POST.get('model', '').strip()
        vehicle.capacity_tons = request.POST.get('capacity_tons') or None
        vehicle.owner_name = request.POST.get('owner_name', 'Own Fleet').strip()
        vehicle.owner_phone = request.POST.get('owner_phone', '').strip()
        vehicle.status = request.POST.get('status', 'ACTIVE')
        vehicle.notes = request.POST.get('notes', '').strip()
        
        # Check duplicate if changed
        if vehicle.vehicle_number != vehicle_number and Vehicle.objects.filter(vehicle_number=vehicle_number).exists():
            messages.error(request, f"Vehicle '{vehicle_number}' already exists.")
            return render(request, 'vehicles/form.html', {'vehicle': vehicle, 'post_data': request.POST})
            
        vehicle.vehicle_number = vehicle_number
        vehicle.save()
        messages.success(request, f"Vehicle {vehicle.vehicle_number} updated successfully.")
        return redirect('vehicles:list')
        
    return render(request, 'vehicles/form.html', {'vehicle': vehicle, 'post_data': {}})


@login_required
def vehicle_detail(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk, created_by=request.user)
    trips = vehicle.trips.select_related('primary_driver').order_by('-entry_date', '-id')[:20]
    trip_count = vehicle.trips.count()
    documents = vehicle.documents.all()
    return render(request, 'vehicles/detail.html', {
        'vehicle': vehicle,
        'trips': trips,
        'trip_count': trip_count,
        'documents': documents,
    })


@login_required
def vehicle_delete(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk, created_by=request.user)
    if request.method == 'POST':
        trip_count = vehicle.trips.count()
        if trip_count > 0:
            messages.error(
                request,
                f"Cannot delete vehicle '{vehicle.vehicle_number}' — it has {trip_count} trip record(s). "
                f"Set it to 'Inactive' instead to hide it from active operations."
            )
            return redirect('vehicles:detail', pk=pk)
        try:
            vnum = vehicle.vehicle_number
            vehicle.delete()
            messages.success(request, f"Vehicle {vnum} deleted successfully.")
        except ProtectedError:
            messages.error(request, f"Cannot delete vehicle '{vehicle.vehicle_number}' because it is linked to existing accounting records.")
        return redirect('vehicles:list')
    return redirect('vehicles:list')

# ========================================================
# VEHICLE DOCUMENTS VIEWS
# ========================================================
from .models import VehicleDocument
from .forms import VehicleDocumentForm
from datetime import date, timedelta

@login_required
def document_list(request):
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    type_filter = request.GET.get('type', '').strip()

    docs = VehicleDocument.objects.select_related('vehicle').filter(vehicle__created_by=request.user)

    if search_query:
        docs = docs.filter(vehicle__vehicle_number__icontains=search_query) | docs.filter(document_number__icontains=search_query)
    
    if type_filter:
        docs = docs.filter(document_type=type_filter)

    if status_filter:
        today = date.today()
        thirty_days = today + timedelta(days=30)
        
        if status_filter == 'VALID':
            docs = docs.filter(expiry_date__gt=thirty_days) | docs.filter(expiry_date__isnull=True)
        elif status_filter == 'EXPIRING SOON':
            docs = docs.filter(expiry_date__gte=today, expiry_date__lte=thirty_days)
        elif status_filter == 'EXPIRED':
            docs = docs.filter(expiry_date__lt=today)

    paginator = Paginator(docs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'vehicles/document_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'type_filter': type_filter,
    })

@login_required
def document_view(request, pk):
    doc = get_object_or_404(VehicleDocument, pk=pk, vehicle__created_by=request.user)
    return render(request, 'vehicles/document_detail.html', {'doc': doc})

@login_required
def document_create(request):
    if request.method == 'POST':
        form = VehicleDocumentForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            doc = form.save()
            messages.success(request, f"Document '{doc.get_document_type_display()}' for {doc.vehicle.vehicle_number} added.")
            return redirect('vehicles:detail', pk=doc.vehicle.id)
    else:
        initial = {}
        vehicle_id = request.GET.get('vehicle')
        if vehicle_id:
            initial['vehicle'] = vehicle_id
        form = VehicleDocumentForm(initial=initial, user=request.user)

    return render(request, 'vehicles/document_form.html', {'form': form, 'title': 'Add Vehicle Document'})

@login_required
def document_edit(request, pk):
    doc = get_object_or_404(VehicleDocument, pk=pk, vehicle__created_by=request.user)
    if request.method == 'POST':
        form = VehicleDocumentForm(request.POST, request.FILES, instance=doc, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Vehicle document updated successfully.")
            return redirect('vehicles:document_list')
    else:
        form = VehicleDocumentForm(instance=doc, user=request.user)

    return render(request, 'vehicles/document_form.html', {'form': form, 'title': 'Edit Vehicle Document', 'doc': doc})

@login_required
def document_delete(request, pk):
    doc = get_object_or_404(VehicleDocument, pk=pk, vehicle__created_by=request.user)
    if request.method == 'POST':
        doc.delete()
        messages.success(request, "Vehicle document deleted successfully.")
    return redirect('vehicles:document_list')

@login_required
def mark_reminder_notified(request, pk):
    from django.http import JsonResponse
    if request.method == 'POST':
        try:
            from vehicles.models import VehicleDocumentReminder
            reminder = VehicleDocumentReminder.objects.get(pk=pk, document__vehicle__created_by=request.user)
            reminder.is_notified = True
            reminder.save()
            return JsonResponse({'status': 'ok'})
        except VehicleDocumentReminder.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Not found'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=400)
