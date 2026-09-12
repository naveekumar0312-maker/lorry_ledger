from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from . import views


app_name = 'accounts'


urlpatterns = [

    # =========================================================
    # AUTHENTICATION
    # =========================================================

    path(
        'register/',
        views.register_view,
        name='register'
    ),

    path(
        'login/',
        views.login_view,
        name='login'
    ),

    path(
        'logout/',
        views.logout_view,
        name='logout'
    ),

    path(
        'profile/',
        views.profile_view,
        name='profile'
    ),

    path(
        'change-password/',
        views.change_password_view,
        name='change_password'
    ),


]