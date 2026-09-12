from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone
import datetime

from accounts.models import UserProfile
from vehicles.models import Vehicle
from drivers.models import Driver
from expenses.models import ExpenseCategory
from custom_fields.models import CustomFieldDefinition, CustomFieldValue
from trips.models import (
    Trip, TripKMDetail, TripFuelEntry, TripIncomeEntry, 
    TripCommission, TripLoadingEntry, TripUnloadingEntry, TripExpenseEntry
)

class Command(BaseCommand):
    help = 'Seeds initial sample data for vehicles, drivers, expense categories, custom fields and trips'

    def handle(self, *args, **options):
        self.stdout.write("Seeding sample vehicle ledger data...")

        # 1. Admin User
        admin_user, created = User.objects.get_or_create(username='admin', defaults={
            'email': 'admin@ledger.com',
            'first_name': 'Fleet',
            'last_name': 'Admin',
            'is_staff': True,
            'is_superuser': True
        })
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            UserProfile.objects.get_or_create(user=admin_user, role='ADMIN', phone_number='9876543210')
            self.stdout.write("Created default admin user (username: admin, password: admin123)")

        # 2. Expense Categories
        categories = ['Diesel', 'Food / Bata', 'Toll Tax', 'RTO / Checkpost', 'Police / Permit', 'Repair / Spare Parts', 'Maintenance', 'Parking', 'Demurrage', 'Misc Expense']
        cat_objs = {}
        for cat_name in categories:
            cat, _ = ExpenseCategory.objects.get_or_create(category_name=cat_name)
            cat_objs[cat_name] = cat
        self.stdout.write(f"Seeded {len(categories)} expense categories.")

        # 3. Custom Fields
        cf1, _ = CustomFieldDefinition.objects.get_or_create(field_name='Weighbridge Slip No', field_type='TEXT')
        cf2, _ = CustomFieldDefinition.objects.get_or_create(field_name='E-Way Bill Number', field_type='TEXT')

        # 4. Vehicles
        v1, _ = Vehicle.objects.get_or_create(
            vehicle_number='TN 66 AY 1092',
            defaults={'vehicle_type': 'Multi-Axle Lorry', 'model': 'Ashok Leyland 3118', 'capacity_tons': Decimal('25.00'), 'owner_name': 'Fleet Corp', 'status': 'ACTIVE', 'created_by': admin_user}
        )
        v2, _ = Vehicle.objects.get_or_create(
            vehicle_number='KA 01 MJ 4588',
            defaults={'vehicle_type': 'Container Trailer', 'model': 'Tata Signa 4825', 'capacity_tons': Decimal('32.00'), 'owner_name': 'Fleet Corp', 'status': 'ACTIVE', 'created_by': admin_user}
        )
        v3, _ = Vehicle.objects.get_or_create(
            vehicle_number='MH 12 QW 9901',
            defaults={'vehicle_type': '10-Wheeler Truck', 'model': 'Eicher Pro 6028', 'capacity_tons': Decimal('18.50'), 'owner_name': 'Contractor Owner', 'status': 'ACTIVE', 'created_by': admin_user}
        )

        # 5. Drivers
        d1, _ = Driver.objects.get_or_create(
            mobile_number='9842101010',
            defaults={'full_name': 'R. Murugan', 'license_number': 'TN66201800049', 'status': 'ACTIVE'}
        )
        d2, _ = Driver.objects.get_or_create(
            mobile_number='9789123456',
            defaults={'full_name': 'K. Selvam', 'license_number': 'KA01201900088', 'status': 'ACTIVE'}
        )
        d3, _ = Driver.objects.get_or_create(
            mobile_number='9123456789',
            defaults={'full_name': 'S. Kumar', 'license_number': 'MH12202000123', 'status': 'ACTIVE'}
        )

        # 6. Sample Trips
        today = datetime.date.today()

        if not Trip.objects.exists():
            # Trip 1
            trip1 = Trip.objects.create(
                trip_ref_no='TRIP-202609-001',
                entry_date=today - datetime.timedelta(days=5),
                period_from=today - datetime.timedelta(days=7),
                period_to=today - datetime.timedelta(days=5),
                vehicle=v1,
                primary_driver=d1,
                secondary_driver=d2,
                notes='Full load textile machinery cargo',
                created_by=admin_user
            )
            TripKMDetail.objects.create(trip=trip1, start_km=Decimal('120500.00'), end_km=Decimal('121050.00'), total_km=Decimal('550.00'))
            TripFuelEntry.objects.create(trip=trip1, fuel_type='Diesel', quantity=Decimal('110.000'), rate=Decimal('92.50'), station_name='HPCL Villupuram', fuel_date=today - datetime.timedelta(days=6))
            TripIncomeEntry.objects.create(trip=trip1, freight_amount=Decimal('48000.00'), advance_amount=Decimal('15000.00'), other_income=Decimal('1000.00'))
            TripCommission.objects.create(trip=trip1, commission_type='FIXED', rate_or_percentage=Decimal('1200.00'), amount=Decimal('1200.00'))
            TripLoadingEntry.objects.create(trip=trip1, loading_date=today - datetime.timedelta(days=7), location='Chennai Port Yard', amount=Decimal('800.00'))
            TripUnloadingEntry.objects.create(trip=trip1, unloading_date=today - datetime.timedelta(days=5), location='Coimbatore Warehouse', amount=Decimal('1000.00'))
            TripExpenseEntry.objects.create(trip=trip1, category=cat_objs['Toll Tax'], expense_name='Fastag Toll Highway', expense_date=today - datetime.timedelta(days=6), amount=Decimal('1450.00'), payment_method='FASTAG')
            TripExpenseEntry.objects.create(trip=trip1, category=cat_objs['Food / Bata'], expense_name='Driver Bata Allowance', expense_date=today - datetime.timedelta(days=6), amount=Decimal('2000.00'), payment_method='CASH')
            CustomFieldValue.objects.create(trip=trip1, field_def=cf1, field_value='WB-99482')

            # Trip 2
            trip2 = Trip.objects.create(
                trip_ref_no='TRIP-202609-002',
                entry_date=today - datetime.timedelta(days=2),
                period_from=today - datetime.timedelta(days=3),
                period_to=today - datetime.timedelta(days=1),
                vehicle=v2,
                primary_driver=d2,
                notes='Steel pipes transport',
                created_by=admin_user
            )
            TripKMDetail.objects.create(trip=trip2, start_km=Decimal('85200.00'), end_km=Decimal('86180.00'), total_km=Decimal('980.00'))
            TripFuelEntry.objects.create(trip=trip2, fuel_type='Diesel', quantity=Decimal('195.000'), rate=Decimal('91.80'), station_name='IOCL Belagavi', fuel_date=today - datetime.timedelta(days=2))
            TripIncomeEntry.objects.create(trip=trip2, freight_amount=Decimal('82000.00'), advance_amount=Decimal('30000.00'))
            TripCommission.objects.create(trip=trip2, commission_type='PERCENTAGE', rate_or_percentage=Decimal('2.50'), amount=Decimal('2050.00'))
            TripExpenseEntry.objects.create(trip=trip2, category=cat_objs['Toll Tax'], expense_name='NH Toll Taxes', expense_date=today - datetime.timedelta(days=2), amount=Decimal('2850.00'), payment_method='FASTAG')
            TripExpenseEntry.objects.create(trip=trip2, category=cat_objs['Food / Bata'], expense_name='Driver Food Bata', expense_date=today - datetime.timedelta(days=2), amount=Decimal('3000.00'), payment_method='CASH')

            self.stdout.write("Created 2 sample trip ledger entries successfully.")

        self.stdout.write(self.style.SUCCESS("Database seeding completed cleanly!"))
