import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import UserDashboard from '../components/UserDashboard';
import RecursoDashboard from '../components/RecursoDashboard';

const HomePage: React.FC = () => {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/login" />;
  }

  if (user.is_staff || user.perfil?.is_sede_admin) {
    return <Navigate to="/reports" />;
  }

  if (user.groups.includes('Recurso') || user.groups.includes('Colaborador')) {
    return <RecursoDashboard />;
  }

  return <UserDashboard />;
};

export default HomePage;
