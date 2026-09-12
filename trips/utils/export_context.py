from decimal import Decimal
from django.shortcuts import get_object_or_404
from trips.models import Trip
from vehicles.models import Vehicle
from drivers.models import Driver

def build_trip_voucher_context(trip_id):
    trip = get_object_or_404(
        Trip.objects.select_related(
            'vehicle', 'primary_driver', 'secondary_driver', 'km_detail'
        ).prefetch_related(
            'fuel_entries', 'load_revenue_entries', 'expense_entries',
            'rto_pc_entries', 'other_toll_expenses'
        ),
        pk=trip_id
    )

    km_detail = getattr(trip, "km_detail", None)
    if km_detail:
        total_km = km_detail.total_km or Decimal("0.00")
        start_km = km_detail.start_km or Decimal("0.00")
        end_km = km_detail.end_km or Decimal("0.00")
    else:
        total_km = Decimal("0.00")
        start_km = Decimal("0.00")
        end_km = Decimal("0.00")

    load_entries = [entry for entry in trip.load_revenue_entries.all() if not entry.is_archived]
    total_ton = sum((entry.ton or Decimal("0.00") for entry in load_entries), Decimal("0.00"))
    overall_income = sum((entry.income_amount or Decimal("0.00") for entry in load_entries), Decimal("0.00"))
    commission_total = sum((entry.commission_amount or Decimal("0.00") for entry in load_entries), Decimal("0.00"))
    loading_charges = sum((entry.loading_charges or Decimal("0.00") for entry in load_entries), Decimal("0.00"))
    unloading_charges = sum((entry.unloading_charges or Decimal("0.00") for entry in load_entries), Decimal("0.00"))

    fuel_entries = list(trip.fuel_entries.all())
    diesel_entries = [f for f in fuel_entries if f.fuel_type == "Diesel"]
    adblue_entries = [f for f in fuel_entries if f.fuel_type == "AdBlue"]
    
    total_diesel_quantity = sum((f.quantity or Decimal("0.000") for f in diesel_entries), Decimal("0.000"))
    total_adblue_quantity = sum((f.quantity or Decimal("0.000") for f in adblue_entries), Decimal("0.000"))
    total_fuel_quantity = total_diesel_quantity + total_adblue_quantity

    diesel_cost = sum((f.total_cost or Decimal("0.00") for f in diesel_entries), Decimal("0.00"))
    adblue_cost = sum((f.total_cost or Decimal("0.00") for f in adblue_entries), Decimal("0.00"))
    total_fuel_cost = diesel_cost + adblue_cost

    if total_diesel_quantity > Decimal("0.000"):
        mileage = round(total_km / total_diesel_quantity, 2)
    else:
        mileage = Decimal("0.00")

    expense_entries = list(trip.expense_entries.all())
    other_expenses = sum((ex.amount or Decimal("0.00") for ex in expense_entries), Decimal("0.00"))

    rto_pc_entries = list(trip.rto_pc_entries.all())
    rto_expense = sum((e.total_amount for e in rto_pc_entries if e.expense_type == "RTO"), Decimal("0.00"))
    pc_expense = sum((e.total_amount for e in rto_pc_entries if e.expense_type == "PC"), Decimal("0.00"))
    rto_pc_total = rto_expense + pc_expense

    other_toll_entries = list(trip.other_toll_expenses.all())
    other_toll_expense = sum((e.amount or Decimal("0.00") for e in other_toll_entries), Decimal("0.00"))

    cleaner_salary = trip.cleaner_salary or Decimal("0.00")
    workshop_expense = trip.workshop_expense or Decimal("0.00")
    toll_gate_expense = trip.toll_gate_expense or Decimal("0.00")

    driver_salary = (overall_income * Decimal("13.00") / Decimal("100.00")).quantize(Decimal("0.01"))
    accounting_total = driver_salary + cleaner_salary + workshop_expense + toll_gate_expense

    overall_expense = (
        diesel_cost + adblue_cost + loading_charges + unloading_charges +
        accounting_total + rto_expense +
        pc_expense + other_toll_expense + other_expenses +
        commission_total
    )

    final_balance = overall_income - overall_expense

    if total_km > Decimal("0.00"):
        fuel_cost_per_km = round(total_fuel_cost / total_km, 2)
    else:
        fuel_cost_per_km = Decimal("0.00")

    return {
        "trip": trip,
        "km_detail": km_detail,
        "start_km": start_km,
        "end_km": end_km,
        "total_km": total_km,
        "load_entries": load_entries,
        "total_ton": total_ton,
        "overall_income": overall_income,
        "commission_total": commission_total,
        "loading_charges": loading_charges,
        "unloading_charges": unloading_charges,
        "fuel_entries": fuel_entries,
        "total_diesel_quantity": total_diesel_quantity,
        "total_adblue_quantity": total_adblue_quantity,
        "total_fuel_quantity": total_fuel_quantity,
        "diesel_cost": diesel_cost,
        "adblue_cost": adblue_cost,
        "total_fuel_cost": total_fuel_cost,
        "mileage": mileage,
        "fuel_cost_per_km": fuel_cost_per_km,
        "expense_entries": expense_entries,
        "other_expenses": other_expenses,
        "rto_pc_entries": rto_pc_entries,
        "rto_expense": rto_expense,
        "pc_expense": pc_expense,
        "rto_pc_total": rto_pc_total,
        "other_toll_entries": other_toll_entries,
        "other_toll_expense": other_toll_expense,
        "driver_salary": driver_salary,
        "cleaner_salary": cleaner_salary,
        "workshop_expense": workshop_expense,
        "toll_gate_expense": toll_gate_expense,
        "accounting_total": accounting_total,
        "overall_expense": overall_expense,
        "final_balance": final_balance,
    }


