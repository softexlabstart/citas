import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useNavigate, Link } from 'react-router-dom';
import { Container, Row, Col, Card, Form, Button, Alert, InputGroup } from 'react-bootstrap';
import { Person, Lock } from 'react-bootstrap-icons';

const LoginPage: React.FC = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const { user, login } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        if (user) {
            navigate('/');
        }
    }, [user, navigate]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await login(username, password);
            navigate('/');
        } catch (error) {
            setError('Credenciales incorrectas. Por favor, inténtalo de nuevo.');
            console.error('Failed to login', error);
        }
    };

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
                            <Card.Title className="text-center mb-4 h2">Iniciar Sesión</Card.Title>
                            {error && <Alert variant="danger">{error}</Alert>}
                            <Form onSubmit={handleSubmit}>
                                <Form.Group className="mb-4">
                                    <InputGroup>
                                        <InputGroup.Text><Person /></InputGroup.Text>
                                        <Form.Control
                                            type="text"
                                            placeholder="Usuario"
                                            value={username}
                                            onChange={(e) => setUsername(e.target.value)}
                                            required
                                        />
                                    </InputGroup>
                                </Form.Group>

                                <Form.Group className="mb-4">
                                    <InputGroup>
                                        <InputGroup.Text><Lock /></InputGroup.Text>
                                        <Form.Control
                                            type="password"
                                            placeholder="Contraseña"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            required
                                        />
                                    </InputGroup>
                                </Form.Group>

                                <div className="d-grid">
                                    <Button variant="primary" type="submit" className="btn-block fw-bold">
                                        Iniciar Sesión
                                    </Button>
                                </div>
                            </Form>
                            <p className="mt-4 text-center">
                                ¿No tienes cuenta? <Link to="/register">Registrarse</Link>
                            </p>
                            <p className="text-center">
                                <Link to="/register-organization" className="text-primary fw-bold">
                                    Crear Nueva Organización
                                </Link>
                            </p>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </Container>
    );
};

export default LoginPage;
