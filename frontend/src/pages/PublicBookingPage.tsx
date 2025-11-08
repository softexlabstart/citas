import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert, Spinner } from 'react-bootstrap';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { CheckCircleFill } from 'react-bootstrap-icons';
import { createPublicBooking, getServicios, getDisponibilidad, PublicBookingData } from '../api';
import { useApi } from '../hooks/useApi';
import { useAppointmentForm } from '../hooks/useAppointmentForm';

const PublicBookingPage: React.FC = () => {
    const navigate = useNavigate();
    const { organizacionSlug } = useParams<{ organizacionSlug: string }>();
    const {
        sedes,
        servicios,
        recursos,
        selectedSede,
        selectedRecurso,
        loadingSedes,
        setSelectedSede,
        setSelectedRecurso,
    } = useAppointmentForm(organizacionSlug);

    const [nombre, setNombre] = useState('');
    const [email, setEmail] = useState('');
    const [telefono, setTelefono] = useState('');
    const [selectedServicios, setSelectedServicios] = useState<string[]>([]);
    const [date, setDate] = useState('');
    const [selectedSlot, setSelectedSlot] = useState('');
    const [comentario, setComentario] = useState('');
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [orgInfo, setOrgInfo] = useState<any>(null);
    const [checkingPermission, setCheckingPermission] = useState(true);
    const [branding, setBranding] = useState<any>(null);

    const { data: availability, request: fetchAvailableSlots } = useApi<{ disponibilidad: any[] }, [string, number, string, string[]]>(getDisponibilidad);

    const availableSlots = availability?.disponibilidad.filter(slot => slot.status === 'disponible') || [];

    // Verificar si la organización permite agendamiento público
    useEffect(() => {
        const checkPublicBookingPermission = async () => {
            try {
                const response = await fetch(`/api/organizacion/organizaciones/${organizacionSlug}/`);
                if (!response.ok) {
                    navigate('/login?message=Organización no encontrada');
                    return;
                }

                const data = await response.json();
                setOrgInfo(data);

                // Guardar branding si existe
                if (data.branding) {
                    setBranding(data.branding);
                }

                if (!data.permitir_agendamiento_publico) {
                    navigate(`/login?message=Esta organización requiere iniciar sesión para agendar citas&org=${organizacionSlug}`);
                }
            } catch (error) {
                console.error('Error al verificar permisos de agendamiento:', error);
                navigate('/login?message=Error al cargar información de la organización');
            } finally {
                setCheckingPermission(false);
            }
        };

        if (organizacionSlug) {
            checkPublicBookingPermission();
        }
    }, [organizacionSlug, navigate]);

    useEffect(() => {
        if (date && selectedRecurso && selectedSede && selectedServicios.length > 0) {
            fetchAvailableSlots(date, parseInt(selectedRecurso, 10), selectedSede, selectedServicios);
        }
    }, [date, selectedRecurso, selectedSede, selectedServicios, fetchAvailableSlots]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const bookingData: PublicBookingData = {
                nombre,
                email_cliente: email,
                telefono_cliente: telefono,
                fecha: selectedSlot,
                servicios_ids: selectedServicios.map(id => parseInt(id, 10)),
                colaboradores_ids: [parseInt(selectedRecurso)],
                sede_id: parseInt(selectedSede),
                comentario,
            };

            await createPublicBooking(bookingData);
            setSuccess(true);
        } catch (err: any) {
            console.error('Error al crear reserva:', err);
            let errorMsg = err.response?.data?.error ||
                           err.response?.data?.detail ||
                           'Error al crear la reserva. Por favor, inténtalo de nuevo.';

            // If it's an array (from ValidationError), get the first message
            if (Array.isArray(errorMsg)) {
                errorMsg = errorMsg[0];
            }

            // If it's an appointment conflict, reload available slots
            if (err.response?.data?.code === 'appointment_conflict' ||
                (Array.isArray(err.response?.data?.code) && err.response?.data?.code[0] === 'appointment_conflict')) {
                errorMsg += ' Por favor, selecciona otro horario.';
                // Reload available slots
                if (date && selectedRecurso && selectedSede && selectedServicios.length > 0) {
                    fetchAvailableSlots(date, parseInt(selectedRecurso, 10), selectedSede, selectedServicios);
                }
            }

            setError(errorMsg);
        } finally {
            setLoading(false);
        }
    };

    if (checkingPermission || loadingSedes) {
        return (
            <Container className="mt-5 text-center">
                <Spinner animation="border" />
                <p className="mt-3">Cargando...</p>
            </Container>
        );
    }

    if (success) {
        const successButtonStyle: React.CSSProperties = branding ? {
            backgroundColor: branding.color_primario,
            borderColor: branding.color_primario,
            color: '#ffffff'
        } : {};

        return (
            <Container className="mt-5">
                <Row className="justify-content-center">
                    <Col md={6}>
                        <Alert variant="success" className="text-center">
                            <CheckCircleFill size={64} className="mb-3 text-success" />
                            <h3>¡Reserva Confirmada!</h3>
                            <p className="mt-3">
                                Hemos enviado un enlace a <strong>{email}</strong> para que puedas ver tus citas.
                            </p>
                            <p>
                                El enlace es válido por 15 minutos. Revisa tu bandeja de entrada.
                            </p>
                            <hr />
                            <Button
                                variant={branding ? undefined : "primary"}
                                onClick={() => setSuccess(false)}
                                style={branding ? successButtonStyle : undefined}
                            >
                                Hacer Otra Reserva
                            </Button>
                        </Alert>
                    </Col>
                </Row>
            </Container>
        );
    }

    const organizacionNombre = sedes && sedes.length > 0 ? sedes[0].organizacion_nombre : null;

    // Estilos dinámicos basados en branding
    const containerStyle: React.CSSProperties = branding ? {
        backgroundColor: branding.color_fondo
    } : {};

    const cardStyle: React.CSSProperties = branding ? {
        border: `2px solid ${branding.color_primario}`,
        backgroundColor: branding.color_fondo
    } : {};

    const titleStyle: React.CSSProperties = branding ? {
        color: branding.color_primario
    } : {};

    const textStyle: React.CSSProperties = branding ? {
        color: branding.color_texto
    } : {};

    const buttonStyle: React.CSSProperties = branding ? {
        backgroundColor: branding.color_primario,
        borderColor: branding.color_primario,
        color: '#ffffff'
    } : {};

    return (
        <Container className="mt-5" style={containerStyle}>
            <Row className="justify-content-center">
                <Col md={8}>
                    <Card style={cardStyle}>
                        <Card.Body>
                            {/* Logo personalizado */}
                            {branding?.logo_url && (
                                <div className="text-center mb-4">
                                    <img
                                        src={branding.logo_url}
                                        alt={organizacionNombre || 'Logo'}
                                        style={{ maxHeight: '80px', maxWidth: '200px', objectFit: 'contain' }}
                                    />
                                </div>
                            )}

                            <Card.Title className="text-center mb-4">
                                <h2 style={titleStyle}>Agenda tu Cita</h2>
                                {organizacionNombre && (
                                    <h4 style={titleStyle}>{organizacionNombre}</h4>
                                )}
                                {branding?.texto_bienvenida ? (
                                    <p style={textStyle}>{branding.texto_bienvenida}</p>
                                ) : (
                                    <p className="text-muted">Completa el formulario para reservar</p>
                                )}
                            </Card.Title>

                            {error && <Alert variant="danger">{error}</Alert>}

                            <Form onSubmit={handleSubmit}>
                                {/* Información Personal */}
                                <h5 className="mb-3" style={titleStyle}>Información Personal</h5>
                                <Form.Group className="mb-3">
                                    <Form.Label>Nombre Completo *</Form.Label>
                                    <Form.Control
                                        type="text"
                                        value={nombre}
                                        onChange={(e) => setNombre(e.target.value)}
                                        required
                                        placeholder="Juan Pérez"
                                    />
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>Email *</Form.Label>
                                    <Form.Control
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                        placeholder="tu@email.com"
                                    />
                                    <Form.Text className="text-muted">
                                        Recibirás un enlace para ver tu cita
                                    </Form.Text>
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>Teléfono *</Form.Label>
                                    <Form.Control
                                        type="tel"
                                        value={telefono}
                                        onChange={(e) => setTelefono(e.target.value)}
                                        required
                                        placeholder="+57 123 456 7890"
                                    />
                                </Form.Group>

                                <hr />

                                {/* Detalles de la Cita */}
                                <h5 className="mb-3" style={titleStyle}>Detalles de la Cita</h5>
                                <Form.Group className="mb-3">
                                    <Form.Label>Sede *</Form.Label>
                                    <Form.Control
                                        as="select"
                                        value={selectedSede}
                                        onChange={(e) => setSelectedSede(e.target.value)}
                                        required
                                    >
                                        <option value="">Selecciona una sede</option>
                                        {sedes.map((sede) => (
                                            <option key={sede.id} value={sede.id}>{sede.nombre}</option>
                                        ))}
                                    </Form.Control>
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>Servicios *</Form.Label>
                                    <Form.Control
                                        as="select"
                                        multiple
                                        value={selectedServicios}
                                        onChange={(e) => {
                                            const selected = Array.from((e.target as unknown as HTMLSelectElement).selectedOptions, option => option.value);
                                            setSelectedServicios(selected);
                                        }}
                                        required
                                        style={{ height: '120px' }}
                                    >
                                        {servicios.map((servicio) => (
                                            <option key={servicio.id} value={servicio.id}>
                                                {servicio.nombre} - ${servicio.precio}
                                            </option>
                                        ))}
                                    </Form.Control>
                                    <Form.Text className="text-muted">
                                        Mantén Ctrl (Cmd en Mac) para seleccionar múltiples
                                    </Form.Text>
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>Colaborador *</Form.Label>
                                    <Form.Control
                                        as="select"
                                        value={selectedRecurso}
                                        onChange={(e) => setSelectedRecurso(e.target.value)}
                                        required
                                        disabled={!selectedSede}
                                    >
                                        <option value="">Selecciona un colaborador</option>
                                        {recursos.map((recurso) => (
                                            <option key={recurso.id} value={recurso.id}>{recurso.nombre}</option>
                                        ))}
                                    </Form.Control>
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>Fecha *</Form.Label>
                                    <Form.Control
                                        type="date"
                                        value={date}
                                        onChange={(e) => setDate(e.target.value)}
                                        min={new Date().toISOString().split('T')[0]}
                                        required
                                        disabled={!selectedRecurso || selectedServicios.length === 0}
                                    />
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>Hora *</Form.Label>
                                    <Form.Control
                                        as="select"
                                        value={selectedSlot}
                                        onChange={(e) => setSelectedSlot(e.target.value)}
                                        required
                                        disabled={!date || availableSlots.length === 0}
                                    >
                                        <option value="">Selecciona una hora</option>
                                        {availableSlots.map((slot) => (
                                            <option key={slot.start} value={slot.start}>
                                                {new Date(slot.start).toLocaleTimeString('es-ES', {
                                                    hour: '2-digit',
                                                    minute: '2-digit'
                                                })}
                                            </option>
                                        ))}
                                    </Form.Control>
                                    {date && availableSlots.length === 0 && (
                                        <Form.Text className="text-danger">
                                            No hay horarios disponibles para esta fecha
                                        </Form.Text>
                                    )}
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>Comentarios (Opcional)</Form.Label>
                                    <Form.Control
                                        as="textarea"
                                        rows={3}
                                        value={comentario}
                                        onChange={(e) => setComentario(e.target.value)}
                                        placeholder="Información adicional..."
                                    />
                                </Form.Group>

                                <hr />

                                <div className="d-grid gap-2">
                                    <Button
                                        variant={branding ? undefined : "primary"}
                                        type="submit"
                                        disabled={loading}
                                        size="lg"
                                        style={branding ? buttonStyle : undefined}
                                    >
                                        {loading ? (
                                            <>
                                                <Spinner
                                                    as="span"
                                                    animation="border"
                                                    size="sm"
                                                    className="me-2"
                                                />
                                                Procesando...
                                            </>
                                        ) : (
                                            'Confirmar Reserva'
                                        )}
                                    </Button>
                                </div>
                            </Form>

                            <div className="text-center mt-4">
                                <p className="text-muted">
                                    ¿Ya tienes cuenta? <Link to="/login">Iniciar Sesión</Link>
                                </p>
                            </div>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </Container>
    );
};

export default PublicBookingPage;
