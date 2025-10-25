import React, { useState, useEffect } from 'react';
import { Form, Button, Spinner, Alert, Row, Col, Card } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import { useApi } from '../hooks/useApi';
import { createUserWithRole, getSedes } from '../api';
import { RoleType, ROLE_CHOICES, CreateUserPayload } from '../interfaces/Role';
import { Sede } from '../interfaces/User';
import RoleBadge from './RoleBadge';
import MultiSelectDropdown from './MultiSelectDropdown';

interface CreateUserFormProps {
    onSuccess?: () => void;
    onCancel?: () => void;
}

const CreateUserForm: React.FC<CreateUserFormProps> = ({ onSuccess, onCancel }) => {
    const { t } = useTranslation();

    // Form state
    const [email, setEmail] = useState('');
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [role, setRole] = useState<RoleType>('cliente');
    const [additionalRoles, setAdditionalRoles] = useState<RoleType[]>([]);
    const [sedePrincipalId, setSedePrincipalId] = useState<number | undefined>(undefined);
    const [sedesTrabajo, setSedesTrabajo] = useState<number[]>([]);
    const [sedesAdministradas, setSedesAdministradas] = useState<number[]>([]);

    // Sedes data
    const [sedes, setSedes] = useState<Sede[]>([]);
    const { loading: loadingSedes, request: fetchSedes } = useApi(getSedes);
    const { loading: creating, error, request: callCreateUser } = useApi(createUserWithRole);

    // Validation state
    const [passwordMatch, setPasswordMatch] = useState(true);

    useEffect(() => {
        loadSedes();
    }, []);

    const loadSedes = async () => {
        const result = await fetchSedes();
        if (result.success && result.data) {
            setSedes(result.data);
        }
    };

    useEffect(() => {
        setPasswordMatch(password === confirmPassword || confirmPassword === '');
    }, [password, confirmPassword]);

    const handleRoleChange = (newRole: RoleType) => {
        setRole(newRole);
        // Clear sede fields based on role
        if (newRole === 'owner' || newRole === 'admin') {
            setSedePrincipalId(undefined);
            setSedesTrabajo([]);
            setSedesAdministradas([]);
        } else if (newRole === 'cliente') {
            setSedesTrabajo([]);
            setSedesAdministradas([]);
        } else if (newRole === 'colaborador') {
            setSedesAdministradas([]);
        } else if (newRole === 'sede_admin') {
            setSedesTrabajo([]);
        }
    };

    const handleAdditionalRoleToggle = (roleValue: RoleType) => {
        if (additionalRoles.includes(roleValue)) {
            setAdditionalRoles(additionalRoles.filter(r => r !== roleValue));
        } else {
            setAdditionalRoles([...additionalRoles, roleValue]);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!passwordMatch) {
            toast.error('Las contraseñas no coinciden');
            return;
        }

        if (password.length < 8) {
            toast.error('La contraseña debe tener al menos 8 caracteres');
            return;
        }

        const userData: CreateUserPayload = {
            email,
            first_name: firstName,
            last_name: lastName,
            password,
            role,
            additional_roles: additionalRoles.length > 0 ? additionalRoles : undefined,
            sede_principal_id: sedePrincipalId,
            sedes_trabajo_ids: sedesTrabajo.length > 0 ? sedesTrabajo : undefined,
            sedes_administradas_ids: sedesAdministradas.length > 0 ? sedesAdministradas : undefined,
        };

        const result = await callCreateUser(userData);

        if (result.success) {
            toast.success(`Usuario creado exitosamente como ${ROLE_CHOICES.find(r => r.value === role)?.label}`);
            // Reset form
            setEmail('');
            setFirstName('');
            setLastName('');
            setPassword('');
            setConfirmPassword('');
            setRole('cliente');
            setAdditionalRoles([]);
            setSedePrincipalId(undefined);
            setSedesTrabajo([]);
            setSedesAdministradas([]);

            if (onSuccess) {
                onSuccess();
            }
        } else if (result.error) {
            // Extraer mensaje de error específico del backend
            let errorMessage = 'No se pudo crear el usuario';

            // Manejar errores de validación del backend (formato: {campo: ["mensaje"]})
            if (typeof result.error === 'object' && result.error !== null) {
                // Extraer mensajes de errores de validación
                const errorObj = result.error as Record<string, string[]>;
                const errorMessages: string[] = [];

                for (const [field, messages] of Object.entries(errorObj)) {
                    if (Array.isArray(messages)) {
                        errorMessages.push(...messages);
                    } else if (typeof messages === 'string') {
                        errorMessages.push(messages);
                    }
                }

                if (errorMessages.length > 0) {
                    errorMessage = errorMessages.join('. ');
                }
            } else if (typeof result.error === 'string') {
                errorMessage = result.error;
            }

            // Personalizar mensajes comunes
            if (errorMessage.includes('Ya existe un usuario con este email')) {
                // El mensaje del backend ya es claro, usarlo directamente
                toast.error(errorMessage);
            } else if (errorMessage.toLowerCase().includes('permisos')) {
                toast.error(`⛔ ${errorMessage}`);
            } else if (errorMessage.toLowerCase().includes('email')) {
                toast.error(`📧 ${errorMessage}`);
            } else {
                toast.error(`❌ ${errorMessage}`);
            }
        }
    };

    const showSedeFields = !['owner', 'admin'].includes(role);
    const showSedesTrabajoField = role === 'colaborador';
    const showSedesAdministradasField = role === 'sede_admin';

    return (
        <Form onSubmit={handleSubmit}>
            {error && <Alert variant="danger">{error}</Alert>}

            <Card className="mb-3">
                <Card.Header className="bg-primary text-white">
                    <h5 className="mb-0">Información del Usuario</h5>
                </Card.Header>
                <Card.Body>
                    <Row>
                        <Col md={6}>
                            <Form.Group className="mb-3">
                                <Form.Label>Email *</Form.Label>
                                <Form.Control
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    placeholder="usuario@ejemplo.com"
                                />
                            </Form.Group>
                        </Col>
                        <Col md={6}>
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
                        </Col>
                    </Row>

                    <Row>
                        <Col md={6}>
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
                        </Col>
                        <Col md={6}>
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
                        </Col>
                    </Row>

                    <Row>
                        <Col md={6}>
                            <Form.Group className="mb-3">
                                <Form.Label>Confirmar Contraseña *</Form.Label>
                                <Form.Control
                                    type="password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    required
                                    isInvalid={!passwordMatch}
                                    placeholder="Confirma la contraseña"
                                />
                                <Form.Control.Feedback type="invalid">
                                    Las contraseñas no coinciden
                                </Form.Control.Feedback>
                            </Form.Group>
                        </Col>
                    </Row>
                </Card.Body>
            </Card>

            <Card className="mb-3">
                <Card.Header className="bg-success text-white">
                    <h5 className="mb-0">Sistema de Roles</h5>
                </Card.Header>
                <Card.Body>
                    <Form.Group className="mb-3">
                        <Form.Label>Rol Principal *</Form.Label>
                        <div className="d-flex flex-wrap gap-2">
                            {ROLE_CHOICES.map((roleChoice) => (
                                <div
                                    key={roleChoice.value}
                                    className={`p-3 border rounded cursor-pointer ${
                                        role === roleChoice.value ? 'border-primary bg-light' : ''
                                    }`}
                                    style={{ cursor: 'pointer', minWidth: '200px' }}
                                    onClick={() => handleRoleChange(roleChoice.value)}
                                >
                                    <div className="mb-2">
                                        <RoleBadge role={roleChoice.value} showAdditionalCount={false} />
                                    </div>
                                    <small className="text-muted">{roleChoice.description}</small>
                                </div>
                            ))}
                        </div>
                    </Form.Group>

                    <Form.Group className="mb-3">
                        <Form.Label>
                            Roles Adicionales (opcional)
                            <small className="text-muted ms-2">
                                Ej: Un colaborador que también es cliente
                            </small>
                        </Form.Label>
                        <div className="d-flex flex-wrap gap-2">
                            {ROLE_CHOICES.filter(r => r.value !== role).map((roleChoice) => (
                                <Form.Check
                                    key={roleChoice.value}
                                    type="checkbox"
                                    id={`additional-role-${roleChoice.value}`}
                                    label={
                                        <span>
                                            {roleChoice.emoji} {roleChoice.label}
                                        </span>
                                    }
                                    checked={additionalRoles.includes(roleChoice.value)}
                                    onChange={() => handleAdditionalRoleToggle(roleChoice.value)}
                                />
                            ))}
                        </div>
                    </Form.Group>

                    {additionalRoles.length > 0 && (
                        <Alert variant="info" className="mb-0">
                            <strong>Vista previa del badge:</strong>
                            <div className="mt-2">
                                <RoleBadge role={role} additionalRoles={additionalRoles} />
                            </div>
                        </Alert>
                    )}
                </Card.Body>
            </Card>

            {showSedeFields && (
                <Card className="mb-3">
                    <Card.Header className="bg-warning text-dark">
                        <h5 className="mb-0">Asignación de Sedes</h5>
                    </Card.Header>
                    <Card.Body>
                        {loadingSedes ? (
                            <div className="text-center">
                                <Spinner animation="border" size="sm" />
                                <span className="ms-2">Cargando sedes...</span>
                            </div>
                        ) : (
                            <>
                                <Form.Group className="mb-3">
                                    <Form.Label>
                                        Sede Principal
                                        {role === 'cliente' && <small className="text-muted ms-2">(Opcional para clientes)</small>}
                                    </Form.Label>
                                    <Form.Select
                                        value={sedePrincipalId || ''}
                                        onChange={(e) => setSedePrincipalId(e.target.value ? parseInt(e.target.value) : undefined)}
                                        required={role !== 'cliente'}
                                    >
                                        <option value="">Selecciona una sede</option>
                                        {sedes.map((sede) => (
                                            <option key={sede.id} value={sede.id}>
                                                {sede.nombre}
                                            </option>
                                        ))}
                                    </Form.Select>
                                </Form.Group>

                                {showSedesTrabajoField && (
                                    <Form.Group className="mb-3">
                                        <Form.Label>
                                            Sedes de Trabajo (Multi-Sede)
                                            <small className="text-muted ms-2">
                                                Para colaboradores que trabajan en múltiples sedes
                                            </small>
                                        </Form.Label>
                                        <MultiSelectDropdown
                                            options={sedes.map(s => ({ id: s.id, nombre: s.nombre }))}
                                            selected={sedesTrabajo.map(String)}
                                            onChange={(values) => setSedesTrabajo(values.map(Number))}
                                            label=""
                                            placeholder="Selecciona sedes de trabajo"
                                        />
                                    </Form.Group>
                                )}

                                {showSedesAdministradasField && (
                                    <Form.Group className="mb-3">
                                        <Form.Label>
                                            Sedes Administradas *
                                            <small className="text-muted ms-2">
                                                Sedes que este administrador gestionará
                                            </small>
                                        </Form.Label>
                                        <MultiSelectDropdown
                                            options={sedes.map(s => ({ id: s.id, nombre: s.nombre }))}
                                            selected={sedesAdministradas.map(String)}
                                            onChange={(values) => setSedesAdministradas(values.map(Number))}
                                            label=""
                                            placeholder="Selecciona sedes a administrar"
                                        />
                                        {sedesAdministradas.length === 0 && (
                                            <Form.Text className="text-danger">
                                                Los administradores de sede requieren al menos una sede asignada
                                            </Form.Text>
                                        )}
                                    </Form.Group>
                                )}

                                <Alert variant="info" className="mb-0">
                                    <small>
                                        <strong>💡 Nota:</strong>
                                        {role === 'owner' || role === 'admin' ? (
                                            ' Los propietarios y administradores tienen acceso automático a todas las sedes.'
                                        ) : role === 'colaborador' ? (
                                            ' Los colaboradores pueden trabajar en una o varias sedes. La sede principal es obligatoria.'
                                        ) : role === 'sede_admin' ? (
                                            ' Los administradores de sede solo pueden gestionar las sedes que se les asignen aquí.'
                                        ) : (
                                            ' Los clientes pueden agendar en cualquier sede de la organización.'
                                        )}
                                    </small>
                                </Alert>
                            </>
                        )}
                    </Card.Body>
                </Card>
            )}

            <div className="d-flex justify-content-end gap-2 mt-4">
                {onCancel && (
                    <Button variant="secondary" onClick={onCancel}>
                        Cancelar
                    </Button>
                )}
                <Button
                    variant="primary"
                    type="submit"
                    disabled={creating || !passwordMatch || (role === 'sede_admin' && sedesAdministradas.length === 0)}
                >
                    {creating ? (
                        <>
                            <Spinner as="span" animation="border" size="sm" className="me-2" />
                            Creando usuario...
                        </>
                    ) : (
                        'Crear Usuario'
                    )}
                </Button>
            </div>
        </Form>
    );
};

export default CreateUserForm;
