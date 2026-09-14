# trips/views.py

from decimal import Decimal, InvalidOperation
from datetime import datetime
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from decimal import Decimal, InvalidOperation

from .models import (
    Trip,
    TripKMDetail,
    TripFuelEntry,
    TripIncomeEntry,
    TripCommission,
    TripLoadingEntry,
    TripUnloadingEntry,
    TripExpenseEntry,
    TripLoadRevenueEntry,
    TripRtoPcEntry,
    TripOtherTollExpense,
    TripRtoPcEntry,
)

from vehicles.models import Vehicle
from drivers.models import Driver
from expenses.models import ExpenseCategory
from audit.models import AuditLog


# ================================================================
# CONSTANTS
# ================================================================

ZERO = Decimal("0.00")
ZERO_QTY = Decimal("0.000")

FUEL_TYPES = {"Diesel", "AdBlue"}
RTO_PC_TYPES = {"RTO", "PC"}

DRIVER_SALARY_PERCENTAGE = Decimal("13.00")


# ================================================================
# HELPERS
# ================================================================

def _dec(value, default="0.00"):
    """
    Safely convert a POST value to Decimal.
    Invalid / empty values fall back to default.
    """

    try:
        if value is None or str(value).strip() == "":
            return Decimal(default)

        return Decimal(str(value).strip())

    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def _safe_int(value):
    """
    Safely convert a value to int.
    """

    try:
        return int(value)

    except (TypeError, ValueError):
        return None


def _get_post_list(request, name):
    """
    Always return a list for repeated form fields.
    """

    return request.POST.getlist(name)


def _audit(
    user,
    action,
    model_name,
    object_id,
    details=None,
):
    """
    Centralized audit logging.
    """

    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=str(object_id),
        details=details or {},
    )


def _positive_decimal(
    value,
    field_name,
    default="0.00",
    allow_zero=True,
):
    """
    Convert decimal and reject negative values.
    """

    amount = _dec(value, default)

    if amount < ZERO:
        raise ValueError(
            f"{field_name} cannot be negative."
        )

    if not allow_zero and amount == ZERO:
        raise ValueError(
            f"{field_name} must be greater than zero."
        )

    return amount


def _validate_dates(
    entry_date,
    period_from,
    period_to,
):
    """
    Validate trip date relationships.
    """

    if period_from > period_to:
        raise ValueError(
            "Period From cannot be after Period To."
        )


def _validate_vehicle_driver(
    vehicle_id,
    primary_driver_id,
    secondary_driver_id=None,
):
    """
    Validate active vehicle and driver selections.
    """

    if not vehicle_id:
        raise ValueError(
            "Please select a vehicle."
        )

    if not primary_driver_id:
        raise ValueError(
            "Please select a primary driver."
        )

    if (
        secondary_driver_id
        and str(primary_driver_id)
        == str(secondary_driver_id)
    ):
        raise ValueError(
            "Primary Driver and Secondary Driver cannot be the same."
        )

    vehicle = get_object_or_404(
        Vehicle,
        pk=vehicle_id,
        status="ACTIVE",
        created_by=request.user,
    )

    primary_driver = get_object_or_404(
        Driver,
        pk=primary_driver_id,
        status="ACTIVE",
        user=request.user,
    )

    secondary_driver = None

    if secondary_driver_id:
        secondary_driver = get_object_or_404(
            Driver,
            pk=secondary_driver_id,
            status="ACTIVE",
            user=request.user,
        )

    return (
        vehicle,
        primary_driver,
        secondary_driver,
    )


def _generate_trip_reference():
    """
    Generate a unique trip reference number.
    """

    for _ in range(10):

        ref = (
            "TRIP-"
            f"{timezone.now().strftime('%Y%m%d')}-"
            f"{uuid.uuid4().hex[:6].upper()}"
        )

        if not Trip.objects.filter(
            trip_ref_no=ref
        ).exists():
            return ref

    raise ValueError(
        "Unable to generate a unique trip reference number."
    )


def _audit_trip_change(
    user,
    action,
    trip,
):
    """
    Standard trip audit payload.
    """

    _audit(
        user=user,
        action=action,
        model_name="Trip",
        object_id=trip.id,
        details={
            "ref_no": trip.trip_ref_no,
            "vehicle": str(trip.vehicle),
            "driver": str(trip.primary_driver),
            "income": str(trip.total_income),
            "expense": str(trip.overall_expense),
            "balance": str(trip.balance),
        },
    )


# ================================================================
# TRIP LIST / LEDGER
# ================================================================

