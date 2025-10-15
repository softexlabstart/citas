import React, { useState } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert } from 'react-bootstrap';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { LockFill, CheckCircleFill } from 'react-bootstrap-icons';
import { confirmPasswordReset } from '../api';

const ResetPasswordPage: React.FC = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const token = searchParams.get('token');

    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!token) {
            setError('Token inválido o faltante.');
            return;
        }

        if (password !== confirmPassword) {
            setError('Las contraseñas no coinciden.');
            return;
        }

        if (password.length < 6) {
            setError('La contraseña debe tener al menos 6 caracteres.');
            return;
        }

        setLoading(true);

        try {
            await confirmPasswordReset(token, password);
            setSuccess(true);
            setTimeout(() => {
                navigate('/login');
            }, 3000);
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
                                <Card.Title className="mb-4 h2">Contraseña Restablecida</Card.Title>
                                <p className="text-muted">
                                    Tu contraseña ha sido restablecida exitosamente.
                                </p>
                                <p className="text-muted small">
                                    Serás redirigido al inicio de sesión en unos segundos...
                                </p>
                                <Link to="/login">
                                    <Button variant="primary" className="mt-3 w-100">
                                        Ir al Inicio de Sesión
                                    </Button>
                                </Link>
                            </Card.Body>
                        </Card>
                    </Col>
                </Row>
            </Container>
        );
    }

    if (!token) {
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
                                <Alert variant="danger">
                                    El enlace de recuperación es inválido o ha expirado.
                                </Alert>
                                <Link to="/forgot-password">
                                    <Button variant="primary" className="w-100">
                                        Solicitar Nuevo Enlace
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
                            <Card.Title className="text-center mb-4 h2">Nueva Contraseña</Card.Title>
                            <p className="text-center text-muted mb-4">
                                Ingresa tu nueva contraseña.
                            </p>
                            {error && <Alert variant="danger">{error}</Alert>}
                            <Form onSubmit={handleSubmit}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Nueva Contraseña</Form.Label>
                                    <div className="input-group">
                                        <span className="input-group-text">
                                            <LockFill />
                                        </span>
                                        <Form.Control
                                            type="password"
                                            placeholder="Mínimo 6 caracteres"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            required
                                        />
                                    </div>
                                </Form.Group>

                                <Form.Group className="mb-4">
                                    <Form.Label>Confirmar Contraseña</Form.Label>
                                    <div className="input-group">
                                        <span className="input-group-text">
                                            <LockFill />
                                        </span>
                                        <Form.Control
                                            type="password"
                                            placeholder="Confirma tu contraseña"
                                            value={confirmPassword}
                                            onChange={(e) => setConfirmPassword(e.target.value)}
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
                                        {loading ? 'Restableciendo...' : 'Restablecer Contraseña'}
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

export default ResetPasswordPage;
