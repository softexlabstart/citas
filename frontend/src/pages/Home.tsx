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
    if (user?.groups.includes('Recurso')) {
      return <RecursoDashboard />;
    }
    if (user?.is_staff || user?.perfil?.is_sede_admin) {
      return <AdminDashboard data={data as AdminDashboardSummary} />;
    }
    return <UserDashboard data={data as UserDashboardSummary} />;
  };

  return (
    <Container className="mt-4">{renderDashboard()}</Container>
  );
};

export default Home;
