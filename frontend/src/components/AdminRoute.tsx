import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const AdminRoute: React.FC = () => {
    const { user } = useAuth();

    if (!user) {
        // Not logged in, redirect to login page
        return <Navigate to="/login" />;
    }

    // Excluir explícitamente a colaboradores (grupo Recurso)
    if (user.groups.includes('Recurso')) {
        return <Navigate to="/" />;
    }

    if (!(user.is_staff || user.perfil?.is_sede_admin || user.groups.includes('SedeAdmin'))) {
        // Solo staff y sede admin pueden acceder a rutas administrativas
        return <Navigate to="/" />;
    }

    // Tiene acceso, renderiza las rutas hijas
    return <Outlet />;
};

export default AdminRoute;