@login_required
def trip_list(request):

    search_query = request.GET.get(
        "q",
        "",
    ).strip()

    vehicle_filter = request.GET.get(
        "vehicle",
        "",
    ).strip()

    driver_filter = request.GET.get(
        "driver",
        "",
    ).strip()

    from_date = request.GET.get(
        "from_date",
        "",
    ).strip()

    to_date = request.GET.get(
        "to_date",
        "",
    ).strip()

    show_archived = (
        request.GET.get("archived") == "1"
    )

    trips = (
        Trip.objects
        .filter(created_by=request.user)
        .select_related(
            "vehicle",
            "primary_driver",
            "secondary_driver",
            "km_detail",
        )
        .prefetch_related(
            "fuel_entries",
            "load_revenue_entries",
            "expense_entries",
            "rto_pc_entries",
        )
        .filter(
            is_archived=show_archived
        )
        .order_by(
            "-entry_date",
            "-id",
        )
    )

    # ------------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------------

    if search_query:

        trips = trips.filter(
            Q(
                trip_ref_no__icontains=search_query
            )
            | Q(
                vehicle__vehicle_number__icontains=search_query
            )
            | Q(
                vehicle__owner_name__icontains=search_query
            )
            | Q(
                primary_driver__full_name__icontains=search_query
            )
            | Q(
                secondary_driver__full_name__icontains=search_query
            )
        )

    # ------------------------------------------------------------
    # FILTERS
    # ------------------------------------------------------------

    if vehicle_filter:
        trips = trips.filter(
            vehicle_id=vehicle_filter
        )

    if driver_filter:
        trips = trips.filter(
            primary_driver_id=driver_filter
        )

    if from_date:
        trips = trips.filter(
            entry_date__gte=from_date
        )

    if to_date:
        trips = trips.filter(
            entry_date__lte=to_date
        )

    # ------------------------------------------------------------
    # PAGINATION
    # ------------------------------------------------------------

    paginator = Paginator(
        trips,
        20,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    # ------------------------------------------------------------
    # DROPDOWN DATA
    # ------------------------------------------------------------

    vehicles = Vehicle.objects.filter(
        status="ACTIVE",
        created_by=request.user
    ).order_by(
        "vehicle_number"
    )

    drivers = Driver.objects.filter(
        status="ACTIVE",
        user=request.user
    ).order_by(
        "full_name"
    )

    return render(
        request,
        "trips/list.html",
        {
            "page_obj": page_obj,
            "search_query": search_query,
            "vehicle_filter": vehicle_filter,
            "driver_filter": driver_filter,
            "from_date": from_date,
            "to_date": to_date,
            "show_archived": show_archived,
            "vehicles": vehicles,
            "drivers": drivers,
        },
    )


# ================================================================
# TRIP CREATE
# ================================================================

@login_required
def trip_create(request):

    vehicles = Vehicle.objects.filter(
        status="ACTIVE",
        created_by=request.user
    ).order_by(
        "vehicle_number"
    )

    drivers = Driver.objects.filter(
        status="ACTIVE",
        user=request.user
    ).order_by(
        "full_name"
    )

    expense_categories = ExpenseCategory.objects.filter(
        is_active=True,
        user=request.user
    ).order_by(
        "category_name"
    )

    if request.method == "POST":

        try:

            with transaction.atomic():

                # ------------------------------------------------
                # BASIC INFORMATION
                # ------------------------------------------------

                entry_date = (
                    request.POST.get(
                        "entry_date"
                    )
                    or timezone.localdate().isoformat()
                )

                period_from = (
                    request.POST.get(
                        "period_from"
                    )
                    or entry_date
                )

                period_to = (
                    request.POST.get(
                        "period_to"
                    )
                    or entry_date
                )

                vehicle_id = request.POST.get(
                    "vehicle_id"
                )

                primary_driver_id = request.POST.get(
                    "primary_driver_id"
                )

                secondary_driver_id = (
                    request.POST.get(
                        "secondary_driver_id"
                    )
                    or None
                )

                # ------------------------------------------------
                # DATE VALIDATION
                # ------------------------------------------------

                _validate_dates(
                    entry_date,
                    period_from,
                    period_to,
                )

                # ------------------------------------------------
                # VEHICLE / DRIVER VALIDATION
                # ------------------------------------------------

                (
                    vehicle,
                    primary_driver,
                    secondary_driver,
                ) = _validate_vehicle_driver(
                    vehicle_id,
                    primary_driver_id,
                    secondary_driver_id,
                )

                # ------------------------------------------------
                # TRIP REFERENCE
                # ------------------------------------------------

                trip_ref_no = (
                    request.POST.get(
                        "trip_ref_no",
                        "",
                    )
                    .strip()
                )

                if not trip_ref_no:
                    trip_ref_no = (
                        _generate_trip_reference()
                    )

                elif Trip.objects.filter(created_by=request.user,
                    trip_ref_no=trip_ref_no
                ).exists():
                    raise ValueError(
                        "Trip reference number already exists."
                    )

                # ------------------------------------------------
                # MANUAL ACCOUNTING
                # ------------------------------------------------

                cleaner_salary = _positive_decimal(
                    request.POST.get(
                        "cleaner_salary"
                    ),
                    "Cleaner Salary",
                )

                workshop_expense = _positive_decimal(
                    request.POST.get(
                        "workshop_expense"
                    ),
                    "Workshop Expense",
                )

                toll_gate_expense = _positive_decimal(
                    request.POST.get(
                        "toll_gate_expense"
                    ),
                    "Toll Gate Expense",
                )

                # ------------------------------------------------
                # CREATE TRIP
                # ------------------------------------------------

                trip = Trip.objects.create(
                    trip_ref_no=trip_ref_no,
                    entry_date=entry_date,
                    period_from=period_from,
                    period_to=period_to,
                    vehicle=vehicle,
                    primary_driver=primary_driver,
                    secondary_driver=secondary_driver,
                    notes=request.POST.get(
                        "notes",
                        "",
                    ).strip(),
                    cleaner_salary=cleaner_salary,
                    workshop_expense=workshop_expense,
                    toll_gate_expense=toll_gate_expense,
                    created_by=request.user,
                    updated_by=request.user,
                )

                # ------------------------------------------------
                # CHILD RECORDS
                # ------------------------------------------------

                _save_trip_subentries(
                    request=request,
                    trip=trip,
                    entry_date=entry_date,
                )

                # ------------------------------------------------
                # AUDIT
                # ------------------------------------------------

                _audit_trip_change(
                    user=request.user,
                    action="CREATE",
                    trip=trip,
                )

                messages.success(
                    request,
                    (
                        f"Trip #{trip.trip_ref_no} "
                        "created successfully!"
                    ),
                )

                return redirect(
                    "trips:detail",
                    pk=trip.pk,
                )

        except Exception as e:

            messages.error(
                request,
                f"Error creating trip: {str(e)}",
            )

    # ------------------------------------------------------------
    # GET
    # ------------------------------------------------------------

    today = timezone.localdate().isoformat()

    auto_ref = _generate_trip_reference()

    return render(
        request,
        "trips/form.html",
        {
            "trip": None,
            "vehicles": vehicles,
            "drivers": drivers,
            "expense_categories": expense_categories,
            "today": today,
            "auto_ref": auto_ref,
            "is_edit": False,
        },
    )


# ================================================================
# TRIP EDIT
# ================================================================

@login_required
def trip_edit(request, pk):

    trip = get_object_or_404(
        Trip.objects.select_related(
            "vehicle",
            "primary_driver",
            "secondary_driver",
            "km_detail",
        ),
        pk=pk, created_by=request.user,
    )

    vehicles = Vehicle.objects.filter(
        status="ACTIVE",
        created_by=request.user
    ).order_by(
        "vehicle_number"
    )

    drivers = Driver.objects.filter(
        status="ACTIVE",
        user=request.user
    ).order_by(
        "full_name"
    )

    expense_categories = ExpenseCategory.objects.filter(
        is_active=True,
        user=request.user
    ).order_by(
        "category_name"
    )

    if request.method == "POST":

        try:

            with transaction.atomic():

                entry_date = (
                    request.POST.get(
                        "entry_date"
                    )
                    or trip.entry_date.isoformat()
                )

                period_from = (
                    request.POST.get(
                        "period_from"
                    )
                    or trip.period_from.isoformat()
                )

                period_to = (
                    request.POST.get(
                        "period_to"
                    )
                    or trip.period_to.isoformat()
                )

                vehicle_id = request.POST.get(
                    "vehicle_id"
                )

                primary_driver_id = request.POST.get(
                    "primary_driver_id"
                )

                secondary_driver_id = (
                    request.POST.get(
                        "secondary_driver_id"
                    )
                    or None
                )

                # ------------------------------------------------
                # VALIDATION
                # ------------------------------------------------

                _validate_dates(
                    entry_date,
                    period_from,
                    period_to,
                )

                (
                    vehicle,
                    primary_driver,
                    secondary_driver,
                ) = _validate_vehicle_driver(
                    vehicle_id,
                    primary_driver_id,
                    secondary_driver_id,
                )

                # ------------------------------------------------
                # UPDATE BASIC DATA
                # ------------------------------------------------

                trip.entry_date = entry_date
                trip.period_from = period_from
                trip.period_to = period_to
                trip.vehicle = vehicle
                trip.primary_driver = primary_driver
                trip.secondary_driver = secondary_driver

                trip.notes = request.POST.get(
                    "notes",
                    "",
                ).strip()

                trip.cleaner_salary = _positive_decimal(
                    request.POST.get(
                        "cleaner_salary"
                    ),
                    "Cleaner Salary",
                    str(
                        trip.cleaner_salary
                    ),
                )

                trip.workshop_expense = _positive_decimal(
                    request.POST.get(
                        "workshop_expense"
                    ),
                    "Workshop Expense",
                    str(
                        trip.workshop_expense
                    ),
                )

                trip.toll_gate_expense = _positive_decimal(
                    request.POST.get(
                        "toll_gate_expense"
                    ),
                    "Toll Gate Expense",
                    str(
                        trip.toll_gate_expense
                    ),
                )

                trip.updated_by = request.user

                trip.save()

                # ------------------------------------------------
                # SAVE CHILD RECORDS
                # ------------------------------------------------

                _save_trip_subentries(
                    request=request,
                    trip=trip,
                    entry_date=entry_date,
                )

                # ------------------------------------------------
                # AUDIT
                # ------------------------------------------------

                _audit_trip_change(
                    user=request.user,
                    action="UPDATE",
                    trip=trip,
                )

                messages.success(
                    request,
                    (
                        f"Trip #{trip.trip_ref_no} "
                        "updated successfully!"
                    ),
                )

                return redirect(
                    "trips:detail",
                    pk=trip.pk,
                )

        except Exception as e:

            messages.error(
                request,
                f"Error updating trip: {str(e)}",
            )

    # ------------------------------------------------------------
    # GET
    # ------------------------------------------------------------

    today = timezone.localdate().isoformat()

    return render(
        request,
        "trips/form.html",
        {
            "trip": trip,
            "vehicles": vehicles,
            "drivers": drivers,
            "expense_categories": expense_categories,
            "today": today,
            "is_edit": True,
        },
    )


# ================================================================
# SAVE ALL TRIP SUB-ENTRIES
# ================================================================

def _save_trip_subentries(
    request,
    trip,
    entry_date,
):
    """
    AUTHORITATIVE CURRENT TRIP FORM FLOW

    1. KM
    2. Section 2 - Load / Revenue
       - Income
       - Commission
       - Loading
       - Unloading

    3. Fuel
       - Diesel
       - AdBlue

    4. Section 4 - Other Expenses
       - Category
       - Name
       - Date
       - Amount
       - Description
       - Payment Method
       - Receipt

    5. RTO / PC
       - Place
       - Type
       - Onward
       - Return

    6. Other Toll Expenses
       - Toll Name
       - Date
       - Amount
       - Notes

    IMPORTANT:
    - Commission is displayed but NOT included in Overall Expense.
    - Section 4 Other Expenses ARE included in Overall Expense.
    - Toll Gate Expense is stored on Trip itself.
    - Other Toll Expenses are stored as multiple child rows.
    - Other Toll Expenses ARE included in Overall Expense.

    EXISTING ID -> UPDATE
    EMPTY ID    -> CREATE
    REMOVED ID  -> DELETE

    NOT USED:
    - Custom Fields
    - Separate Commission
    - Separate Loading
    - Separate Unloading
    - Legacy Income creation
    """

    # ============================================================
    # 1. KM DETAILS
    # ============================================================

    start_km = _positive_decimal(
        request.POST.get(
            "start_km"
        ),
        "Starting KM",
    )

    end_km = _positive_decimal(
        request.POST.get(
            "end_km"
        ),
        "Ending KM",
    )

    # Adjustment removed from current UI.
    # Keep database value as ZERO for compatibility.
    km_adjustment = ZERO

    calculated_km = (
        end_km
        - start_km
    )

    if calculated_km < ZERO:
        raise ValueError(
            "Ending KM cannot be less than Starting KM."
        )

    TripKMDetail.objects.update_or_create(
        trip=trip,
        defaults={
            "start_km": start_km,
            "end_km": end_km,
            "km_adjustment": km_adjustment,
            "total_km": calculated_km,
            "km_notes": "",
        },
    )

    # ============================================================
    # 2. LOAD / REVENUE
    # ============================================================

    load_ids = _get_post_list(
        request,
        "load_entry_id[]",
    )

    load_dates = _get_post_list(
        request,
        "load_date[]",
    )

    from_locations = _get_post_list(
        request,
        "from_location[]",
    )

    to_locations = _get_post_list(
        request,
        "to_location[]",
    )

    load_places = _get_post_list(
        request,
        "load_place[]",
    )

    tons = _get_post_list(
        request,
        "load_ton[]",
    )

    incomes = _get_post_list(
        request,
        "load_income[]",
    )

    commissions = _get_post_list(
        request,
        "load_commission[]",
    )

    loadings = _get_post_list(
        request,
        "load_loading[]",
    )

    unloadings = _get_post_list(
        request,
        "load_unloading[]",
    )

    submitted_load_ids = []

    row_count = max(
        len(load_ids),
        len(load_dates),
        len(from_locations),
        len(to_locations),
        len(load_places),
        len(tons),
        len(incomes),
        len(commissions),
        len(loadings),
        len(unloadings),
    )

    for i in range(row_count):

        entry_id = (
            load_ids[i].strip()
            if i < len(load_ids)
            else ""
        )

        row_date = (
            load_dates[i].strip()
            if i < len(load_dates)
            else ""
        )

        from_location = (
            from_locations[i].strip()
            if i < len(from_locations)
            else ""
        )

        to_location = (
            to_locations[i].strip()
            if i < len(to_locations)
            else ""
        )

        load_place = (
            load_places[i].strip()
            if i < len(load_places)
            else ""
        )

        ton = _positive_decimal(
            tons[i]
            if i < len(tons)
            else "0.00",
            "Load Ton",
        )

        income_amount = _positive_decimal(
            incomes[i]
            if i < len(incomes)
            else "0.00",
            "Income",
        )

        commission_amount = _positive_decimal(
            commissions[i]
            if i < len(commissions)
            else "0.00",
            "Commission",
        )

        loading_charges = _positive_decimal(
            loadings[i]
            if i < len(loadings)
            else "0.00",
            "Loading Charges",
        )

        unloading_charges = _positive_decimal(
            unloadings[i]
            if i < len(unloadings)
            else "0.00",
            "Unloading Charges",
        )

        has_data = (
            bool(entry_id)
            or bool(row_date)
            or bool(from_location)
            or bool(to_location)
            or bool(load_place)
            or ton > ZERO
            or income_amount > ZERO
            or commission_amount > ZERO
            or loading_charges > ZERO
            or unloading_charges > ZERO
        )

        if not has_data:
            continue

        if not row_date:
            row_date = entry_date

        # --------------------------------------------------------
        # EXISTING -> UPDATE
        # --------------------------------------------------------

        if entry_id:

            entry_pk = _safe_int(
                entry_id
            )

            if not entry_pk:
                raise ValueError(
                    "Invalid Load / Revenue entry ID."
                )

            entry = (
                TripLoadRevenueEntry.objects
                .filter(
                    pk=entry_pk,
                    trip=trip,
                )
                .first()
            )

            if not entry:
                raise ValueError(
                    "Load / Revenue entry does not belong to this trip."
                )

            entry.date = row_date
            entry.from_location = from_location
            entry.to_location = to_location
            entry.load_place = load_place
            entry.ton = ton
            entry.income_amount = income_amount
            entry.commission_amount = commission_amount
            entry.loading_charges = loading_charges
            entry.unloading_charges = unloading_charges
            entry.updated_by = request.user
            entry.is_archived = False

            entry.save()

        # --------------------------------------------------------
        # NEW -> CREATE
        # --------------------------------------------------------

        else:

            entry = TripLoadRevenueEntry.objects.create(
                trip=trip,
                date=row_date,
                from_location=from_location,
                to_location=to_location,
                load_place=load_place,
                ton=ton,
                income_amount=income_amount,
                commission_amount=commission_amount,
                loading_charges=loading_charges,
                unloading_charges=unloading_charges,
                created_by=request.user,
                updated_by=request.user,
                is_archived=False,
            )

        submitted_load_ids.append(
            entry.id
        )

    # ------------------------------------------------------------
    # ARCHIVE REMOVED LOAD / REVENUE ROWS
    # ------------------------------------------------------------

    TripLoadRevenueEntry.objects.filter(
        trip=trip,
        is_archived=False,
    ).exclude(
        pk__in=submitted_load_ids
    ).update(
        is_archived=True,
        updated_by=request.user,
    )

    # ============================================================
    # 3. FUEL
    # ============================================================

    fuel_ids = _get_post_list(
        request,
        "fuel_id[]",
    )

    fuel_dates = _get_post_list(
        request,
        "fuel_date[]",
    )

    fuel_stations = _get_post_list(
        request,
        "fuel_station[]",
    )

    fuel_types = _get_post_list(
        request,
        "fuel_type[]",
    )

    fuel_quantities = _get_post_list(
        request,
        "fuel_quantity[]",
    )

    fuel_rates = _get_post_list(
        request,
        "fuel_rate[]",
    )

    fuel_receipts = _get_post_list(
        request,
        "fuel_receipt[]",
    )

    fuel_notes = _get_post_list(
        request,
        "fuel_notes[]",
    )

    submitted_fuel_ids = []

    row_count = max(
        len(fuel_ids),
        len(fuel_dates),
        len(fuel_stations),
        len(fuel_types),
        len(fuel_quantities),
        len(fuel_rates),
        len(fuel_receipts),
        len(fuel_notes),
    )

    for i in range(row_count):

        fuel_id = (
            fuel_ids[i].strip()
            if i < len(fuel_ids)
            else ""
        )

        fuel_date = (
            fuel_dates[i].strip()
            if i < len(fuel_dates)
            else ""
        )

        station_name = (
            fuel_stations[i].strip()
            if i < len(fuel_stations)
            else ""
        )

        fuel_type = (
            fuel_types[i].strip()
            if i < len(fuel_types)
            else "Diesel"
        )

        quantity = _positive_decimal(
            fuel_quantities[i]
            if i < len(fuel_quantities)
            else "0.000",
            "Fuel Quantity",
            "0.000",
        )

        rate = _positive_decimal(
            fuel_rates[i]
            if i < len(fuel_rates)
            else "0.00",
            "Fuel Rate",
        )

        receipt_number = (
            fuel_receipts[i].strip()
            if i < len(fuel_receipts)
            else ""
        )

        notes = (
            fuel_notes[i].strip()
            if i < len(fuel_notes)
            else ""
        )

        if fuel_type not in FUEL_TYPES:
            raise ValueError(
                "Invalid fuel type."
            )

        has_data = (
            bool(fuel_id)
            or bool(fuel_date)
            or bool(station_name)
            or quantity > ZERO_QTY
            or rate > ZERO
            or bool(receipt_number)
            or bool(notes)
        )

        if not has_data:
            continue

        if not fuel_date:
            fuel_date = entry_date

        # --------------------------------------------------------
        # EXISTING -> UPDATE
        # --------------------------------------------------------

        if fuel_id:

            fuel_pk = _safe_int(
                fuel_id
            )

            if not fuel_pk:
                raise ValueError(
                    "Invalid fuel entry ID."
                )

            fuel = (
                TripFuelEntry.objects
                .filter(
                    pk=fuel_pk,
                    trip=trip,
                )
                .first()
            )

            if not fuel:
                raise ValueError(
                    "Fuel entry does not belong to this trip."
                )

            fuel.fuel_type = fuel_type
            fuel.quantity = quantity
            fuel.rate = rate
            fuel.station_name = station_name
            fuel.fuel_date = fuel_date
            fuel.receipt_number = receipt_number
            fuel.notes = notes

            # Model save recalculates total_cost.
            fuel.save()

        # --------------------------------------------------------
        # NEW -> CREATE
        # --------------------------------------------------------

        else:

            fuel = TripFuelEntry.objects.create(
                trip=trip,
                fuel_type=fuel_type,
                quantity=quantity,
                rate=rate,
                total_cost=ZERO,
                station_name=station_name,
                fuel_date=fuel_date,
                receipt_number=receipt_number,
                notes=notes,
            )

        submitted_fuel_ids.append(
            fuel.id
        )

    # ------------------------------------------------------------
    # DELETE REMOVED FUEL ROWS
    # ------------------------------------------------------------

    if row_count > 0:

        trip.fuel_entries.exclude(
            pk__in=submitted_fuel_ids
        ).delete()

    # ============================================================
    # 4. SECTION 4 — OTHER EXPENSES
    # ============================================================

    expense_ids = _get_post_list(
        request,
        "expense_id[]",
    )

    expense_categories = _get_post_list(
        request,
        "expense_category[]",
    )

    expense_names = _get_post_list(
        request,
        "expense_name[]",
    )

    expense_dates = _get_post_list(
        request,
        "expense_date[]",
    )

    expense_amounts = _get_post_list(
        request,
        "expense_amount[]",
    )

    expense_descriptions = _get_post_list(
        request,
        "expense_description[]",
    )

    expense_payment_methods = _get_post_list(
        request,
        "expense_payment_method[]",
    )

    expense_receipts = _get_post_list(
        request,
        "expense_receipt[]",
    )

    submitted_expense_ids = []

    row_count = max(
        len(expense_ids),
        len(expense_categories),
        len(expense_names),
        len(expense_dates),
        len(expense_amounts),
        len(expense_descriptions),
        len(expense_payment_methods),
        len(expense_receipts),
    )

    for i in range(row_count):

        expense_id = (
            expense_ids[i].strip()
            if i < len(expense_ids)
            else ""
        )

        category_id = (
            expense_categories[i].strip()
            if i < len(expense_categories)
            else ""
        )

        expense_name = (
            expense_names[i].strip()
            if i < len(expense_names)
            else ""
        )

        expense_date = (
            expense_dates[i].strip()
            if i < len(expense_dates)
            else ""
        )

        amount = _positive_decimal(
            expense_amounts[i]
            if i < len(expense_amounts)
            else "0.00",
            "Other Expense Amount",
        )

        description = (
            expense_descriptions[i].strip()
            if i < len(expense_descriptions)
            else ""
        )

        payment_method = (
            expense_payment_methods[i].strip().upper()
            if i < len(expense_payment_methods)
            else "CASH"
        )

        receipt_number = (
            expense_receipts[i].strip()
            if i < len(expense_receipts)
            else ""
        )

        # --------------------------------------------------------
        # IMPORTANT
        # Don't create empty expense rows just because
        # payment method defaults to CASH.
        # --------------------------------------------------------

        has_data = (
            bool(expense_id)
            or bool(category_id)
            or bool(expense_name)
            or bool(expense_date)
            or amount > ZERO
            or bool(description)
            or bool(receipt_number)
        )

        if not has_data:
            continue

        if not expense_name:
            expense_name = "Expense"

        category = None

        if category_id:

            category_pk = _safe_int(
                category_id
            )

            if category_pk:

                category = (
                    ExpenseCategory.objects
                    .filter(
                        pk=category_pk,
                        is_active=True,
                    )
                    .first()
                )

        if not expense_date:
            expense_date = entry_date

        # --------------------------------------------------------
        # EXISTING -> UPDATE
        # --------------------------------------------------------

        if expense_id:

            expense_pk = _safe_int(
                expense_id
            )

            if not expense_pk:
                raise ValueError(
                    "Invalid expense entry ID."
                )

            expense = (
                TripExpenseEntry.objects
                .filter(
                    pk=expense_pk,
                    trip=trip,
                )
                .first()
            )

            if not expense:
                raise ValueError(
                    "Expense entry does not belong to this trip."
                )

            expense.category = category
            expense.expense_name = expense_name
            expense.expense_date = expense_date
            expense.amount = amount
            expense.description = description
            expense.receipt_number = receipt_number
            expense.payment_method = (
                payment_method
                or "CASH"
            )

            expense.save()

        # --------------------------------------------------------
        # NEW -> CREATE
        # --------------------------------------------------------

        else:

            expense = TripExpenseEntry.objects.create(
                trip=trip,
                category=category,
                expense_name=expense_name,
                expense_date=expense_date,
                amount=amount,
                payment_method=(
                    payment_method
                    or "CASH"
                ),
                receipt_number=receipt_number,
                description=description,
            )

        submitted_expense_ids.append(
            expense.id
        )

    # ------------------------------------------------------------
    # DELETE REMOVED SECTION 4 EXPENSES
    # ------------------------------------------------------------

    if row_count > 0:

        trip.expense_entries.exclude(
            pk__in=submitted_expense_ids
        ).delete()

    # ============================================================
    # 5. RTO / PC
    # ============================================================

    rto_pc_ids = _get_post_list(
        request,
        "rto_pc_id[]",
    )

    rto_pc_places = _get_post_list(
        request,
        "rto_pc_place[]",
    )

    rto_pc_types = _get_post_list(
        request,
        "rto_pc_type[]",
    )

    onward_amounts = _get_post_list(
        request,
        "rto_pc_onward[]",
    )

    return_amounts = _get_post_list(
        request,
        "rto_pc_return[]",
    )

    submitted_rto_pc_ids = []

    row_count = max(
        len(rto_pc_ids),
        len(rto_pc_places),
        len(rto_pc_types),
        len(onward_amounts),
        len(return_amounts),
    )

    for i in range(row_count):

        rto_pc_id = (
            rto_pc_ids[i].strip()
            if i < len(rto_pc_ids)
            else ""
        )

        place = (
            rto_pc_places[i].strip()
            if i < len(rto_pc_places)
            else ""
        )

        expense_type = (
            rto_pc_types[i].strip().upper()
            if i < len(rto_pc_types)
            else "RTO"
        )

        onward = _positive_decimal(
            onward_amounts[i]
            if i < len(onward_amounts)
            else "0.00",
            "RTO / PC Onward Amount",
        )

        return_amount = _positive_decimal(
            return_amounts[i]
            if i < len(return_amounts)
            else "0.00",
            "RTO / PC Return Amount",
        )

        if expense_type not in RTO_PC_TYPES:
            raise ValueError(
                "Invalid RTO / PC expense type."
            )

        has_data = (
            bool(rto_pc_id)
            or bool(place)
            or onward > ZERO
            or return_amount > ZERO
        )

        if not has_data:
            continue

        if not place:
            raise ValueError(
                "RTO / PC place is required."
            )

        # --------------------------------------------------------
        # EXISTING -> UPDATE
        # --------------------------------------------------------

        if rto_pc_id:

            rto_pc_pk = _safe_int(
                rto_pc_id
            )

            if not rto_pc_pk:
                raise ValueError(
                    "Invalid RTO / PC entry ID."
                )

            entry = (
                TripRtoPcEntry.objects
                .filter(
                    pk=rto_pc_pk,
                    trip=trip,
                )
                .first()
            )

            if not entry:
                raise ValueError(
                    "RTO / PC entry does not belong to this trip."
                )

            entry.place = place
            entry.expense_type = expense_type
            entry.onward_amount = onward
            entry.return_amount = return_amount

            entry.save()

        # --------------------------------------------------------
        # NEW -> CREATE
        # --------------------------------------------------------

        else:

            entry = TripRtoPcEntry.objects.create(
                trip=trip,
                place=place,
                expense_type=expense_type,
                onward_amount=onward,
                return_amount=return_amount,
            )

        submitted_rto_pc_ids.append(
            entry.id
        )

    # ------------------------------------------------------------
    # DELETE REMOVED RTO / PC
    # ------------------------------------------------------------

    if row_count > 0:

        trip.rto_pc_entries.exclude(
            pk__in=submitted_rto_pc_ids
        ).delete()

    # ============================================================
    # 6. OTHER TOLL EXPENSES
    # ============================================================
    #
    # MAIN TOLL GATE EXPENSE:
    #     trip.toll_gate_expense
    #
    # OTHER TOLL:
    #     Multiple child rows
    #
    # BOTH ARE INCLUDED IN OVERALL EXPENSE.
    # ============================================================

    other_toll_ids = _get_post_list(
        request,
        "other_toll_id[]",
    )

    other_toll_names = _get_post_list(
        request,
        "other_toll_name[]",
    )

    other_toll_dates = _get_post_list(
        request,
        "other_toll_date[]",
    )

    other_toll_amounts = _get_post_list(
        request,
        "other_toll_amount[]",
    )

    other_toll_notes = _get_post_list(
        request,
        "other_toll_notes[]",
    )

    submitted_other_toll_ids = []

    row_count = max(
        len(other_toll_ids),
        len(other_toll_names),
        len(other_toll_dates),
        len(other_toll_amounts),
        len(other_toll_notes),
    )

    for i in range(row_count):

        # --------------------------------------------------------
        # READ VALUES
        # --------------------------------------------------------

        other_toll_id = (
            other_toll_ids[i].strip()
            if i < len(other_toll_ids)
            else ""
        )

        toll_name = (
            other_toll_names[i].strip()
            if i < len(other_toll_names)
            else ""
        )

        toll_date = (
            other_toll_dates[i].strip()
            if i < len(other_toll_dates)
            else ""
        )

        amount = _positive_decimal(
            other_toll_amounts[i]
            if i < len(other_toll_amounts)
            else "0.00",
            "Other Toll Expense Amount",
        )

        notes = (
            other_toll_notes[i].strip()
            if i < len(other_toll_notes)
            else ""
        )

        # --------------------------------------------------------
        # EMPTY ROW -> SKIP
        # --------------------------------------------------------

        has_data = (
            bool(other_toll_id)
            or bool(toll_name)
            or bool(toll_date)
            or amount > ZERO
            or bool(notes)
        )

        if not has_data:
            continue

        # --------------------------------------------------------
        # TOLL NAME REQUIRED
        # --------------------------------------------------------

        if not toll_name:
            raise ValueError(
                "Other Toll name is required."
            )

        # --------------------------------------------------------
        # DATE DEFAULT
        # --------------------------------------------------------

        if not toll_date:
            toll_date = entry_date

        # --------------------------------------------------------
        # EXISTING -> UPDATE
        # --------------------------------------------------------

        if other_toll_id:

            other_toll_pk = _safe_int(
                other_toll_id
            )

            if not other_toll_pk:
                raise ValueError(
                    "Invalid Other Toll entry ID."
                )

            other_toll = (
                TripOtherTollExpense.objects
                .filter(
                    pk=other_toll_pk,
                    trip=trip,
                )
                .first()
            )

            if not other_toll:
                raise ValueError(
                    "Other Toll entry does not belong to this trip."
                )

            other_toll.toll_name = toll_name
            other_toll.toll_date = toll_date
            other_toll.amount = amount
            other_toll.notes = notes

            other_toll.save()

        # --------------------------------------------------------
        # NEW -> CREATE
        # --------------------------------------------------------

        else:

            other_toll = (
                TripOtherTollExpense.objects.create(
                    trip=trip,
                    toll_name=toll_name,
                    toll_date=toll_date,
                    amount=amount,
                    notes=notes,
                )
            )

        submitted_other_toll_ids.append(
            other_toll.id
        )

    # ------------------------------------------------------------
    # DELETE REMOVED OTHER TOLL ROWS
    # ------------------------------------------------------------

    if row_count > 0:

        trip.other_toll_expenses.exclude(
            pk__in=submitted_other_toll_ids
        ).delete()

    # ============================================================
    # DONE
    # ============================================================
# ================================================================
# TRIP DETAIL
# ================================================================

@login_required
def trip_detail(request, pk):
    """
    Premium Trip Ledger Detail Page.

    FINAL ACCOUNTING FORMULA:

    Overall Income
        = Section 2 Income

    Driver Salary
        = 13% of Overall Income

    Overall Expense
        = Diesel
        + AdBlue
        + Loading
        + Unloading
        + Driver Salary
        + Cleaner Salary
        + Workshop Expense
        + RTO
        + PC
        + Toll Gate
        + Section 4 Other Expenses

    Commission:
        Displayed for reference only.
        NOT included in Overall Expense.
    """

    # ============================================================
    # LOAD TRIP
    # ============================================================

    trip = get_object_or_404(
        Trip.objects
        .select_related(
            "vehicle",
            "primary_driver",
            "secondary_driver",
            "km_detail",
            "created_by",
            "updated_by",
        )
        .prefetch_related(
            "load_revenue_entries",
            "fuel_entries",
            "expense_entries",
            "rto_pc_entries",
        ),
        pk=pk,
    )

    # ============================================================
    # KM
    # ============================================================

    km_detail = getattr(trip, "km_detail", None)

    if km_detail:
        total_km = km_detail.total_km or Decimal("0.00")
        start_km = km_detail.start_km or Decimal("0.00")
        end_km = km_detail.end_km or Decimal("0.00")
    else:
        total_km = Decimal("0.00")
        start_km = Decimal("0.00")
        end_km = Decimal("0.00")

    # ============================================================
    # SECTION 2 - LOAD & REVENUE
    # ============================================================

    load_entries = [
        entry
        for entry in trip.load_revenue_entries.all()
        if not entry.is_archived
    ]

    total_ton = sum(
        (entry.ton or Decimal("0.00") for entry in load_entries),
        Decimal("0.00"),
    )

    overall_income = sum(
        (
            entry.income_amount or Decimal("0.00")
            for entry in load_entries
        ),
        Decimal("0.00"),
    )

    commission_total = sum(
        (
            entry.commission_amount or Decimal("0.00")
            for entry in load_entries
        ),
        Decimal("0.00"),
    )

    loading_charges = sum(
        (
            entry.loading_charges or Decimal("0.00")
            for entry in load_entries
        ),
        Decimal("0.00"),
    )

    unloading_charges = sum(
        (
            entry.unloading_charges or Decimal("0.00")
            for entry in load_entries
        ),
        Decimal("0.00"),
    )

    # ============================================================
    # FUEL
    # ============================================================

    fuel_entries = list(trip.fuel_entries.all())

    diesel_entries = [
        fuel
        for fuel in fuel_entries
        if fuel.fuel_type == "Diesel"
    ]

    adblue_entries = [
        fuel
        for fuel in fuel_entries
        if fuel.fuel_type == "AdBlue"
    ]

    total_diesel_quantity = sum(
        (
            fuel.quantity or Decimal("0.000")
            for fuel in diesel_entries
        ),
        Decimal("0.000"),
    )

    total_adblue_quantity = sum(
        (
            fuel.quantity or Decimal("0.000")
            for fuel in adblue_entries
        ),
        Decimal("0.000"),
    )

    total_fuel_quantity = (
        total_diesel_quantity
        + total_adblue_quantity
    )

    diesel_cost = sum(
        (
            fuel.total_cost or Decimal("0.00")
            for fuel in diesel_entries
        ),
        Decimal("0.00"),
    )

    adblue_cost = sum(
        (
            fuel.total_cost or Decimal("0.00")
            for fuel in adblue_entries
        ),
        Decimal("0.00"),
    )

    total_fuel_cost = (
        diesel_cost
        + adblue_cost
    )

    # ============================================================
    # MILEAGE
    # Mileage is based ONLY on Diesel consumption.
    # ============================================================

    if total_diesel_quantity > Decimal("0.000"):
        mileage = round(
            total_km / total_diesel_quantity,
            2,
        )
    else:
        mileage = Decimal("0.00")

    # ============================================================
    # SECTION 4 - OTHER EXPENSES
    # ============================================================

    expense_entries = list(
        trip.expense_entries.all()
    )

    other_expenses = sum(
        (
            expense.amount or Decimal("0.00")
            for expense in expense_entries
        ),
        Decimal("0.00"),
    )

    # ============================================================
    # RTO / PC
    # ============================================================

    rto_pc_entries = list(
        trip.rto_pc_entries.all()
    )

    rto_expense = sum(
        (
            entry.total_amount
            for entry in rto_pc_entries
            if entry.expense_type == "RTO"
        ),
        Decimal("0.00"),
    )

    pc_expense = sum(
        (
            entry.total_amount
            for entry in rto_pc_entries
            if entry.expense_type == "PC"
        ),
        Decimal("0.00"),
    )

    rto_pc_total = (
        rto_expense
        + pc_expense
    )
    
    # ============================================================
# OTHER TOLL EXPENSES
# ============================================================

    other_toll_entries = list(
    trip.other_toll_expenses.all()
)

    other_toll_expense = sum(
    (
        entry.amount or Decimal("0.00")
        for entry in other_toll_entries
    ),
    Decimal("0.00"),
)
    # ============================================================
    # MANUAL ACCOUNTING EXPENSES
    # ============================================================

    cleaner_salary = (
        trip.cleaner_salary
        or Decimal("0.00")
    )

    workshop_expense = (
        trip.workshop_expense
        or Decimal("0.00")
    )

    toll_gate_expense = (
        trip.toll_gate_expense
        or Decimal("0.00")
    )

    # ============================================================
    # DRIVER SALARY
    # 13% OF SECTION 2 OVERALL INCOME
    # ============================================================

    driver_salary = (
        overall_income
        * Decimal("13.00")
        / Decimal("100.00")
    ).quantize(
        Decimal("0.01")
    )

    # ============================================================
    # FINAL OVERALL EXPENSE
    #
    # COMMISSION IS INCLUDED
    # ============================================================

    overall_expense = (
        diesel_cost
        + adblue_cost
        + loading_charges
        + unloading_charges
        + driver_salary
        + cleaner_salary
        + workshop_expense
        + rto_expense
        + pc_expense
        + toll_gate_expense
        + other_toll_expense
        + other_expenses
        + commission_total
    )

    # ============================================================
    # FINAL BALANCE
    # ============================================================

    final_balance = (
        overall_income
        - overall_expense
    )

    # ============================================================
    # FUEL COST PER KM
    # ============================================================

    if total_km > Decimal("0.00"):
        fuel_cost_per_km = round(
            total_fuel_cost / total_km,
            2,
        )
    else:
        fuel_cost_per_km = Decimal("0.00")

    # ============================================================
    # EXPENSE CATEGORIES
    # IMPORTANT: category_name, NOT name
    # ============================================================

    expense_cats = (
        ExpenseCategory.objects
        .filter(is_active=True)
        .order_by("category_name")
    )

    # ============================================================
    # CONTEXT
    # ============================================================

    context = {
        "trip": trip,

        # -------------------------
        # KM
        # -------------------------

        "km_detail": km_detail,
        "start_km": start_km,
        "end_km": end_km,
        "total_km": total_km,

        # -------------------------
        # LOAD / REVENUE
        # -------------------------

        "load_entries": load_entries,
        "total_ton": total_ton,
        "overall_income": overall_income,
        "commission_total": commission_total,
        "loading_charges": loading_charges,
        "unloading_charges": unloading_charges,

        # -------------------------
        # FUEL
        # -------------------------

        "fuel_entries": fuel_entries,
        "total_diesel_quantity": total_diesel_quantity,
        "total_adblue_quantity": total_adblue_quantity,
        "total_fuel_quantity": total_fuel_quantity,

        "diesel_cost": diesel_cost,
        "adblue_cost": adblue_cost,
        "total_fuel_cost": total_fuel_cost,

        "mileage": mileage,
        "fuel_cost_per_km": fuel_cost_per_km,

        # -------------------------
        # SECTION 4
        # -------------------------

        "expense_entries": expense_entries,
        "other_expenses": other_expenses,
        "expense_cats": expense_cats,

        # -------------------------
        # RTO / PC
        # -------------------------

        "rto_pc_entries": rto_pc_entries,
        "rto_expense": rto_expense,
        "pc_expense": pc_expense,
        "rto_pc_total": rto_pc_total,

        # -------------------------
        # MANUAL EXPENSES
        # -------------------------

        "driver_salary": driver_salary,
        "cleaner_salary": cleaner_salary,
        "workshop_expense": workshop_expense,
        "toll_gate_expense": toll_gate_expense,

        # -------------------------
        # FINAL ACCOUNTING
        # -------------------------

        "overall_expense": overall_expense,
        "final_balance": final_balance,
    }

    return render(
        request,
        "trips/detail.html",
        context,
    )
# ================================================================
# TRIP DELETE
# ================================================================

@login_required
def trip_delete(request, pk):

    trip = get_object_or_404(
        Trip,
        pk=pk,
        created_by=request.user,
    )

    if request.method == "POST":

        ref = trip.trip_ref_no

        with transaction.atomic():

            _audit(
                user=request.user,
                action="DELETE",
                model_name="Trip",
                object_id=trip.id,
                details={
                    "ref_no": ref,
                    "vehicle": str(
                        trip.vehicle
                    ),
                    "income": str(
                        trip.total_income
                    ),
                    "expense": str(
                        trip.overall_expense
                    ),
                    "balance": str(
                        trip.balance
                    ),
                },
            )

            trip.delete()

        messages.success(
            request,
            (
                f"Trip #{ref} "
                "deleted successfully."
            ),
        )

    return redirect(
        "trips:list"
    )


# ================================================================
# TRIP ARCHIVE / RESTORE
# ================================================================

@login_required
def trip_archive(request, pk):

    trip = get_object_or_404(
        Trip,
        pk=pk,
        created_by=request.user,
    )

    trip.is_archived = not trip.is_archived

    trip.updated_by = request.user

    trip.save(
        update_fields=[
            "is_archived",
            "updated_by",
            "updated_at",
        ],
    )

    if trip.is_archived:

        action = "ARCHIVE"
        status_text = "archived"

    else:

        action = "RESTORE"
        status_text = "restored"

    _audit(
        user=request.user,
        action=action,
        model_name="Trip",
        object_id=trip.id,
        details={
            "ref_no": trip.trip_ref_no,
        },
    )

    messages.info(
        request,
        (
            f"Trip #{trip.trip_ref_no} "
            f"has been {status_text}."
        ),
    )

    return redirect(
        "trips:list"
    )


# ================================================================
# FUEL LOGBOOK
# ================================================================

@login_required
def fuel_logbook(request):

    fuel_entries = (
        TripFuelEntry.objects
        .filter(trip__created_by=request.user)
        .select_related(
            "trip",
            "trip__vehicle",
            "trip__primary_driver",
        )
        .order_by(
            "-fuel_date",
            "-id",
        )
    )

    paginator = Paginator(
        fuel_entries,
        25,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    return render(
        request,
        "trips/fuel_logbook.html",
        {
            "page_obj": page_obj,
        },
    )


# ================================================================
# FUEL EDIT
# ================================================================

@login_required
def fuel_edit(request, pk):
    fuel = get_object_or_404(
        TripFuelEntry.objects.select_related('trip'),
        pk=pk, trip__created_by=request.user
    )

    if request.method == 'GET':
        return render(
            request,
            'trips/partials/edit_fuel_modal.html',
            {
                'fuel': fuel,
            }
        )

    if request.method != 'POST':
        return JsonResponse(
            {
                'success': False,
                'message': 'Invalid request method.'
            },
            status=405
        )

    fuel_type = request.POST.get('fuel_type', '').strip()
    quantity = request.POST.get('quantity', '').strip()
    rate = request.POST.get('rate', '').strip()
    station = request.POST.get('station', '').strip()
    fuel_date = request.POST.get('fuel_date', '').strip()

    errors = {}

    if fuel_type not in ['Diesel', 'AdBlue']:
        errors['fuel_type'] = 'Select Diesel or AdBlue.'

    try:
        quantity_decimal = Decimal(quantity or '0')

        if quantity_decimal <= 0:
            errors['quantity'] = 'Quantity must be greater than zero.'

    except (InvalidOperation, ValueError):
        quantity_decimal = Decimal('0')
        errors['quantity'] = 'Enter a valid quantity.'

    try:
        rate_decimal = Decimal(rate or '0')

        if rate_decimal < 0:
            errors['rate'] = 'Rate cannot be negative.'

    except (InvalidOperation, ValueError):
        rate_decimal = Decimal('0')
        errors['rate'] = 'Enter a valid rate.'

    parsed_date = None

    if fuel_date:
        try:
            parsed_date = datetime.strptime(
                fuel_date,
                '%Y-%m-%d'
            ).date()
        except ValueError:
            errors['fuel_date'] = 'Enter a valid date.'

    if errors:
        return render(
            request,
            'trips/partials/edit_fuel_modal.html',
            {
                'fuel': fuel,
                'errors': errors,
            },
            status=400
        )

    fuel.fuel_type = fuel_type
    fuel.quantity = quantity_decimal
    fuel.rate_per_litre = rate_decimal
    fuel.station_name = station
    fuel.fuel_date = parsed_date

    fuel.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Fuel entry updated successfully.',
            'id': fuel.id,
        })

    return redirect(
        'trips:detail',
        pk=fuel.trip_id
    )
