# ClassroomHub

ClassroomHub es un sitio web sencillo hecho con Django para consultar recursos de aprendizaje de un aula. Tiene una página de bienvenida, un listado de recursos con su categoría y disponibilidad, y una página informativa sobre su propósito. Las páginas comparten una plantilla base y un menú de navegación.

Los recursos se guardan en MySQL o MariaDB, se administran desde Django Admin y se consultan con el ORM de Django.

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

## Ejecutar el servidor

```bash
python manage.py runserver
```

El sitio queda disponible en <http://127.0.0.1:8000/>. Para detener el servidor, pulsa `Ctrl + C`.

## Rutas públicas

| Ruta | Página | Contenido |
| --- | --- | --- |
| `/` | Inicio | Encabezado y mensaje de bienvenida |
| `/resources/` | Recursos | Recursos guardados en la base, con su categoría y disponibilidad |
| `/resources/available/` | Disponibles | Solo los recursos disponibles |
| `/about/` | Acerca de | Propósito de ClassroomHub |

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

Las 11 pruebas deben pasar. Usan la base temporal `test_classroom_hub`, no `classroom_hub`.

## Funcionalidades que todavía no incluye

- Crear, editar o eliminar recursos desde las páginas públicas (solo desde `/admin/`).
- Formularios públicos.
- Registro e inicio de sesión de usuarios propios.
- API REST.
- Despliegue en producción.
