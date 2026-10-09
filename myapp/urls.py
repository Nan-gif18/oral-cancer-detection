"""oralcancer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
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
from myapp import views

urlpatterns = [
    path('',views.home,name="home"),
    path('adminhome/', views.adminhome, name="adminhome"),
    path('logout_user/', views.logout_user, name='logout_user'),
    path('login/', views.login, name='login'),
    path('user_register/', views.user_register, name='user_register'),
    path('admin_manage_hospital/', views.admin_manage_hospital, name='admin_manage_hospital'),
    path('admin_delete_hospital/<int:id>/', views.admin_delete_hospital, name='admin_delete_hospital'),
    path('admin_edit_hospital/<int:id>/', views.admin_edit_hospital, name='admin_edit_hospital'),
    path('user_home/', views.user_home, name="user_home"),
    path('hospital_home/', views.hospital_home, name="hospital_home"),
    path('admin_view_users/', views.admin_view_users, name='admin_view_users'),
    path('user_view_profile/', views.user_view_profile, name='user_view_profile'),
    path('user_update_profile/<int:id>/', views.user_update_profile, name='user_update_profile'),
    path('user_send_complaint/', views.user_send_complaint, name='user_send_complaint'),
    path('admin_view_complaints/', views.admin_view_complaints, name='admin_view_complaints'),
    path('hospital_view_profile/', views.hospital_view_profile, name='hospital_view_profile'),
    path('hospital_update_profile/<int:id>/', views.hospital_update_profile, name='hospital_update_profile'),
    path('hospital_manage_appointment/', views.hospital_manage_appointment, name='hospital_manage_appointment'),
    path('admin_manage_educational_material/', views.admin_manage_educational_material,name='admin_manage_educational_material'),
    path('admin_delete_educational_material/<int:id>/',views.admin_delete_educational_material,name='admin_delete_educational_material'),
    path('public_home/', views.public_home, name='public_home'),
    path('hospital_manage_camps/', views.hospital_manage_camps, name='hospital_manage_camps'),
    path('hospital_update_camp/<int:id>/', views.hospital_update_camp, name='hospital_update_camp'),
    path('hospital_delete_camp/<int:id>/', views.hospital_delete_camp, name='hospital_delete_camp'),
    path('admin_view_camps/', views.admin_view_camps, name='admin_view_camps'),
    path('admin_edit_educational_material/<int:id>/', views.admin_edit_educational_material, name='admin_edit_educational_material'),
    path('hospital_update_appointment/<int:id>/', views.hospital_update_appointment, name='hospital_update_appointment'),
    path('hospital_delete_appointment/<int:id>/', views.hospital_delete_appointment, name='hospital_delete_appointment'),
    path('public_view_screening_camps/',views.public_view_screening_camps,name='public_view_screening_camps'),

    path('user_view_nearby_hospitals/',views.user_view_nearby_hospitals,name='user_view_nearby_hospitals'),
    path('user_view_hospital_appointments/<int:id>/',views.user_view_hospital_appointments,name='user_view_hospital_appointments'),
    path('user_book_appointment/<int:appointment_id>/',views.user_book_appointment,name='user_book_appointment'),
    path('user_view_appointment_status/',views.user_view_appointment_status,name='user_view_appointment_status'),
    path('hospital_view_appointment_requests/',views.hospital_view_appointment_requests,name='hospital_view_appointment_requests'),
    path('hospital_accept_appointment/<int:id>/',views.hospital_accept_appointment,name='hospital_accept_appointment'),
    path('hospital_reject_appointment/<int:id>/',views.hospital_reject_appointment,name='hospital_reject_appointment'),
    path('user_view_nearby_screening_camps/',views.user_view_nearby_screening_camps,name='user_view_nearby_screening_camps'),


    path('user_chat/<int:id>/', views.user_chat_with_hospital, name='user_chat_with_hospital'),
    path('user_view_chat/', views.user_view_chat, name='user_view_chat'),
    path('user_send_chat/', views.user_send_chat, name='user_send_chat'),


    path('hospital_chat/<int:id>/', views.hospital_chat_with_user, name='hospital_chat_with_user'),
    path('hospital_view_chat/', views.hospital_view_chat, name='hospital_view_chat'),
    path('hospital_send_chat/', views.hospital_send_chat, name='hospital_send_chat'),
    # path('user_symptom_checker/', views.user_symptom_checker, name='user_symptom_checker'),
    path('detect/', views.detect_oral_cancer, name='detect_oral_cancer'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),

]
