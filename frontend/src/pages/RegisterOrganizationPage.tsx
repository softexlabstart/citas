import React, { useState, useEffect } from 'react';
import { registerWithOrganization } from '../api';
import { useNavigate, Link } from 'react-router-dom';
import { MultiTenantRegistrationData } from '../interfaces/Organization';
import { Container, Row, Col, Card, Form, Button, Alert, InputGroup, Tabs, Tab } from 'react-bootstrap';
import { Person, Lock, Envelope, PersonBadge, Building, MapPin, Phone, Shield } from 'react-bootstrap-icons';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../hooks/useAuth';

const RegisterOrganizationPage: React.FC = () => {
    const { t } = useTranslation();
    const { user } = useAuth();
    const [formData, setFormData] = useState<MultiTenantRegistrationData>({
        username: '',
        email: '',
        first_name: '',
        last_name: '',
        password: '',
        organizacion_nombre: '',
        sede_nombre: '',
        sede_direccion: '',
        sede_telefono: '',
        telefono: '',
        ciudad: '',
        barrio: '',
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    });
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        // Verificar si el usuario es superadmin
        if (user && !user.is_staff) {
            setError('Solo los administradores del sistema pueden crear organizaciones.');
        }
    }, [user]);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const response = await registerWithOrganization(formData);
            
            // Guardar token y datos del usuario
            localStorage.setItem('token', response.tokens.access);
            localStorage.setItem('refreshToken', response.tokens.refresh);
            localStorage.setItem('user', JSON.stringify(response.user));
            
            // Redirigir al dashboard
            navigate('/');
        } catch (error: any) {
            setError(error.response?.data?.error || 'Error al crear la organización. Por favor, verifica tus datos.');
            console.error('Failed to register organization', error);
        } finally {
            setLoading(false);
        }
    };

    // Si hay error de permisos, mostrar mensaje de error
    if (error && error.includes('Solo los administradores')) {
        return (
            <Container fluid className="p-0 vh-100">
                <Row className="g-0 h-100">
                    <Col className="d-flex justify-content-center align-items-center">
                        <Card style={{ width: '28rem' }} className="shadow-lg border-0">
                            <Card.Body className="p-5 text-center">
                                <Shield size={64} className="text-danger mb-4" />
                                <h2 className="mb-4">Acceso Restringido</h2>
                                <Alert variant="danger">{error}</Alert>
                                <p className="mt-4">
                                    <Link to="/login" className="btn btn-primary">
                                        Volver al Login
                                    </Link>
                                </p>
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
                <Col md={6} className="d-none d-md-flex align-items-center justify-content-center bg-primary">
                    <div className="text-white text-center p-5">
                        <Building size={64} className="mb-4" />
                        <h1 className="display-4 fw-bold">Citas Médicas</h1>
                        <p className="lead">Crea tu organización y gestiona todas tus sedes desde un solo lugar.</p>
                    </div>
                </Col>
                <Col xs={12} md={6} className="d-flex justify-content-center align-items-center">
                    <Card style={{ width: '28rem' }} className="shadow-lg border-0">
                        <Card.Body className="p-5">
                            <Card.Title className="text-center mb-4 h2">
                                <Building className="me-2" />
                                Crear Organización
                            </Card.Title>
                            {error && <Alert variant="danger">{error}</Alert>}
                            
                            <Form onSubmit={handleSubmit}>
                                <Tabs defaultActiveKey="usuario" className="mb-4">
                                    <Tab eventKey="usuario" title="Usuario">
                                        <div className="mt-3">
                                            <Form.Group className="mb-3">
                                                <InputGroup>
                                                    <InputGroup.Text><Person /></InputGroup.Text>
                                                    <Form.Control 
                                                        type="text" 
                                                        name="username"
                                                        placeholder="Nombre de usuario" 
                                                        value={formData.username} 
                                                        onChange={handleInputChange} 
                                                        required 
                                                    />
                                                </InputGroup>
                                            </Form.Group>

                                            <Form.Group className="mb-3">
                                                <InputGroup>
                                                    <InputGroup.Text><Lock /></InputGroup.Text>
                                                    <Form.Control 
                                                        type="password" 
                                                        name="password"
                                                        placeholder="Contraseña" 
                                                        value={formData.password} 
                                                        onChange={handleInputChange} 
                                                        required 
                                                        minLength={8}
                                                    />
                                                </InputGroup>
                                            </Form.Group>

                                            <Form.Group className="mb-3">
                                                <InputGroup>
                                                    <InputGroup.Text><Envelope /></InputGroup.Text>
                                                    <Form.Control 
                                                        type="email" 
                                                        name="email"
                                                        placeholder="Email" 
                                                        value={formData.email} 
                                                        onChange={handleInputChange} 
                                                        required 
                                                    />
                                                </InputGroup>
                                            </Form.Group>

                                            <Row>
                                                <Col md={6}>
                                                    <Form.Group className="mb-3">
                                                        <InputGroup>
                                                            <InputGroup.Text><PersonBadge /></InputGroup.Text>
                                                            <Form.Control 
                                                                type="text" 
                                                                name="first_name"
                                                                placeholder="Nombre" 
                                                                value={formData.first_name} 
                                                                onChange={handleInputChange} 
                                                                required 
                                                            />
                                                        </InputGroup>
                                                    </Form.Group>
                                                </Col>
                                                <Col md={6}>
                                                    <Form.Group className="mb-3">
                                                        <InputGroup>
                                                            <InputGroup.Text><PersonBadge /></InputGroup.Text>
                                                            <Form.Control 
                                                                type="text" 
                                                                name="last_name"
                                                                placeholder="Apellido" 
                                                                value={formData.last_name} 
                                                                onChange={handleInputChange} 
                                                                required 
                                                            />
                                                        </InputGroup>
                                                    </Form.Group>
                                                </Col>
                                            </Row>
                                        </div>
                                    </Tab>

                                    <Tab eventKey="organizacion" title="Organización">
                                        <div className="mt-3">
                                            <Form.Group className="mb-3">
                                                <InputGroup>
                                                    <InputGroup.Text><Building /></InputGroup.Text>
                                                    <Form.Control 
                                                        type="text" 
                                                        name="organizacion_nombre"
                                                        placeholder="Nombre de la organización" 
                                                        value={formData.organizacion_nombre} 
                                                        onChange={handleInputChange} 
                                                        required 
                                                    />
                                                </InputGroup>
                                            </Form.Group>

                                            <Form.Group className="mb-3">
                                                <InputGroup>
                                                    <InputGroup.Text><MapPin /></InputGroup.Text>
                                                    <Form.Control 
                                                        type="text" 
                                                        name="sede_nombre"
                                                        placeholder="Nombre de la sede principal" 
                                                        value={formData.sede_nombre} 
                                                        onChange={handleInputChange} 
                                                        required 
                                                    />
                                                </InputGroup>
                                            </Form.Group>

                                            <Form.Group className="mb-3">
                                                <InputGroup>
                                                    <InputGroup.Text><MapPin /></InputGroup.Text>
                                                    <Form.Control 
                                                        type="text" 
                                                        name="sede_direccion"
                                                        placeholder="Dirección de la sede" 
                                                        value={formData.sede_direccion} 
                                                        onChange={handleInputChange} 
                                                    />
                                                </InputGroup>
                                            </Form.Group>

                                            <Form.Group className="mb-3">
                                                <InputGroup>
                                                    <InputGroup.Text><Phone /></InputGroup.Text>
                                                    <Form.Control 
                                                        type="text" 
                                                        name="sede_telefono"
                                                        placeholder="Teléfono de la sede" 
                                                        value={formData.sede_telefono} 
                                                        onChange={handleInputChange} 
                                                    />
                                                </InputGroup>
                                            </Form.Group>
                                        </div>
                                    </Tab>

                                    <Tab eventKey="perfil" title="Perfil">
                                        <div className="mt-3">
                                            <Form.Group className="mb-3">
                                                <InputGroup>
                                                    <InputGroup.Text><Phone /></InputGroup.Text>
                                                    <Form.Control 
                                                        type="text" 
                                                        name="telefono"
                                                        placeholder="Tu teléfono" 
                                                        value={formData.telefono} 
                                                        onChange={handleInputChange} 
                                                    />
                                                </InputGroup>
                                            </Form.Group>

                                            <Row>
                                                <Col md={6}>
                                                    <Form.Group className="mb-3">
                                                        <Form.Control 
                                                            type="text" 
                                                            name="ciudad"
                                                            placeholder="Ciudad" 
                                                            value={formData.ciudad} 
                                                            onChange={handleInputChange} 
                                                        />
                                                    </Form.Group>
                                                </Col>
                                                <Col md={6}>
                                                    <Form.Group className="mb-3">
                                                        <Form.Control 
                                                            type="text" 
                                                            name="barrio"
                                                            placeholder="Barrio" 
                                                            value={formData.barrio} 
                                                            onChange={handleInputChange} 
                                                        />
                                                    </Form.Group>
                                                </Col>
                                            </Row>

                                            <Form.Group className="mb-3">
                                                <Form.Select 
                                                    name="genero"
                                                    value={formData.genero || ''} 
                                                    onChange={handleInputChange}
                                                >
                                                    <option value="">Seleccionar género</option>
                                                    <option value="M">Masculino</option>
                                                    <option value="F">Femenino</option>
                                                    <option value="O">Otro</option>
                                                </Form.Select>
                                            </Form.Group>

                                            <Form.Group className="mb-3">
                                                <Form.Control 
                                                    type="date" 
                                                    name="fecha_nacimiento"
                                                    value={formData.fecha_nacimiento || ''} 
                                                    onChange={handleInputChange} 
                                                />
                                            </Form.Group>
                                        </div>
                                    </Tab>
                                </Tabs>

                                <div className="d-grid">
                                    <Button 
                                        variant="primary" 
                                        type="submit" 
                                        className="btn-block fw-bold"
                                        disabled={loading}
                                    >
                                        {loading ? 'Creando...' : 'Crear Organización'}
                                    </Button>
                                </div>
                            </Form>
                            
                            <p className="mt-4 text-center">
                                ¿Ya tienes una cuenta? <Link to="/login">Iniciar sesión</Link>
                            </p>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </Container>
    );
};

export default RegisterOrganizationPage;
