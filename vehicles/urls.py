from django.urls import path
from . import views

app_name = 'vehicles'

urlpatterns = [
    path('', views.vehicle_list, name='list'),
    path('create/', views.vehicle_create, name='create'),
    path('<int:pk>/', views.vehicle_detail, name='detail'),
    path('<int:pk>/edit/', views.vehicle_edit, name='edit'),
    path('<int:pk>/delete/', views.vehicle_delete, name='delete'),
    
    # Vehicle Documents
    path('documents/', views.document_list, name='document_list'),
    path('documents/add/', views.document_create, name='document_create'),
    path('documents/<int:pk>/', views.document_view, name='document_view'),
    path('documents/<int:pk>/edit/', views.document_edit, name='document_edit'),
    path('documents/<int:pk>/delete/', views.document_delete, name='document_delete'),
    
    # Reminders
    path('reminders/<int:pk>/mark/', views.mark_reminder_notified, name='mark_reminder_notified'),
]
