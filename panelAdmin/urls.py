from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('clients/', views.client_list, name='client_list'),
    path('clients/add/', views.client_create, name='client_form.html'),
    path('clients/<int:client_id>/', views.client_detail, name='client_detail'),
    path('clients/<int:client_id>/edit/', views.client_edit, name='client_edit'),
]
   
