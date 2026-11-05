# ClassroomHub

ClassroomHub es un sitio web sencillo hecho con Django para consultar recursos de aprendizaje de un aula. Tiene una página de bienvenida, un listado de recursos con su categoría y disponibilidad, y una página informativa sobre su propósito. Las tres páginas comparten una plantilla base y un menú de navegación.

Los recursos son datos de ejemplo definidos en `pages/views.py`.

## Versiones

- **Python:** 3.12 o superior (Django 6.1 admite Python 3.12, 3.13, 3.14 y 3.15)
- **Django:** 6.1.3

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

## Ejecutar el servidor

```bash
python manage.py runserver
```

El sitio queda disponible en <http://127.0.0.1:8000/>. Para detener el servidor, pulsa `Ctrl + C`.

## Rutas públicas

| Ruta | Página | Contenido |
| --- | --- | --- |
| `/` | Inicio | Encabezado y mensaje de bienvenida |
| `/resources/` | Recursos | Lista de recursos con su disponibilidad |
| `/about/` | Acerca de | Propósito de ClassroomHub |

Cualquier ruta desconocida devuelve un error `404`.

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

Las cinco pruebas deben pasar. Comprueban las tres páginas, el enlace de navegación hacia los recursos y la respuesta `404` de una ruta inexistente.

## Funcionalidades que todavía no incluye

- Modelos ni almacenamiento de recursos en una base de datos.
- Crear, editar o eliminar recursos. La lista siempre vuelve a los valores definidos en el código.
- Administración de recursos desde el panel de Django.
- Formularios.
- Registro e inicio de sesión de usuarios.
- Despliegue en producción.
