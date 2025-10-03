import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert, Spinner } from 'react-bootstrap';
import { useNavigate, Link } from 'react-router-dom';
import { CheckCircleFill } from 'react-bootstrap-icons';
import { createPublicBooking, getServicios, getDisponibilidad, PublicBookingData } from '../api';
import { useApi } from '../hooks/useApi';
import { useAppointmentForm } from '../hooks/useAppointmentForm';

const PublicBookingPage: React.FC = () => {
    const navigate = useNavigate();
    const {
        sedes,
        servicios,
        recursos,
        selectedSede,
        selectedRecurso,
        loadingSedes,
        setSelectedSede,
        setSelectedRecurso,
    } = useAppointmentForm();

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

    const { data: availability, request: fetchAvailableSlots } = useApi<{ disponibilidad: any[] }, [string, number, string, string[]]>(getDisponibilidad);

    const availableSlots = availability?.disponibilidad.filter(slot => slot.status === 'disponible') || [];

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

    if (loadingSedes) {
        return (
            <Container className="mt-5 text-center">
                <Spinner animation="border" />
                <p className="mt-3">Cargando...</p>
            </Container>
        );
    }

    if (success) {
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
                            <Button variant="primary" onClick={() => setSuccess(false)}>
                                Hacer Otra Reserva
                            </Button>
                        </Alert>
                    </Col>
                </Row>
            </Container>
        );
    }

    return (
        <Container className="mt-5">
            <Row className="justify-content-center">
                <Col md={8}>
                    <Card>
                        <Card.Body>
                            <Card.Title className="text-center mb-4">
                                <h2>Agenda tu Cita</h2>
                                <p className="text-muted">Completa el formulario para reservar</p>
                            </Card.Title>

                            {error && <Alert variant="danger">{error}</Alert>}

                            <Form onSubmit={handleSubmit}>
                                {/* Información Personal */}
                                <h5 className="mb-3">Información Personal</h5>
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
                                <h5 className="mb-3">Detalles de la Cita</h5>
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
                                    <Button variant="primary" type="submit" disabled={loading} size="lg">
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