# ================================================================
# FUEL DELETE
# ================================================================

@login_required
def fuel_delete(request, pk):

    entry = get_object_or_404(
        TripFuelEntry.objects.select_related(
            "trip"
        ),
        pk=pk,
    )

    trip = entry.trip

    if request.method == "POST":

        _audit(
            user=request.user,
            action="DELETE",
            model_name="TripFuelEntry",
            object_id=entry.id,
            details={
                "trip": trip.trip_ref_no,
                "fuel_type": entry.fuel_type,
                "amount": str(
                    entry.total_cost
                ),
            },
        )

        entry.delete()

        messages.success(
            request,
            "Fuel entry deleted successfully.",
        )

    return redirect(
        "trips:detail",
        pk=trip.pk,
    )


# ================================================================
# LOAD / REVENUE EDIT
# ================================================================

@login_required
def load_revenue_edit(request, pk):

    entry = get_object_or_404(
        TripLoadRevenueEntry,
        pk=pk, trip__created_by=request.user
    )

    trip = entry.trip

    # ============================================================
    # GET → RETURN ONLY MODAL FORM
    # ============================================================

    if request.method == "GET":

        return render(
            request,
            "trips/partials/edit_load_revenue_modal.html",
            {
                "entry": entry,
            }
        )

    # ============================================================
    # POST → UPDATE
    # ============================================================

    if request.method == "POST":

        entry.date = request.POST.get(
            "date",
            str(entry.date)
        )

        entry.from_location = request.POST.get(
            "from_location",
            entry.from_location or ""
        ).strip()

        entry.to_location = request.POST.get(
            "to_location",
            entry.to_location or ""
        ).strip()

        entry.load_place = request.POST.get(
            "load_place",
            entry.load_place or ""
        ).strip()

        entry.ton = _dec(
            request.POST.get(
                "ton",
                str(entry.ton)
            ),
            str(entry.ton)
        )

        entry.income_amount = _dec(
            request.POST.get(
                "income_amount",
                str(entry.income_amount)
            ),
            str(entry.income_amount)
        )

        entry.commission_amount = _dec(
            request.POST.get(
                "commission_amount",
                str(entry.commission_amount)
            ),
            str(entry.commission_amount)
        )

        entry.loading_charges = _dec(
            request.POST.get(
                "loading_charges",
                str(entry.loading_charges)
            ),
            str(entry.loading_charges)
        )

        entry.unloading_charges = _dec(
            request.POST.get(
                "unloading_charges",
                str(entry.unloading_charges)
            ),
            str(entry.unloading_charges)
        )

        entry.updated_by = request.user
        entry.is_archived = False

        entry.save()

        _audit(
            user=request.user,
            action="UPDATE",
            model_name="TripLoadRevenueEntry",
            object_id=entry.id,
            details={
                "trip": trip.trip_ref_no,
            },
        )

        # ========================================================
        # AJAX → JSON
        # ========================================================

        if request.headers.get(
            "X-Requested-With"
        ) == "XMLHttpRequest":

            return JsonResponse({
                "success": True,
                "message": "Load / Revenue entry updated successfully.",
                "id": entry.id,
            })

        # Normal browser request
        return redirect(
            "trips:detail",
            pk=trip.pk
        )

    return JsonResponse(
        {
            "success": False,
            "message": "Invalid request method."
        },
        status=405
    )

