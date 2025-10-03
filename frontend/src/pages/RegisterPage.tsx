import React, { useState, useEffect } from 'react';
import { register } from '../api';
import { useNavigate, Link, useParams } from 'react-router-dom';
import { RegisterUser } from '../interfaces/User';
import { Container, Row, Col, Card, Form, Button, Alert, InputGroup } from 'react-bootstrap';
import { Person, Lock, Envelope, PersonBadge } from 'react-bootstrap-icons';
import { useTranslation } from 'react-i18next'; // Import useTranslation
import axios from 'axios';

const RegisterPage: React.FC = () => {
    const { t } = useTranslation(); // Initialize useTranslation
    const { organizacionSlug } = useParams<{ organizacionSlug?: string }>();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [email, setEmail] = useState('');
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [hasConsented, setHasConsented] = useState(false); // New state for consent
    const [error, setError] = useState<string | null>(null);
    const [organizacionNombre, setOrganizacionNombre] = useState<string>('');
    const navigate = useNavigate();

    useEffect(() => {
        // Si hay slug de organización, obtener información de la organización
        const fetchOrganizacion = async () => {
            if (organizacionSlug) {
                try {
                    const API_URL = process.env.REACT_APP_API_URL;
                    const response = await axios.get(`${API_URL}/api/organizacion/organizaciones/${organizacionSlug}/`);
                    setOrganizacionNombre(response.data.nombre);
                    setError(null);
                } catch (error: any) {
                    setError('Organización no encontrada. Verifica el enlace de registro.');
                    setOrganizacionNombre('');
                }
            }
        };

        fetchOrganizacion();
    }, [organizacionSlug]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!hasConsented) {
            setError(t('consent_required'));
            return;
        }
        try {
            const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

            if (organizacionSlug) {
                // Registro con organización específica
                const API_URL = process.env.REACT_APP_API_URL;
                const response = await axios.post(`${API_URL}/api/register/${organizacionSlug}/`, {
                    username,
                    password,
                    email,
                    first_name: firstName,
                    last_name: lastName,
                    has_consented_data_processing: hasConsented
                });

                // Si el backend devuelve tokens, guardarlos y redirigir
                if (response.data.tokens) {
                    localStorage.setItem('token', response.data.tokens.access);
                    localStorage.setItem('user', JSON.stringify(response.data.user));
                    navigate('/');
                } else {
                    navigate('/login');
                }
            } else {
                // Registro genérico (sin organización)
                const newUser: RegisterUser = {
                    username,
                    password,
                    email,
                    first_name: firstName,
                    last_name: lastName,
                    timezone,
                    has_consented_data_processing: hasConsented
                };
                await register(newUser);
                navigate('/login');
            }
        } catch (error: any) {
            const errorMessage = error.response?.data?.error || 'Error al registrar. Por favor, verifica tus datos.';
            setError(errorMessage);
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
                            <Card.Title className="text-center mb-4 h2">
                                {t('register')}
                                {organizacionNombre && (
                                    <div className="text-muted fs-6 mt-2">{organizacionNombre}</div>
                                )}
                            </Card.Title>
                            {error && <Alert variant="danger">{error}</Alert>}
                            <Form onSubmit={handleSubmit}>
                                <Form.Group className="mb-3">
                                    <InputGroup>
                                        <InputGroup.Text><Person /></InputGroup.Text>
                                        <Form.Control type="text" placeholder={t('username')} value={username} onChange={(e) => setUsername(e.target.value)} required />
                                    </InputGroup>
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <InputGroup>
                                        <InputGroup.Text><Lock /></InputGroup.Text>
                                        <Form.Control type="password" placeholder={t('password')} value={password} onChange={(e) => setPassword(e.target.value)} required />
                                    </InputGroup>
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <InputGroup>
                                        <InputGroup.Text><Envelope /></InputGroup.Text>
                                        <Form.Control type="email" placeholder={t('email')} value={email} onChange={(e) => setEmail(e.target.value)} required />
                                    </InputGroup>
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <InputGroup>
                                        <InputGroup.Text><PersonBadge /></InputGroup.Text>
                                        <Form.Control type="text" placeholder={t('first_name')} value={firstName} onChange={(e) => setFirstName(e.target.value)} required />
                                    </InputGroup>
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <InputGroup>
                                        <InputGroup.Text><PersonBadge /></InputGroup.Text>
                                        <Form.Control type="text" placeholder={t('last_name')} value={lastName} onChange={(e) => setLastName(e.target.value)} required />
                                    </InputGroup>
                                </Form.Group>

                                {/* Consent Checkbox */}
                                <Form.Group className="mb-3">
                                    <Form.Check 
                                        type="checkbox"
                                        id="dataConsent"
                                        label={<span dangerouslySetInnerHTML={{ __html: t('consent_privacy_policy') }} />}
                                        checked={hasConsented}
                                        onChange={(e) => setHasConsented(e.target.checked)}
                                        required
                                    />
                                </Form.Group>

                                <div className="d-grid">
                                    <Button variant="primary" type="submit" className="btn-block fw-bold">
                                        {t('register')}
                                    </Button>
                                </div>
                            </Form>
                            <p className="mt-4 text-center">
                                {t('already_have_account')} <Link to="/login">{t('login')}</Link>
                            </p>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </Container>
    );
};

export default RegisterPage;
