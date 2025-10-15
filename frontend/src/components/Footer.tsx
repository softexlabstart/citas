import React, { useState } from 'react';
import { Container, Row, Col } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { EnvelopeFill, TelephoneFill, GeoAltFill } from 'react-bootstrap-icons';
import LegalModal from './LegalModal';

const Footer: React.FC = () => {
    const currentYear = new Date().getFullYear();
    const [showLegalModal, setShowLegalModal] = useState(false);

    return (
        <footer className="bg-dark text-light mt-auto py-4">
            <Container>
                <Row className="g-4">
                    {/* Columna 1: Sobre Nosotros */}
                    <Col md={4}>
                        <h5 className="mb-3">Sistema de Citas</h5>
                        <p className="text-muted small">
                            Plataforma profesional para la gestión de citas, servicios y clientes.
                            Simplifica la administración de tu negocio con tecnología moderna y confiable.
                        </p>
                    </Col>

                    {/* Columna 2: Enlaces Útiles */}
                    <Col md={4}>
                        <h5 className="mb-3">Enlaces Útiles</h5>
                        <ul className="list-unstyled">
                            <li className="mb-2">
                                <Link to="/terms" className="text-muted text-decoration-none">
                                    Términos y Condiciones
                                </Link>
                            </li>
                            <li className="mb-2">
                                <Link to="/privacy-policy" className="text-muted text-decoration-none">
                                    Política de Privacidad
                                </Link>
                            </li>
                            <li className="mb-2">
                                <Link to="/guide" className="text-muted text-decoration-none">
                                    Guía de Usuario
                                </Link>
                            </li>
                            <li className="mb-2">
                                <button
                                    onClick={() => setShowLegalModal(true)}
                                    className="btn btn-link text-muted text-decoration-none p-0"
                                    style={{ textAlign: 'left' }}
                                >
                                    Ley 1581 de 2012
                                </button>
                            </li>
                        </ul>
                    </Col>

                    {/* Columna 3: Contacto */}
                    <Col md={4}>
                        <h5 className="mb-3">Contacto</h5>
                        <ul className="list-unstyled text-muted small">
                            <li className="mb-2">
                                <EnvelopeFill className="me-2" />
                                <a href="mailto:info@softexlab.com" className="text-muted text-decoration-none">
                                    info@softexlab.com
                                </a>
                            </li>
                            <li className="mb-2">
                                <TelephoneFill className="me-2" />
                                <a href="tel:+573193636323" className="text-muted text-decoration-none">
                                    +57 319 363 6323
                                </a>
                            </li>
                            <li className="mb-2">
                                <GeoAltFill className="me-2" />
                                Colombia
                            </li>
                        </ul>
                    </Col>
                </Row>

                <hr className="my-4 bg-secondary" />

                {/* Copyright */}
                <Row>
                    <Col className="text-center">
                        <p className="text-muted small mb-0">
                            &copy; {currentYear} Sistema de Citas. Todos los derechos reservados.
                        </p>
                        <p className="text-muted small mb-0 mt-1">
                            Desarrollado por softexlab
                        </p>
                    </Col>
                </Row>
            </Container>

            {/* Modal de Ley 1581 */}
            <LegalModal show={showLegalModal} onHide={() => setShowLegalModal(false)} />
        </footer>
    );
};

export default Footer;
