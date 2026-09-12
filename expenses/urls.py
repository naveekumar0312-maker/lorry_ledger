from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    path('categories/', views.category_list, name='category_list'),
    path('categories/<int:pk>/toggle/', views.category_toggle, name='category_toggle'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
]
