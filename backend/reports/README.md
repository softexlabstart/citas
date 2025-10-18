# Reports App - Dashboard Financiero

## Descripción

Módulo de reportes financieros que proporciona análisis detallado de ingresos, citas y servicios para la plataforma de gestión de citas.

## Características Principales

### 1. Endpoint de Resumen Financiero

**URL**: `/api/reports/financial-summary/`
**Método**: GET
**Permisos**: `IsAuthenticated`, `IsAdminOrSedeAdmin`

#### Query Parameters

- `start_date` (opcional): Fecha inicio en formato YYYY-MM-DD
- `end_date` (opcional): Fecha fin en formato YYYY-MM-DD

**Por defecto**: Si no se proporcionan fechas, usa los últimos 30 días.

#### Respuesta

```json
{
  "periodo": {
    "inicio": "2024-01-01",
    "fin": "2024-01-31"
  },
  "metricas_principales": {
    "ingresos_realizados": 1500000,
    "ingresos_proyectados": 500000,
    "ingresos_perdidos": 200000,
    "ingresos_cancelados": 100000,
    "total_ingresos": 2000000
  },
  "citas_por_estado": [
    {
      "estado": "Asistio",
      "cantidad": 25,
      "porcentaje": 50.0
    },
    // ... otros estados
  ],
  "ingresos_por_servicio": [
    {
      "servicio": "Corte de Cabello",
      "total_ingresos": 750000,
      "cantidad_citas": 15
    },
    // ... top 10 servicios
  ],
  "total_citas": 50
}
```

### 2. Optimizaciones Implementadas

#### Una Sola Query Principal
Todas las métricas principales se calculan en **UNA SOLA QUERY** usando `aggregate()`:

```python
metrics = queryset.aggregate(
    ingresos_realizados=Coalesce(Sum('servicios__precio', filter=Q(estado='Asistio')), Value(0)),
    ingresos_proyectados=Coalesce(Sum('servicios__precio', filter=Q(estado__in=['Pendiente', 'Confirmada'])), Value(0)),
    # ... más métricas
)
```

**Ventajas**:
- Reducción de queries a la base de datos
- Mayor velocidad de respuesta
- Menos carga en el servidor

#### Prefetch y Select Related
```python
queryset = Cita.all_objects.select_related(
    'sede',
    'sede__organizacion'
).prefetch_related('servicios')
```

Evita el problema N+1 al cargar relaciones.

### 3. Multi-Tenancy

El endpoint respeta la arquitectura multi-tenant:

- **Superusuarios**: Ven datos de todas las organizaciones
- **Administradores de Organización**: Solo datos de su organización
- **Administradores de Sede**: Solo datos de su organización

#### Lógica de Filtrado

```python
def _apply_organization_filter(self, user):
    # Obtener organización del usuario desde:
    # 1. Perfil
    # 2. Colaborador (si es admin de sede)

    if user_org:
        queryset = queryset.filter(sede__organizacion=user_org)
    else:
        queryset = queryset.none()
```

### 4. Sistema de Permisos

#### IsAdminOrSedeAdmin

Permiso personalizado que permite acceso a:
- Superusuarios
- Administradores de organización
- Administradores de sede

```python
class IsAdminOrSedeAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True

        # Verificar perfil de organización
        # Verificar grupo SedeAdmin
```

## Frontend - Dashboard Financiero

### Ruta
`/financial-dashboard`

### Características

1. **Filtros de Fecha**: Rango personalizable con valores por defecto (últimos 30 días)
2. **Cards de Métricas**:
   - Ingresos Realizados (verde)
   - Ingresos Proyectados (azul)
   - Ingresos Perdidos (amarillo)
   - Ingresos Cancelados (rojo)
3. **Card Total**: Suma de realizados + proyectados con gradiente
4. **Gráfico de Citas por Estado**: Barras de progreso con porcentajes
5. **Top 10 Servicios**: Tabla ordenada por ingresos

### Diseño Consistente

Los estilos siguen el diseño de la aplicación:
- Gradientes: `#457b9d` y `#a8dadc`
- Colores de Bootstrap para estados
- Transiciones suaves y hover effects
- Responsive design

### Formateo de Moneda

```typescript
const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
};
```

Formatea cantidades como: `$ 1.500.000` (pesos colombianos)

## Instalación y Configuración

### Backend

1. La app `reports` ya está agregada a `INSTALLED_APPS` en `core/settings.py`
2. Las URLs están configuradas en `core/urls.py`:
   ```python
   path('api/reports/', include('reports.urls', namespace='reports'))
   ```

### Frontend

1. Componente: `frontend/src/pages/FinancialDashboard.tsx`
2. Estilos: `frontend/src/pages/FinancialDashboard.css`
3. Ruta configurada en `App.tsx` bajo `AdminRoute`
4. Entrada en menú de navegación (Layout.tsx)

## Uso

### Como Administrador

1. Inicia sesión como administrador de organización o sede
2. Ve al menú lateral y selecciona "Dashboard Financiero"
3. Ajusta el rango de fechas si es necesario
4. Visualiza:
   - Métricas principales de ingresos
   - Distribución de citas por estado
   - Servicios más rentables

### Como Desarrollador

#### Ejemplo de petición al endpoint

```javascript
import { getFinancialSummary } from '../api';

const fetchData = async () => {
    const response = await getFinancialSummary('2024-01-01', '2024-01-31');
    console.log(response.data);
};
```

## Métricas Calculadas

| Métrica | Descripción | Estados Incluidos |
|---------|-------------|-------------------|
| Ingresos Realizados | Ingresos de citas completadas | Asistio |
| Ingresos Proyectados | Ingresos esperados de citas futuras | Pendiente, Confirmada |
| Ingresos Perdidos | Ingresos no obtenidos por inasistencias | No Asistio |
| Ingresos Cancelados | Ingresos no obtenidos por cancelaciones | Cancelada |
| Total Ingresos | Suma de realizados + proyectados | - |

## Rendimiento

### Optimizaciones Aplicadas

1. **Una sola query principal** con múltiples agregaciones
2. **Select related** para relaciones ForeignKey
3. **Prefetch related** para relaciones ManyToMany
4. **Limit** en top 10 servicios
5. **Índices** en campos de fecha y organización
6. **Lazy loading** en frontend (React.lazy)

### Tiempos Esperados

- Con ~1000 citas: < 200ms
- Con ~10000 citas: < 500ms
- Con ~100000 citas: < 2s

## Próximas Mejoras

- [ ] Exportar a PDF/Excel
- [ ] Gráficos interactivos con Chart.js o Recharts
- [ ] Comparación con períodos anteriores
- [ ] Proyecciones y tendencias
- [ ] Filtros adicionales (sede, colaborador, servicio)
- [ ] Cache de resultados para períodos cerrados

## Soporte

Para cualquier duda o problema, contacta al equipo de desarrollo.
