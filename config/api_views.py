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
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Vehicle.objects.filter(created_by=self.request.user)
        
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class DriverViewSet(viewsets.ModelViewSet):
    serializer_class = DriverSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Driver.objects.filter(user=self.request.user)
        
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ExpenseCategory.objects.filter(user=self.request.user)
        
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TripViewSet(viewsets.ModelViewSet):
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Trip.objects.filter(created_by=self.request.user)
        
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
