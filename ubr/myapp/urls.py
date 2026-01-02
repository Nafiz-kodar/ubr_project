from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    # Use a simple function-based logout that allows GET (resolves 405 on GET /logout/)
    path('logout/', views.custom_logout, name='logout'),

    # Dashboard redirects based on user type
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    path('owner/dashboard/', views.owner_dashboard, name='owner_dashboard'),
    path('owner/request-inspection/', views.request_inspection, name='request_inspection'),
    path('owner/complaint/', views.owner_complaint, name='owner_complaint'),
    path('owner/inbox/', views.inbox, name='inbox'),
    path('owner/messages/send/', views.send_message, name='send_message'),
    path('owner/messages/<int:pk>/', views.view_message, name='view_message'),
    path('owner/payment/', views.owner_payments, name='owner_payments'),
    path('owner/payment/<int:pk>/', views.payment, name='payment'),
    # Admin flows
    path('admin/dashboard/manage-inspectors/', views.admin_approve_inspectors, name='admin_approve_inspectors'),
    path('admin/complaints/', views.admin_manage_complaints, name='admin_manage_complaints'),
    path('admin/set-fee/<int:pk>/', views.admin_set_fee, name='admin_set_fee'),
    path('admin/users/', views.admin_view_users, name='admin_view_users'),
    path('admin/assign-inspector/<int:pk>/', views.admin_assign_inspector, name='admin_assign_inspector'),
    path('admin/assign-inspector/', views.admin_assign_inspector, name='admin_assign_inspector_list'),
    # Inspector flows
    path('inspector/inspect/<int:pk>/', views.inspector_inspection_view, name='inspector_inspection'),
    path('inspector/dashboard/', views.inspector_dashboard, name='inspector_dashboard'),
    path('inspector/profile/edit/', views.edit_profile, name='edit_profile'),
    path('report/<int:pk>/', views.view_report, name='view_report'),
    path('report/<int:pk>/download/', views.download_report, name='download_report'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
]
