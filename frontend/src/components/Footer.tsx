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
                        <h5 className="mb-3 text-white">Sistema de Citas</h5>
                        <p className="text-light small opacity-75">
                            Plataforma profesional para la gestión de citas, servicios y clientes.
                            Simplifica la administración de tu negocio con tecnología moderna y confiable.
                        </p>
                    </Col>

                    {/* Columna 2: Enlaces Útiles */}
                    <Col md={4}>
                        <h5 className="mb-3 text-white">Enlaces Útiles</h5>
                        <ul className="list-unstyled">
                            <li className="mb-2">
                                <Link to="/terms" className="text-light text-decoration-none opacity-75" style={{ transition: 'opacity 0.2s' }} onMouseEnter={(e) => e.currentTarget.style.opacity = '1'} onMouseLeave={(e) => e.currentTarget.style.opacity = '0.75'}>
                                    Términos y Condiciones
                                </Link>
                            </li>
                            <li className="mb-2">
                                <Link to="/privacy-policy" className="text-light text-decoration-none opacity-75" style={{ transition: 'opacity 0.2s' }} onMouseEnter={(e) => e.currentTarget.style.opacity = '1'} onMouseLeave={(e) => e.currentTarget.style.opacity = '0.75'}>
                                    Política de Privacidad
                                </Link>
                            </li>
                            <li className="mb-2">
                                <Link to="/guide" className="text-light text-decoration-none opacity-75" style={{ transition: 'opacity 0.2s' }} onMouseEnter={(e) => e.currentTarget.style.opacity = '1'} onMouseLeave={(e) => e.currentTarget.style.opacity = '0.75'}>
                                    Guía de Usuario
                                </Link>
                            </li>
                            <li className="mb-2">
                                <button
                                    onClick={() => setShowLegalModal(true)}
                                    className="btn btn-link text-light text-decoration-none p-0 opacity-75"
                                    style={{ textAlign: 'left', transition: 'opacity 0.2s' }}
                                    onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
                                    onMouseLeave={(e) => e.currentTarget.style.opacity = '0.75'}
                                >
                                    Ley 1581 de 2012
                                </button>
                            </li>
                        </ul>
                    </Col>

                    {/* Columna 3: Contacto */}
                    <Col md={4}>
                        <h5 className="mb-3 text-white">Contacto</h5>
                        <ul className="list-unstyled small">
                            <li className="mb-2 text-light opacity-75">
                                <EnvelopeFill className="me-2" />
                                <a href="mailto:info@softexlab.com" className="text-light text-decoration-none" style={{ transition: 'opacity 0.2s' }} onMouseEnter={(e) => e.currentTarget.style.opacity = '1'} onMouseLeave={(e) => e.currentTarget.style.opacity = '0.75'}>
                                    info@softexlab.com
                                </a>
                            </li>
                            <li className="mb-2 text-light opacity-75">
                                <TelephoneFill className="me-2" />
                                <a href="tel:+573193636323" className="text-light text-decoration-none" style={{ transition: 'opacity 0.2s' }} onMouseEnter={(e) => e.currentTarget.style.opacity = '1'} onMouseLeave={(e) => e.currentTarget.style.opacity = '0.75'}>
                                    +57 319 363 6323
                                </a>
                            </li>
                            <li className="mb-2 text-light opacity-75">
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
                        <p className="text-light small mb-0 opacity-75">
                            &copy; {currentYear} Sistema de Citas. Todos los derechos reservados.
                        </p>
                        <p className="text-light small mb-0 mt-1 opacity-75">
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
