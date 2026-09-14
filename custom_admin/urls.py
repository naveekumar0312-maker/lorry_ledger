from django.urls import path
from . import views

app_name = 'custom_admin'

urlpatterns = [
    path('', views.admin_login_view, name='login'),
    path('logout/', views.admin_logout_view, name='logout'),
    path('dashboard/', views.admin_dashboard_view, name='dashboard'),
    path('users/', views.admin_user_list_view, name='user_list'),
    path('users/create/', views.admin_user_create_view, name='user_create'),
    path('users/<int:id>/', views.admin_user_detail_view, name='user_detail'),
    path('users/<int:id>/edit/', views.admin_user_edit_view, name='user_edit'),
    path('users/<int:id>/delete/', views.admin_user_delete_view, name='user_delete'),
]
