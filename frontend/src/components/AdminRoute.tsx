import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const AdminRoute: React.FC = () => {
    const { user } = useAuth();

    if (!user) {
        // Not logged in, redirect to login page
        return <Navigate to="/login" />;
    }

    if (!user.is_staff) {
        // Logged in but not an admin, redirect to home page
        return <Navigate to="/" />;
    }

    // Logged in and is an admin, render the child routes
    return <Outlet />;
};

export default AdminRoute;