# ================================================================
# LOAD / REVENUE DELETE
# ================================================================

@login_required
def load_revenue_delete(request, pk):

    entry = get_object_or_404(
        TripLoadRevenueEntry.objects.select_related(
            "trip"
        ),
        pk=pk,
    )

    trip = entry.trip

    if request.method == "POST":

        _audit(
            user=request.user,
            action="DELETE",
            model_name="TripLoadRevenueEntry",
            object_id=entry.id,
            details={
                "trip": trip.trip_ref_no,
                "income": str(
                    entry.income_amount
                ),
            },
        )

        entry.delete()

        messages.success(
            request,
            (
                "Load / Revenue entry "
                "deleted successfully."
            ),
        )

    return redirect(
        "trips:detail",
        pk=trip.pk,
    )


# ================================================================
# EXPENSE EDIT
# ================================================================

@login_required
def expense_entry_edit(request, pk):

    expense = get_object_or_404(
        TripExpenseEntry,
        pk=pk, trip__created_by=request.user
    )

    if request.method == "GET":

        return render(
            request,
            "trips/partials/edit_expense_entry_modal.html",
            {
                "expense": expense,
            }
        )

    if request.method == "POST":

        expense_name = request.POST.get(
            "expense_name",
            ""
        ).strip()

        amount = request.POST.get(
            "amount",
            "0.00"
        ).strip()

        errors = {}

        # Expense Name
        if not expense_name:
            errors["expense_name"] = (
                "Expense name is required."
            )

        # Amount
        try:
            amount_decimal = Decimal(
                amount or "0.00"
            )

            if amount_decimal < Decimal("0.00"):
                errors["amount"] = (
                    "Amount cannot be negative."
                )

        except (InvalidOperation, ValueError):
            amount_decimal = Decimal("0.00")

            errors["amount"] = (
                "Enter a valid amount."
            )

        # Validation
        if errors:

            return render(
                request,
                "trips/partials/edit_expense_entry_modal.html",
                {
                    "expense": expense,
                    "errors": errors,
                },
                status=400
            )

        # Update existing record
        expense.expense_name = expense_name
        expense.amount = amount_decimal

        expense.save()

        # AJAX success
        if request.headers.get(
            "X-Requested-With"
        ) == "XMLHttpRequest":

            return JsonResponse({
                "success": True,
                "message": (
                    "Other Expense updated successfully."
                ),
                "id": expense.id,
            })

        # Normal request
        return redirect(
            "trips:detail",
            pk=expense.trip_id
        )

    return JsonResponse(
        {
            "success": False,
            "message": "Invalid request method."
        },
        status=405
    )
