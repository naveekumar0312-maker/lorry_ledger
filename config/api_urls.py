from django.urls import path, include
# pyrefly: ignore [missing-import]
from rest_framework.routers import DefaultRouter
# pyrefly: ignore [missing-import]
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .api_views import VehicleViewSet, DriverViewSet, ExpenseCategoryViewSet, TripViewSet

router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet)
router.register(r'drivers', DriverViewSet)
router.register(r'expense-categories', ExpenseCategoryViewSet)
router.register(r'trips', TripViewSet)

urlpatterns = [
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]
