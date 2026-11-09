# ClassroomHub

ClassroomHub es un sitio web sencillo hecho con Django para consultar recursos de aprendizaje de un aula. Tiene una página de bienvenida, un listado de recursos con su categoría y disponibilidad, y una página informativa sobre su propósito. Las páginas comparten una plantilla base y un menú de navegación.

Los recursos se guardan en MySQL o MariaDB, se administran desde Django Admin y se consultan con el ORM de Django.

Desde el Laboratorio 09, las cuentas del grupo `Catalog editors` pueden crear, editar y eliminar recursos desde las propias páginas de ClassroomHub (CRUD protegido por permisos), y cualquier visitante puede ver el detalle de cada recurso y buscar por título.

Desde el Laboratorio 08 el sitio también permite registrar cuentas, iniciar y cerrar sesión, visitar un panel privado y revisar el catálogo solo si la cuenta pertenece al grupo `Catalog reviewers`. Todo usa el sistema de autenticación incluido en Django (`django.contrib.auth` y `django.contrib.sessions`).

## Versiones

- **Python:** 3.12 o superior (Django 6.1 admite Python 3.12, 3.13, 3.14 y 3.15)
- **Django:** 6.1.3
- **Base de datos:** MySQL 8.4 o superior, o MariaDB 10.11 o superior

## Crear y activar el entorno

Abre una terminal en la carpeta raíz del proyecto, donde está `manage.py`, y crea el entorno virtual:

```bash
python -m venv .venv
```

Actívalo según tu sistema:

```powershell
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

```bat
:: Windows (CMD)
.venv\Scripts\activate.bat
```

```bash
# Linux o macOS
source .venv/bin/activate
```

Si tu equipo usa otro ejecutable, como `py` o `python3`, adapta los comandos de esta guía.

## Instalar dependencias

Con el entorno activado:

```bash
python -m pip install -r requirements.txt
```

## Crear la base de datos

En el cliente `mysql` o `mariadb`, con una cuenta administrativa y usando tu propia contraseña:

```sql
CREATE DATABASE IF NOT EXISTS classroom_hub
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'classroomhub_user'@'127.0.0.1'
IDENTIFIED BY 'replace_with_a_private_password';

GRANT ALL PRIVILEGES ON classroom_hub.* TO 'classroomhub_user'@'127.0.0.1';
GRANT ALL PRIVILEGES ON test_classroom_hub.* TO 'classroomhub_user'@'127.0.0.1';
```

## Configurar la conexión

Copia `.env.example` como `.env` y escribe tu contraseña real en `.env`. Ese archivo no se sube a Git.

```powershell
# Windows (PowerShell)
Copy-Item .env.example .env
```

```bash
# Linux o macOS
cp .env.example .env
```

## Crear las tablas y el administrador

```bash
python manage.py migrate
python manage.py createsuperuser
```

La base empieza vacía: crea categorías y recursos en `/admin/` para verlos en el catálogo.

## Preparar el grupo revisor

El registro público crea cuentas **sin privilegios** (no son staff, ni superusuario, ni pertenecen a grupos). Para que una cuenta pueda abrir `/resources/review/`:

1. Entra en `/admin/` con el superusuario.
2. En **Groups**, crea el grupo `Catalog reviewers` y asígnale solo el permiso `pages | resource | Can view resource` (`pages.view_resource`).
3. En **Users**, abre la cuenta de prueba y agrégala al grupo. No marques `Staff status`: no hace falta.

También puedes hacerlo desde `python manage.py shell`:

```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from pages.models import Resource

content_type = ContentType.objects.get_for_model(Resource)
view_permission = Permission.objects.get(content_type=content_type, codename="view_resource")
reviewers, created = Group.objects.get_or_create(name="Catalog reviewers")
reviewers.permissions.add(view_permission)

get_user_model().objects.get(username="your_username").groups.add(reviewers)
```

Las contraseñas se crean siempre con el formulario de registro, `create_user()` o `set_password()`, nunca escribiéndolas directamente en SQL.

## Preparar categorías y el grupo editor

Las categorías se gestionan **solo desde Django Admin**: entra en `/admin/` → **Categories** y crea algunas (por ejemplo `Programming`, `Collaboration` y `Web development`). Sin categorías, el formulario de recursos no tiene opciones.

Para que una cuenta de prueba pueda gestionar recursos:

1. En `/admin/` → **Groups**, crea `Catalog editors` con los permisos `pages | resource | Can view resource`, `Can add resource`, `Can change resource` y `Can delete resource`.
2. En **Users**, agrega **solo** la cuenta de demostración elegida a ese grupo. No marques `Staff status`: el CRUD público usa permisos, no acceso al admin.

Desde `python manage.py shell`:

```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from pages.models import Resource

