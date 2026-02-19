from django.contrib import admin
from django.urls import path
from med import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Registration
    path('',views.registration1,name='registration1'),
    path('registration2',views.registration2,name='registration2'),
    path('registration3',views.registration3,name='registration3'),
    path('registrationsuccess',views.registrationsuccess,name='registrationsuccess'),
    path("patients_list", views.patients_list, name="patients_list"),

    # Oct-26 Page
    path('confirmlogin',views.confirmlogin,name='confirmlogin'),
    path('confirmation',views.confirmation,name='confirmation'),
    path('confirmationsuccess',views.confirmationsuccess,name='confirmationsuccess'),
    path('api/search_patients/', views.search_patients, name='search_patients'),
    path('api/verify_pin/', views.verify_pin, name='verify_pin'),
    path('api/verify_securitypin/', views.verify_securitypin, name='verify_securitypin'),
    path('api/mark_followup/', views.mark_followup, name='mark_followup'),
    path('api/mark_medicine/', views.mark_medicine, name='mark_medicine'),

    # Spot Registration
    path('spotregistration1',views.spotregistration1,name='spotregistration1'),
    path('spotregistration2',views.spotregistration2,name='spotregistration2'),
    path('spotregistrationsuccess',views.spotregistrationsuccess,name='spotregistrationsuccess'),

    # Admin
    path('admin1/dashboard',views.dashboard,name='dashboard'),
    path('admin1/adduser',views.ashaworkers,name='ashaworkers'),
    path('admin1/department',views.departments,name='department'),
    path('admin1/managepatient',views.managepatient,name='managepatient'),
    path('admin1/editpatient',views.editpatient,name='editpatient'),
    path('admin1/deletepatient',views.deletepatient,name='deletepatient'),
    path('admin1/editdepartment',views.editdepartment,name='editdepartment'),
    path('admin1/patient_report',views.patient_report,name='patient_report'),
    path('admin1/spotregister_report',views.spotregister_report,name='spotregister_report'),
    path('admin1/token_report',views.token_report,name='token_report'),
    path('admin1/consulted_report',views.consulted_report,name='consulted_report'),
    path('admin1/medicine_report',views.medicine_report,name='medicine_report'),
    path("admin1/adduser/upload/", views.upload_ashaworkers, name="upload_ashaworkers"),
    path('admin1/login',views.login,name='login'),
    path('admin1/home',views.home,name='home'),
    path('logout', views.logout),
    path('admin1/desksuccess',views.desksuccess,name='desksuccess'),
    path('admin1/all_volunteers', views.all_volunteers, name='all_volunteers'),
    path('admin1/consolidated_report', views.consolidated_report, name='consolidated_report'),

]+static( settings.STATIC_URL,document_root=settings.STATIC_ROOT)