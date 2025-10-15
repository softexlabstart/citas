import React, { useState } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { EnvelopeFill, CheckCircleFill } from 'react-bootstrap-icons';
import { requestPasswordReset } from '../api';

const ForgotPasswordPage: React.FC = () => {
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            await requestPasswordReset(email);
            setSuccess(true);
        } catch (err: any) {
            setError(err.response?.data?.error || 'Ocurrió un error. Por favor, intenta nuevamente.');
        } finally {
            setLoading(false);
        }
    };

    if (success) {
        return (
            <Container fluid className="p-0 vh-100">
                <Row className="g-0 h-100">
                    <Col md={6} className="d-none d-md-flex align-items-center justify-content-center">
                        <div className="text-white text-center p-5">
                            <h1 className="display-4 fw-bold">Sistema de Citas</h1>
                            <p className="lead">Una solución completa para la gestión de citas.</p>
                        </div>
                    </Col>
                    <Col xs={12} md={6} className="d-flex justify-content-center align-items-center">
                        <Card style={{ width: '24rem' }} className="shadow-lg border-0 card-transparent">
                            <Card.Body className="p-5 text-center">
                                <CheckCircleFill size={64} className="text-success mb-4" />
                                <Card.Title className="mb-4 h2">Correo Enviado</Card.Title>
                                <p className="text-muted">
                                    Si el correo está registrado, recibirás un enlace para restablecer tu contraseña en los próximos minutos.
                                </p>
                                <p className="text-muted small">
                                    Revisa tu bandeja de entrada y la carpeta de spam.
                                </p>
                                <Link to="/login">
                                    <Button variant="primary" className="mt-3 w-100">
                                        Volver al Inicio de Sesión
                                    </Button>
                                </Link>
                            </Card.Body>
                        </Card>
                    </Col>
                </Row>
            </Container>
        );
    }

    return (
        <Container fluid className="p-0 vh-100">
            <Row className="g-0 h-100">
                <Col md={6} className="d-none d-md-flex align-items-center justify-content-center">
                    <div className="text-white text-center p-5">
                        <h1 className="display-4 fw-bold">Sistema de Citas</h1>
                        <p className="lead">Una solución completa para la gestión de citas.</p>
                    </div>
                </Col>
                <Col xs={12} md={6} className="d-flex justify-content-center align-items-center">
                    <Card style={{ width: '24rem' }} className="shadow-lg border-0 card-transparent">
                        <Card.Body className="p-5">
                            <Card.Title className="text-center mb-4 h2">Recuperar Contraseña</Card.Title>
                            <p className="text-center text-muted mb-4">
                                Ingresa tu correo electrónico y te enviaremos un enlace para restablecer tu contraseña.
                            </p>
                            {error && <Alert variant="danger">{error}</Alert>}
                            <Form onSubmit={handleSubmit}>
                                <Form.Group className="mb-4">
                                    <Form.Label>Correo Electrónico</Form.Label>
                                    <div className="input-group">
                                        <span className="input-group-text">
                                            <EnvelopeFill />
                                        </span>
                                        <Form.Control
                                            type="email"
                                            placeholder="tu@email.com"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            required
                                        />
                                    </div>
                                </Form.Group>

                                <div className="d-grid">
                                    <Button
                                        variant="primary"
                                        type="submit"
                                        className="fw-bold"
                                        disabled={loading}
                                    >
                                        {loading ? 'Enviando...' : 'Enviar Enlace de Recuperación'}
                                    </Button>
                                </div>
                            </Form>

                            <div className="text-center mt-4">
                                <Link to="/login" className="text-decoration-none">
                                    <small>Volver al inicio de sesión</small>
                                </Link>
                            </div>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </Container>
    );
};

export default ForgotPasswordPage;
