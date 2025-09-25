import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import { Spinner } from 'react-bootstrap'; // Import Spinner
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import RegisterOrganizationPage from './pages/RegisterOrganizationPage';
import OrganizationPage from './pages/OrganizationPage';
import PrivateRoute from './components/PrivateRoute';
import AdminRoute from './components/AdminRoute'; // Import AdminRoute
import { AuthProvider } from './contexts/AuthContext';

// Lazy load components for code splitting
const Home = lazy(() => import('./pages/Home'));
const Services = lazy(() => import('./components/Services'));
const Appointments = lazy(() => import('./components/Appointments'));
const AppointmentsCalendar = lazy(() => import('./components/AppointmentsCalendar'));
const Disponibilidad = lazy(() => import('./components/Disponibilidad'));
const ReportsPage = lazy(() => import('./pages/ReportsPage'));
const AdminSettings = lazy(() => import('./components/AdminSettings'));
const UserGuide = lazy(() => import('./components/UserGuide'));
const RecursoDashboard = lazy(() => import('./components/RecursoDashboard'));
const Clients = lazy(() => import('./components/Clients'));
const MarketingPage = lazy(() => import('./pages/MarketingPage')); // Import MarketingPage
const EditProfilePage = lazy(() => import('./pages/EditProfilePage')); // New lazy-loaded component

// Centered spinner component for Suspense fallback
const CenteredSpinner = () => (
  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
    <Spinner animation="border" role="status">
      <span className="visually-hidden">Cargando...</span>
    </Spinner>
  </div>
);

const App: React.FC = () => {
  return (
    <AuthProvider> 
      <Router>
        <Layout>
          <ToastContainer />
          <Suspense fallback={<CenteredSpinner />}> {/* Use the new spinner component */}
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/register-organization" element={<RegisterOrganizationPage />} />
              
              {/* Routes for all authenticated users */}
              <Route element={<PrivateRoute />}>
                <Route path="/" element={<Home />} />
                <Route path="/appointments" element={<Appointments />} />
                <Route path="/calendar" element={<AppointmentsCalendar />} />
                <Route path="/disponibilidad" element={<Disponibilidad />} />
                <Route path="/organization" element={<OrganizationPage />} />
                <Route path="/user-guide" element={<UserGuide />} />
                <Route path="/recurso-dashboard" element={<RecursoDashboard />} />
                <Route path="/profile/edit" element={<EditProfilePage />} /> {/* New route for editing user profile */}
              </Route>

              {/* Routes for admin users only */}
              <Route element={<AdminRoute />}>
                <Route path="/services" element={<Services />} />
                <Route path="/reports" element={<ReportsPage />} />
                <Route path="/admin-settings" element={<AdminSettings />} />
                <Route path="/clients" element={<Clients />} />
                <Route path="/marketing" element={<MarketingPage />} />
              </Route>
            </Routes>
          </Suspense>
        </Layout>
      </Router>
    </AuthProvider>
  );
};

export default App;
