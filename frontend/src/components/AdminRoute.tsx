import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useRolePermissions } from '../hooks/useRolePermissions';

/**
 * AdminRoute - Protege rutas que solo deben ser accesibles por:
 * - Propietarios (owner)
 * - Administradores (admin)
 * - Administradores de Sede (sede_admin)
 */
const AdminRoute: React.FC = () => {
    const { user } = useAuth();
    const { isSedeAdminOrHigher } = useRolePermissions();

    if (!user) {
        // No está autenticado, redirigir al login
        return <Navigate to="/login" />;
    }

    // Verificar si tiene permisos administrativos
    const isAuthorized = user.is_superuser || isSedeAdminOrHigher;

    if (!isAuthorized) {
        // No tiene permisos administrativos, redirigir al home
        return <Navigate to="/" />;
    }

    // Tiene acceso, renderiza las rutas hijas
    return <Outlet />;
};

export default AdminRoute;