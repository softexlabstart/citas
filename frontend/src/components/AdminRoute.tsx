import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const AdminRoute: React.FC = () => {
    const { user } = useAuth();

    if (!user) {
        // Not logged in, redirect to login page
        return <Navigate to="/login" />;
    }

    if (!(user.is_staff || user.perfil?.is_sede_admin || user.groups?.includes('Recurso'))) {
        // Logged in but not allowed, redirect to home page
        return <Navigate to="/" />;
    }

    // Logged in and has access, render the child routes
    return <Outlet />;
};

export default AdminRoute;