# ================================================================
# EXPENSE DELETE
# ================================================================

@login_required
def expense_entry_delete(request, pk):

    entry = get_object_or_404(
        TripExpenseEntry.objects.select_related(
            "trip"
        ),
        pk=pk,
    )

    trip = entry.trip

    if request.method == "POST":

        _audit(
            user=request.user,
            action="DELETE",
            model_name="TripExpenseEntry",
            object_id=entry.id,
            details={
                "trip": trip.trip_ref_no,
                "expense_name": entry.expense_name,
                "amount": str(
                    entry.amount
                ),
            },
        )

        entry.delete()

        messages.success(
            request,
            "Expense deleted successfully.",
        )

    return redirect(
        "trips:detail",
        pk=trip.pk,
    )


# ================================================================
# RTO / PC EDIT
# ================================================================

@login_required
def rto_pc_edit(request, pk):

    entry = get_object_or_404(
        TripRtoPcEntry,
        pk=pk, trip__created_by=request.user
    )

    if request.method == "GET":

        return render(
            request,
            "trips/partials/edit_rto_pc_modal.html",
            {
                "entry": entry,
            }
        )

    if request.method == "POST":

        place = request.POST.get(
            "place",
            ""
        ).strip()

        expense_type = request.POST.get(
            "expense_type",
            "RTO"
        ).strip().upper()

        onward_amount = request.POST.get(
            "onward_amount",
            "0.00"
        ).strip()

        return_amount = request.POST.get(
            "return_amount",
            "0.00"
        ).strip()

        errors = {}

        if not place:
            errors["place"] = "Place is required."

        if expense_type not in ("RTO", "PC"):
            errors["expense_type"] = "Select RTO or PC."

        onward = _dec(
            onward_amount,
            "0.00"
        )

        return_value = _dec(
            return_amount,
            "0.00"
        )

        if onward < Decimal("0.00"):
            errors["onward_amount"] = (
                "Onward amount cannot be negative."
            )

        if return_value < Decimal("0.00"):
            errors["return_amount"] = (
                "Return amount cannot be negative."
            )

        if errors:

            return render(
                request,
                "trips/partials/edit_rto_pc_modal.html",
                {
                    "entry": entry,
                    "errors": errors,
                },
                status=400
            )

        entry.place = place
        entry.expense_type = expense_type
        entry.onward_amount = onward
        entry.return_amount = return_value

        entry.save()

        if request.headers.get(
            "X-Requested-With"
        ) == "XMLHttpRequest":

            return JsonResponse({
                "success": True,
                "message": (
                    "RTO / PC entry updated successfully."
                ),
                "id": entry.id,
            })

        return redirect(
            "trips:detail",
            pk=entry.trip_id
        )

    return JsonResponse(
        {
            "success": False,
            "message": "Invalid request method."
        },
        status=405
    )