content_type = ContentType.objects.get_for_model(Resource)
codes = ["view_resource", "add_resource", "change_resource", "delete_resource"]
permissions = Permission.objects.filter(content_type=content_type, codename__in=codes)
editors, created = Group.objects.get_or_create(name="Catalog editors")
editors.permissions.add(*permissions)

get_user_model().objects.get(username="your_editor_username").groups.add(editors)
```

**Los permisos nunca se asignan desde el formulario de registro público**: toda cuenta nueva empieza sin grupos ni privilegios.

| Operación | Anónimo | Cuenta común | Catalog reviewers | Catalog editors |
| --- | --- | --- | --- | --- |
| Ver lista, detalle y buscar | Sí | Sí | Sí | Sí |
| Panel personal | No | Sí | Sí | Sí |
| Revisión del catálogo | No | No | Sí | Sí |
| Crear, editar y eliminar recursos | No | No | No | Sí |

## Ejecutar el servidor

```bash
python manage.py runserver
```

El sitio queda disponible en <http://127.0.0.1:8000/>. Para detener el servidor, pulsa `Ctrl + C`.

## Rutas

| Ruta | Acceso | Contenido |
| --- | --- | --- |
| `/` | Público | Encabezado y mensaje de bienvenida |
| `/resources/` | Público | Recursos guardados en la base; admite búsqueda por título con `?q=` |
| `/resources/<pk>/` | Público | Detalle de un recurso (`404` si no existe) |
| `/resources/new/` | Permiso `pages.add_resource` | GET muestra el formulario; POST crea el recurso |
| `/resources/<pk>/edit/` | Permiso `pages.change_resource` | GET muestra el formulario con los datos; POST guarda los cambios |
| `/resources/<pk>/delete/` | Permiso `pages.delete_resource` | GET solo muestra la confirmación; POST elimina el recurso |
| `/resources/available/` | Público | Solo los recursos disponibles |
| `/about/` | Público | Propósito de ClassroomHub |
| `/accounts/signup/` | Público | Registro de cuentas normales con `UserCreationForm` |
| `/accounts/login/` | Público | Inicio de sesión con `LoginView` |
| `/accounts/logout/` | Solo POST | Cierre de sesión con `LogoutView` (por GET responde `405`) |
| `/dashboard/` | Cuenta autenticada | Panel privado con contador de visitas guardado en la sesión |
| `/dashboard/summary/` | Cuenta autenticada | Total de recursos y recursos disponibles (solo lectura) |
| `/resources/review/` | Permiso `pages.view_resource` | Revisión del catálogo para `Catalog reviewers` |

Un visitante anónimo que abre una ruta privada es redirigido a `/accounts/login/?next=...`. Una cuenta autenticada sin el permiso necesario recibe `403`, aunque escriba la URL a mano. Crear y editar usan el mismo `ResourceForm` (`pages/forms.py`) y la misma plantilla; tras guardar o eliminar se redirige a `/resources/`.

Métodos HTTP del CRUD:

```text
GET  /resources/
GET  /resources/<pk>/
GET  /resources/new/
POST /resources/new/
GET  /resources/<pk>/edit/
POST /resources/<pk>/edit/
GET  /resources/<pk>/delete/
POST /resources/<pk>/delete/
```

El panel de administración está en `/admin/`. Cualquier ruta desconocida devuelve un error `404`.

## Ejecutar las pruebas

Primero, comprueba la configuración del proyecto:

```bash
python manage.py check
```

La respuesta esperada es `System check identified no issues (0 silenced).`

Después, ejecuta las pruebas automatizadas:

```bash
python manage.py test pages
```

Las 64 pruebas deben pasar: 11 del Laboratorio 07, 18 del Laboratorio 08 y 2 de su reto (resumen privado), 30 de CRUD y permisos del Laboratorio 09 y 3 de su reto (búsqueda). Usan la base temporal `test_classroom_hub`, no `classroom_hub`.

También puedes comprobar que no hay cambios de modelos sin migración:

```bash
python manage.py makemigrations --check --dry-run
```

## Credenciales y datos privados

- `.env` contiene la contraseña de la base y está en `.gitignore`: no se sube.
- No compartas usuarios reales, contraseñas, cookies de sesión (`sessionid`) ni exportaciones SQL.
- Las contraseñas que aparecen en `pages/tests.py` son datos ficticios de prueba.

## Funcionalidades que todavía no incluye

- Crear, editar o eliminar **categorías** desde las páginas públicas (solo desde `/admin/`).
- Carga de archivos, paginación o filtros avanzados.
- Recuperación de contraseña por correo, autenticación multifactor u OAuth.
- Modelo de usuario personalizado.
- API REST ni interfaces JavaScript avanzadas.
- Despliegue en producción.
