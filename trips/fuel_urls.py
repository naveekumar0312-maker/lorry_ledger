from django.urls import path
from . import views

app_name = 'fuel'

urlpatterns = [
    path('', views.fuel_logbook, name='index'),
]
