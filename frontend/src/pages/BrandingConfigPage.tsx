import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert, Spinner } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL;
const api = axios.create({
    baseURL: API_URL,
});

// Agregar token de autenticación a las peticiones
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

interface BrandingConfig {
    usar_branding_personalizado: boolean;
    logo?: File | null;
    logo_url?: string | null;
    color_primario: string;
    color_secundario: string;
    color_texto: string;
    color_fondo: string;
    texto_bienvenida: string;
}

const BrandingConfigPage: React.FC = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    const [config, setConfig] = useState<BrandingConfig>({
        usar_branding_personalizado: false,
        logo: null,
        logo_url: null,
        color_primario: '#007bff',
        color_secundario: '#6c757d',
        color_texto: '#212529',
        color_fondo: '#ffffff',
        texto_bienvenida: ''
    });

    const [logoPreview, setLogoPreview] = useState<string | null>(null);

    useEffect(() => {
        fetchBrandingConfig();
    }, []);

    const fetchBrandingConfig = async () => {
        try {
            const response = await api.get('/api/organizacion/branding/');
            const data = response.data;

            setConfig({
                usar_branding_personalizado: data.usar_branding_personalizado || false,
                logo: null,
                logo_url: data.logo_url || null,
                color_primario: data.color_primario || '#007bff',
                color_secundario: data.color_secundario || '#6c757d',
                color_texto: data.color_texto || '#212529',
                color_fondo: data.color_fondo || '#ffffff',
                texto_bienvenida: data.texto_bienvenida || ''
            });

            if (data.logo_url) {
                setLogoPreview(data.logo_url);
            }

            setLoading(false);
        } catch (err: any) {
            console.error('Error al cargar configuración:', err);
            if (err.response?.status === 403) {
                setError('No tienes permisos para acceder a esta página');
            } else {
                setError('Error al cargar la configuración de branding');
            }
            setLoading(false);
        }
    };

    const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            // Validar tamaño (máx 2MB)
            if (file.size > 2 * 1024 * 1024) {
                setError('El logo no puede superar los 2MB');
                return;
            }

            // Validar tipo
            if (!['image/png', 'image/jpeg', 'image/jpg', 'image/svg+xml'].includes(file.type)) {
                setError('El logo debe ser PNG, JPG o SVG');
                return;
            }

            setConfig({ ...config, logo: file });

            // Crear preview
            const reader = new FileReader();
            reader.onloadend = () => {
                setLogoPreview(reader.result as string);
            };
            reader.readAsDataURL(file);
            setError(null);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        setError(null);
        setSuccess(false);

        try {
            const formData = new FormData();
            formData.append('usar_branding_personalizado', String(config.usar_branding_personalizado));

            if (config.logo) {
                formData.append('logo', config.logo);
            }

            formData.append('color_primario', config.color_primario);
            formData.append('color_secundario', config.color_secundario);
            formData.append('color_texto', config.color_texto);
            formData.append('color_fondo', config.color_fondo);
            formData.append('texto_bienvenida', config.texto_bienvenida);

            await api.patch('/api/organizacion/branding/', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });

            setSuccess(true);
            // Recargar configuración para obtener la URL actualizada del logo
            await fetchBrandingConfig();

        } catch (err: any) {
            console.error('Error al guardar:', err);
            if (err.response?.status === 403) {
                setError('No tienes permisos para modificar el branding. Solo administradores y propietarios pueden hacerlo.');
            } else {
                setError(err.response?.data?.error || 'Error al guardar la configuración');
            }
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <Container className="mt-5 text-center">
                <Spinner animation="border" />
                <p className="mt-3">Cargando configuración...</p>
            </Container>
        );
    }

    return (
        <Container className="mt-4">
            <Row>
                <Col md={8} className="mx-auto">
                    <Card>
                        <Card.Body>
                            <Card.Title as="h2" className="mb-4">
                                Configuración de Branding
                            </Card.Title>

                            {error && <Alert variant="danger" dismissible onClose={() => setError(null)}>{error}</Alert>}
                            {success && <Alert variant="success" dismissible onClose={() => setSuccess(false)}>
                                ¡Configuración guardada exitosamente!
                            </Alert>}

                            <Form onSubmit={handleSubmit}>
                                <Form.Group className="mb-4">
                                    <Form.Check
                                        type="switch"
                                        id="usar-branding"
                                        label="Activar branding personalizado"
                                        checked={config.usar_branding_personalizado}
                                        onChange={(e) => setConfig({ ...config, usar_branding_personalizado: e.target.checked })}
                                    />
                                    <Form.Text className="text-muted">
                                        Activa esta opción para personalizar la apariencia de tu página pública de agendamiento
                                    </Form.Text>
                                </Form.Group>

                                {config.usar_branding_personalizado && (
                                    <>
                                        <hr />

                                        {/* Logo */}
                                        <Form.Group className="mb-4">
                                            <Form.Label>Logo de la Organización</Form.Label>
                                            {logoPreview && (
                                                <div className="mb-3">
                                                    <img
                                                        src={logoPreview}
                                                        alt="Logo preview"
                                                        style={{ maxHeight: '100px', maxWidth: '250px', objectFit: 'contain' }}
                                                    />
                                                </div>
                                            )}
                                            <Form.Control
                                                type="file"
                                                accept="image/png,image/jpeg,image/jpg,image/svg+xml"
                                                onChange={handleLogoChange}
                                            />
                                            <Form.Text className="text-muted">
                                                PNG, JPG o SVG. Máximo 2MB.
                                            </Form.Text>
                                        </Form.Group>

                                        {/* Colores */}
                                        <h5 className="mb-3">Colores</h5>

                                        <Row>
                                            <Col md={6}>
                                                <Form.Group className="mb-3">
                                                    <Form.Label>Color Primario</Form.Label>
                                                    <div className="d-flex gap-2">
                                                        <Form.Control
                                                            type="color"
                                                            value={config.color_primario}
                                                            onChange={(e) => setConfig({ ...config, color_primario: e.target.value })}
                                                            style={{ width: '60px' }}
                                                        />
                                                        <Form.Control
                                                            type="text"
                                                            value={config.color_primario}
                                                            onChange={(e) => setConfig({ ...config, color_primario: e.target.value })}
                                                            placeholder="#007bff"
                                                        />
                                                    </div>
                                                    <Form.Text className="text-muted">
                                                        Color principal de botones y títulos
                                                    </Form.Text>
                                                </Form.Group>
                                            </Col>

                                            <Col md={6}>
                                                <Form.Group className="mb-3">
                                                    <Form.Label>Color Secundario</Form.Label>
                                                    <div className="d-flex gap-2">
                                                        <Form.Control
                                                            type="color"
                                                            value={config.color_secundario}
                                                            onChange={(e) => setConfig({ ...config, color_secundario: e.target.value })}
                                                            style={{ width: '60px' }}
                                                        />
                                                        <Form.Control
                                                            type="text"
                                                            value={config.color_secundario}
                                                            onChange={(e) => setConfig({ ...config, color_secundario: e.target.value })}
                                                            placeholder="#6c757d"
                                                        />
                                                    </div>
                                                    <Form.Text className="text-muted">
                                                        Color para elementos secundarios
                                                    </Form.Text>
                                                </Form.Group>
                                            </Col>
                                        </Row>

                                        <Row>
                                            <Col md={6}>
                                                <Form.Group className="mb-3">
                                                    <Form.Label>Color de Texto</Form.Label>
                                                    <div className="d-flex gap-2">
                                                        <Form.Control
                                                            type="color"
                                                            value={config.color_texto}
                                                            onChange={(e) => setConfig({ ...config, color_texto: e.target.value })}
                                                            style={{ width: '60px' }}
                                                        />
                                                        <Form.Control
                                                            type="text"
                                                            value={config.color_texto}
                                                            onChange={(e) => setConfig({ ...config, color_texto: e.target.value })}
                                                            placeholder="#212529"
                                                        />
                                                    </div>
                                                    <Form.Text className="text-muted">
                                                        Color del texto principal
                                                    </Form.Text>
                                                </Form.Group>
                                            </Col>

                                            <Col md={6}>
                                                <Form.Group className="mb-3">
                                                    <Form.Label>Color de Fondo</Form.Label>
                                                    <div className="d-flex gap-2">
                                                        <Form.Control
                                                            type="color"
                                                            value={config.color_fondo}
                                                            onChange={(e) => setConfig({ ...config, color_fondo: e.target.value })}
                                                            style={{ width: '60px' }}
                                                        />
                                                        <Form.Control
                                                            type="text"
                                                            value={config.color_fondo}
                                                            onChange={(e) => setConfig({ ...config, color_fondo: e.target.value })}
                                                            placeholder="#ffffff"
                                                        />
                                                    </div>
                                                    <Form.Text className="text-muted">
                                                        Color de fondo de la página
                                                    </Form.Text>
                                                </Form.Group>
                                            </Col>
                                        </Row>

                                        {/* Texto de bienvenida */}
                                        <Form.Group className="mb-4">
                                            <Form.Label>Mensaje de Bienvenida</Form.Label>
                                            <Form.Control
                                                as="textarea"
                                                rows={3}
                                                value={config.texto_bienvenida}
                                                onChange={(e) => setConfig({ ...config, texto_bienvenida: e.target.value })}
                                                placeholder="Ej: Bienvenido a nuestro sistema de agendamiento. Reserva tu cita fácilmente."
                                            />
                                            <Form.Text className="text-muted">
                                                Este mensaje aparecerá en la página pública de agendamiento
                                            </Form.Text>
                                        </Form.Group>
                                    </>
                                )}

                                <hr />

                                <div className="d-flex gap-2">
                                    <Button variant="primary" type="submit" disabled={saving}>
                                        {saving ? (
                                            <>
                                                <Spinner as="span" animation="border" size="sm" className="me-2" />
                                                Guardando...
                                            </>
                                        ) : (
                                            'Guardar Configuración'
                                        )}
                                    </Button>
                                    <Button variant="secondary" onClick={() => navigate(-1)} disabled={saving}>
                                        Cancelar
                                    </Button>
                                </div>
                            </Form>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </Container>
    );
};

export default BrandingConfigPage;