# ================================================================
# RTO / PC DELETE
# ================================================================

@login_required
def rto_pc_delete(request, pk):

    entry = get_object_or_404(
        TripRtoPcEntry.objects.select_related(
            "trip"
        ),
        pk=pk,
    )

    trip = entry.trip

    if request.method == "POST":

        _audit(
            user=request.user,
            action="DELETE",
            model_name="TripRtoPcEntry",
            object_id=entry.id,
            details={
                "trip": trip.trip_ref_no,
                "type": entry.expense_type,
                "total": str(
                    entry.total_amount
                ),
            },
        )

        entry.delete()

        messages.success(
            request,
            "RTO / PC entry deleted successfully.",
        )

    return redirect(
        "trips:detail",
        pk=trip.pk,
    )


# ================================================================
# VEHICLE OWNER AJAX
# ================================================================

@login_required
def vehicle_owner_api(request, pk):

    vehicle = get_object_or_404(
        Vehicle,
        pk=pk,
        created_by=request.user,
    )

    return JsonResponse(
        {
            "success": True,
            "owner_name": (
                vehicle.owner_name
                or ""
            ),
            "vehicle_number": (
                vehicle.vehicle_number
                or ""
            ),
        }
    )

# ============================================================
# OTHER TOLL EXPENSE - EDIT
# ============================================================

