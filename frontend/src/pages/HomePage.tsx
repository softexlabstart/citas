import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import UserDashboard from '../components/UserDashboard';
import AdminDashboard from '../components/AdminDashboard'; // Import AdminDashboard
import RecursoDashboard from '../components/RecursoDashboard';
import { getDashboardSummary, UserDashboardSummary, AdminDashboardSummary } from '../api'; // Import AdminDashboardSummary
import { useTranslation } from 'react-i18next';

const HomePage: React.FC = () => {
  const { user } = useAuth();
  const { t } = useTranslation();
  const [dashboardData, setDashboardData] = useState<UserDashboardSummary | AdminDashboardSummary | null>(null); // Update state type
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

    if (user && !user.groups.includes('Recurso') && !user.groups.includes('Colaborador')) {
      fetchDashboardData();
    } else {
      setLoading(false);
    }
  }, [user, t]);

  if (!user) {
    return <Navigate to="/login" />;
  }

  if (loading) {
    return <div>{t('loading')}...</div>;
  }

  if (error) {
    return <div className="alert alert-danger">{error}</div>;
  }

  if (user.groups.includes('Recurso') || user.groups.includes('Colaborador')) {
    return <RecursoDashboard />;
  }

  if (dashboardData) {
    if (user.is_staff || user.perfil?.is_sede_admin) {
      return <AdminDashboard data={dashboardData as AdminDashboardSummary} />;
    }
    return <UserDashboard data={dashboardData as UserDashboardSummary} />;
  }

  return null; // Or some other fallback UI
};

export default HomePage;
