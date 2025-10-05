import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import UserDashboard from '../components/UserDashboard';
import AdminDashboard from '../components/AdminDashboard';
import RecursoDashboard from '../components/RecursoDashboard';
import { getDashboardSummary, UserDashboardSummary, AdminDashboardSummary } from '../api';
import { useTranslation } from 'react-i18next';

const HomePage: React.FC = () => {
  const { user } = useAuth();
  const { t } = useTranslation();
  const [dashboardData, setDashboardData] = useState<UserDashboardSummary | AdminDashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const response = await getDashboardSummary();
        setDashboardData(response.data);
      } catch (err) {
        setError(t('error_fetching_dashboard_data'));
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      const isColaborador = user.groups.includes('Recurso') || user.groups.includes('Colaborador');
      const isAdmin = !isColaborador && (user.is_staff || user.perfil?.is_sede_admin || (user.perfil?.sedes_administradas && user.perfil.sedes_administradas.length > 0));

      if (isAdmin || !isColaborador) {
        fetchDashboardData();
      } else {
        setLoading(false); // It's a colaborador but not an admin, no data needed for RecursoDashboard
      }
    } else {
      setLoading(false);
    }
  }, [user, t]);

  if (!user) {
    return <Navigate to="/login" />;
  }

  const isColaborador = user.groups.includes('Recurso') || user.groups.includes('Colaborador');
  const isAdmin = !isColaborador && (user.is_staff || user.perfil?.is_sede_admin || (user.perfil?.sedes_administradas && user.perfil.sedes_administradas.length > 0));

  if (loading) {
    return <div>{t('loading')}...</div>;
  }

  if (error) {
    return <div className="alert alert-danger">{error}</div>;
  }

  if (isColaborador) {
    return <RecursoDashboard />;
  }

  if (isAdmin) {
    if (dashboardData) {
      return <AdminDashboard data={dashboardData as AdminDashboardSummary} />;
    }
    return null; // Data is loading or there was an error, handled above
  }

  if (dashboardData) {
    return <UserDashboard data={dashboardData as UserDashboardSummary} />;
  }

  return null; // Or some other fallback UI
};

export default HomePage;