@login_required
def other_toll_edit(request, pk):
    toll = get_object_or_404(
        TripOtherTollExpense.objects.select_related('trip'),
        pk=pk, trip__created_by=request.user
    )

    if request.method == 'GET':
        return render(
            request,
            'trips/partials/edit_other_toll_modal.html',
            {
                'toll': toll,
            }
        )

    if request.method != 'POST':
        return JsonResponse(
            {
                'success': False,
                'message': 'Invalid request method.'
            },
            status=405
        )

    toll_name = request.POST.get('toll_name', '').strip()
    toll_date = request.POST.get('toll_date', '').strip()
    amount = request.POST.get('amount', '').strip()
    notes = request.POST.get('notes', '').strip()

    errors = {}

    # Toll name
    if not toll_name:
        errors['toll_name'] = 'Toll name is required.'

    # Amount
    try:
        amount_decimal = Decimal(amount or '0.00')

        if amount_decimal < Decimal('0.00'):
            errors['amount'] = 'Amount cannot be negative.'

    except (InvalidOperation, ValueError):
        amount_decimal = Decimal('0.00')
        errors['amount'] = 'Enter a valid amount.'

    # Date
    parsed_date = None

    if toll_date:
        try:
            parsed_date = datetime.strptime(
                toll_date,
                '%Y-%m-%d'
            ).date()
        except ValueError:
            errors['toll_date'] = 'Enter a valid date.'

    # Validation error
    if errors:
        return render(
            request,
            'trips/partials/edit_other_toll_modal.html',
            {
                'toll': toll,
                'errors': errors,
            },
            status=400
        )

    # Update
    toll.toll_name = toll_name
    toll.toll_date = parsed_date
    toll.amount = amount_decimal
    toll.notes = notes

    toll.save()

    # AJAX success
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Other Toll Expense updated successfully.',
            'id': toll.id,
        })

    return redirect(
        'trips:detail',
        pk=toll.trip_id
    )

