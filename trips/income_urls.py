from django.urls import path
from . import views_income

app_name = 'income'

urlpatterns = [
    path('', views_income.income_list, name='list'),
    path('add/', views_income.income_create, name='add'),
    path('<int:pk>/', views_income.income_detail, name='detail'),
    path('<int:pk>/edit/', views_income.income_edit, name='edit'),
    path('<int:pk>/delete/', views_income.income_delete, name='delete'),
]
