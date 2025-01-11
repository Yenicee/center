from django.shortcuts import render, get_object_or_404, redirect
from .models import Client, Domain
from .forms import ClientForm
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string  
from django.db import IntegrityError
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db.models import Sum


def dashboard(request):
    clients = Client.objects.all()
    
    active_clients = clients.filter(status='active')
    monthly_income = active_clients.aggregate(
        total=Sum('monthly_payment'))['total'] or 0
    
    total_users = User.objects.count()
 
    pending_payments = clients.filter(
        status='morose'
    ).aggregate(total=Sum('monthly_payment'))['total'] or 0
    
    metrics = {
        'total_clients': clients.count(),
        'active_clients': active_clients.count(),
        'morose_clients': clients.filter(status='morose').count(),
        'projected_monthly_income': monthly_income,
        'total_users': total_users,
        'pending_payments': pending_payments,
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


def client_edit(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            try:
                with transaction.atomic():
                    #campos que se van a cambiar 
                    client.monthly_payment = form.cleaned_data['monthly_payment']
                    client.status = form.cleaned_data['status']
                    client.specialists_limit = form.cleaned_data['specialists_limit']
                    
                    # Si se proporciona una nueva contraseña, la actualizamos
                    new_password = form.cleaned_data.get('initial_password')
                    if new_password:
                        client.user.set_password(new_password)
                        client.user.save()
                        client.initial_password = new_password
                    
                    # Guardamos el cliente
                    client.save()

                    messages.success(request, 'Cliente actualizado exitosamente')
                    return redirect('client_list')

            except ValidationError as e:
                form.add_error(None, f'Error de validación: {str(e)}')
                messages.error(request, f'Error de validación: {str(e)}')
                
            except Exception as e:
                form.add_error(None, f'Error al actualizar el cliente: {str(e)}')
                messages.error(request, f'Error al actualizar el cliente: {str(e)}')
    else:
        # Para el GET, pre-poblamos el formulario con los datos actuales
        initial_data = {
            'schema_name': client.schema_name,
            'name': client.name,
            'admin_name': client.admin_name,
            'admin_email': client.user.email,
            'specialists_limit': client.specialists_limit,
            'monthly_payment': client.monthly_payment,
            'status': client.status,
        }
        form = ClientForm(instance=client, initial=initial_data)
        
        #solo lectura
        form.fields['schema_name'].widget.attrs['readonly'] = True
        form.fields['admin_email'].widget.attrs['readonly'] = True

    return render(request, 'client/client_edit.html', {
        'form': form,
        'client': client
    })

def client_detail(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    return render(request, 'client/client_detail.html', {'client': client})