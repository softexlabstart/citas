import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert, Spinner } from 'react-bootstrap';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { CheckCircleFill, PersonFill, CalendarCheck, ClockFill, InfoCircleFill } from 'react-bootstrap-icons';
import { createPublicBooking, getServicios, getDisponibilidad, PublicBookingData } from '../api';
import { useApi } from '../hooks/useApi';
import { useAppointmentForm } from '../hooks/useAppointmentForm';
import './PublicBookingPage.css';

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

    // Determinar paso actual
    const getCurrentStep = () => {
        if (!nombre || !email || !telefono) return 1;
        if (!selectedSede || !selectedServicios.length || !selectedRecurso) return 2;
        if (!date || !selectedSlot) return 3;
        return 3;
    };

    const currentStep = getCurrentStep();

    if (checkingPermission || loadingSedes) {
        return (
            <div className="public-booking-page">
                <Container>
                    <Row className="justify-content-center">
                        <Col md={8}>
                            <div className="loading-overlay">
                                <div className="loading-spinner"></div>
                                <p className="loading-text">Cargando información...</p>
                            </div>
                        </Col>
                    </Row>
                </Container>
            </div>
        );
    }

    // Aplicar estilos de branding dinámicamente
    useEffect(() => {
        if (branding) {
            const root = document.documentElement;
            root.style.setProperty('--brand-primary', branding.color_primario || '#667eea');
            root.style.setProperty('--brand-secondary', branding.color_secundario || '#764ba2');
            root.style.setProperty('--brand-text', branding.color_texto || '#2d3748');
            root.style.setProperty('--brand-background', branding.color_fondo || '#ffffff');
        }

        // Cleanup: restaurar colores por defecto al desmontar
        return () => {
            const root = document.documentElement;
            root.style.removeProperty('--brand-primary');
            root.style.removeProperty('--brand-secondary');
            root.style.removeProperty('--brand-text');
            root.style.removeProperty('--brand-background');
        };
    }, [branding]);

    if (success) {
        return (
            <div className="public-booking-page">
                <Container>
                    <Row className="justify-content-center">
                        <Col md={8} lg={6}>
                            <Card className="booking-card">
                                <Card.Body className="booking-card-body">
                                    <div className="success-screen">
                                        <div className="success-icon">
                                            <CheckCircleFill />
                                        </div>
                                        <h2 className="success-title">¡Reserva Confirmada!</h2>
                                        <div className="success-message">
                                            <p>
                                                Hemos enviado un enlace de confirmación a<br />
                                                <strong>{email}</strong>
                                            </p>
                                            <div className="info-box">
                                                <InfoCircleFill className="info-box-icon" />
                                                <span className="info-box-text">
                                                    El enlace es válido por 15 minutos. Revisa tu bandeja de entrada.
                                                </span>
                                            </div>
                                        </div>
                                        <Button
                                            className="submit-button"
                                            onClick={() => {
                                                setSuccess(false);
                                                setNombre('');
                                                setEmail('');
                                                setTelefono('');
                                                setSelectedServicios([]);
                                                setDate('');
                                                setSelectedSlot('');
                                                setComentario('');
                                            }}
                                        >
                                            Hacer Otra Reserva
                                        </Button>
                                    </div>
                                </Card.Body>
                            </Card>
                        </Col>
                    </Row>
                </Container>
            </div>
        );
    }

    const organizacionNombre = sedes && sedes.length > 0 ? sedes[0].organizacion_nombre : null;

    return (
        <div className="public-booking-page">
            <Container>
                <Row className="justify-content-center">
                    <Col md={10} lg={8}>
                        {/* Header */}
                        <div className="booking-header">
                            {branding?.logo_url && (
                                <img
                                    src={branding.logo_url}
                                    alt={organizacionNombre || 'Logo'}
                                    className="booking-logo"
                                />
                            )}
                            <h1 className="booking-title">Agenda tu Cita</h1>
                            {organizacionNombre && (
                                <h2 className="booking-subtitle">{organizacionNombre}</h2>
                            )}
                            <p className="booking-description">
                                {branding?.texto_bienvenida || 'Completa el formulario para reservar tu cita de manera rápida y sencilla'}
                            </p>
                        </div>

                        {/* Main Card */}
                        <Card className="booking-card">
                            <Card.Body className="booking-card-body">
                                {/* Step Indicator */}
                                <div className="step-indicator">
                                    <div className={`step-item ${currentStep >= 1 ? 'active' : ''} ${currentStep > 1 ? 'completed' : ''}`}>
                                        <div className="step-number">
                                            {currentStep > 1 ? '✓' : '1'}
                                        </div>
                                        <div className="step-label">Tus Datos</div>
                                    </div>
                                    <div className={`step-item ${currentStep >= 2 ? 'active' : ''} ${currentStep > 2 ? 'completed' : ''}`}>
                                        <div className="step-number">
                                            {currentStep > 2 ? '✓' : '2'}
                                        </div>
                                        <div className="step-label">Servicio</div>
                                    </div>
                                    <div className={`step-item ${currentStep >= 3 ? 'active' : ''}`}>
                                        <div className="step-number">3</div>
                                        <div className="step-label">Fecha y Hora</div>
                                    </div>
                                </div>

                                {error && (
                                    <Alert variant="danger" className="mb-4">
                                        <strong>Error:</strong> {error}
                                    </Alert>
                                )}

                                <Form onSubmit={handleSubmit}>
                                    {/* Información Personal */}
                                    <div className="section-header">
                                        <div className="section-icon">
                                            <PersonFill />
                                        </div>
                                        <h3 className="section-title">Información Personal</h3>
                                    </div>

                                    <Row>
                                        <Col md={12} className="form-group-enhanced">
                                            <Form.Label className="form-label-enhanced">
                                                Nombre Completo
                                                <span className="required-indicator">*</span>
                                            </Form.Label>
                                            <Form.Control
                                                type="text"
                                                value={nombre}
                                                onChange={(e) => setNombre(e.target.value)}
                                                required
                                                placeholder="Juan Pérez"
                                                className="form-control-enhanced"
                                            />
                                        </Col>
                                    </Row>

                                    <Row>
                                        <Col md={6} className="form-group-enhanced">
                                            <Form.Label className="form-label-enhanced">
                                                Email
                                                <span className="required-indicator">*</span>
                                            </Form.Label>
                                            <Form.Control
                                                type="email"
                                                value={email}
                                                onChange={(e) => setEmail(e.target.value)}
                                                required
                                                placeholder="tu@email.com"
                                                className="form-control-enhanced"
                                            />
                                            <Form.Text className="text-muted">
                                                <small>Recibirás confirmación por email</small>
                                            </Form.Text>
                                        </Col>

                                        <Col md={6} className="form-group-enhanced">
                                            <Form.Label className="form-label-enhanced">
                                                Teléfono
                                                <span className="required-indicator">*</span>
                                            </Form.Label>
                                            <Form.Control
                                                type="tel"
                                                value={telefono}
                                                onChange={(e) => setTelefono(e.target.value)}
                                                required
                                                placeholder="+57 123 456 7890"
                                                className="form-control-enhanced"
                                            />
                                        </Col>
                                    </Row>

                                    {/* Detalles de la Cita */}
                                    <div className="section-header">
                                        <div className="section-icon">
                                            <CalendarCheck />
                                        </div>
                                        <h3 className="section-title">Detalles de la Cita</h3>
                                    </div>

                                    <Row>
                                        <Col md={6} className="form-group-enhanced">
                                            <Form.Label className="form-label-enhanced">
                                                Sede
                                                <span className="required-indicator">*</span>
                                            </Form.Label>
                                            <Form.Control
                                                as="select"
                                                value={selectedSede}
                                                onChange={(e) => setSelectedSede(e.target.value)}
                                                required
                                                className="form-control-enhanced"
                                            >
                                                <option value="">Selecciona una sede</option>
                                                {sedes.map((sede) => (
                                                    <option key={sede.id} value={sede.id}>{sede.nombre}</option>
                                                ))}
                                            </Form.Control>
                                        </Col>

                                        <Col md={6} className="form-group-enhanced">
                                            <Form.Label className="form-label-enhanced">
                                                Colaborador
                                                <span className="required-indicator">*</span>
                                            </Form.Label>
                                            <Form.Control
                                                as="select"
                                                value={selectedRecurso}
                                                onChange={(e) => setSelectedRecurso(e.target.value)}
                                                required
                                                disabled={!selectedSede}
                                                className="form-control-enhanced"
                                            >
                                                <option value="">Selecciona un colaborador</option>
                                                {recursos.map((recurso) => (
                                                    <option key={recurso.id} value={recurso.id}>{recurso.nombre}</option>
                                                ))}
                                            </Form.Control>
                                        </Col>
                                    </Row>

                                    <div className="form-group-enhanced">
                                        <Form.Label className="form-label-enhanced">
                                            Servicios
                                            <span className="required-indicator">*</span>
                                        </Form.Label>
                                        <div className="services-grid">
                                            {servicios.map((servicio) => (
                                                <div
                                                    key={servicio.id}
                                                    className={`service-card ${selectedServicios.includes(servicio.id.toString()) ? 'selected' : ''}`}
                                                    onClick={() => {
                                                        const servicioId = servicio.id.toString();
                                                        if (selectedServicios.includes(servicioId)) {
                                                            setSelectedServicios(selectedServicios.filter(id => id !== servicioId));
                                                        } else {
                                                            setSelectedServicios([...selectedServicios, servicioId]);
                                                        }
                                                    }}
                                                >
                                                    <div className="service-card-header">
                                                        <Form.Check
                                                            type="checkbox"
                                                            checked={selectedServicios.includes(servicio.id.toString())}
                                                            onChange={() => {}}
                                                            className="service-checkbox"
                                                        />
                                                        <div className="service-name">{servicio.nombre}</div>
                                                    </div>
                                                    <div className="service-price">${servicio.precio}</div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Fecha y Hora */}
                                    <div className="section-header">
                                        <div className="section-icon">
                                            <ClockFill />
                                        </div>
                                        <h3 className="section-title">Fecha y Hora</h3>
                                    </div>

                                    <Row>
                                        <Col md={12} className="form-group-enhanced">
                                            <Form.Label className="form-label-enhanced">
                                                Fecha
                                                <span className="required-indicator">*</span>
                                            </Form.Label>
                                            <Form.Control
                                                type="date"
                                                value={date}
                                                onChange={(e) => setDate(e.target.value)}
                                                min={new Date().toISOString().split('T')[0]}
                                                required
                                                disabled={!selectedRecurso || selectedServicios.length === 0}
                                                className="form-control-enhanced"
                                            />
                                        </Col>
                                    </Row>

                                    {date && availableSlots.length > 0 && (
                                        <div className="form-group-enhanced">
                                            <Form.Label className="form-label-enhanced">
                                                Horarios Disponibles
                                                <span className="required-indicator">*</span>
                                            </Form.Label>
                                            <div className="time-slots-grid">
                                                {availableSlots.map((slot) => (
                                                    <button
                                                        key={slot.start}
                                                        type="button"
                                                        className={`time-slot-btn ${selectedSlot === slot.start ? 'selected' : ''}`}
                                                        onClick={() => setSelectedSlot(slot.start)}
                                                    >
                                                        {new Date(slot.start).toLocaleTimeString('es-ES', {
                                                            hour: '2-digit',
                                                            minute: '2-digit'
                                                        })}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {date && availableSlots.length === 0 && (
                                        <Alert variant="warning" className="mt-3">
                                            <InfoCircleFill className="me-2" />
                                            No hay horarios disponibles para esta fecha. Por favor, selecciona otra fecha.
                                        </Alert>
                                    )}

                                    <div className="form-group-enhanced">
                                        <Form.Label className="form-label-enhanced">
                                            Comentarios (Opcional)
                                        </Form.Label>
                                        <Form.Control
                                            as="textarea"
                                            rows={3}
                                            value={comentario}
                                            onChange={(e) => setComentario(e.target.value)}
                                            placeholder="¿Algo que debamos saber?"
                                            className="form-control-enhanced"
                                        />
                                    </div>

                                    <Button
                                        type="submit"
                                        disabled={loading || !selectedSlot}
                                        className="submit-button"
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

                                    <div className="text-center mt-4">
                                        <p className="text-muted">
                                            ¿Ya tienes cuenta? <Link to="/login">Iniciar Sesión</Link>
                                        </p>
                                    </div>
                                </Form>
                            </Card.Body>
                        </Card>
                    </Col>
                </Row>
            </Container>
        </div>
    );
};

export default PublicBookingPage;
