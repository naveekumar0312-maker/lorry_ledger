import os
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import transaction
from django.utils import timezone
from audit.models import AuditLog
from trips.models import TripIncomeEntry, Trip
from vehicles.models import Vehicle

def _dec(val, default='0.00'):
    try:
        return Decimal(str(val).strip())
    except (TypeError, ValueError, AttributeError):
        return Decimal(default)

@login_required
def income_list(request):
    query = request.GET.get('q', '').strip()
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    vehicle_id = request.GET.get('vehicle_id', '')
    income_type = request.GET.get('income_type', '')

    entries = TripIncomeEntry.objects.select_related('trip', 'trip__vehicle').all()

    if query:
        entries = entries.filter(
            Q(trip__trip_ref_no__icontains=query) |
            Q(trip__vehicle__vehicle_number__icontains=query) |
            Q(trip__primary_driver__full_name__icontains=query) |
            Q(description__icontains=query) |
            Q(income_type__icontains=query)
        )
    
    if date_from:
        entries = entries.filter(trip__entry_date__gte=date_from)
    if date_to:
        entries = entries.filter(trip__entry_date__lte=date_to)
    if vehicle_id:
        entries = entries.filter(trip__vehicle_id=vehicle_id)
    if income_type:
        entries = entries.filter(income_type=income_type)
        
    entries = entries.order_by('-id')

    # Aggregates for the summary cards
    total_freight = sum((e.freight_amount for e in entries), Decimal('0.00'))
    total_advance = sum((e.advance_amount for e in entries), Decimal('0.00'))
    total_balance = sum((e.balance_amount for e in entries), Decimal('0.00'))
    total_income = sum((e.total_income for e in entries), Decimal('0.00'))

    # Chart Data: Income by Type
    type_counts = {}
    for e in entries:
        t = e.income_type if e.income_type != 'Other' else e.custom_income_name or 'Other'
        type_counts[t] = type_counts.get(t, 0) + float(e.total_income)
        
    type_labels = list(type_counts.keys())
    type_data = list(type_counts.values())

    # Chart Data: Monthly Trend (simple mock or basic logic for demonstration)
    import json
    # In a real scenario, group by month. Here we just provide a basic mock or simple agg.
    trend_labels = ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    trend_data = [0, 0, float(total_income), 0, 0, 0] # Simplified for now

    paginator = Paginator(entries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    vehicles = Vehicle.objects.filter(created_by=request.user)
    
    context = {
        'page_obj': page_obj,
        'vehicles': vehicles,
        'q': query,
        'date_from': date_from,
        'date_to': date_to,
        'vehicle_id': vehicle_id,
        'income_type': income_type,
        'total_freight': total_freight,
        'total_advance': total_advance,
        'total_balance': total_balance,
        'total_income': total_income,
        'type_labels': json.dumps(type_labels),
        'type_data': json.dumps(type_data),
        'trend_labels': json.dumps(trend_labels),
        'trend_data': json.dumps(trend_data),
    }
    return render(request, 'income/list.html', context)

@login_required
def income_create(request):
    trips = Trip.objects.filter(is_archived=False).order_by('-entry_date')
    
    if request.method == 'POST':
        trip_id = request.POST.get('trip_id')
        inc_type = request.POST.get('income_type', 'Freight')
        custom_name = request.POST.get('custom_income_name', '').strip()
        if inc_type != 'Other':
            custom_name = ''
        freight = _dec(request.POST.get('freight_amount'))
        advance = _dec(request.POST.get('advance_amount'))
        other_inc = _dec(request.POST.get('other_income'))
        desc = request.POST.get('description', '').strip()
        
        trip = get_object_or_404(Trip, pk=trip_id)
        
        try:
            with transaction.atomic():
                entry = TripIncomeEntry.objects.create(
                    trip=trip,
                    income_type=inc_type,
                    custom_income_name=custom_name,
                    freight_amount=freight,
                    advance_amount=advance,
                    other_income=other_inc,
                    description=desc
                )
                AuditLog.objects.create(
                    user=request.user, 
                    action='CREATE', 
                    model_name='TripIncomeEntry', 
                    object_id=str(entry.id), 
                    details={'trip': trip.trip_ref_no}
                )
                messages.success(request, f"Income for Trip {trip.trip_ref_no} added successfully.")
                if 'save_and_add' in request.POST:
                    return redirect('income:add')
                return redirect('income:list')
        except Exception as e:
            messages.error(request, f"Error saving income: {str(e)}")

    return render(request, 'income/form.html', {
        'trips': trips
    })

@login_required
def income_edit(request, pk):
    entry = get_object_or_404(TripIncomeEntry, pk=pk)
    trips = Trip.objects.filter(is_archived=False).order_by('-entry_date')
    
    if request.method == 'POST':
        trip_id = request.POST.get('trip_id')
        entry.trip = get_object_or_404(Trip, pk=trip_id)
        entry.income_type = request.POST.get('income_type', 'Freight')
        custom_name = request.POST.get('custom_income_name', '').strip()
        if entry.income_type != 'Other':
            custom_name = ''
        entry.custom_income_name = custom_name
        entry.freight_amount = _dec(request.POST.get('freight_amount'))
        entry.advance_amount = _dec(request.POST.get('advance_amount'))
        entry.other_income = _dec(request.POST.get('other_income'))
        entry.description = request.POST.get('description', '').strip()
        
        try:
            with transaction.atomic():
                entry.save()
                AuditLog.objects.create(
                    user=request.user, 
                    action='UPDATE', 
                    model_name='TripIncomeEntry', 
                    object_id=str(entry.id), 
                    details={'trip': entry.trip.trip_ref_no}
                )
                messages.success(request, f"Income for Trip {entry.trip.trip_ref_no} updated successfully.")
                return redirect('income:list')
        except Exception as e:
            messages.error(request, f"Error updating income: {str(e)}")

    return render(request, 'income/form.html', {
        'entry': entry,
        'trips': trips,
        'is_edit': True
    })

@login_required
def income_delete(request, pk):
    entry = get_object_or_404(TripIncomeEntry, pk=pk)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                AuditLog.objects.create(
                    user=request.user, 
                    action='DELETE', 
                    model_name='TripIncomeEntry', 
                    object_id=str(entry.id), 
                    details={'trip': entry.trip.trip_ref_no}
                )
                entry.delete()
                messages.success(request, "Income entry deleted successfully.")
        except Exception as e:
            messages.error(request, f"Error deleting income entry: {str(e)}")
    return redirect('income:list')

@login_required
def income_detail(request, pk):
    entry = get_object_or_404(TripIncomeEntry.objects.select_related('trip'), pk=pk)
    return render(request, 'income/detail.html', {'entry': entry})
