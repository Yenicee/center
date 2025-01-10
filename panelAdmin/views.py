from django.shortcuts import render, get_object_or_404, redirect
from .models import Client, Domain
from .forms import ClientForm
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string  
from django.db import IntegrityError
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib import messages


def dashboard(request):
    clients = Client.objects.all()
    metrics = {
        'total_clients': clients.count(),
        'active_clients': clients.filter(status='active').count(),
        'morose_clients': clients.filter(status='morose').count(),
    }
    return render(request, 'base/dashboard.html', {'metrics': metrics})

def client_list(request):
    clients = Client.objects.all()
    return render(request, 'client/client_list.html', {'clients': clients})

def client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Preparar el cliente pero no guardarlo aún
                    client = form.save(commit=False)
                    
                    schema_name = form.cleaned_data['schema_name']
                    client.schema_name = schema_name
                    
                    if not form.cleaned_data.get('initial_password'):
                        password = get_random_string(length=8)
                    else:
                        password = form.cleaned_data['initial_password']
                        
                    username = form.cleaned_data['admin_email']
                    
                    # Crear usuario
                    user = User.objects.create_user(
                        username=username,
                        email=form.cleaned_data['admin_email'],
                        password=password
                    )
                    
                    client.user = user
                    client.initial_password = password
                    client.save()
                    
                    # Esto es para dominio
                    domain = Domain.objects.create(
                        domain=f"{schema_name}.localhost",
                        tenant=client,
                        is_primary=True
                    )

                    messages.success(request, 'Cliente creado exitosamente')
                    return redirect('client_list')

            except IntegrityError as e:
                if 'user' in locals():
                    user.delete()
                form.add_error(None, f'Error de integridad al crear el cliente: {str(e)}')
                messages.error(request, f'Error de integridad al crear el cliente: {str(e)}')
            
            except ValidationError as e:
                if 'user' in locals():
                    user.delete()
                form.add_error(None, f'Error de validación: {str(e)}')
                messages.error(request, f'Error de validación: {str(e)}')
                
            except Exception as e:
                if 'user' in locals():
                    user.delete()
                form.add_error(None, f'Error al crear el cliente: {str(e)}')
                messages.error(request, f'Error al crear el cliente: {str(e)}')

    else:
        form = ClientForm()

    return render(request, 'client/client_form.html', {'form': form})

def client_detail(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    return render(request, 'client/client_detail.html', {'client': client})