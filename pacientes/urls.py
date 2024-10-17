from django.urls import path
from . import views
from .forms import CustomAuthenticationForm
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.patient_list, name='patient_list'),
    path('patients/', views.patient_list, name='patient_list'),
    path('patient/<int:patient_id>/schedule/', views.patient_schedule, name='patient_schedule'),
    path('activity/<int:activity_id>/add-result/', views.add_session_result, name='add_session_result'),
    #path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', views.SignUpView.as_view(), name='register'),
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='registration/login.html', 
        authentication_form=CustomAuthenticationForm), 
        name='login'),
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset.html'), name='password_reset'),
    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done2.html'), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm2.html'), name='password_reset_confirm'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete2.html'), name='password_reset_complete'),
    path('pacientes/nuevo/', views.create_patient, name='new_patient'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('api/activities/', views.get_activities, name='get_activities'),
]


