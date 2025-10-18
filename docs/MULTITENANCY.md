# Arquitectura Multi-Tenant

Este documento describe la implementación de la arquitectura multi-tenant en el proyecto de citas. El objetivo es que una única instancia de la aplicación pueda servir a múltiples organizaciones de forma aislada.

## Concepto Clave

El modelo principal que define a un "tenant" (inquilino) es la clase `Organizacion`. Cada `Organizacion` es una entidad independiente con sus propias sedes, colaboradores, servicios, citas y usuarios.

La separación de datos se logra a nivel de aplicación, no a nivel de base de datos. Esto significa que todos los datos de todas las organizaciones residen en las mismas tablas, pero se añade una clave foránea (`ForeignKey`) a `Organizacion` en los modelos relevantes para filtrar los datos.

## Implementación

### 1. Modelos Principales

- **`organizacion.Organizacion`**: Es el modelo central que representa a un tenant.
- **`organizacion.Sede`**: Cada sede pertenece a una `Organizacion`.
- **`usuarios.PerfilUsuario`**: Cada usuario del sistema (que no sea superusuario) está vinculado a una `Organizacion` a través de su perfil.
- **Modelos dependientes**: Modelos como `citas.Colaborador`, `citas.Servicio`, y `citas.Cita` están vinculados indirectamente a una `Organizacion` a través de su relación con `Sede`.

### 2. Aislamiento de Datos

El aislamiento de datos se implementa principalmente a través de un gestor de modelos (`Manager`) personalizado:

- **`organizacion.managers.OrganizacionManager`**: Este es el gestor de modelos por defecto (`objects`) para los modelos que necesitan ser filtrados por organización (como `Sede`).
- **Funcionamiento**: El `OrganizacionManager` sobreescribe el método `get_queryset()` para filtrar automáticamente los objetos basándose en la `organizacion` del usuario que realiza la solicitud. La organización del usuario se obtiene de `request.user.perfil.organizacion`.
- **Acceso sin filtro**: Para poder acceder a todos los objetos sin el filtro automático (por ejemplo, en el panel de administración para un superusuario), los modelos también tienen un gestor secundario llamado `all_objects` (`models.Manager()`).

### 3. Panel de Administración de Django

Un desafío clave es el panel de administración, ya que por defecto usaría el `OrganizacionManager`, impidiendo a los superusuarios ver los objetos de todas las organizaciones.

- **Solución**: En las clases `ModelAdmin` correspondientes (ej. `SedeAdmin`, `ColaboradorAdmin`), se sobreescribe el método `get_queryset()` para usar `all_objects` y mostrar todos los registros si el usuario es un superusuario.
- **Filtrado de Desplegables**: Para los menús desplegables (claves foráneas como el campo `sede`), se sobreescribe el método `formfield_for_foreignkey`. Dentro de este método, se asigna manualmente un `queryset` que utiliza `all_objects` para los superusuarios, y un queryset filtrado por organización para los demás usuarios. Esto asegura que cada tipo de usuario vea las opciones correctas en los formularios.

