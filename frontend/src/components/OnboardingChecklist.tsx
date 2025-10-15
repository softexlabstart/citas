import React from 'react';
import { Card, ProgressBar, ListGroup, Button, Badge, Alert } from 'react-bootstrap';
import { CheckCircleFill, Circle, XCircle } from 'react-bootstrap-icons';
import { useOnboarding } from '../hooks/useOnboarding';
import { Link } from 'react-router-dom';

const OnboardingChecklist: React.FC = () => {
    const { progress, loading, shouldShowOnboarding, dismiss } = useOnboarding();

    if (loading) return null;
    if (!shouldShowOnboarding || !progress) return null;

    const steps = [
        {
            key: 'has_created_service',
            completed: progress.has_created_service,
            label: 'Crear tu primer servicio',
            description: 'Agrega los servicios que ofreces',
            link: '/admin-settings',
            icon: '🛠️',
            required: true,
        },
        {
            key: 'has_added_collaborator',
            completed: progress.has_added_collaborator,
            label: 'Agregar colaboradores',
            description: 'Invita a tu equipo (opcional)',
            link: '/admin-settings',
            icon: '👥',
            required: false,
        },
        {
            key: 'has_completed_profile',
            completed: progress.has_completed_profile,
            label: 'Completar tu perfil',
            description: 'Agrega tus datos personales',
            link: '/profile/edit',
            icon: '👤',
            required: false,
        },
        {
            key: 'has_viewed_public_link',
            completed: progress.has_viewed_public_link,
            label: 'Ver tu enlace público',
            description: 'Comparte este enlace con tus clientes',
            link: '/marketing',
            icon: '🔗',
            required: false,
        },
    ];

    const completedCount = steps.filter(step => step.completed).length;
    const totalSteps = steps.length;

    return (
        <Card className="mb-4 border-primary">
            <Card.Header className="bg-primary text-white d-flex justify-content-between align-items-center">
                <div>
                    <h5 className="mb-0">🎯 Primeros Pasos</h5>
                    <small>Completa estos pasos para empezar</small>
                </div>
                <Button
                    variant="outline-light"
                    size="sm"
                    onClick={dismiss}
                >
                    <XCircle className="me-1" />
                    Omitir
                </Button>
            </Card.Header>
            <Card.Body>
                <div className="mb-3">
                    <div className="d-flex justify-content-between mb-2">
                        <span className="text-muted">Progreso</span>
                        <span className="fw-bold">{progress.completion_percentage}%</span>
                    </div>
                    <ProgressBar
                        now={progress.completion_percentage}
                        variant={progress.completion_percentage === 100 ? 'success' : 'primary'}
                        animated
                    />
                </div>

                <ListGroup variant="flush">
                    {steps.map((step, index) => (
                        <ListGroup.Item
                            key={step.key}
                            className="d-flex align-items-center border-0 py-3"
                        >
                            <div className="me-3">
                                {step.completed ? (
                                    <CheckCircleFill size={24} className="text-success" />
                                ) : (
                                    <Circle size={24} className="text-muted" />
                                )}
                            </div>
                            <div className="flex-grow-1">
                                <div className="d-flex align-items-center mb-1">
                                    <span className="me-2">{step.icon}</span>
                                    <strong>{step.label}</strong>
                                    {step.required && (
                                        <Badge bg="danger" className="ms-2" pill>
                                            Requerido
                                        </Badge>
                                    )}
                                </div>
                                <small className="text-muted">{step.description}</small>
                            </div>
                            {!step.completed && (
                                <Link to={step.link}>
                                    <Button variant="outline-primary" size="sm">
                                        Ir
                                    </Button>
                                </Link>
                            )}
                        </ListGroup.Item>
                    ))}
                </ListGroup>

                {progress.completion_percentage === 100 && (
                    <Alert variant="success" className="mt-3 mb-0">
                        <Alert.Heading>¡Felicitaciones! 🎉</Alert.Heading>
                        <p className="mb-0">
                            Has completado todos los pasos iniciales. Ya puedes empezar a usar el sistema.
                        </p>
                    </Alert>
                )}

                {progress.completion_percentage > 0 && progress.completion_percentage < 100 && (
                    <div className="mt-3 text-center">
                        <small className="text-muted">
                            {completedCount} de {totalSteps} pasos completados
                        </small>
                    </div>
                )}
            </Card.Body>
        </Card>
    );
};

export default OnboardingChecklist;
