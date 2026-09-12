from django.test import TestCase, Client
from django.contrib.auth.models import User
from decimal import Decimal
from vehicles.models import Vehicle
from drivers.models import Driver
from expenses.models import ExpenseCategory
from trips.models import Trip, TripKMDetail, TripFuelEntry, TripLoadRevenueEntry, TripIncomeEntry, TripCommission, TripExpenseEntry
import datetime

class TripCalculationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.vehicle = Vehicle.objects.create(vehicle_number='TN 01 AB 1234', created_by=self.user)
        self.driver = Driver.objects.create(full_name='Test Driver', mobile_number='9998887776')
        self.cat = ExpenseCategory.objects.create(category_name='Toll')

    def test_case_1_commission_0(self):
        # CASE 1: Commission = 0
        trip = Trip.objects.create(
            trip_ref_no='TRIP-TEST-001', entry_date=datetime.date.today(),
            period_from=datetime.date.today(), period_to=datetime.date.today(),
            vehicle=self.vehicle, primary_driver=self.driver, created_by=self.user
        )
        TripLoadRevenueEntry.objects.create(
            trip=trip, date=datetime.date.today(), income_amount=Decimal('50000.00'), commission_amount=Decimal('0.00')
        )
        # Income = 50000, Salary = 6500 (13%). Overall = 6500. Net = 43500.
        self.assertEqual(trip.overall_expense, Decimal('6500.00'))
        self.assertEqual(trip.net_income, Decimal('43500.00'))

    def test_case_2_commission_1000(self):
        # CASE 2: Commission = 1000
        trip = Trip.objects.create(
            trip_ref_no='TRIP-TEST-002', entry_date=datetime.date.today(),
            period_from=datetime.date.today(), period_to=datetime.date.today(),
            vehicle=self.vehicle, primary_driver=self.driver, created_by=self.user
        )
        TripLoadRevenueEntry.objects.create(
            trip=trip, date=datetime.date.today(), income_amount=Decimal('50000.00'), commission_amount=Decimal('1000.00')
        )
        # Income = 50000, Salary = 6500, Comm = 1000. Overall = 7500. Net = 42500.
        self.assertEqual(trip.overall_expense, Decimal('7500.00'))
        self.assertEqual(trip.net_income, Decimal('42500.00'))

    def test_case_3_commission_and_other_toll(self):
        # CASE 3: Commission + Other Toll
        trip = Trip.objects.create(
            trip_ref_no='TRIP-TEST-003', entry_date=datetime.date.today(),
            period_from=datetime.date.today(), period_to=datetime.date.today(),
            vehicle=self.vehicle, primary_driver=self.driver, created_by=self.user
        )
        TripLoadRevenueEntry.objects.create(
            trip=trip, date=datetime.date.today(), income_amount=Decimal('50000.00'), commission_amount=Decimal('1000.00')
        )
        from trips.models import TripOtherTollExpense
        TripOtherTollExpense.objects.create(trip=trip, toll_name='Border Toll', amount=Decimal('500.00'))
        
        # Salary = 6500. Comm = 1000. Toll = 500. Overall = 8000. Net = 42000.
        self.assertEqual(trip.overall_expense, Decimal('8000.00'))
        self.assertEqual(trip.net_income, Decimal('42000.00'))

    def test_case_4_commission_and_full_expenses(self):
        # CASE 4: Commission + Fuel + Other Expense + Driver Salary
        trip = Trip.objects.create(
            trip_ref_no='TRIP-TEST-004', entry_date=datetime.date.today(),
            period_from=datetime.date.today(), period_to=datetime.date.today(),
            vehicle=self.vehicle, primary_driver=self.driver, created_by=self.user
        )
        # Income = 50000, Comm = 1000
        TripLoadRevenueEntry.objects.create(
            trip=trip, date=datetime.date.today(), income_amount=Decimal('50000.00'), commission_amount=Decimal('1000.00')
        )
        # Fuel = 9000
        TripFuelEntry.objects.create(
            trip=trip, quantity=Decimal('100.000'), rate=Decimal('90.00'), fuel_date=datetime.date.today()
        )
        # Expense = 2000
        TripExpenseEntry.objects.create(
            trip=trip, category=self.cat, expense_name='Toll', expense_date=datetime.date.today(), amount=Decimal('2000.00')
        )
        
        # Salary = 6500
        # Overall = Fuel (9000) + Expense (2000) + Comm (1000) + Salary (6500) = 18500
        self.assertEqual(trip.overall_expense, Decimal('18500.00'))
        self.assertEqual(trip.net_income, Decimal('31500.00'))

    def test_case_5_commission_no_double_counting(self):
        # CASE 5: Verify commission is NOT double-counted when both models exist
        trip = Trip.objects.create(
            trip_ref_no='TRIP-TEST-005', entry_date=datetime.date.today(),
            period_from=datetime.date.today(), period_to=datetime.date.today(),
            vehicle=self.vehicle, primary_driver=self.driver, created_by=self.user
        )
        # 1. New model commission: 1000
        TripLoadRevenueEntry.objects.create(
            trip=trip, date=datetime.date.today(), income_amount=Decimal('50000.00'), commission_amount=Decimal('1000.00')
        )
        # 2. Legacy model freight and commission: 1000
        TripIncomeEntry.objects.create(
            trip=trip, freight_amount=Decimal('50000.00'), advance_amount=Decimal('10000.00')
        )
        TripCommission.objects.create(trip=trip, commission_type='PERCENTAGE', rate_or_percentage=Decimal('2.00'))

        # Salary = 6500
        # Overall should only count 1000 ONCE. So Overall = Salary (6500) + Comm (1000) = 7500.
        self.assertEqual(trip.overall_expense, Decimal('7500.00'))
        self.assertEqual(trip.net_income, Decimal('42500.00'))
