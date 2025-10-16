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
from django_tenants.utils import schema_context 
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def dashboard(request):
    clients = Client.objects.all()
    
    active_clients = clients.filter(status='active')
    morose_clients = clients.filter(status='morose')
    suspended_clients = clients.filter(status='suspended')
    
    monthly_income = active_clients.aggregate(total=Sum('monthly_payment'))['total'] or 0
    total_users = User.objects.count()
    pending_payments = morose_clients.aggregate(total=Sum('monthly_payment'))['total'] or 0
    
    metrics = {
        'total_clients': clients.count(),
        'active_clients': active_clients.count(),
        'morose_clients': morose_clients.count(),
        'suspended_clients': suspended_clients.count(),
        'projected_monthly_income': monthly_income,
        'total_users': total_users,
        'pending_payments': pending_payments,
    }
    
    # Datos para el gráfico de Top 5 clientes (tu compañero los usará en CSS)
    top_clients = active_clients.order_by('-monthly_payment')[:5]
    top_clients_data = [
        {
            'name': client.name[:20] + '...' if len(client.name) > 20 else client.name,
            'payment': float(client.monthly_payment)
        } 
        for client in top_clients
    ]
    
    context = {
        'metrics': metrics,
        'top_clients': top_clients_data,
    }
    
    return render(request, 'base/dashboard.html', context)


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
                        password = get_random_string(length=12)
                    else:
                        password = form.cleaned_data['initial_password']
                        
                    username = form.cleaned_data['admin_email']
                    
                    # Crear usuario EN EL ESQUEMA PÚBLICO
                    user = User.objects.create_user(
                        username=username,
                        email=form.cleaned_data['admin_email'],
                        password=password
                    )
                    
                    client.user = user
                    client.initial_password = password
                    client.save()  # Esto crea el tenant y ejecuta migraciones
                    
                    # Crear dominio
                    domain = Domain.objects.create(
                        domain=f"{schema_name}.localhost",
                        tenant=client,
                        is_primary=True
                    )

                    # Crear usuario EN EL TENANT después de las migraciones
                    try:
                        with schema_context(schema_name):
                            if not User.objects.filter(email=form.cleaned_data['admin_email']).exists():
                                tenant_user = User.objects.create_user(
                                    username=form.cleaned_data['admin_name'].lower().replace(' ', '.'),
                                    email=form.cleaned_data['admin_email'],
                                    password=password,
                                    first_name=form.cleaned_data['admin_name'].split(' ')[0] if form.cleaned_data['admin_name'] else '',
                                    last_name=' '.join(form.cleaned_data['admin_name'].split(' ')[1:]) if form.cleaned_data['admin_name'] and len(form.cleaned_data['admin_name'].split(' ')) > 1 else '',
                                    is_staff=True,
                                    is_active=True
                                )
                                print(f"✅ Usuario creado en tenant {schema_name}: {tenant_user.email}")
                    except Exception as tenant_error:
                        print(f"Error creando usuario en tenant: {tenant_error}")
                    
                    # ========== ENVIA EMAIL DE BIENVENIDA ==========
                    try:     
                        #URL del dominio
                        # Construir URL del dominio con ruta al login
                        domain_url = f"http://{domain.domain}:8000/pacientes/login/"
                        
                        # Contexto para el template
                        context = {
                            'client': client,
                            'username': client.admin_name,
                            'password': password,
                            'domain_url': domain_url,
                        }
                        
                        # Renderizar template HTML
                        html_message = render_to_string('email/email_client.html', context)
                        
                        # Versión texto plano
                        text_message = f'''
Hola {client.admin_name},

Tu cuenta ha sido creada exitosamente en nuestro sistema.

Datos de acceso:
- Centro: {client.name}
-Usuario: {client.admin_name}
- Contraseña: {password}
- Dominio: {domain_url}

Por favor, guarda estas credenciales en un lugar seguro.

¡Bienvenido!
El equipo de TuCentro
                        '''
                        
                        # Crear y enviar email
                        email = EmailMultiAlternatives(
                            subject=f'Bienvenido a TuCentro - {client.name}',
                            body=text_message,
                            from_email=None,  # Usa DEFAULT_FROM_EMAIL del settings
                            to=[client.admin_email]
                        )
                        email.attach_alternative(html_message, "text/html")
                        email.send()
                        
                        print(f"✅ Email de bienvenida enviado a {client.admin_email}")
                        messages.success(request, f'Cliente creado exitosamente. Email enviado a {client.admin_email}. Contraseña: {password}')
                        
                    except Exception as email_error:
                        print(f"⚠️ Error enviando email: {email_error}")
                        messages.warning(request, f'Cliente creado exitosamente pero hubo un error al enviar el email. Contraseña: {password}')
                    # ================================================

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
    """Muestra los detalles de un cliente"""
    client = get_object_or_404(Client, id=client_id)
    return render(request, 'client/client_detail.html', {'client': client})


def client_delete(request, client_id):
    """Elimina un cliente y toda su información asociada"""
    from django.db import connection
    
    client = get_object_or_404(Client, id=client_id)
    
    if request.method == 'POST':
        client_name = client.name
        schema_name = client.schema_name
        user_id = client.user.id if client.user else None
        
        try:
            # 1. Eliminar dominios
            with connection.cursor() as cursor:
                cursor.execute('DELETE FROM public."panelAdmin_domain" WHERE tenant_id = %s', [client.id])
            print(f"✅ Dominios eliminados")
            
            # 2. Eliminar schema
            with connection.cursor() as cursor:
                cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
            print(f"✅ Schema eliminado: {schema_name}")
            
            # 3. Eliminar cliente
            with connection.cursor() as cursor:
                cursor.execute('DELETE FROM public."panelAdmin_client" WHERE id = %s', [client.id])
            print(f"✅ Cliente eliminado: {client_name}")
            
            # 4. Eliminar usuario
            if user_id:
                with connection.cursor() as cursor:
                    cursor.execute('DELETE FROM auth_user WHERE id = %s', [user_id])
                print(f"✅ Usuario eliminado")
            
            messages.success(request, f'Cliente "{client_name}" eliminado exitosamente.')
                
        except Exception as e:
            messages.error(request, f'Error al eliminar el cliente: {str(e)}')
            print(f"❌ Error: {e}")
        
        return redirect('client_list')
    
    messages.warning(request, 'Método no permitido.')
    return redirect('client_list')