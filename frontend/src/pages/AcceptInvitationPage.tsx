import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Container, Card, Form, Button, Alert, Spinner } from 'react-bootstrap';
import { toast } from 'react-toastify';
import { getInvitationDetails, acceptInvitation } from '../api';

interface InvitationDetails {
    is_valid: boolean;
    invitation?: {
        email: string;
        organization_name: string;
        role: string;
        role_display: string;
        sede_name: string | null;
        sender_name: string;
        first_name: string;
        last_name: string;
        expires_at: string;
    };
    error?: string;
}

const AcceptInvitationPage: React.FC = () => {
    const { token } = useParams<{ token: string }>();
    const navigate = useNavigate();

    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [invitationDetails, setInvitationDetails] = useState<InvitationDetails | null>(null);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');

    useEffect(() => {
        loadInvitationDetails();
    }, [token]);

    const loadInvitationDetails = async () => {
        if (!token) {
            setLoading(false);
            return;
        }

        try {
            const response = await getInvitationDetails(token);
            setInvitationDetails(response.data);

            if (response.data.is_valid && response.data.invitation) {
                // Pre-llenar nombre y apellido si vienen en la invitación
                setFirstName(response.data.invitation.first_name || '');
                setLastName(response.data.invitation.last_name || '');
                // Sugerir username basado en email
                const emailUsername = response.data.invitation.email.split('@')[0];
                setUsername(emailUsername);
            }
        } catch (error: any) {
            console.error('Error loading invitation:', error);
            toast.error('Error al cargar la invitación');
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (password !== confirmPassword) {
            toast.error('Las contraseñas no coinciden');
            return;
        }

        if (password.length < 8) {
            toast.error('La contraseña debe tener al menos 8 caracteres');
            return;
        }

        if (!token) return;

        setSubmitting(true);

        try {
            await acceptInvitation(token, {
                username,
                password,
                first_name: firstName,
                last_name: lastName
            });

            toast.success('¡Cuenta creada exitosamente! Ahora puedes iniciar sesión.');

            // Redirigir al login después de 2 segundos
            setTimeout(() => {
                navigate('/login');
            }, 2000);
        } catch (error: any) {
            console.error('Error accepting invitation:', error);
            const errorMessage = error.response?.data?.error || 'Error al crear la cuenta';
            toast.error(errorMessage);
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) {
        return (
            <Container className="py-5">
                <div className="text-center">
                    <Spinner animation="border" role="status">
                        <span className="visually-hidden">Cargando...</span>
                    </Spinner>
                    <p className="mt-3">Verificando invitación...</p>
                </div>
            </Container>
        );
    }

    if (!invitationDetails?.is_valid || !invitationDetails.invitation) {
        return (
            <Container className="py-5">
                <Card className="mx-auto" style={{ maxWidth: '500px' }}>
                    <Card.Body className="text-center">
                        <div className="text-danger mb-3">
                            <i className="bi bi-exclamation-triangle" style={{ fontSize: '3rem' }}></i>
                        </div>
                        <h3>Invitación Inválida</h3>
                        <p className="text-muted">
                            {invitationDetails?.error || 'Esta invitación ha expirado o ya ha sido utilizada.'}
                        </p>
                        <Button variant="primary" onClick={() => navigate('/login')}>
                            Ir al Login
                        </Button>
                    </Card.Body>
                </Card>
            </Container>
        );
    }

    const { invitation } = invitationDetails;

    return (
        <Container className="py-5">
            <Card className="mx-auto" style={{ maxWidth: '600px' }}>
                <Card.Header className="bg-primary text-white">
                    <h4 className="mb-0">
                        <i className="bi bi-envelope-check me-2"></i>
                        Aceptar Invitación
                    </h4>
                </Card.Header>
                <Card.Body>
                    <Alert variant="info">
                        <strong>{invitation.sender_name}</strong> te ha invitado a unirte a{' '}
                        <strong>{invitation.organization_name}</strong> como{' '}
                        <strong>{invitation.role_display}</strong>
                        {invitation.sede_name && (
                            <> en la sede <strong>{invitation.sede_name}</strong></>
                        )}
                        .
                    </Alert>

                    <Form onSubmit={handleSubmit}>
                        <h5 className="mb-3">Crea tu cuenta</h5>

                        <Form.Group className="mb-3">
                            <Form.Label>Email</Form.Label>
                            <Form.Control
                                type="email"
                                value={invitation.email}
                                disabled
                                readOnly
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Nombre de usuario *</Form.Label>
                            <Form.Control
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                required
                                placeholder="Ej: juan.perez"
                            />
                            <Form.Text className="text-muted">
                                Este será tu nombre de usuario para iniciar sesión
                            </Form.Text>
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Nombre *</Form.Label>
                            <Form.Control
                                type="text"
                                value={firstName}
                                onChange={(e) => setFirstName(e.target.value)}
                                required
                                placeholder="Juan"
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Apellido *</Form.Label>
                            <Form.Control
                                type="text"
                                value={lastName}
                                onChange={(e) => setLastName(e.target.value)}
                                required
                                placeholder="Pérez"
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Contraseña *</Form.Label>
                            <Form.Control
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                minLength={8}
                                placeholder="Mínimo 8 caracteres"
                            />
                        </Form.Group>

                        <Form.Group className="mb-4">
                            <Form.Label>Confirmar Contraseña *</Form.Label>
                            <Form.Control
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                required
                                isInvalid={confirmPassword !== '' && password !== confirmPassword}
                                placeholder="Confirma tu contraseña"
                            />
                            <Form.Control.Feedback type="invalid">
                                Las contraseñas no coinciden
                            </Form.Control.Feedback>
                        </Form.Group>

                        <div className="d-grid gap-2">
                            <Button
                                variant="primary"
                                type="submit"
                                size="lg"
                                disabled={submitting || password !== confirmPassword}
                            >
                                {submitting ? (
                                    <>
                                        <Spinner
                                            as="span"
                                            animation="border"
                                            size="sm"
                                            className="me-2"
                                        />
                                        Creando cuenta...
                                    </>
                                ) : (
                                    <>
                                        <i className="bi bi-check-circle me-2"></i>
                                        Crear Cuenta y Unirse
                                    </>
                                )}
                            </Button>
                        </div>

                        <p className="text-muted text-center mt-3 mb-0 small">
                            La invitación expira el{' '}
                            {new Date(invitation.expires_at).toLocaleDateString('es-ES', {
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                            })}
                        </p>
                    </Form>
                </Card.Body>
            </Card>
        </Container>
    );
};

export default AcceptInvitationPage;
