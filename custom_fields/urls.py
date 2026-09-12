from django.urls import path
from . import views

app_name = 'custom_fields'

urlpatterns = [
    path('', views.custom_field_list, name='list'),
    path('<int:pk>/toggle/', views.custom_field_toggle, name='toggle'),
]
