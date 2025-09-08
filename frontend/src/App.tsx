import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import Home from './pages/Home';
import Services from './components/Services';
import Appointments from './components/Appointments';
import AppointmentsCalendar from './components/AppointmentsCalendar';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import PrivateRoute from './components/PrivateRoute';
import Disponibilidad from './components/Disponibilidad';
import ReportsPage from './pages/ReportsPage'; // Importar ReportsPage
import { AuthProvider } from './contexts/AuthContext'; // Importar AuthProvider
import AdminSettings from './components/AdminSettings';
import UserGuide from './components/UserGuide';

const App: React.FC = () => {
  return (
    <AuthProvider> {/* Envolver la aplicación con AuthProvider */}
      <Router>
        <Layout>
          <ToastContainer />
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route element={<PrivateRoute />}>
              <Route path="/" element={<Home />} />
              <Route path="/services" element={<Services />} />
              <Route path="/appointments" element={<Appointments />} />
              <Route path="/calendar" element={<AppointmentsCalendar />} />
              <Route path="/disponibilidad" element={<Disponibilidad />} />
              <Route path="/reports" element={<ReportsPage />} /> {/*ruta para informes */}
              <Route path="/admin-settings" element={<AdminSettings />} />
              <Route path="/user-guide" element={<UserGuide />} />
            </Route>
          </Routes>
        </Layout>
      </Router>
    </AuthProvider>
  );
};

export default App;
