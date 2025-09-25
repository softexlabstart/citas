import React, { useState } from 'react';
import { Container, Navbar, Nav, Button, Offcanvas, NavDropdown } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useTranslation } from 'react-i18next';
import moment from 'moment';
import { HouseDoor, Briefcase, CalendarCheck, CalendarWeek, BarChart, Gear, QuestionCircle, Search, People, Megaphone, Building } from 'react-bootstrap-icons';
import '../styles/custom.css';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, logout } = useAuth();
  console.log('User object in Layout:', user); // Add this line
  const [show, setShow] = useState(false);
  const { t, i18n } = useTranslation();

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
              <Nav className="flex-row align-items-center">
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
                  <Nav.Link as={Link} to="/services" onClick={handleClose} className="nav-link-custom">
                    <Briefcase className="nav-icon" /> {t('services')}
                  </Nav.Link>
                  <Nav.Link as={Link} to="/appointments" onClick={handleClose} className="nav-link-custom">
                    <CalendarCheck className="nav-icon" /> {t('appointments')}
                  </Nav.Link>
                  <Nav.Link as={Link} to="/calendar" onClick={handleClose} className="nav-link-custom">
                    <CalendarWeek className="nav-icon" /> {t('calendar')}
                  </Nav.Link>
                  <Nav.Link as={Link} to="/disponibilidad" onClick={handleClose} className="nav-link-custom">
                    <Search className="nav-icon" /> {t('availability')}
                  </Nav.Link>
                  {user?.is_staff && (
                    <Nav.Link as={Link} to="/organization" onClick={handleClose} className="nav-link-custom">
                      <Building className="nav-icon" /> Organización
                    </Nav.Link>
                  )}
                  {(user?.is_staff || user?.perfil?.is_sede_admin || user?.groups.includes('SedeAdmin')) && (
                    <>
                      <hr className="my-2" />
                      <h6 className="text-muted ps-3 mt-2 mb-1">{t('admin_tools')}</h6>
                      <Nav.Link as={Link} to="/clients" onClick={handleClose} className="nav-link-custom">
                        <People className="nav-icon" /> {t('clients')}
                      </Nav.Link>
                      <Nav.Link as={Link} to="/marketing" onClick={handleClose} className="nav-link-custom">
                        <Megaphone className="nav-icon" /> {t('marketing')}
                      </Nav.Link>
                      <Nav.Link as={Link} to="/reports" onClick={handleClose} className="nav-link-custom">
                        <BarChart className="nav-icon" /> {t('reports')}
                      </Nav.Link>
                      <Nav.Link as={Link} to="/admin-settings" onClick={handleClose} className="nav-link-custom">
                        <Gear className="nav-icon" /> {t('admin_settings')}
                      </Nav.Link>
                      <Nav.Link as={Link} to="/user-guide" onClick={handleClose} className="nav-link-custom">
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
      <footer className="footer mt-auto py-3 bg-dark text-white border-top">
        <Container className="text-center">
          <span>© {new Date().getFullYear()} Softex-labs. {t('all_rights_reserved')}.</span>
        </Container>
      </footer>
    </div>
  );
};

export default Layout;