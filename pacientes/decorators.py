from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib import messages

def admin_only(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'specialist_profile'):
            if request.user.specialist_profile.role == 'administrador':
                return view_func(request, *args, **kwargs)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Acceso restringido a administradores'}, status=403)
        messages.error(request, 'Acceso restringido a administradores.')
        return redirect('patient_list')
    return wrapper
