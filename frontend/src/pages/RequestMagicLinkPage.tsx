import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Container, Row, Col, Card, Form, Button, Alert, InputGroup, Spinner } from 'react-bootstrap';
import { EnvelopeFill, CheckCircleFill } from 'react-bootstrap-icons';
import { requestMagicLink } from '../api';

const RequestMagicLinkPage: React.FC = () => {
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setSuccess(false);

        try {
            await requestMagicLink(email);
            setSuccess(true);
            setEmail(''); // Limpiar el campo
        } catch (err: any) {
            console.error('Error al solicitar magic link:', err);
            setError('Ocurrió un error al procesar tu solicitud. Por favor, inténtalo de nuevo.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container fluid className="p-0 vh-100">
            <Row className="g-0 h-100">
                <Col md={6} className="d-none d-md-flex align-items-center justify-content-center">
                    <div className="text-white text-center p-5">
                        <h1 className="display-4 fw-bold">Acceso sin Contraseña</h1>
                        <p className="lead">Recibe un enlace mágico en tu correo para acceder a tus citas.</p>
                    </div>
                </Col>
                <Col xs={12} md={6} className="d-flex justify-content-center align-items-center">
                    <Card style={{ width: '24rem' }} className="shadow-lg border-0 card-transparent">
                        <Card.Body className="p-5">
                            <Card.Title className="text-center mb-4 h2">
                                Ver Mis Citas
                            </Card.Title>

                            {!success ? (
                                <>
                                    <p className="text-center text-muted mb-4">
                                        Ingresa tu correo electrónico y te enviaremos un enlace para acceder a tu historial de citas.
                                    </p>

                                    {error && <Alert variant="danger">{error}</Alert>}

                                    <Form onSubmit={handleSubmit}>
                                        <Form.Group className="mb-4">
                                            <InputGroup>
                                                <InputGroup.Text><EnvelopeFill /></InputGroup.Text>
                                                <Form.Control
                                                    type="email"
                                                    placeholder="tu@correo.com"
                                                    value={email}
                                                    onChange={(e) => setEmail(e.target.value)}
                                                    required
                                                    disabled={loading}
                                                />
                                            </InputGroup>
                                        </Form.Group>

                                        <div className="d-grid">
                                            <Button
                                                variant="primary"
                                                type="submit"
                                                className="btn-block fw-bold"
                                                disabled={loading}
                                            >
                                                {loading ? (
                                                    <>
                                                        <Spinner
                                                            as="span"
                                                            animation="border"
                                                            size="sm"
                                                            role="status"
                                                            aria-hidden="true"
                                                            className="me-2"
                                                        />
                                                        Enviando...
                                                    </>
                                                ) : (
                                                    'Enviar Enlace Mágico'
                                                )}
                                            </Button>
                                        </div>
                                    </Form>
                                </>
                            ) : (
                                <Alert variant="success" className="text-center">
                                    <CheckCircleFill size={48} className="mb-3" />
                                    <h5>¡Revisa tu correo!</h5>
                                    <p className="mb-0">
                                        Si el correo existe en nuestro sistema, recibirás un enlace para acceder a tus citas.
                                        El enlace es válido por <strong>15 minutos</strong>.
                                    </p>
                                </Alert>
                            )}

                            <hr className="my-4" />

                            <div className="text-center">
                                <p className="mb-2">
                                    ¿Prefieres iniciar sesión con contraseña?
                                </p>
                                <Link to="/login" className="btn btn-outline-secondary w-100">
                                    Iniciar Sesión
                                </Link>
                            </div>

                            <p className="mt-4 text-center">
                                <small className="text-muted">
                                    ¿No tienes cuenta? <Link to="/register">Registrarse</Link>
                                </small>
                            </p>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </Container>
    );
};

export default RequestMagicLinkPage;
