import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import UserDashboard from '../components/UserDashboard';
import RecursoDashboard from '../components/RecursoDashboard';
import { getDashboardSummary, UserDashboardSummary } from '../api';
import { useTranslation } from 'react-i18next';

const HomePage: React.FC = () => {
  const { user } = useAuth();
  const { t } = useTranslation();
  const [dashboardData, setDashboardData] = useState<UserDashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user && !user.is_staff && !user.perfil?.is_sede_admin && !user.groups.includes('Recurso') && !user.groups.includes('Colaborador')) {
      const fetchDashboardData = async () => {
        try {
          setLoading(true);
          const response = await getDashboardSummary();
          setDashboardData(response.data as UserDashboardSummary);
        } catch (err) {
          setError(t('error_fetching_dashboard_data'));
        } finally {
          setLoading(false);
        }
      };
      fetchDashboardData();
    } else {
      setLoading(false);
    }
  }, [user, t]);

  if (!user) {
    return <Navigate to="/login" />;
  }

  if (user.is_staff || user.perfil?.is_sede_admin) {
    return <Navigate to="/appointments" />;
  }

  if (user.groups.includes('Recurso') || user.groups.includes('Colaborador')) {
    return <RecursoDashboard />;
  }

  if (loading) {
    return <div>{t('loading')}...</div>;
  }

  if (error) {
    return <div className="alert alert-danger">{error}</div>;
  }

  if (dashboardData) {
    return <UserDashboard data={dashboardData} />;
  }

  return null; // Or some other fallback UI
};

export default HomePage;
