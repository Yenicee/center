# Sistema SaaS Multi-tenant para Gestión de Consultorios Médicos

## Descripción

Sistema SaaS (Software as a Service) multi-tenant desarrollado con Django que permite a múltiples consultorios médicos gestionar sus pacientes, especialistas y sesiones de forma completamente aislada. Cada consultorio opera en su propio tenant con base de datos separada, garantizando total privacidad y seguridad de los datos.

## Características Principales

- **Multi-tenancy**: Cada cliente (consultorio) tiene su propia instancia aislada
- **Gestión de Pacientes**: CRUD completo para pacientes con historial médico
- **Gestión de Especialistas**: Administración de profesionales médicos
- **Sistema de Sesiones**: Programación y seguimiento de citas médicas
- **Panel Administrativo**: Gestión centralizada de clientes y facturación
- **Autenticación por Email**: Login seguro por tenant
- **Escalabilidad**: Modelo de negocio B2B con límites configurables

## Arquitectura del Sistema

### Componentes Principales

```
├── config/                 # Configuración principal de Django
├── panelAdmin/            # App para gestión de clientes (esquema público)
│   ├── models.py         # Modelos Client y Domain
│   ├── views.py          # Vistas administrativas
│   ├── forms.py          # Formularios de clientes
│   └── templates/        # Templates del panel admin
├── pacientes/            # App principal (esquemas de tenants)
│   ├── models.py         # Modelos Patient, Specialist, Session
│   ├── views.py          # Vistas del sistema médico
│   ├── backends.py       # Backend de autenticación por email
│   └── templates/        # Templates del sistema médico
└── templates/            # Templates compartidos
```

### Base de Datos Multi-tenant

- **Esquema Público**: Almacena información de clientes y dominios
- **Esquemas de Tenant**: Cada consultorio tiene su propio esquema con tablas aisladas
- **PostgreSQL**: Base de datos requerida para soporte de esquemas

## Requisitos del Sistema

### Software Requerido

- Python 3.11+
- PostgreSQL 12+
- Git

### Dependencias Python

```
asgiref==3.8.1
Django==5.1.2
tzdata==2024.2
django-tenants==3.9.0
psycopg2-binary==2.9.10
pillow==11.3.0
```

## Instalación y Configuración

### 1. Clonar el Repositorio

```bash
git clone https://github.com/Yenicee/center.git
cd center
```

### 2. Crear Entorno Virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Base de Datos PostgreSQL

```sql
-- Conectar a PostgreSQL y crear base de datos
CREATE DATABASE BD;
CREATE USER postgres WITH PASSWORD '1234';
GRANT ALL PRIVILEGES ON DATABASE BD TO postgres;
```

### 5. Configurar Variables de Entorno

Crear archivo `.env` (opcional) o usar la configuración por defecto en `settings.py`:

```env
DATABASE_NAME=BD
DATABASE_USER=postgres
DATABASE_PASSWORD=1234
DATABASE_HOST=localhost
DATABASE_PORT=5432
SECRET_KEY=your-secret-key-here
DEBUG=True
```

### 6. Aplicar Migraciones

```bash
# Migraciones del esquema público
python manage.py migrate_schemas --shared

# Migraciones de todos los tenants
python manage.py migrate_schemas
```

### 7. Crear Superusuario (Esquema Público)

```bash
python manage.py createsuperuser
```

### 8. Ejecutar Servidor

```bash
python manage.py runserver
```

## Uso del Sistema

### Acceso al Panel Administrativo

- URL: `http://localhost:8000/panel/`
- Gestión de clientes, facturación y métricas del negocio

### Acceso de Clientes a su Tenant

Cada consultorio accede a través de su subdominio:

- URL: `http://[schema-name].localhost:8000/pacientes/login/`
- Login: Email y contraseña proporcionados
- Ejemplo: `http://consultorio-medico.localhost:8000/pacientes/login/`

### Funcionalidades por Tenant

Cada consultorio puede gestionar:

- **Pacientes**: Registro, historial, seguimiento
- **Especialistas**: Profesionales del consultorio
- **Sesiones**: Citas y consultas médicas
- **Salas**: Espacios físicos del consultorio
- **Pagos**: Facturación de pacientes

## Desarrollo

### Estructura de URLs

```python
# URLs principales
admin/              # Django admin
panel/              # Panel administrativo SaaS
pacientes/          # Aplicación médica (por tenant)
```

### Modelo de Datos

#### Esquema Público (panelAdmin)
- `Client`: Información de consultorios
- `Domain`: Dominios de acceso por tenant

#### Esquemas Tenant (pacientes)
- `Patient`: Pacientes del consultorio
- `Specialist`: Especialistas médicos
- `Session`: Citas y consultas
- `Room`: Salas del consultorio
- `Payment`: Facturación

### Comandos Útiles

```bash
# Listar tenants existentes
python manage.py list_tenants

# Ejecutar comando en tenant específico
python manage.py tenant_command [comando] --schema=[nombre-tenant]

# Crear migraciones
python manage.py makemigrations
python manage.py makemigrations panelAdmin
python manage.py makemigrations pacientes

# Aplicar migraciones específicas
python manage.py migrate_schemas --shared  # Solo esquema público
python manage.py migrate_schemas --tenant   # Solo tenants
```

## Deployment

### Variables de Entorno de Producción

```env
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,*.yourdomain.com
DATABASE_URL=postgresql://user:password@host:port/database
SECRET_KEY=your-production-secret-key
```

### Configuración de Servidor Web

- Configurar nginx/Apache para manejar subdominios
- SSL/TLS para todas las conexiones
- Configurar variables de entorno
- Migrar base de datos de producción

## Contribuir

1. Fork del repositorio
2. Crear rama de feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit de cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

## Soporte

Para reportar bugs o solicitar funcionalidades, crear un issue en GitHub.

## Contacto

- Desarrollador: Yenice Vazquez, Jose 
