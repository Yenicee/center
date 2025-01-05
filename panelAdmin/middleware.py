from django.core.exceptions import PermissionDenied

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            print(f"Usuario autenticado: {request.user.username}")

            if request.user.is_superuser:
                request.tenant = None
                print("Usuario es superuser")
                return self.get_response(request)
            
            try:
                specialist = request.user.specialist_profile
                print(f"Specialist encontrado: {specialist}")
                print(f"Client del specialist: {specialist.client}")  
                
                if specialist.client:
                    request.tenant = specialist.client
                    print(f"Tenant asignado correctamente: {request.tenant.name}")  
                else:
                    request.tenant = None
                    print("ALERTA: Specialist no tiene client asignado")
            except Exception as e:
                print(f"Error específico al obtener specialist: {str(e)}")
                request.tenant = None
                    
            if '/pacientes/' in request.path:
                if request.tenant is None:
                    print("ALERTA: Acceso denegado - No hay tenant")
                    raise PermissionDenied
                else:
                    print(f"Acceso permitido para tenant: {request.tenant.name}")  
                
        return self.get_response(request)