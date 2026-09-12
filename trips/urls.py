from django.urls import path
from . import views


app_name = 'trips'


urlpatterns = [

    # ============================================================
    # TRIP CRUD
    # ============================================================

    path(
        '',
        views.trip_list,
        name='list'
    ),

    path(
        'new/',
        views.trip_create,
        name='create'
    ),

    path(
        '<int:pk>/',
        views.trip_detail,
        name='detail'
    ),

    path(
        '<int:pk>/edit/',
        views.trip_edit,
        name='edit'
    ),

    path(
        '<int:pk>/delete/',
        views.trip_delete,
        name='delete'
    ),

    path(
        '<int:pk>/archive/',
        views.trip_archive,
        name='archive'
    ),


    # ============================================================
    # FUEL
    # ============================================================

    path(
        'fuel/<int:pk>/edit/',
        views.fuel_edit,
        name='fuel_edit'
    ),

    path(
        'fuel/<int:pk>/delete/',
        views.fuel_delete,
        name='fuel_delete'
    ),


    # ============================================================
    # LOAD / REVENUE
    # Section 2:
    # Income + Commission + Loading + Unloading
    # ============================================================

    path(
        'load/<int:pk>/edit/',
        views.load_revenue_edit,
        name='load_revenue_edit'
    ),

    path(
        'load/<int:pk>/delete/',
        views.load_revenue_delete,
        name='load_revenue_delete'
    ),


    # ============================================================
    # SECTION 4 — OTHER EXPENSES
    # ============================================================

    path(
        'expense-entry/<int:pk>/edit/',
        views.expense_entry_edit,
        name='expense_entry_edit'
    ),

    path(
        'expense-entry/<int:pk>/delete/',
        views.expense_entry_delete,
        name='expense_entry_delete'
    ),


    # ============================================================
    # RTO / PC
    # ============================================================

    path(
        'rto-pc/<int:pk>/edit/',
        views.rto_pc_edit,
        name='rto_pc_edit'
    ),

    path(
        'rto-pc/<int:pk>/delete/',
        views.rto_pc_delete,
        name='rto_pc_delete'
    ),


    # ============================================================
    # OTHER TOLL EXPENSES
    # ============================================================

    path(
        'other-toll/<int:pk>/edit/',
        views.other_toll_edit,
        name='other_toll_edit'
    ),

    path(
        'other-toll/<int:pk>/delete/',
        views.other_toll_delete,
        name='other_toll_delete'
    ),


    # ============================================================
    # EXPORT VIEWS
    # ============================================================

    path(
        'reports/summary/pdf/',
        views.reports_summary_pdf,
        name='reports_summary_pdf'
    ),

    path(
        'reports/summary/word/',
        views.reports_summary_word,
        name='reports_summary_word'
    ),

    path(
        '<int:trip_id>/voucher/pdf/',
        views.trip_voucher_pdf,
        name='trip_voucher_pdf'
    ),

    path(
        '<int:trip_id>/voucher/word/',
        views.trip_voucher_word,
        name='trip_voucher_word'
    ),


    # ============================================================
    # FUEL LOGBOOK
    # ============================================================

    path(
        'fuel-logbook/',
        views.fuel_logbook,
        name='fuel_logbook'
    ),


    # ============================================================
    # VEHICLE OWNER AJAX
    # ============================================================

    path(
        'vehicle/<int:pk>/owner/',
        views.vehicle_owner_api,
        name='vehicle_owner_api'
    ),

]