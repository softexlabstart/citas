import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { Container, Row, Col, Card, Alert, Spinner } from 'react-bootstrap';
import { CheckCircleFill, XCircleFill } from 'react-bootstrap-icons';
import { useAuth } from '../hooks/useAuth';

const MagicLinkAuthPage: React.FC = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const { loginWithMagicLink, user } = useAuth();
    const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
    const [errorMessage, setErrorMessage] = useState('');

    useEffect(() => {
        // Si ya hay un usuario autenticado, redirigir al home
        if (user) {
            navigate('/');
            return;
        }

        const token = searchParams.get('token');

        if (!token) {
            setStatus('error');
            setErrorMessage('No se proporcionó un token válido. Por favor, solicita un nuevo enlace.');
            return;
        }

        const authenticateUser = async () => {
            try {
                await loginWithMagicLink(token);
                setStatus('success');
                // Redirigir al home después de 2 segundos
                setTimeout(() => {
                    navigate('/');
                }, 2000);
            } catch (error: any) {
                console.error('Error al autenticar con magic link:', error);
                setStatus('error');

                if (error.response?.status === 400) {
                    setErrorMessage(
                        error.response?.data?.error ||
                        'El enlace ha expirado o ya fue utilizado. Por favor, solicita un nuevo enlace.'
                    );
                } else {
                    setErrorMessage('Ocurrió un error al procesar tu solicitud. Por favor, inténtalo de nuevo.');
                }
            }
        };

        authenticateUser();
    }, [searchParams, loginWithMagicLink, navigate, user]);

    return (
        <Container fluid className="p-0 vh-100">
            <Row className="g-0 h-100">
                <Col md={6} className="d-none d-md-flex align-items-center justify-content-center">
                    <div className="text-white text-center p-5">
                        <h1 className="display-4 fw-bold">Acceso Seguro</h1>
                        <p className="lead">Verificando tu enlace mágico...</p>
                    </div>
                </Col>
                <Col xs={12} md={6} className="d-flex justify-content-center align-items-center">
                    <Card style={{ width: '24rem' }} className="shadow-lg border-0 card-transparent">
                        <Card.Body className="p-5">
                            {status === 'loading' && (
                                <div className="text-center">
                                    <Spinner animation="border" variant="primary" className="mb-3" />
                                    <h5>Autenticando...</h5>
                                    <p className="text-muted">
                                        Por favor, espera mientras verificamos tu enlace.
                                    </p>
                                </div>
                            )}

                            {status === 'success' && (
                                <Alert variant="success" className="text-center">
                                    <CheckCircleFill size={64} className="mb-3 text-success" />
                                    <h4>¡Autenticación Exitosa!</h4>
                                    <p className="mb-0">
                                        Has iniciado sesión correctamente. Redirigiendo...
                                    </p>
                                </Alert>
                            )}

                            {status === 'error' && (
                                <>
                                    <Alert variant="danger" className="text-center">
                                        <XCircleFill size={64} className="mb-3 text-danger" />
                                        <h4>Error de Autenticación</h4>
                                        <p className="mb-0">{errorMessage}</p>
                                    </Alert>

                                    <hr className="my-4" />

                                    <div className="d-grid gap-2">
                                        <Link to="/mis-citas" className="btn btn-primary">
                                            Solicitar Nuevo Enlace
                                        </Link>
                                        <Link to="/login" className="btn btn-outline-secondary">
                                            Iniciar Sesión con Contraseña
                                        </Link>
                                    </div>
                                </>
                            )}
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </Container>
    );
};

export default MagicLinkAuthPage;
