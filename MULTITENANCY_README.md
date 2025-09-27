# Arquitectura Multi-Tenant del Proyecto

Este documento describe la implementación de la arquitectura multi-tenant en este proyecto de Django.

## 1. Visión General

Se utiliza un enfoque de **Base de Datos Compartida, Esquema Compartido**. Esto significa que todos los tenants (organizaciones) comparten la misma base de datos y las mismas tablas. La separación de datos se logra a nivel de aplicación, añadiendo una referencia a cada tenant en los datos que le pertenecen.

## 2. Componentes Clave

### a. El Modelo del Tenant (`Organizacion`)

- **Ubicación:** `backend/organizacion/models.py`
- **Modelo Principal:** `Organizacion`

Este modelo es el pilar central. Cada instancia de `Organizacion` representa un tenant separado en el sistema.

### b. Aislamiento de Datos (Models y Managers)

Para asegurar que una organización solo vea sus propios datos, se implementó lo siguiente:

- **ForeignKeys:** Todos los modelos que deben ser aislados (como `Sede`, `Servicio`, `Colaborador`, `Cita`, etc.) tienen una relación `ForeignKey` que, directa o indirectamente, apunta al modelo `Organizacion`.

- **`OrganizacionManager`:**
    - **Ubicación:** `backend/organizacion/managers.py`
    - Es el gestor de modelos (`objects`) por defecto para todos los modelos aislados.
    - Su función es **filtrar automáticamente CUALQUIER consulta a la base de datos**. Intercepta las llamadas (`.all()`, `.filter()`, etc.) y añade un filtro para que solo se devuelvan los objetos que pertenecen a la organización activa en la petición actual.

- **`all_objects` Manager:**
    - Como el `OrganizacionManager` es muy agresivo, todos los modelos aislados también tienen un segundo gestor: `all_objects = models.Manager()`.
    - Este gestor **no tiene ningún filtro** y se usa explícitamente en lugares donde necesitamos ver todos los datos, como en el panel de administración para un superusuario.

### c. Identificación del Tenant (Middleware)

- **Ubicación:** `backend/organizacion/middleware.py`
- **Clase:** `OrganizacionMiddleware`

Este middleware se ejecuta en cada petición y su trabajo es averiguar a qué organización pertenece la petición actual. Lo hace de dos maneras:

1.  **Para usuarios autenticados:** Revisa el perfil del usuario (`request.user.perfil.organizacion`) y establece esa como la organización activa.
2.  **Para páginas públicas:** Revisa la URL en busca de un `slug` de organización (ej: `dominio.com/api/nombre-organizacion/...`) para identificar al tenant.

Una vez identificada, guarda la organización activa en una variable `thread_local`, que es la que el `OrganizacionManager` usa para filtrar las consultas.

### d. Panel de Administración (`admin.py`)

El panel de administración requirió ajustes especiales para funcionar correctamente con el `OrganizacionManager`:

- **`get_queryset()`:** En cada `ModelAdmin`, este método fue sobreescrito para usar `self.model.all_objects.all()` en lugar del gestor por defecto. Esto nos da una lista sin filtrar, sobre la cual aplicamos nuestra propia lógica: si el usuario es superusuario, ve todo; si no, filtramos por su organización.

- **`formfield_for_foreignkey()` y `formfield_for_manytomany()`:** Estos métodos se sobreescribieron para controlar el contenido de los menús desplegables y cajas de selección en los formularios de creación/edición. Al igual que con `get_queryset`, se usa `all_objects` para asegurar que un superusuario pueda ver y asignar objetos de cualquier organización.