# ============================================================
# OTHER TOLL EXPENSE — DELETE
# ============================================================

@login_required
def other_toll_delete(request, pk):

    toll = get_object_or_404(
        TripOtherTollExpense,
        pk=pk, trip__created_by=request.user
    )

    trip_id = toll.trip_id

    # ========================================================
    # ONLY POST ALLOWED
    # ========================================================

    if request.method != 'POST':

        if request.headers.get(
            'X-Requested-With'
        ) == 'XMLHttpRequest':

            return JsonResponse(
                {
                    'success': False,
                    'message': (
                        'Invalid request method.'
                    )
                },
                status=405
            )

        return redirect(
            'trips:detail',
            pk=trip_id
        )

    # ========================================================
    # DELETE
    # ========================================================

    toll.delete()

    # ========================================================
    # AJAX SUCCESS
    # ========================================================

    if request.headers.get(
        'X-Requested-With'
    ) == 'XMLHttpRequest':

        return JsonResponse(
            {
                'success': True,
                'message': (
                    'Other Toll Expense '
                    'deleted successfully.'
                )
            }
        )

    return redirect(
        'trips:detail',
        pk=trip_id
    )

# ============================================================
# EXPORT VIEWS
# ============================================================

from django.http import HttpResponse
from datetime import datetime
from trips.utils.export_context import build_trip_voucher_context, build_reports_context
from trips.utils.pdf_generator import generate_trip_voucher_pdf, generate_reports_summary_pdf
from trips.utils.word_generator import generate_trip_voucher_word, generate_reports_summary_word

@login_required
def reports_summary_pdf(request):
    context = build_reports_context(request)
    response = HttpResponse(content_type='application/pdf')
    filename = f"vehicle_ledger_reports_{datetime.now().strftime('%Y-%m-%d')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    generate_reports_summary_pdf(context, response)
    return response

@login_required
def reports_summary_word(request):
    context = build_reports_context(request)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    filename = f"vehicle_ledger_reports_{datetime.now().strftime('%Y-%m-%d')}.docx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    generate_reports_summary_word(context, response)
    return response

@login_required
def trip_voucher_pdf(request, trip_id):
    context = build_trip_voucher_context(trip_id)
    response = HttpResponse(content_type='application/pdf')
    filename = f"trip_ledger_voucher_{trip_id}_{datetime.now().strftime('%Y-%m-%d')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    generate_trip_voucher_pdf(context, response)
    return response

@login_required
def trip_voucher_word(request, trip_id):
    context = build_trip_voucher_context(trip_id)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    filename = f"trip_ledger_voucher_{trip_id}_{datetime.now().strftime('%Y-%m-%d')}.docx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    generate_trip_voucher_word(context, response)
    return response