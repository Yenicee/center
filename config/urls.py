from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('panel/', include('panelAdmin.urls')),
    path('pacientes/', include('pacientes.urls')),
    path('accounts/', include('django.contrib.auth.urls')),   
]

