from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Sum, Count
from decimal import Decimal

from trips.models import (
    Trip,
    TripFuelEntry,
    TripExpenseEntry,
)

from vehicles.models import Vehicle, VehicleDocument
from drivers.models import Driver


@method_decorator(login_required, name='dispatch')
class DashboardView(View):

    def get(self, request):

        # ========================================================
        # ACTIVE TRIPS
        # ========================================================

        trips = (
            Trip.objects
            .filter(is_archived=False)
            .select_related(
                'vehicle',
                'primary_driver',
                'secondary_driver',
                'km_detail',
            )
            .prefetch_related(
                'load_revenue_entries',
                'fuel_entries',
                'expense_entries',
                'rto_pc_entries',
                'other_toll_expenses',
            )
            .order_by(
                '-entry_date',
                '-id',
            )
        )


        # ========================================================
        # BASIC COUNTS
        # ========================================================

        total_trips = trips.count()

        total_vehicles = (
            Vehicle.objects
            .filter(status='ACTIVE')
            .count()
        )

        total_drivers = (
            Driver.objects
            .filter(status='ACTIVE')
            .count()
        )


        # ========================================================
        # INITIAL TOTALS
        # ========================================================

        total_income = Decimal('0.00')

        total_expenses = Decimal('0.00')

        total_fuel_cost = Decimal('0.00')

        total_diesel_cost = Decimal('0.00')

        total_adblue_cost = Decimal('0.00')

        total_fuel_qty = Decimal('0.000')

        total_diesel_qty = Decimal('0.000')

        total_adblue_qty = Decimal('0.000')

        total_km = Decimal('0.00')

        total_loading = Decimal('0.00')

        total_unloading = Decimal('0.00')

        total_driver_salary = Decimal('0.00')

        total_cleaner_salary = Decimal('0.00')

        total_workshop_expense = Decimal('0.00')

        total_rto_expense = Decimal('0.00')

        total_pc_expense = Decimal('0.00')

        total_toll_gate_expense = Decimal('0.00')

        total_other_toll_expense = Decimal('0.00')

        total_section4_expense = Decimal('0.00')

        total_commission = Decimal('0.00')


        # ========================================================
        # CALCULATE EVERY TRIP
        #
        # FINAL ACCOUNTING FORMULA:
        #
        # Overall Expense =
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
        # + Section 4 Other Expenses
        #
        # Commission is EXCLUDED.
        # ========================================================

        for trip in trips:

            # ----------------------------------------------------
            # INCOME
            # ----------------------------------------------------

            trip_income = (
                trip.total_income
                or Decimal('0.00')
            )

            total_income += trip_income


            # ----------------------------------------------------
            # KM
            # ----------------------------------------------------

            trip_km = (
                trip.total_km
                or Decimal('0.00')
            )

            total_km += trip_km


            # ----------------------------------------------------
            # FUEL
            # ----------------------------------------------------

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

            trip_fuel_qty = (
                diesel_qty
                + adblue_qty
            )

            trip_fuel_cost = (
                diesel_cost
                + adblue_cost
            )


            total_diesel_qty += diesel_qty

            total_adblue_qty += adblue_qty

            total_fuel_qty += trip_fuel_qty

            total_diesel_cost += diesel_cost

            total_adblue_cost += adblue_cost

            total_fuel_cost += trip_fuel_cost


            # ----------------------------------------------------
            # SECTION 2
            # ----------------------------------------------------

            loading = (
                trip.total_loading_charges
                or Decimal('0.00')
            )

            unloading = (
                trip.total_unloading_charges
                or Decimal('0.00')
            )

            commission = (
                trip.total_revenue_commission
                or Decimal('0.00')
            )


            total_loading += loading

            total_unloading += unloading

            total_commission += commission


            # ----------------------------------------------------
            # DRIVER SALARY
            #
            # 13% OF OVERALL INCOME
            # ----------------------------------------------------

            driver_salary = (
                trip_income
                * Decimal('13.00')
                / Decimal('100.00')
            ).quantize(
                Decimal('0.01')
            )


            total_driver_salary += (
                driver_salary
            )


            # ----------------------------------------------------
            # MANUAL ACCOUNTING EXPENSES
            # ----------------------------------------------------

            cleaner_salary = (
                trip.cleaner_salary
                or Decimal('0.00')
            )

            workshop_expense = (
                trip.workshop_expense
                or Decimal('0.00')
            )

            toll_gate_expense = (
                trip.toll_gate_expense
                or Decimal('0.00')
            )


            total_cleaner_salary += (
                cleaner_salary
            )

            total_workshop_expense += (
                workshop_expense
            )

            total_toll_gate_expense += (
                toll_gate_expense
            )


            # ----------------------------------------------------
            # RTO
            # ----------------------------------------------------

            rto_expense = (
                trip.total_rto_expense
                or Decimal('0.00')
            )


            # ----------------------------------------------------
            # PC
            # ----------------------------------------------------

            pc_expense = (
                trip.total_pc_expense
                or Decimal('0.00')
            )


            total_rto_expense += (
                rto_expense
            )

            total_pc_expense += (
                pc_expense
            )


            # ----------------------------------------------------
            # SECTION 4 OTHER EXPENSES
            # ----------------------------------------------------

            section4_expense = (
                trip.total_other_expenses
                or Decimal('0.00')
            )


            total_section4_expense += (
                section4_expense
            )


            # ----------------------------------------------------
            # OTHER TOLL EXPENSES
            # ----------------------------------------------------

            other_toll_expense = (
                trip.total_other_toll_expense
                if hasattr(
                    trip,
                    'total_other_toll_expense'
                )
                else Decimal('0.00')
            )


            total_other_toll_expense += (
                other_toll_expense
            )


            # ----------------------------------------------------
            # FINAL TRIP EXPENSE
            # ----------------------------------------------------

            trip_overall_expense = (

                diesel_cost

                + adblue_cost

                + loading

                + unloading

                + driver_salary

                + cleaner_salary

                + workshop_expense

                + rto_expense

                + pc_expense

                + toll_gate_expense

                + other_toll_expense

                + section4_expense

                + commission
            )


            total_expenses += (
                trip_overall_expense
            )


        # ========================================================
        # FINAL DASHBOARD BALANCE
        # ========================================================

        net_income = (
            total_income
            - total_expenses
        )


        # ========================================================
        # AVERAGE MILEAGE
        #
        # IMPORTANT:
        # Mileage uses DIESEL only.
        # AdBlue is excluded.
        # ========================================================

        if total_diesel_qty > Decimal('0.000'):

            avg_mileage = round(
                total_km
                / total_diesel_qty,
                2
            )

        else:

            avg_mileage = Decimal('0.00')


        # ========================================================
        # FUEL COST PER KM
        # ========================================================

        if total_km > Decimal('0.00'):

            fuel_cost_per_km = round(
                total_fuel_cost
                / total_km,
                2
            )

        else:

            fuel_cost_per_km = Decimal('0.00')


        # ========================================================
        # EXPENSE RATIO
        # ========================================================

        if total_income > Decimal('0.00'):

            expense_ratio = round(
                (
                    total_expenses
                    / total_income
                ) * Decimal('100.00'),
                2
            )

        else:

            expense_ratio = Decimal('0.00')


        # ========================================================
        # PROFIT MARGIN
        # ========================================================

        if total_income > Decimal('0.00'):

            profit_margin = round(
                (
                    net_income
                    / total_income
                ) * Decimal('100.00'),
                2
            )

        else:

            profit_margin = Decimal('0.00')


        # ========================================================
        # RECENT TRIPS
        # ========================================================

        recent_trips = trips[:10]


        # ========================================================
        # SECTION 4 CATEGORY EXPENSE BREAKDOWN
        #
        # IMPORTANT:
        # category_name, NOT name
        # ========================================================

        expenses_by_cat = (
            TripExpenseEntry.objects
            .filter(
                trip__is_archived=False
            )
            .values(
                'category__category_name'
            )
            .annotate(
                total=Sum('amount')
            )
            .order_by(
                '-total'
            )
        )


        # ========================================================
        # VEHICLE-WISE SUMMARY
        # ========================================================

        vehicle_summary = (
            Trip.objects
            .filter(
                is_archived=False
            )
            .values(
                'vehicle__vehicle_number'
            )
            .annotate(
                total_trips=Count('id')
            )
            .order_by(
                '-total_trips'
            )[:5]
        )


        # ========================================================
        # DRIVER-WISE SUMMARY
        # ========================================================

        driver_summary = (
            Trip.objects
            .filter(
                is_archived=False
            )
            .values(
                'primary_driver__full_name'
            )
            .annotate(
                total_trips=Count('id')
            )
            .order_by(
                '-total_trips'
            )[:5]
        )


        # ========================================================
        # RECENT SECTION 4 EXPENSES
        # ========================================================

        recent_expenses = (
            TripExpenseEntry.objects
            .filter(
                trip__is_archived=False
            )
            .select_related(
                'trip',
                'category'
            )
            .order_by(
                '-id'
            )[:10]
        )


        # ========================================================
        # CONTEXT
        # ========================================================

        context = {

            # ----------------------------------------------------
            # COUNTS
            # ----------------------------------------------------

            'total_trips':
                total_trips,

            'total_vehicles':
                total_vehicles,

            'total_drivers':
                total_drivers,


            # ----------------------------------------------------
            # FINAL ACCOUNTING
            # ----------------------------------------------------

            'total_income':
                total_income,

            'total_expenses':
                total_expenses,

            'net_income':
                net_income,


            # ----------------------------------------------------
            # DISTANCE
            # ----------------------------------------------------

            'total_km':
                total_km,


            # ----------------------------------------------------
            # FUEL
            # ----------------------------------------------------

            'total_fuel_cost':
                total_fuel_cost,

            'total_diesel_cost':
                total_diesel_cost,

            'total_adblue_cost':
                total_adblue_cost,

            'total_fuel_qty':
                total_fuel_qty,

            'total_diesel_qty':
                total_diesel_qty,

            'total_adblue_qty':
                total_adblue_qty,

            'avg_mileage':
                avg_mileage,

            'fuel_cost_per_km':
                fuel_cost_per_km,


            # ----------------------------------------------------
            # SECTION 2
            # ----------------------------------------------------

            'total_loading':
                total_loading,

            'total_unloading':
                total_unloading,

            'total_commission':
                total_commission,


            # ----------------------------------------------------
            # ACCOUNTING EXPENSES
            # ----------------------------------------------------

            'total_driver_salary':
                total_driver_salary,

            'total_cleaner_salary':
                total_cleaner_salary,

            'total_workshop_expense':
                total_workshop_expense,

            'total_rto_expense':
                total_rto_expense,

            'total_pc_expense':
                total_pc_expense,

            'total_toll_gate_expense':
                total_toll_gate_expense,

            'total_other_toll_expense':
                total_other_toll_expense,

            'total_section4_expense':
                total_section4_expense,


            # ----------------------------------------------------
            # ANALYTICS
            # ----------------------------------------------------

            'expense_ratio':
                expense_ratio,

            'profit_margin':
                profit_margin,


            # ----------------------------------------------------
            # TABLE DATA
            # ----------------------------------------------------

            'recent_trips':
                recent_trips,

            'expenses_by_cat':
                expenses_by_cat,

            'vehicle_summary':
                vehicle_summary,

            'driver_summary':
                driver_summary,

            'recent_expenses':
                recent_expenses,
        }

        # ========================================================
        # VEHICLE DOCUMENT ALERTS
        # ========================================================
        from datetime import date, timedelta
        
        today = date.today()
        thirty_days = today + timedelta(days=30)
        
        document_alerts = VehicleDocument.objects.filter(
            is_active=True,
            expiry_date__lte=thirty_days
        ).select_related('vehicle').order_by('expiry_date')
        
        expired_count = 0
        expiring_soon_count = 0
        valid_count = VehicleDocument.objects.filter(is_active=True).count()
        
        alert_docs = []
        for doc in document_alerts:
            status = doc.status
            if status == 'EXPIRED':
                expired_count += 1
                alert_docs.append(doc)
            elif status == 'EXPIRING SOON':
                expiring_soon_count += 1
                alert_docs.append(doc)
                
        valid_count = valid_count - expired_count - expiring_soon_count
                
        context['document_alerts'] = alert_docs
        context['expired_count'] = expired_count
        context['expiring_soon_count'] = expiring_soon_count
        context['valid_count'] = valid_count


        # ========================================================
        # RENDER
        # ========================================================

        return render(
            request,
            'dashboard/index.html',
            context
        )