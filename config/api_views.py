# pyrefly: ignore [missing-import]
from rest_framework import viewsets, permissions
from vehicles.models import Vehicle
from drivers.models import Driver
from trips.models import Trip
from expenses.models import ExpenseCategory
from .api_serializers import (
    VehicleSerializer, DriverSerializer, TripSerializer, ExpenseCategorySerializer
)

class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]

class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    permission_classes = [permissions.IsAuthenticated]

class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated]
