from django.shortcuts import render, get_object_or_404, redirect
from .models import Client
from .forms import ClientForm

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
            form.save()
            return redirect('client_list')
    else:
        form = ClientForm()
    return render(request, 'client/client_form.html', {'form': form})

def client_detail(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    return render(request, 'client/client_detail.html', {'client': client})
