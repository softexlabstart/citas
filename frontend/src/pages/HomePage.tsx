import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { Container, Row, Col, Button } from 'react-bootstrap';
import { useAuth } from '../contexts/AuthContext';
import UserDashboard from '../components/UserDashboard';
import AdminDashboard from '../components/AdminDashboard';
import RecursoDashboard from '../components/RecursoDashboard';
import OnboardingWizard from '../components/OnboardingWizard';
import { getDashboardSummary, UserDashboardSummary, AdminDashboardSummary } from '../api';
import { useTranslation } from 'react-i18next';
import { useOnboarding } from '../hooks/useOnboarding';
import OnboardingChecklist from '../components/OnboardingChecklist';

const HomePage: React.FC = () => {
  const { user } = useAuth();
  const { t } = useTranslation();
  const [dashboardData, setDashboardData] = useState<UserDashboardSummary | AdminDashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showWizard, setShowWizard] = useState(false);
  const { progress, shouldShowOnboarding } = useOnboarding();

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const response = await getDashboardSummary();
        setDashboardData(response.data);
      } catch (err: any) {
        // Solo mostrar error si NO es 401 (no autorizado es esperado al cargar)
        if (err.response?.status !== 401) {
          setError(t('error_fetching_dashboard_data'));
        }
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

  // Auto-show wizard for new users
  useEffect(() => {
    if (progress && shouldShowOnboarding) {
      setShowWizard(true);
    }
  }, [progress]);

  if (!user) {
    return <Navigate to="/login" />;
  }

  const isColaborador = user.groups.includes('Recurso') || user.groups.includes('Colaborador');
  const isAdmin = !isColaborador && (user.is_staff || user.perfil?.is_sede_admin || (user.perfil?.sedes_administradas && user.perfil.sedes_administradas.length > 0));
  const isCliente = user.perfil?.role === 'cliente';

  if (loading) {
    return <div>{t('loading')}...</div>;
  }

  if (error) {
    return <div className="alert alert-danger">{error}</div>;
  }

  // Dashboard para Clientes
  if (isCliente) {
    return (
      <Container>
        <Row>
          <Col lg={12}>
            <h2>Bienvenido, {user.first_name || user.username}!</h2>
            <p className="text-muted">Desde aquí puedes ver y gestionar tus citas.</p>
            <div className="alert alert-info mt-3">
              <h5>Panel de Cliente</h5>
              <p>Utiliza el menú para:</p>
              <ul>
                <li>Ver tus citas programadas</li>
                <li>Agendar nuevas citas</li>
                <li>Gestionar tu perfil</li>
              </ul>
            </div>
          </Col>
        </Row>
      </Container>
    );
  }

  if (isColaborador) {
    return <RecursoDashboard />;
  }

  if (isAdmin) {
    if (dashboardData) {
      return (
        <Container>
          <Row>
            <Col lg={12}>
              <OnboardingChecklist />
            </Col>
          </Row>
          <AdminDashboard data={dashboardData as AdminDashboardSummary} />
        </Container>
      );
    }
    return null; // Data is loading or there was an error, handled above
  }

  if (dashboardData) {
    return (
      <Container>
        <Row>
          <Col lg={12}>
            <OnboardingChecklist />
          </Col>
        </Row>
        <UserDashboard data={dashboardData as UserDashboardSummary} />
      </Container>
    );
  }

  return null; // Or some other fallback UI
};

export default HomePage;
