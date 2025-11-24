import React, { useState } from 'react';
import { Container, Navbar, Nav, Button, Offcanvas, NavDropdown } from 'react-bootstrap';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useTranslation } from 'react-i18next';
import moment from 'moment';
import { HouseDoor, Briefcase, CalendarCheck, CalendarWeek, Gear, QuestionCircle, Search, People, Megaphone, Building, PlusCircle, CurrencyDollar, PersonPlus, Whatsapp } from 'react-bootstrap-icons';
import Footer from './Footer';
import OrganizationSelector from './OrganizationSelector';
import RoleBadge from './RoleBadge';
import { useRolePermissions } from '../hooks/useRolePermissions';
import '../styles/custom.css';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [show, setShow] = useState(false);
  const { t, i18n } = useTranslation();
  const { canManageUsers, canViewReports, isSedeAdminOrHigher, isCliente } = useRolePermissions();

  const handleClose = () => setShow(false);
  const handleShow = () => setShow(true);

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
    moment.locale(lng); // Also update moment's locale
  };

  return (
    <div className="d-flex flex-column min-vh-100">
      {user && (
        <Navbar bg="white" variant="light" expand={false} className="mb-3 shadow-sm" sticky="top" >
          <Container fluid className="navbar-container-custom">
            <div className="navbar-section-left">
              <Navbar.Toggle aria-controls="offcanvasNavbar" onClick={handleShow} />
            </div>
            <div className="navbar-section-center text-center">
              <Navbar.Brand as={Link} to="/" className="fw-bold text-primary">
                {t('system_name')}
              </Navbar.Brand>
            </div>
            <div className="navbar-section-right">
              <Nav className="flex-row align-items-center gap-2">
                {user?.perfil?.role && (
                  <div className="d-none d-md-block">
                    <RoleBadge
                      role={user.perfil.role}
                      additionalRoles={user.perfil.additional_roles as any || []}
                      size="sm"
                    />
                  </div>
                )}
                <OrganizationSelector />
                <NavDropdown title={t('language')} id="language-dropdown" align="end">
                  <NavDropdown.Item onClick={() => changeLanguage('es')}>Español</NavDropdown.Item>
                  <NavDropdown.Item onClick={() => changeLanguage('en')}>English</NavDropdown.Item>
                </NavDropdown>
                <Button variant="outline-danger" onClick={() => logout()} className="ms-2">
                  {t('logout')}
                </Button>
              </Nav>
            </div>

            <Navbar.Offcanvas
              id="offcanvasNavbar"
              aria-labelledby="offcanvasNavbarLabel"
              placement="start"
              show={show}
              onHide={handleClose}
              className="offcanvas-custom"
            >
              <Offcanvas.Header closeButton className="offcanvas-header-custom">
                <Offcanvas.Title id="offcanvasNavbarLabel" className="fw-bold">
                  {t('menu')}
                </Offcanvas.Title>
              </Offcanvas.Header>
              <Offcanvas.Body className="p-0">
                <Nav className="flex-column p-3">
                  <Nav.Link as={Link} to="/" onClick={handleClose} className="nav-link-custom">
                    <HouseDoor className="nav-icon" /> {t('home')}
                  </Nav.Link>

                  {/* Opciones para Clientes */}
                  {isCliente ? (
                    <>
                      <Nav.Link as={Link} to="/appointments" onClick={handleClose} className="nav-link-custom">
                        <CalendarCheck className="nav-icon" /> Mis Citas
                      </Nav.Link>
                      <Nav.Link as={Link} to="/calendar" onClick={handleClose} className="nav-link-custom">
                        <CalendarWeek className="nav-icon" /> Calendario
                      </Nav.Link>
                      <Nav.Link as={Link} to="/availability" onClick={handleClose} className="nav-link-custom">
                        <Search className="nav-icon" /> Agendar Cita
                      </Nav.Link>
                    </>
                  ) : (
                    /* Opciones para Colaboradores y roles superiores */
                    <>
                      <Nav.Link as={Link} to="/services" onClick={handleClose} className="nav-link-custom">
                        <Briefcase className="nav-icon" /> {t('services')}
                      </Nav.Link>
                      <Nav.Link as={Link} to="/appointments" onClick={handleClose} className="nav-link-custom">
                        <CalendarCheck className="nav-icon" /> {t('appointments')}
                      </Nav.Link>
                      <Nav.Link as={Link} to="/calendar" onClick={handleClose} className="nav-link-custom">
                        <CalendarWeek className="nav-icon" /> {t('calendar')}
                      </Nav.Link>
                      <Nav.Link as={Link} to="/availability" onClick={handleClose} className="nav-link-custom">
                        <Search className="nav-icon" /> {t('availability')}
                      </Nav.Link>
                    </>
                  )}

                  {user?.is_superuser && (
                    <>
                      <Nav.Link as={Link} to="/organization" onClick={handleClose} className="nav-link-custom">
                        <Building className="nav-icon" /> Gestionar Organización
                      </Nav.Link>
                      <Nav.Link as={Link} to="/register-organization" onClick={handleClose} className="nav-link-custom">
                        <PlusCircle className="nav-icon" /> Crear Nueva Organización
                      </Nav.Link>
                    </>
                  )}
                  {isSedeAdminOrHigher && (
                    <>
                      <hr className="my-2" />
                      <h6 className="text-muted ps-3 mt-2 mb-1">{t('admin_tools')}</h6>
                      {canManageUsers && (
                        <Nav.Link as={Link} to="/users" onClick={handleClose} className="nav-link-custom">
                          <PersonPlus className="nav-icon" /> Gestión de Usuarios
                        </Nav.Link>
                      )}
                      <Nav.Link as={Link} to="/clients" onClick={handleClose} className="nav-link-custom">
                        <People className="nav-icon" /> {t('clients')}
                      </Nav.Link>
                      <Nav.Link as={Link} to="/marketing" onClick={handleClose} className="nav-link-custom">
                        <Megaphone className="nav-icon" /> {t('marketing')}
                      </Nav.Link>
                      <Nav.Link as={Link} to="/whatsapp-marketing" onClick={handleClose} className="nav-link-custom">
                        <Whatsapp className="nav-icon" /> Marketing WhatsApp
                      </Nav.Link>
                      {canViewReports && (
                        <>
                          <Nav.Link as={Link} to="/reports" onClick={handleClose} className="nav-link-custom">
                            <CurrencyDollar className="nav-icon" /> {t('financial_dashboard') || 'Dashboard Financiero'}
                          </Nav.Link>
                          <Nav.Link as={Link} to="/whatsapp-reports" onClick={handleClose} className="nav-link-custom">
                            <Whatsapp className="nav-icon" /> Reportes WhatsApp
                          </Nav.Link>
                        </>
                      )}
                      <Nav.Link as={Link} to="/admin-settings" onClick={handleClose} className="nav-link-custom">
                        <Gear className="nav-icon" /> {t('admin_settings')}
                      </Nav.Link>
                      <Nav.Link as={Link} to="/guide" onClick={handleClose} className="nav-link-custom">
                        <QuestionCircle className="nav-icon" /> {t('user_guide')}
                      </Nav.Link>
                    </>
                  )}
                </Nav>
              </Offcanvas.Body>
            </Navbar.Offcanvas>
          </Container>
        </Navbar>
      )}
      <Container className="flex-grow-1 mb-4">{children}</Container>
      {location.pathname === '/login' && <Footer />}
    </div>
  );
};

export default Layout;