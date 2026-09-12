# pyrefly: ignore [missing-import]
from rest_framework import serializers
from vehicles.models import Vehicle
from drivers.models import Driver
from trips.models import Trip, TripKMDetail, TripFuelEntry, TripIncomeEntry, TripCommission, TripExpenseEntry
from expenses.models import ExpenseCategory

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'

class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = '__all__'

class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = '__all__'

class TripKMDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripKMDetail
        fields = '__all__'

class TripFuelEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = TripFuelEntry
        fields = '__all__'

class TripIncomeEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = TripIncomeEntry
        fields = '__all__'

class TripCommissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripCommission
        fields = '__all__'

class TripExpenseEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = TripExpenseEntry
        fields = '__all__'

class TripSerializer(serializers.ModelSerializer):
    vehicle_number = serializers.ReadOnlyField(source='vehicle.vehicle_number')
    driver_name = serializers.ReadOnlyField(source='primary_driver.full_name')
    total_income = serializers.ReadOnlyField()
    total_expenses = serializers.ReadOnlyField()
    net_income = serializers.ReadOnlyField()
    total_km = serializers.ReadOnlyField()
    mileage = serializers.ReadOnlyField()

    class Meta:
        model = Trip
        fields = '__all__'
