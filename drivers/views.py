from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models.deletion import ProtectedError
from .models import Driver

@login_required
def driver_list(request):
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    
    drivers = Driver.objects.filter(user=request.user)
    if search_query:
        drivers = drivers.filter(full_name__icontains=search_query) | drivers.filter(mobile_number__icontains=search_query) | drivers.filter(license_number__icontains=search_query)
    if status_filter:
        drivers = drivers.filter(status=status_filter)
        
    paginator = Paginator(drivers, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'drivers/list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
    })

@login_required
def driver_create(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        mobile_number = request.POST.get('mobile_number', '').strip()
        license_number = request.POST.get('license_number', '').strip()
        address = request.POST.get('address', '').strip()
        status = request.POST.get('status', 'ACTIVE')
        notes = request.POST.get('notes', '').strip()
        
        if Driver.objects.filter(mobile_number=mobile_number, user=request.user).exists():
            messages.error(request, f"Driver with mobile number '{mobile_number}' already exists.")
            return render(request, 'drivers/form.html', {'post_data': request.POST})
            
        Driver.objects.create(
            full_name=full_name,
            mobile_number=mobile_number,
            license_number=license_number,
            address=address,
            status=status,
            notes=notes
        )
        messages.success(request, f"Driver {full_name} added successfully.")
        return redirect('drivers:list')
        
    return render(request, 'drivers/form.html', {'post_data': {}})

@login_required
def driver_edit(request, pk):
    driver = get_object_or_404(Driver, pk=pk, user=request.user)
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        mobile_number = request.POST.get('mobile_number', '').strip()
        
        if driver.mobile_number != mobile_number and Driver.objects.filter(mobile_number=mobile_number).exists():
            messages.error(request, f"Driver with mobile number '{mobile_number}' already exists.")
            return render(request, 'drivers/form.html', {'driver': driver, 'post_data': request.POST})
            
        driver.full_name = full_name
        driver.mobile_number = mobile_number
        driver.license_number = request.POST.get('license_number', '').strip()
        driver.address = request.POST.get('address', '').strip()
        driver.status = request.POST.get('status', 'ACTIVE')
        driver.notes = request.POST.get('notes', '').strip()
        driver.save()
        
        messages.success(request, f"Driver {driver.full_name} updated successfully.")
        return redirect('drivers:list')
        
    return render(request, 'drivers/form.html', {'driver': driver, 'post_data': {}})


@login_required
def driver_detail(request, pk):
    driver = get_object_or_404(Driver, pk=pk, user=request.user)
    primary_trips = driver.primary_trips.select_related('vehicle').order_by('-entry_date', '-id')[:15]
    trip_count = driver.primary_trips.count()
    return render(request, 'drivers/detail.html', {
        'driver': driver,
        'primary_trips': primary_trips,
        'trip_count': trip_count,
    })


@login_required
def driver_delete(request, pk):
    driver = get_object_or_404(Driver, pk=pk, user=request.user)
    if request.method == 'POST':
        trip_count = driver.primary_trips.count() + driver.secondary_trips.count()
        if trip_count > 0:
            messages.error(
                request,
                f"Cannot delete driver '{driver.full_name}' — they are linked to {trip_count} trip record(s). "
                f"Set their status to 'Inactive' instead."
            )
            return redirect('drivers:detail', pk=pk)
        try:
            dname = driver.full_name
            driver.delete()
            messages.success(request, f"Driver '{dname}' deleted successfully.")
        except ProtectedError:
            messages.error(request, f"Cannot delete driver '{driver.full_name}' because they are linked to existing accounting records.")
        return redirect('drivers:list')
    return redirect('drivers:list')
