
from django.contrib import admin
from django.urls import path, include
from myapp import views as myapp_views

urlpatterns = [
    # Map the admin dashboard URL explicitly to the app view so it isn't
    # swallowed by Django's admin site URLconf which is mounted at 'admin/'.
    path('admin/dashboard/', myapp_views.admin_dashboard, name='admin_dashboard_root'),
    # Expose assign-inspector endpoints at project level so they take precedence
    # over Django's admin URLconf which is mounted at 'admin/'.
    path('admin/assign-inspector/<int:pk>/', myapp_views.admin_assign_inspector, name='admin_assign_inspector_root'),
    path('admin/assign-inspector/', myapp_views.admin_assign_inspector, name='admin_assign_inspector_list_root'),
    path('', include('myapp.urls')),
    path('admin/', admin.site.urls),
]
