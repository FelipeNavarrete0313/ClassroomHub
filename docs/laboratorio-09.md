# Laboratorio 09 — Formularios y CRUD con Django

Bitácora del Laboratorio 09 de ClassroomHub: qué se hizo en cada práctica, las salidas reales obtenidas y las respuestas a las preguntas de la guía.

- **Aprendiz:** Felipe Andrés Navarrete Calderón — ficha 3388087
- **Guía:** [laboratorio-09.md](https://github.com/ethan-fullstack/python_explorer_integrator_innovator/blob/main/laboratorios/laboratorio-09.md)
- **Entorno de verificación:** Python 3.13, Django 6.1.3, MariaDB 10.11

> Las cuentas `lab08_student` (común), `reader_demo` (Catalog reviewers) y `editor_demo` (Catalog editors) son cuentas locales de demostración.

## Práctica 9.1 — Formularios, GET, POST y validación

Formulario `forms.Form` probado en el shell:

```text
valid_form.is_valid(): True
valid_form.cleaned_data: {'query': 'Django'}
invalid_form.is_valid(): False
invalid_form.errors: {'query': [{'message': 'This field is required.', 'code': 'required'}]}
unbound form is_bound: False
```

**Predicciones**

1. El formulario se muestra con **GET**; los datos se envían con **POST**.
2. Una categoría inexistente no es una opción válida: el formulario marca error en `category` y no guarda nada.
3. Porque `is_valid() == False` significa que los datos no cumplen las reglas; guardar dejaría registros incorrectos en la base.
4. Evita que recargar la página reenvíe el POST y duplique el registro (patrón Post/Redirect/Get).
5. Porque un POST se puede enviar a mano (curl, otro formulario); el servidor debe comprobar el permiso en la vista.

**Ejercicio — Orden de comprobaciones.** `Permission → Form validation → Model save → Redirect`. Si falla el permiso, se responde redirección al login (anónimo) o 403 (sin permiso) y el formulario ni se procesa. Si falla la validación, se devuelve el formulario con errores (200) sin guardar ni redirigir.

## Práctica 9.2 — `ResourceForm`

Se creó `pages/forms.py` con un único `ModelForm` y campos explícitos (`title`, `description`, `resource_type`, `category`, `available`) más `clean_title()`.

```text
Category.objects.first(): Collaboration
valid form is_valid(): True | errors: {}
resources before/after validating (no save): 3 3
short title is_valid(): False | errors: {'title': [{'message': 'Title must contain at least 3 characters.', 'code': ''}]}
unknown category is_valid(): False | errors: ['category']
extra POST keys ignored -> fields: ['title', 'description', 'resource_type', 'category', 'available'] | valid: True
create_form.instance.pk: None
update_form initial title: Django models | instance.pk: 3
```

Campos vacíos, longitudes y normalización del título:

```text
Todo vacío: is_valid=False | errors={'title': ['This field is required.'], 'category': ['This field is required.']}
Título solo espacios: is_valid=False | errors={'title': ['This field is required.']}
Sin categoría: is_valid=False | errors={'category': ['This field is required.']}
Título de 151 caracteres: is_valid=False | errors={'title': ['Ensure this value has at most 150 characters (it has 151).']}
Título con espacios alrededor: is_valid=True | cleaned title='Git basics'
```

**Reto — `Form` vs `ModelForm`.** Con `forms.Form` habría que declarar a mano cada campo repitiendo tipos y longitudes del modelo (`CharField(max_length=150)`, `ModelChoiceField(queryset=Category.objects.all())`, `BooleanField(required=False)`…) y escribir el código que copia `cleaned_data` al objeto y lo guarda. `ModelForm` deriva todo eso de `Resource`, así que el modelo es la única fuente de verdad y no se duplican definiciones.

## Práctica 9.3 — Detalle público y creación

`ResourceDetailView` (público) y `ResourceCreateView` (`LoginRequiredMixin` + `PermissionRequiredMixin` con `pages.add_resource`), plantilla reutilizable `resource_form.html`, títulos del catálogo enlazados al detalle y grupo `Catalog editors`:

```text
Catalog editors permissions: ['add_resource', 'change_resource', 'delete_resource', 'view_resource']
Catalog reviewers permissions: ['view_resource']
editor_demo is_staff: False | add/change/delete: True True True
1. Anonymous GET /resources/new/ -> 302 /accounts/login/?next=/resources/new/
2. Common account GET /resources/new/ -> 403
3. Editor GET /resources/new/ -> 200 | category choices: ['Collaboration', 'Programming', 'Web development']
4-5. Editor POST /resources/new/ -> 302 /resources/
6. 'Web testing' in catalog: True | pk: 4
Public detail /resources/4/ -> 200
Unknown detail /resources/999999/ -> 404
7. After restart (new process): ['Django models', 'Git and GitHub', 'Python basics', 'Web testing']
```

## Práctica 9.4 — Edición

`ResourceUpdateView` con `pages.change_resource`, reutilizando `ResourceForm` y `resource_form.html`:

```text
Before: pk=4 title='Web testing' available=True category=Programming
Editor sees 'Edit resource' on detail: True
Editor GET edit -> 200 | form prefilled title: Web testing
Editor POST edit -> 302 /resources/ | After: pk=4 title='Web testing updated' available=False category=Collaboration
Total resources (no duplicate): 4
Invalid edit 'ab' -> 200 | errors: Title must contain at least 3 characters. | stored title still: 'Web testing updated'
Editor GET /resources/999999/edit/ -> 404
Common account GET edit -> 403
Common account POST edit -> 403 | title unchanged: True
Common account GET /resources/999999/edit/ -> 403 (rejected before revealing existence)
```

**Ejercicio — Error de integración.** Se cambió temporalmente `permission_required` por un permiso inexistente y luego se restableció:

```text
Exercise (nonexistent permission) editor GET edit -> 403
Restored change_resource, editor GET edit -> 200
```

**Predicciones**

1. `CreateView` crea una fila nueva; `UpdateView` carga una fila existente por `pk` y la modifica.
2. Para mostrar los valores actuales y para que `save()` haga `UPDATE` sobre esa fila en vez de `INSERT`.
3. El formulario marca error en `category` y no guarda nada.
4. Son operaciones con riesgos distintos; quien puede añadir no necesariamente debe poder cambiar lo que crearon otros (mínimo privilegio).

## Práctica 9.5 — Eliminación con confirmación

`ResourceDeleteView` con `pages.delete_resource` y plantilla de confirmación con formulario POST:

```text
1-2. Created 'Temporary deletion test' with pk = 5 | total: 5
3. Editor GET confirmation -> 200 | shows title: True
4. Still exists after GET: True
Common account GET delete -> 403 | POST delete -> 403 | still exists: True
Reviewer POST delete -> 403 | still exists: True
Anonymous GET delete -> /accounts/login/?next=/resources/5/delete/
Editor POST delete without CSRF token -> 403 | still exists: True
5-6. Editor POST delete -> 302 /resources/
7. GET old detail -> 404
8. Remaining resources: ['Django models', 'Git and GitHub', 'Python basics', 'Web testing updated']
Category 'Programming' still exists: True
Deleting a category with resources -> ProtectedError (on_delete=PROTECT)
```

## Práctica 9.6 — Reto integrador

Se agregaron el enlace **Add resource** en el catálogo y en el menú (solo con `perms.pages.add_resource`) y los enlaces **Edit/Delete resource** en el detalle según `change_resource` / `delete_resource`.

### Pruebas manuales

| Caso | Acción | Resultado obtenido |
|---|---|---|
| P01 | Abrir /resources/ como visitante | 200 |
| P02 | Detalle de recurso existente | 200, muestra categoría: True |
| P03 | Detalle inexistente | 404 |
| P04 | Creación sin autenticación | 302 → /accounts/login/?next=/resources/new/ |
| P05 | Creación como cuenta común | 403 |
| P06 | Creación como revisor | 403 |
| P07 | Crear recurso como editor | 302 → /resources/; recursos 4→5 |
| P08 | Crear con título de 2 caracteres | 200, error en title, recursos=5 |
| P09 | Crear con categoría inexistente | 200, error en category, creado=False |
| P10 | Editar como cuenta común | 403 |
| P11 | Editar como editor | 302; pk 6→6, título='Manual test resource edited' |
| P12 | Edición inválida | 200; título conservado='Manual test resource edited' |
| P13 | Abrir confirmación de borrado | 200; sigue existiendo=True |
| P14 | Eliminar como cuenta común | 403 |
| P15 | Confirmar borrado como editor | 302 → /resources/; recursos 5→4 |
| P16 | URL del recurso eliminado | 404 |
| P17 | Catálogo actualizado | 'Manual test resource' ausente: True |
| P18 | Reiniciar Django (proceso nuevo) | ['Django models', 'Git and GitHub', 'Python basics', 'Web testing updated'] |
| P19 | /resources/review/ como revisor | 200 |
| P20 | Pruebas automatizadas | 64 pruebas OK sobre test_classroom_hub (base creada y destruida por Django) |

### Cambios reflejados en Django Admin

Se creó, editó y eliminó un recurso desde las páginas de ClassroomHub con `editor_demo` y se consultó `/admin/` con el superusuario local:

```text
Creado desde /resources/new/ -> visible en /admin/pages/resource/: True
Editado desde /resources/7/edit/ -> /admin/ muestra el título nuevo: True
Eliminado desde /resources/7/delete/ -> ya no aparece en /admin/: True
editor_demo entra a /admin/? -> 302 (redirige al login del admin: no es staff)
```

### Pruebas automatizadas

```text
$ python manage.py check
System check identified no issues (0 silenced).
$ python manage.py makemigrations --check --dry-run
No changes detected
$ python manage.py test pages
Ran 64 tests

OK
```

**Sobre el conteo.** La guía dice que `ResourceCrudTests` agrega 27 pruebas, pero la clase que publica contiene **30** métodos `test_`. El total de este repositorio es: 11 (Lab 07, incluye su reto) + 18 (Lab 08) + 2 (reto del Lab 08) + 30 (Lab 09) + 3 (reto de búsqueda) = **64**.

**Reto adicional — Búsqueda.** El listado acepta `GET /resources/?q=texto` y filtra con `title__icontains`. Es pública y de solo lectura; un término vacío o con espacios lista todo. Tiene pruebas para búsqueda con resultados, sin resultados y vacía.

### Preguntas para explicar la solución

1. **`Form` vs `ModelForm`:** `Form` declara los campos a mano; `ModelForm` los genera a partir de un modelo y sabe guardar la instancia.
2. **`Meta.fields` explícito:** evita exponer campos nuevos o internos (como `created_at`) por accidente cuando el modelo crece.
3. **`is_valid()` en `False`:** `errors` se llena, `cleaned_data` solo tiene los campos válidos, no se guarda nada y la vista vuelve a mostrar el formulario con errores.
4. **Ventajas de `CreateView`:** ya maneja GET/POST, crea el formulario, valida, guarda y redirige a `success_url`; no hay que repetir ese código en cada vista.
5. **`UpdateView` recupera el objeto:** para precargar el formulario con `instance` y actualizar esa misma fila (misma PK) en lugar de crear otra.
6. **`DeleteView` GET/POST:** GET es una consulta segura (enlaces, rastreadores, precarga); borrar es irreversible y exige una acción deliberada por POST con CSRF.
7. **`reverse_lazy()`:** los atributos de clase se evalúan al importar el módulo, antes de cargar las URLs; `reverse_lazy` resuelve la ruta solo cuando se necesita.
8. **Sin `pages.change_resource` no se edita:** `PermissionRequiredMixin` comprueba ese permiso exacto en cada solicitud; estar autenticado no basta.
9. **Reviewers vs editors:** `Catalog reviewers` solo tiene `view_resource` (lectura y revisión); `Catalog editors` tiene `view`, `add`, `change` y `delete`.
10. **Enlaces condicionales:** solo mejoran la interfaz; quien conozca la URL puede pedirla directamente, así que la vista debe rechazarla.
11. **ID inexistente:** con permiso, `DetailView`/`UpdateView`/`DeleteView` responden 404; sin permiso se responde primero 403 o redirección, sin revelar si existe.
12. **Conservar la PK:** se compara `resource.pk` antes y después de editar (`refresh_from_db()`), y se verifica que el total de recursos no aumentó.
13. **Base de pruebas:** Django la crea vacía, la llena con datos ficticios y la destruye al terminar; cualquier dato importante allí se perdería.
14. **Limitaciones antes de exponerlo en Internet:** `DEBUG=False`, `SECRET_KEY` y `ALLOWED_HOSTS` reales, HTTPS con cookies seguras, archivos estáticos servidos correctamente, límites de intentos de login, registro de auditoría, copias de seguridad y paginación.

### Lista de comprobación

- [x] ClassroomHub conserva MySQL o MariaDB.
- [x] Los modelos y migraciones de `Category` y `Resource` siguen funcionando.
- [x] `pages/forms.py` define un `ResourceForm` con campos explícitos.
- [x] Las validaciones impiden guardar un título demasiado corto.
- [x] La lista y los detalles siguen siendo públicos.
- [x] Crear exige `pages.add_resource`.
- [x] Editar exige `pages.change_resource`.
- [x] Eliminar exige `pages.delete_resource`.
- [x] Un usuario anónimo es redirigido al login.
- [x] Un usuario autenticado sin permiso recibe 403.
- [x] `Catalog reviewers` mantiene acceso de lectura, no de edición.
- [x] `Catalog editors` puede crear, modificar y eliminar recursos.
- [x] El registro público no asigna grupos privilegiados.
- [x] Crear y editar reutilizan una sola plantilla.
- [x] GET de eliminación no modifica la base.
- [x] POST de eliminación requiere confirmación y autorización.
- [x] Los registros creados y modificados persisten al reiniciar.
- [x] Las pruebas anteriores se conservan.
- [x] Las nuevas pruebas se ejecutan sobre `test_classroom_hub`.
- [x] `.env`, contraseñas y datos sensibles no se versionan.
- [x] El README permite reproducir y comprobar el CRUD.
