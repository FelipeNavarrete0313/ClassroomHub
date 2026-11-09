# Laboratorio 08 — Autenticación, sesiones, grupos y permisos

Bitácora del Laboratorio 08 de ClassroomHub: qué se hizo en cada práctica, las salidas reales obtenidas y las respuestas a las preguntas de la guía.

- **Aprendiz:** Felipe Andrés Navarrete Calderón — ficha 3388087
- **Guía:** [laboratorio-08.md](https://github.com/ethan-fullstack/python_explorer_integrator_innovator/blob/main/laboratorios/laboratorio-08.md)
- **Entorno de verificación:** Python 3.13, Django 6.1.3, MariaDB 10.11

> Las contraseñas que aparecen aquí (`reader_demo`, `lab08_student`, etc.) son cuentas de demostración locales, no credenciales reales.

## Práctica 8.1 — Identidad, contraseñas y sesiones

Estado inicial del proyecto:

```text
$ python -m django --version
6.1.3
$ python manage.py check
System check identified no issues (0 silenced).
$ python manage.py showmigrations auth sessions pages
auth
 [X] 0001_initial
 [X] 0002_alter_permission_name_max_length
 [X] 0003_alter_user_email_max_length
 [X] 0004_alter_user_username_opts
 [X] 0005_alter_user_last_login_null
 [X] 0006_require_contenttypes_0002
 [X] 0007_alter_validators_add_error_messages
 [X] 0008_alter_user_username_max_length
 [X] 0009_alter_user_last_name_max_length
 [X] 0010_alter_group_name_max_length
 [X] 0011_update_proxy_permissions
 [X] 0012_alter_user_first_name_max_length
sessions
 [X] 0001_initial
pages
 [X] 0001_initial
 [X] 0002_resource_resource_type
```

Tablas que Django creó con las migraciones de `auth` y `sessions`:

```text
+----------------------------------+
| Tables_in_classroom_hub (auth_%) |
+----------------------------------+
| auth_group                       |
| auth_group_permissions           |
| auth_permission                  |
| auth_user                        |
| auth_user_groups                 |
| auth_user_user_permissions       |
+----------------------------------+
+------------------------------------------+
| Tables_in_classroom_hub (django_session) |
+------------------------------------------+
| django_session                           |
+------------------------------------------+
```

Prueba del hasher de contraseñas (`make_password` / `check_password`):

```text
True
True
False
pbkdf2_sha256
```

La contraseña nunca se guarda en texto plano: queda como `pbkdf2_sha256$<iteraciones>$<sal>$<hash>`. En `config/settings.py` se conservan `SessionMiddleware` antes de `AuthenticationMiddleware`, `CsrfViewMiddleware` y el procesador `django.contrib.auth.context_processors.auth`.

**Predicciones**

1. A MySQL/MariaDB siempre se conecta `classroomhub_user` (la cuenta de `DATABASES`), sin importar qué persona navegue.
2. Porque autenticarse solo dice *quién es*; los permisos (`has_perm`) dicen *qué puede hacer*, y una cuenta nueva no tiene ninguno.
3. La cookie `sessionid` solo guarda un identificador aleatorio en el navegador; el registro en `django_session` guarda los datos de la sesión en el servidor.
4. Porque cualquiera puede escribir la URL a mano; la comprobación debe hacerse en la vista, en el servidor.

## Práctica 8.2 — Registro con `UserCreationForm`

Se agregó la vista `signup` y `pages/templates/pages/signup.html`. Consulta de usuarios y cuenta creada desde Python:

```text
count: 0
[]
created: True is_staff: False is_superuser: False
password stored hashed: True
```

El formulario público solo expone `username`, `password1` y `password2`: nunca `is_staff`, `is_superuser` ni `groups`. Si el usuario ya existe, las contraseñas no coinciden o incumplen los validadores, el formulario se vuelve a mostrar con errores y no se guarda nada. Una cuenta ya autenticada que visita `/accounts/signup/` se redirige al panel.

## Práctica 8.3 — Login y logout

Se configuraron `LOGIN_URL`, `LOGIN_REDIRECT_URL` y `LOGOUT_REDIRECT_URL`, las rutas `signup`, `login` y `logout`, la plantilla `login.html` y el menú de `base.html` que cambia según `user.is_authenticated`. El logout es un formulario POST con `{% csrf_token %}`.

```text
GET /accounts/signup/ -> 200
POST signup valid -> 302 /accounts/login/
POST signup mismatched -> 200 errors: ['password2']
POST login wrong pw -> 200 authenticated: False
GET /accounts/logout/ -> 405
```

## Práctica 8.4 — Panel privado y sesión

Vista `dashboard` con `@login_required` y contador `dashboard_visits` en `request.session`:

```text
Anonymous GET /dashboard/ -> 302 /accounts/login/?next=/dashboard/
POST login with next -> 302 /dashboard/
GET /dashboard/ #1 -> 200, visit_count=1
GET /dashboard/ #2 -> 200, visit_count=2
GET /dashboard/ #3 -> 200, visit_count=3
POST logout -> 302 / | session keys after: []
GET /dashboard/ after logout -> 302 /accounts/login/?next=/dashboard/
Second browser (new session) visit_count -> 1
```

Ejercicio temporal con `preferred_section` (se restableció el código después de probarlo):

```text
Request 1: preferred_section in session = 'Resources'; shown in HTML = True
Request 2: preferred_section in session = 'Resources'; shown in HTML = True
After logout: preferred_section in session = None
```

**Predicciones**

1. Tras cerrar sesión, `/dashboard/` redirige a `/accounts/login/?next=/dashboard/`.
2. Cada navegador tiene su propia cookie y por tanto su propia sesión; el contador empieza en 1 en cada una.
3. `request.user` es la cuenta autenticada (o `AnonymousUser`); `request.session` es un diccionario de datos temporales ligado a la cookie.
4. Porque la sesión es un dato de conveniencia, no una fuente de autorización: los permisos reales están en `auth_permission` y en los grupos, y se comprueban con `has_perm()`.

## Práctica 8.5 — Grupos y permisos

Creación del grupo `Catalog reviewers`, asignación a `reader_demo` y comprobación de los tres roles:

```text
Resource permissions: ['add_resource', 'change_resource', 'delete_resource', 'view_resource']
Catalog reviewers permissions: ['view_resource']
reader_demo view_resource: True
reader_demo change_resource: False
reader_demo is_staff: False
lab08_student (common) view_resource: False | change_resource: False | groups: 0
Anonymous GET /resources/review/ -> 302 /accounts/login/?next=/resources/review/
Common account GET /resources/review/ -> 403
Common account sees Review link: False
Reviewer GET /resources/review/ -> 200 | shows 'Python basics': True
Reviewer sees Review link: True
Anonymous GET /resources/ -> 200
```

**Reto — Comparar roles.** La cuenta común tiene `view_resource=False` y `change_resource=False`; el revisor tiene `view_resource=True` y `change_resource=False`. Solo el revisor entra a la revisión porque la vista exige `pages.view_resource`. Ninguno puede editar porque no tiene `change_resource` y, además, todavía no existe ninguna vista pública de edición.

## Práctica 8.6 — Reto integrador y pruebas

Lista de comprobación manual:

| Prueba | Acción | Resultado obtenido |
|---|---|---|
| P01 | Abrir catálogo sin sesión | 200 |
| P02 | Abrir registro | 200, formulario con ['username', 'password1', 'password2'] |
| P03 | Registrar cuenta normal | 302 → /accounts/login/; is_staff=False |
| P04 | Contraseñas distintas | 200, cuenta creada=False |
| P05 | Login con contraseña incorrecta | 200, autenticado=False |
| P06 | Login válido | 302 → /dashboard/ |
| P07 | Panel sin autenticación | 302 → /accounts/login/?next=/dashboard/ |
| P08 | Visitar dos veces el panel | contador 1, luego 2 |
| P09 | Revisión como cuenta normal | 403 |
| P10 | Revisión como revisor | 200 |
| P11 | Logout por GET | 405 |
| P12 | Logout por POST | 302 → /; sesión vacía=True |
| P13 | Panel después de salir | 302 → /accounts/login/?next=/dashboard/ |
| P14 | Catálogo tras reiniciar (proceso nuevo) | ['Django models', 'Git and GitHub', 'Python basics'] |

Pruebas automatizadas sobre `test_classroom_hub`:

```text
$ python manage.py check
System check identified no issues (0 silenced).
$ python manage.py makemigrations --check --dry-run
No changes detected
$ python manage.py test pages
Ran 31 tests

OK
```

El total es 31 y no 28 porque el Laboratorio 07 de este repositorio ya tenía **11** pruebas (las 10 de la guía más la del reto `/resources/available/`), a las que se suman las **18** del Laboratorio 08 y **2** del reto adicional.

**Reto adicional — Resumen privado.** `/dashboard/summary/` muestra el total de recursos y los disponibles con `Resource.objects.count()` y `filter(available=True).count()`. Solo usa `@login_required`; tiene pruebas para anónimo (redirección) y autenticado (conteos correctos).

### Preguntas para explicar la solución

1. **Autenticación vs autorización:** autenticar es verificar quién es la persona (usuario y contraseña); autorizar es decidir si esa persona puede usar una función (permisos).
2. **Cuenta SQL:** es la identidad de la aplicación ante el motor; compartirla con las personas les daría acceso directo a toda la base. Las personas usan cuentas de `auth_user`.
3. **`UserCreationForm`:** pide usuario y contraseña dos veces, valida coincidencia, unicidad y los validadores de contraseña, y guarda el hash. No debe permitir elegir privilegios (`is_staff`, `is_superuser`, grupos).
4. **`set_password()`:** aplica el hasher y guarda el hash; asignar `user.password = "texto"` guardaría texto plano y la cuenta no podría autenticarse.
5. **Cookie vs `django_session`:** la cookie está en el navegador y solo contiene la clave de sesión; la tabla guarda los datos en el servidor con su fecha de expiración.
6. **POST en `LoginView`:** las credenciales no deben quedar en la URL, el historial ni los logs, y el POST queda protegido con CSRF.
7. **Logout sin GET:** un GET puede dispararse solo (enlaces, imágenes, precarga); cerrar sesión cambia el estado, así que exige POST con token CSRF.
8. **`{% csrf_token %}`:** inserta un token que el middleware compara con la cookie CSRF para rechazar formularios enviados desde otros sitios.
9. **`next`:** `login_required` redirige a `LOGIN_URL?next=<ruta>`; después del login, `LoginView` vuelve a esa ruta si es segura (mismo host).
10. **`is_staff` vs `has_perm()`:** `is_staff` solo permite entrar a `/admin/`; `has_perm()` comprueba permisos concretos. El revisor tiene permiso de ver recursos sin ser staff.
11. **403 vs redirección:** la redirección significa "no sé quién eres, inicia sesión"; el 403 significa "sé quién eres, pero no tienes permiso".
12. **Permiso en la vista:** la plantilla solo oculta el enlace; la vista es la que realmente recibe la solicitud y debe rechazarla.
13. **Base de pruebas:** el ejecutor crea y destruye `test_classroom_hub`; si apuntara a `classroom_hub` borraría los datos reales.
14. **Lo que falta para un CRUD público:** formularios (`ModelForm`), vistas de crear/editar/eliminar, permisos `add`/`change`/`delete` en cada una y confirmación de borrado por POST (Laboratorio 09).

### Revisión antes de compartir

- [x] El proyecto conserva MySQL o MariaDB.
- [x] Las migraciones de `auth` y `sessions` están aplicadas.
- [x] El formulario de registro valida y crea cuentas sin privilegios.
- [x] `LoginView` autentica credenciales válidas.
- [x] `LogoutView` utiliza POST con CSRF.
- [x] `/dashboard/` exige autenticación.
- [x] El contador se conserva durante la sesión y desaparece después del logout.
- [x] `Catalog reviewers` tiene el permiso `pages.view_resource`.
- [x] `/resources/review/` devuelve 403 a cuentas sin permiso.
- [x] El catálogo `/resources/` permanece público.
- [x] Se conservan las pruebas del Laboratorio 07.
- [x] Se añadieron las dieciocho pruebas del Laboratorio 08.
- [x] Las pruebas se ejecutan contra la base descartable.
- [x] `.env` y las credenciales no se incluyen en Git.
- [x] El README explica rutas y creación de cuentas/grupos.
