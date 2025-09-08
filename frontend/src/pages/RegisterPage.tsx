import React, { useState } from 'react';
import { register } from '../api';
import { useNavigate, Link } from 'react-router-dom';
import { RegisterUser } from '../interfaces/User';
import { Container, Row, Col, Card, Form, Button, Alert, InputGroup } from 'react-bootstrap';
import { Person, Lock, Envelope, PersonBadge } from 'react-bootstrap-icons';

const RegisterPage: React.FC = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [email, setEmail] = useState('');
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
            const newUser: RegisterUser = { username, password, email, first_name: firstName, last_name: lastName, timezone };
            await register(newUser);
            navigate('/login');
        } catch (error) {
            setError('Error al registrar. Por favor, verifica tus datos.');
            console.error('Failed to register', error);
        }
    };

    return (
        <Container fluid className="p-0 vh-100">
            <Row className="g-0 h-100">
                <Col md={6} className="d-none d-md-flex align-items-center justify-content-center">
                    <div className="text-white text-center p-5">
                        <h1 className="display-4 fw-bold">Citas Médicas</h1>
                        <p className="lead">Regístrate para gestionar tus citas.</p>
                    </div>
                </Col>
                <Col xs={12} md={6} className="d-flex justify-content-center align-items-center">
                    <Card style={{ width: '24rem' }} className="shadow-lg border-0 card-transparent">
                        <Card.Body className="p-5">
                            <Card.Title className="text-center mb-4 h2">Registrarse</Card.Title>
                            {error && <Alert variant="danger">{error}</Alert>}
                            <Form onSubmit={handleSubmit}>
                                <Form.Group className="mb-3">
                                    <InputGroup>
                                        <InputGroup.Text><Person /></InputGroup.Text>
                                        <Form.Control type="text" placeholder="Usuario" value={username} onChange={(e) => setUsername(e.target.value)} required />
                                    </InputGroup>
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <InputGroup>
                                        <InputGroup.Text><Lock /></InputGroup.Text>
                                        <Form.Control type="password" placeholder="Contraseña" value={password} onChange={(e) => setPassword(e.target.value)} required />
                                    </InputGroup>
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <InputGroup>
_                                        <InputGroup.Text><Envelope /></InputGroup.Text>
                                        <Form.Control type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
                                    </InputGroup>
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <InputGroup>
                                        <InputGroup.Text><PersonBadge /></InputGroup.Text>
                                        <Form.Control type="text" placeholder="Nombre" value={firstName} onChange={(e) => setFirstName(e.target.value)} required />
                                    </InputGroup>
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <InputGroup>
                                        <InputGroup.Text><PersonBadge /></InputGroup.Text>
                                        <Form.Control type="text" placeholder="Apellido" value={lastName} onChange={(e) => setLastName(e.target.value)} required />
                                    </InputGroup>
                                </Form.Group>

                                <div className="d-grid">
                                    <Button variant="primary" type="submit" className="btn-block fw-bold">
                                        Registrarse
                                    </Button>
                                </div>
                            </Form>
                            <p className="mt-4 text-center">
                                ¿Ya tienes cuenta? <Link to="/login">Iniciar Sesión</Link>
                            </p>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </Container>
    );
};

export default RegisterPage;
