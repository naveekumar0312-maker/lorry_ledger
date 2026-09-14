from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from trips.models import Trip
from vehicles.models import Vehicle
from drivers.models import Driver


@login_required
def reports_index(request):

    # ============================================================
    # FILTERS
    # ============================================================

    vehicle_id = request.GET.get(
        'vehicle_id',
        ''
    ).strip()

    driver_id = request.GET.get(
        'driver_id',
        ''
    ).strip()

    from_date = request.GET.get(
        'from_date',
        ''
    ).strip()

    to_date = request.GET.get(
        'to_date',
        ''
    ).strip()


    # ============================================================
    # BASE QUERY
    # ============================================================

    trips = (
        Trip.objects
        .filter(
            is_archived=False,
            created_by=request.user
        )
        .select_related(
            'vehicle',
            'primary_driver',
            'secondary_driver',
            'km_detail',
        )
        .prefetch_related(
            'fuel_entries',
            'load_revenue_entries',
            'expense_entries',
            'rto_pc_entries',
            'other_toll_expenses',
        )
        .order_by(
            '-entry_date',
            '-id'
        )
    )


    # ============================================================
    # APPLY FILTERS
    # ============================================================

    if vehicle_id:

        trips = trips.filter(
            vehicle_id=vehicle_id
        )


    if driver_id:

        trips = trips.filter(
            primary_driver_id=driver_id
        )


    if from_date:

        trips = trips.filter(
            entry_date__gte=from_date
        )


    if to_date:

        trips = trips.filter(
            entry_date__lte=to_date
        )


    # ============================================================
    # SUMMARY TOTALS
    # ============================================================

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


    # ============================================================
    # TRIP-WISE DATA
    # ============================================================

    report_rows = []


    for trip in trips:

        # --------------------------------------------------------
        # INCOME
        # --------------------------------------------------------

        income = (
            trip.total_income
            or Decimal('0.00')
        )


        # --------------------------------------------------------
        # KM
        # --------------------------------------------------------

        trip_km = (
            trip.total_km
            or Decimal('0.00')
        )


        # --------------------------------------------------------
        # FUEL
        # --------------------------------------------------------

        diesel_qty = (
            trip.total_diesel_quantity
            or Decimal('0.000')
        )

        adblue_qty = (
            trip.total_adblue_quantity
            or Decimal('0.000')
        )

        diesel_cost = (
            trip.total_diesel_cost
            or Decimal('0.00')
        )

        adblue_cost = (
            trip.total_adblue_cost
            or Decimal('0.00')
        )

        fuel_cost = (
            diesel_cost
            + adblue_cost
        )


        # --------------------------------------------------------
        # SECTION 2
        # --------------------------------------------------------

        commission = (
            trip.total_revenue_commission
            or Decimal('0.00')
        )

        loading = (
            trip.total_revenue_loading
            or Decimal('0.00')
        )

        unloading = (
            trip.total_revenue_unloading
            or Decimal('0.00')
        )


        # --------------------------------------------------------
        # DRIVER SALARY
        # 13% OF OVERALL INCOME
        # --------------------------------------------------------

        driver_salary = (
            income
            * Decimal('13.00')
            / Decimal('100.00')
        ).quantize(
            Decimal('0.01')
        )


        # --------------------------------------------------------
        # MANUAL ACCOUNTING EXPENSES
        # --------------------------------------------------------

        cleaner_salary = (
            trip.cleaner_salary
            or Decimal('0.00')
        )

        workshop_expense = (
            trip.workshop_expense
            or Decimal('0.00')
        )

        toll_gate = (
            trip.toll_gate_expense
            or Decimal('0.00')
        )


        # --------------------------------------------------------
        # RTO / PC
        # --------------------------------------------------------

        rto = (
            trip.total_rto_expense
            or Decimal('0.00')
        )

        pc = (
            trip.total_pc_expense
            or Decimal('0.00')
        )


        # --------------------------------------------------------
        # OTHER TOLL EXPENSES
        # --------------------------------------------------------

        other_toll_expense = (
            trip.total_other_toll_expense
            or Decimal('0.00')
        )


        # --------------------------------------------------------
        # SECTION 4 OTHER EXPENSES
        # --------------------------------------------------------

        other_expenses = (
            trip.total_other_expenses
            or Decimal('0.00')
        )


        # ========================================================
        # FINAL OVERALL EXPENSE
        #
        # Diesel
        # + AdBlue
        # + Loading
        # + Unloading
        # + Driver Salary 13%
        # + Cleaner Salary
        # + Workshop
        # + RTO
        # + PC
        # + Toll Gate
        # + Other Toll
        # + Section 4 Expenses
        #
        # Commission is INCLUDED.
        # ========================================================

        overall_expense = (

            diesel_cost

            + adblue_cost

            + loading

            + unloading

            + driver_salary

            + cleaner_salary

            + workshop_expense

            + rto

            + pc

            + toll_gate

            + other_toll_expense

            + other_expenses

            + commission

        )


        # --------------------------------------------------------
        # FINAL BALANCE
        # --------------------------------------------------------

        balance = (
            income
            - overall_expense
        )


        # ========================================================
        # GRAND TOTALS
        # ========================================================

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

        total_other_toll_expense += (
            other_toll_expense
        )

        total_other_expenses += (
            other_expenses
        )

        total_overall_expense += (
            overall_expense
        )

        total_balance += balance


        # ========================================================
        # TRIP-WISE REPORT ROW
        # ========================================================

        report_rows.append({

            'trip': trip,

            'income': income,

            'diesel_qty': diesel_qty,

            'diesel_cost': diesel_cost,

            'adblue_qty': adblue_qty,

            'adblue_cost': adblue_cost,

            'commission': commission,

            'loading': loading,

            'unloading': unloading,

            'driver_salary': driver_salary,

            'cleaner_salary': cleaner_salary,

            'workshop_expense': workshop_expense,

            'rto': rto,

            'pc': pc,

            'toll_gate': toll_gate,

            'other_toll_expense': (
                other_toll_expense
            ),

            'other_expenses': (
                other_expenses
            ),

            'overall_expense': (
                overall_expense
            ),

            'balance': balance,

        })


    # ============================================================
    # AVERAGE MILEAGE
    #
    # Diesel ONLY
    # ============================================================

    if total_diesel_qty > Decimal('0.000'):

        avg_mileage = round(

            total_km
            / total_diesel_qty,

            2

        )

    else:

        avg_mileage = Decimal('0.00')


    # ============================================================
    # FUEL COST PER KM
    #
    # Diesel + AdBlue
    # ============================================================

    if total_km > Decimal('0.00'):

        fuel_cost_per_km = round(

            total_fuel_cost
            / total_km,

            2

        )

    else:

        fuel_cost_per_km = Decimal('0.00')


    # ============================================================
    # EXPENSE RATIO / PROFIT MARGIN
    # ============================================================

    if total_income > Decimal('0.00'):

        expense_ratio = round(

            (
                total_overall_expense
                / total_income
            )
            * Decimal('100.00'),

            2

        )


        profit_margin = round(

            (
                total_balance
                / total_income
            )
            * Decimal('100.00'),

            2

        )

    else:

        expense_ratio = Decimal('0.00')

        profit_margin = Decimal('0.00')


    # ============================================================
    # VEHICLE / DRIVER FILTER OPTIONS
    # ============================================================

    vehicles = (
        Vehicle.objects.filter(created_by=request.user)
        .order_by(
            'vehicle_number'
        )
    )

    drivers = (
        Driver.objects.filter(user=request.user)
        .order_by(
            'full_name'
        )
    )


    # ============================================================
    # CONTEXT
    # ============================================================

    context = {

        # --------------------------------------------------------
        # FILTERS
        # --------------------------------------------------------

        'vehicles': vehicles,

        'drivers': drivers,

        'vehicle_id': vehicle_id,

        'driver_id': driver_id,

        'from_date': from_date,

        'to_date': to_date,


        # --------------------------------------------------------
        # TRIP COUNT
        # --------------------------------------------------------

        'total_trips': total_trips,


        # --------------------------------------------------------
        # INCOME
        # --------------------------------------------------------

        'total_income': total_income,

        'total_commission': total_commission,


        # --------------------------------------------------------
        # KM / MILEAGE
        # --------------------------------------------------------

        'total_km': total_km,

        'avg_mileage': avg_mileage,


        # --------------------------------------------------------
        # FUEL
        # --------------------------------------------------------

        'total_fuel_cost': total_fuel_cost,

        'total_diesel_qty': total_diesel_qty,

        'total_diesel_cost': total_diesel_cost,

        'total_adblue_qty': total_adblue_qty,

        'total_adblue_cost': total_adblue_cost,

        'fuel_cost_per_km': fuel_cost_per_km,


        # --------------------------------------------------------
        # SECTION 2
        # --------------------------------------------------------

        'total_loading': total_loading,

        'total_unloading': total_unloading,


        # --------------------------------------------------------
        # SALARY / MANUAL EXPENSES
        # --------------------------------------------------------

        'total_driver_salary': total_driver_salary,

        'total_cleaner_salary': total_cleaner_salary,

        'total_workshop_expense': total_workshop_expense,

        'total_toll_gate': total_toll_gate,


        # --------------------------------------------------------
        # RTO / PC
        # --------------------------------------------------------

        'total_rto': total_rto,

        'total_pc': total_pc,


        # --------------------------------------------------------
        # OTHER TOLL
        # --------------------------------------------------------

        'total_other_toll_expense': (
            total_other_toll_expense
        ),


        # --------------------------------------------------------
        # SECTION 4
        # --------------------------------------------------------

        'total_other_expenses': (
            total_other_expenses
        ),


        # --------------------------------------------------------
        # FINAL ACCOUNTING
        # --------------------------------------------------------

        'total_overall_expense': (
            total_overall_expense
        ),

        'total_balance': total_balance,

        'expense_ratio': expense_ratio,

        'profit_margin': profit_margin,


        # --------------------------------------------------------
        # TRIP-WISE REPORT
        # --------------------------------------------------------

        'report_rows': report_rows,

    }


    # ============================================================
    # RENDER
    # ============================================================

    return render(
        request,
        'reports/index.html',
        context
    )