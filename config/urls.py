from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
# pyrefly: ignore [missing-import]
from accounts.views import login_view
urlpatterns = [
    path('admin/', include('custom_admin.urls', namespace='custom_admin')),
    path('', login_view, name='index'),
    path('dashboard/', include('dashboard.urls')),
    path('accounts/', include('accounts.urls')),
    path('vehicles/', include('vehicles.urls')),
    path('drivers/', include('drivers.urls')),
    path('trips/', include('trips.urls')),
    path('ledger/', include('trips.ledger_urls')),
    path('fuel/', include('trips.fuel_urls')),
    path('expenses/', include('expenses.urls')),
    path('income/', include('trips.income_urls', namespace='income')),
    path('custom-fields/', include('custom_fields.urls')),
    path('reports/', include('reports.urls')),
    
    # REST API v1
    path('api/v1/', include('config.api_urls')),
    
    # Silence Chrome DevTools 404 warning
    path('.well-known/appspecific/com.chrome.devtools.json', lambda request: JsonResponse({})),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
