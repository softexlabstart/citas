import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const PrivateRoute: React.FC = () => {
    const { user } = useAuth();
    const location = useLocation();

    if (!user) {
        return <Navigate to="/login" />;
    }

    // NUEVO SISTEMA DE ROLES: Verificar rol de colaborador en lugar de grupo 'Recurso'
    const isColaborador = user?.perfil?.role === 'colaborador';

    if (location.pathname === '/recurso-dashboard' && !isColaborador) {
        return <Navigate to="/" />;
    }

    return <Outlet />;
};

export default PrivateRoute;