def build_reports_context(request):
    # This logic matches reports_index from reports/views.py
    vehicle_id = request.GET.get('vehicle_id', '').strip()
    driver_id = request.GET.get('driver_id', '').strip()
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()

    trips = Trip.objects.filter(is_archived=False).select_related(
        'vehicle', 'primary_driver', 'secondary_driver', 'km_detail'
    ).prefetch_related(
        'fuel_entries', 'load_revenue_entries', 'expense_entries',
        'rto_pc_entries', 'other_toll_expenses'
    ).order_by('-entry_date', '-id')

    if vehicle_id:
        trips = trips.filter(vehicle_id=vehicle_id)
    if driver_id:
        trips = trips.filter(primary_driver_id=driver_id)
    if from_date:
        trips = trips.filter(entry_date__gte=from_date)
    if to_date:
        trips = trips.filter(entry_date__lte=to_date)

    total_trips = trips.count()
    total_income = Decimal('0.00')
    total_km = Decimal('0.00')
    total_diesel_qty = Decimal('0.000')
    total_adblue_qty = Decimal('0.000')
    total_diesel_cost = Decimal('0.00')
    total_adblue_cost = Decimal('0.00')
    total_fuel_cost = Decimal('0.00')
    total_commission = Decimal('0.00')
    total_loading = Decimal('0.00')
    total_unloading = Decimal('0.00')
    total_driver_salary = Decimal('0.00')
    total_cleaner_salary = Decimal('0.00')
    total_workshop_expense = Decimal('0.00')
    total_toll_gate = Decimal('0.00')
    total_rto = Decimal('0.00')
    total_pc = Decimal('0.00')
    total_other_toll_expense = Decimal('0.00')
    total_other_expenses = Decimal('0.00')
    total_overall_expense = Decimal('0.00')
    total_balance = Decimal('0.00')
    report_rows = []

    for trip in trips:
        income = trip.total_income or Decimal('0.00')
        trip_km = trip.total_km or Decimal('0.00')
        diesel_qty = trip.total_diesel_quantity or Decimal('0.000')
        adblue_qty = trip.total_adblue_quantity or Decimal('0.000')
        diesel_cost = trip.total_diesel_cost or Decimal('0.00')
        adblue_cost = trip.total_adblue_cost or Decimal('0.00')
        fuel_cost = diesel_cost + adblue_cost
        commission = trip.total_revenue_commission or Decimal('0.00')
        loading = trip.total_revenue_loading or Decimal('0.00')
        unloading = trip.total_revenue_unloading or Decimal('0.00')
        driver_salary = (income * Decimal('13.00') / Decimal('100.00')).quantize(Decimal('0.01'))
        cleaner_salary = trip.cleaner_salary or Decimal('0.00')
        workshop_expense = trip.workshop_expense or Decimal('0.00')
        toll_gate = trip.toll_gate_expense or Decimal('0.00')
        rto = trip.total_rto_expense or Decimal('0.00')
        pc = trip.total_pc_expense or Decimal('0.00')
        other_toll_expense = trip.total_other_toll_expense or Decimal('0.00')
        other_expenses = trip.total_other_expenses or Decimal('0.00')
        overall_expense = (diesel_cost + adblue_cost + loading + unloading + driver_salary +
                           cleaner_salary + workshop_expense + rto + pc + toll_gate +
                           other_toll_expense + other_expenses + commission)
        balance = income - overall_expense

        total_income += income
        total_km += trip_km
        total_diesel_qty += diesel_qty
        total_adblue_qty += adblue_qty
        total_diesel_cost += diesel_cost
        total_adblue_cost += adblue_cost
        total_fuel_cost += fuel_cost
        total_commission += commission
        total_loading += loading
        total_unloading += unloading
        total_driver_salary += driver_salary
        total_cleaner_salary += cleaner_salary
        total_workshop_expense += workshop_expense
        total_toll_gate += toll_gate
        total_rto += rto
        total_pc += pc
        total_other_toll_expense += other_toll_expense
        total_other_expenses += other_expenses
        total_overall_expense += overall_expense
        total_balance += balance
        report_rows.append({
            'trip': trip, 'income': income, 'diesel_qty': diesel_qty, 'diesel_cost': diesel_cost,
            'adblue_qty': adblue_qty, 'adblue_cost': adblue_cost, 'commission': commission,
            'loading': loading, 'unloading': unloading, 'driver_salary': driver_salary,
            'cleaner_salary': cleaner_salary, 'workshop_expense': workshop_expense, 'rto': rto, 'pc': pc,
            'toll_gate': toll_gate, 'other_toll_expense': other_toll_expense,
            'other_expenses': other_expenses, 'overall_expense': overall_expense, 'balance': balance,
        })

    avg_mileage = round(total_km / total_diesel_qty, 2) if total_diesel_qty > Decimal('0.000') else Decimal('0.00')
    fuel_cost_per_km = round(total_fuel_cost / total_km, 2) if total_km > Decimal('0.00') else Decimal('0.00')

    if total_income > Decimal('0.00'):
        expense_ratio = round((total_overall_expense / total_income) * Decimal('100.00'), 2)
        profit_margin = round((total_balance / total_income) * Decimal('100.00'), 2)
    else:
        expense_ratio = Decimal('0.00')
        profit_margin = Decimal('0.00')

    return {
        'total_trips': total_trips, 'total_income': total_income, 'total_commission': total_commission,
        'total_km': total_km, 'avg_mileage': avg_mileage, 'total_fuel_cost': total_fuel_cost,
        'total_diesel_qty': total_diesel_qty, 'total_diesel_cost': total_diesel_cost,
        'total_adblue_qty': total_adblue_qty, 'total_adblue_cost': total_adblue_cost,
        'fuel_cost_per_km': fuel_cost_per_km, 'total_loading': total_loading, 'total_unloading': total_unloading,
        'total_driver_salary': total_driver_salary, 'total_cleaner_salary': total_cleaner_salary,
        'total_workshop_expense': total_workshop_expense, 'total_toll_gate': total_toll_gate,
        'total_rto': total_rto, 'total_pc': total_pc, 'total_other_toll_expense': total_other_toll_expense,
        'total_other_expenses': total_other_expenses, 'total_overall_expense': total_overall_expense,
        'total_balance': total_balance, 'expense_ratio': expense_ratio, 'profit_margin': profit_margin,
        'report_rows': report_rows
    }
