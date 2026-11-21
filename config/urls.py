"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from crm import views

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', views.landing, name='landing'),
    path('home/', views.home, name='home'),
    path('login/admin/', views.portal_login, {'role': 'ADMIN'}, name='admin_login'),
    path('login/staff/', views.portal_login, {'role': 'STAFF'}, name='staff_login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('admin-portal/', views.admin_dashboard, name='admin_dashboard'),
    path('staff-portal/', views.staff_dashboard, name='staff_dashboard'),
    path('admin-portal/leads/upload/', views.upload_leads, name='upload_leads'),
    path('admin-portal/leads/distribute/', views.distribute_leads, name='distribute_leads'),
    path('staff-portal/call/<int:lead_id>/', views.update_call, name='update_call'),
    path('staff-portal/apply/<int:lead_id>/', views.create_application, name='create_application'),
    path('staff-portal/applications/', views.my_applications, name='my_applications'),
    path('admin-portal/applications/', views.applications_list, name='applications_list'),
    path('admin-portal/applications/<int:app_id>/', views.update_application, name='update_application'),
    path('admin-portal/staff/', views.staff_list, name='staff_list'),
    path('admin-portal/staff/add/', views.add_staff, name='add_staff'),
    path('admin-portal/staff/<int:user_id>/toggle/', views.toggle_staff, name='toggle_staff'),
    path('m/', views.mobile_view, name='mobile'),

]

