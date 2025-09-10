import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const PrivateRoute: React.FC = () => {
    const { user } = useAuth();
    const location = useLocation();

    if (!user) {
        return <Navigate to="/login" />;
    }

    const isRecurso = user.groups.includes('Recurso');

    if (location.pathname === '/recurso-dashboard' && !isRecurso) {
        return <Navigate to="/" />;
    }

    return <Outlet />;
};

export default PrivateRoute;
