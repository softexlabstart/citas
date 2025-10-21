import React, { useEffect } from 'react';
import { Container, Spinner, Alert } from 'react-bootstrap';
import { useAuth } from '../hooks/useAuth';
import { useTranslation } from 'react-i18next';
import { useApi } from '../hooks/useApi';
import { getDashboardSummary, DashboardSummary, AdminDashboardSummary, UserDashboardSummary } from '../api';
import AdminDashboard from '../components/AdminDashboard';
import UserDashboard from '../components/UserDashboard';
import RecursoDashboard from '../components/RecursoDashboard';

const Home: React.FC = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const { data, loading, error, request: fetchSummary } = useApi<DashboardSummary, []>(getDashboardSummary);

  useEffect(() => {
    fetchSummary();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const renderDashboard = () => {
    if (loading) {
      return <div className="text-center"><Spinner animation="border" /></div>;
    }
    if (error) {
      return <Alert variant="danger">{t(error)}</Alert>;
    }
    if (!data) {
      return null;
    }

    // NUEVO SISTEMA DE ROLES: Usar user.perfil.role en lugar de groups
    const userRole = user?.perfil?.role;

    // Superusuario siempre ve el dashboard de admin
    if (user?.is_superuser) {
      return <AdminDashboard data={data as AdminDashboardSummary} />;
    }

    // Determinar dashboard según el rol
    switch (userRole) {
      case 'owner':
      case 'admin':
      case 'sede_admin':
        return <AdminDashboard data={data as AdminDashboardSummary} />;

      case 'colaborador':
        return <RecursoDashboard />;

      case 'cliente':
      default:
        return <UserDashboard data={data as UserDashboardSummary} />;
    }
  };

  return (
    <Container className="mt-4">{renderDashboard()}</Container>
  );
};

export default Home;
