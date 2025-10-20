import React, { useState } from 'react';
import { Container, Card, Button, Tab, Tabs, Alert } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import CreateUserForm from '../components/CreateUserForm';
import { useRolePermissions } from '../hooks/useRolePermissions';
import { Navigate } from 'react-router-dom';

const UserManagementPage: React.FC = () => {
    const { t } = useTranslation();
    const { canManageUsers } = useRolePermissions();
    const [activeTab, setActiveTab] = useState<string>('create');
    const [showForm, setShowForm] = useState(false);

    // Redirect if user doesn't have permission
    if (!canManageUsers) {
        return <Navigate to="/" replace />;
    }

    const handleUserCreated = () => {
        setShowForm(false);
        // Could refresh user list here if we had a list view
    };

    return (
        <Container className="py-4">
            <div className="d-flex justify-content-between align-items-center mb-4">
                    <div>
                        <h2>Gestión de Usuarios</h2>
                        <p className="text-muted mb-0">
                            Crea y administra usuarios con diferentes roles en tu organización
                        </p>
                    </div>
                    {!showForm && (
                        <Button
                            variant="primary"
                            size="lg"
                            onClick={() => setShowForm(true)}
                        >
                            <i className="bi bi-person-plus me-2"></i>
                            Crear Usuario
                        </Button>
                    )}
                </div>

                <Alert variant="info" className="mb-4">
                    <i className="bi bi-info-circle me-2"></i>
                    <strong>Sistema Multi-Rol:</strong> Los usuarios pueden tener múltiples roles simultáneamente.
                    Por ejemplo, un colaborador puede ser también cliente.
                </Alert>

                {showForm ? (
                    <Card>
                        <Card.Header className="bg-primary text-white">
                            <h4 className="mb-0">
                                <i className="bi bi-person-plus me-2"></i>
                                Crear Nuevo Usuario
                            </h4>
                        </Card.Header>
                        <Card.Body>
                            <CreateUserForm
                                onSuccess={handleUserCreated}
                                onCancel={() => setShowForm(false)}
                            />
                        </Card.Body>
                    </Card>
                ) : (
                    <Card>
                        <Card.Body className="text-center py-5">
                            <i className="bi bi-people display-1 text-muted mb-3"></i>
                            <h4>Gestión de Usuarios</h4>
                            <p className="text-muted mb-4">
                                Haz clic en "Crear Usuario" para agregar un nuevo miembro a tu organización
                            </p>
                            <Button
                                variant="primary"
                                size="lg"
                                onClick={() => setShowForm(true)}
                            >
                                <i className="bi bi-person-plus me-2"></i>
                                Crear Primer Usuario
                            </Button>
                        </Card.Body>
                    </Card>
                )}

                <Card className="mt-4">
                    <Card.Header>
                        <h5 className="mb-0">
                            <i className="bi bi-info-circle me-2"></i>
                            Roles Disponibles
                        </h5>
                    </Card.Header>
                    <Card.Body>
                        <div className="row">
                            <div className="col-md-6 mb-3">
                                <div className="border rounded p-3">
                                    <h6>
                                        <span className="me-2">👑</span>
                                        <strong>Propietario</strong>
                                    </h6>
                                    <p className="small text-muted mb-0">
                                        Dueño de la organización con acceso total a todas las funcionalidades y sedes.
                                    </p>
                                </div>
                            </div>
                            <div className="col-md-6 mb-3">
                                <div className="border rounded p-3">
                                    <h6>
                                        <span className="me-2">🔴</span>
                                        <strong>Administrador</strong>
                                    </h6>
                                    <p className="small text-muted mb-0">
                                        Administrador global con acceso a todas las sedes. Puede gestionar usuarios y configuración.
                                    </p>
                                </div>
                            </div>
                            <div className="col-md-6 mb-3">
                                <div className="border rounded p-3">
                                    <h6>
                                        <span className="me-2">🟠</span>
                                        <strong>Administrador de Sede</strong>
                                    </h6>
                                    <p className="small text-muted mb-0">
                                        Administrador de sedes específicas. Acceso limitado a las sedes asignadas.
                                    </p>
                                </div>
                            </div>
                            <div className="col-md-6 mb-3">
                                <div className="border rounded p-3">
                                    <h6>
                                        <span className="me-2">🟢</span>
                                        <strong>Colaborador</strong>
                                    </h6>
                                    <p className="small text-muted mb-0">
                                        Empleado que atiende citas. Puede trabajar en una o varias sedes.
                                    </p>
                                </div>
                            </div>
                            <div className="col-md-12 mb-3">
                                <div className="border rounded p-3">
                                    <h6>
                                        <span className="me-2">🔵</span>
                                        <strong>Cliente</strong>
                                    </h6>
                                    <p className="small text-muted mb-0">
                                        Usuario final que agenda citas. Puede reservar servicios en cualquier sede.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </Card.Body>
                </Card>
        </Container>
    );
};

export default UserManagementPage;
