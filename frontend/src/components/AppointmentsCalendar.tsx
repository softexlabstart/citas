import React, { useEffect, useMemo, useState } from 'react';
import { Calendar, momentLocalizer, Event, Views, NavigateAction } from 'react-big-calendar';
import moment from 'moment';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import { Container, Spinner, Alert, Modal, Button, Badge, Row, Col, Form, ListGroup } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { useApi } from '../hooks/useApi';
import { getAllAppointments, getBloqueos, Bloqueo, getRecursos } from '../api';
import { Appointment } from '../interfaces/Appointment';
import { Recurso } from '../interfaces/Recurso';
import { statusConfig } from '../constants/appointmentStatus';

const localizer = momentLocalizer(moment);

// Extend the Event type from react-big-calendar to include our custom properties
interface CalendarEvent extends Event {
    type: 'appointment' | 'block';
    resource: Appointment | Bloqueo;
}

const AppointmentsCalendar: React.FC = () => {
    const { t } = useTranslation();
    const { data: appointments, loading: loadingAppointments, error: errorAppointments, request: fetchAppointments } = useApi<Appointment[], [string, string]>(getAllAppointments);
    const { data: bloqueos, loading: loadingBloqueos, error: errorBloqueos, request: fetchBloqueos } = useApi<Bloqueo[], [string | undefined, string, string]>(getBloqueos);
    const { data: recursos, loading: loadingRecursos, request: fetchRecursos } = useApi<Recurso[], [string | undefined]>(getRecursos);
    const [showModal, setShowModal] = useState(false);
    const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);
    const [selectedResourceId, setSelectedResourceId] = useState<string>('');
    const [dateRange, setDateRange] = useState<{ start: Date, end: Date } | null>(null);
    const [showMoreModal, setShowMoreModal] = useState(false);
    const [moreModalEvents, setMoreModalEvents] = useState<CalendarEvent[]>([]);
    const [moreModalDate, setMoreModalDate] = useState<Date | null>(null);

    // Set the initial date range on component mount
    useEffect(() => {
        const today = new Date();
        setDateRange({
            start: moment(today).startOf('month').toDate(),
            end: moment(today).endOf('month').toDate(),
        });
        fetchRecursos(undefined);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Fetch data whenever the date range changes
    useEffect(() => {
        if (dateRange) {
            fetchAppointments(dateRange.start.toISOString(), dateRange.end.toISOString());
            fetchBloqueos(undefined, dateRange.start.toISOString(), dateRange.end.toISOString());
        }
    }, [dateRange, fetchAppointments, fetchBloqueos]);

    const events: CalendarEvent[] = useMemo(() => {
        const filteredAppointments = appointments?.filter(app => !selectedResourceId || app.colaboradores.some(r => r.id === Number(selectedResourceId))) || [];
        const appointmentEvents = filteredAppointments.map((appointment) => ({
            title: `${appointment.nombre} - ${appointment.servicios.map(s => s.nombre).join(', ')}`,
            start: new Date(appointment.fecha),
            end: new Date(new Date(appointment.fecha).getTime() + (appointment.servicios.reduce((sum, s) => sum + (s.duracion_estimada || 0), 0) || 60) * 60 * 1000),
            resource: appointment,
            type: 'appointment' as 'appointment', // Explicitly cast the literal type
        }));

        const filteredBloqueos = bloqueos?.filter(block => !selectedResourceId || block.colaborador.id === Number(selectedResourceId)) || [];
        const blockEvents = filteredBloqueos.map((bloqueo) => ({
            title: `${t('block')}: ${bloqueo.motivo}`,
            start: new Date(bloqueo.fecha_inicio),
            end: new Date(bloqueo.fecha_fin),
            resource: bloqueo,
            type: 'block' as 'block', // Explicitly cast the literal type
        }));

        return [...appointmentEvents, ...blockEvents];
    }, [appointments, bloqueos, t, selectedResourceId]);

    const handleSelectEvent = (event: CalendarEvent) => {
        // Only open modal for appointments, not for blocks
        if (event.type === 'appointment') {
            setSelectedAppointment(event.resource as Appointment);
            setShowModal(true);
        }
    };

    const handleCloseModal = () => {
        setShowModal(false);
        setSelectedAppointment(null);
    };

    const handleShowMore = (events: CalendarEvent[], date: Date) => {
        setMoreModalEvents(events);
        setMoreModalDate(date);
        setShowMoreModal(true);
    };

    const handleNavigate = (newDate: Date, view: string) => {
        setDateRange({
            start: moment(newDate).startOf(view as moment.unitOfTime.StartOf).toDate(),
            end: moment(newDate).endOf(view as moment.unitOfTime.StartOf).toDate(),
        });
    };

    const eventPropGetter = (event: CalendarEvent) => {
        let style: React.CSSProperties = {};
        if (event.type === 'block') {
            style.backgroundColor = '#6c757d'; // Bootstrap 'secondary' color for blocks
        } else if (event.type === 'appointment') {
            const appointment = event.resource as Appointment;
            style.backgroundColor = statusConfig[appointment.estado]?.color || '#cccccc';
        }
        return { style };
    };

    const calendarMessages = {
        allDay: t('all_day'),
        previous: t('previous'),
        next: t('next'),
        today: t('today'),
        month: t('month'),
        week: t('week'),
        day: t('day'),
        agenda: t('agenda'),
        date: t('date'),
        time: t('time'),
        event: t('event'),
        noEventsInRange: t('no_events_in_range'),
    };

    const errorMessage = errorAppointments || errorBloqueos;

    return (
        <Container className="mt-5 bg-white p-4 rounded shadow-sm">
            <Row className="align-items-center mb-4">
                <Col md={8}>
                    <h2>{t('appointments_calendar')}</h2>
                </Col>
                <Col md={4}>
                    <Form.Group>
                        <Form.Label>{t('filtrar por colaborador')}</Form.Label>
                        <Form.Control as="select" value={selectedResourceId} onChange={(e) => setSelectedResourceId(e.target.value)} disabled={loadingRecursos}>
                            <option value="">{t('todos los colaboradores')}</option>
                            {recursos?.map(r => <option key={r.id} value={r.id}>{r.nombre}</option>)}
                        </Form.Control>
                    </Form.Group>
                </Col>
            </Row>
            
            {(loadingAppointments || loadingBloqueos || loadingRecursos) && <div className="text-center"><Spinner animation="border" /></div>}
            {errorMessage && <Alert variant="danger">{t(errorMessage)}</Alert>}
            
            {!(loadingAppointments || loadingBloqueos || loadingRecursos) && (
                <div style={{ height: '70vh' }}>
                    <Calendar<CalendarEvent> localizer={localizer} events={events} startAccessor="start" endAccessor="end" messages={calendarMessages} onSelectEvent={handleSelectEvent} eventPropGetter={eventPropGetter} onNavigate={handleNavigate} onShowMore={handleShowMore} style={{ height: '100%' }} />
                </div>
            )}

            <Modal show={showModal} onHide={handleCloseModal} centered>
                <Modal.Header closeButton>
                    <Modal.Title>{t('appointment_details')}</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    {selectedAppointment && (
                        <div>
                            <p><strong>{t('client_name')}:</strong> {selectedAppointment.nombre}</p>
                            <p><strong>{t('service')}:</strong> {selectedAppointment.servicios.map(s => s.nombre).join(', ')}</p>
                            <p><strong>{t('sede_label')}:</strong> {selectedAppointment.sede.nombre}</p>
                            <p><strong>{t('date')}:</strong> {new Date(selectedAppointment.fecha).toLocaleString()}</p>
                            <p><strong>{t('resources')}:</strong> {selectedAppointment.colaboradores.map(r => r.nombre).join(', ')}</p>
                            <p><strong>{t('status')}:</strong> 
                                <Badge bg={statusConfig[selectedAppointment.estado]?.color || 'light'}>
                                    {t(statusConfig[selectedAppointment.estado]?.key || selectedAppointment.estado.toLowerCase())}
                                </Badge>
                            </p>
                        </div>
                    )}
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={handleCloseModal}>
                        {t('close')}
                    </Button>
                </Modal.Footer>
            </Modal>

            <Modal show={showMoreModal} onHide={() => setShowMoreModal(false)} centered>
                <Modal.Header closeButton>
                    <Modal.Title>{t('appointments_for_date', { date: moreModalDate ? moment(moreModalDate).format('LL') : '' })}</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    {moreModalEvents.length > 0 ? (
                        <ListGroup>
                            {moreModalEvents.map((event, index) => (
                                <ListGroup.Item key={index} action onClick={() => {
                                    if (event.type === 'appointment') {
                                        setSelectedAppointment(event.resource as Appointment);
                                        setShowModal(true);
                                        setShowMoreModal(false); // Close the "more" modal
                                    }
                                }}>
                                    <strong>{event.title}</strong>
                                    <br />
                                    <small>{moment(event.start).format('LT')} - {moment(event.end).format('LT')}</small>
                                    {event.type === 'appointment' && (
                                        <>
                                            <br />
                                            <Badge bg={statusConfig[(event.resource as Appointment).estado]?.color || 'light'}>
                                                {t(statusConfig[(event.resource as Appointment).estado]?.key || (event.resource as Appointment).estado.toLowerCase())}
                                            </Badge>
                                        </>
                                    )}
                                </ListGroup.Item>
                            ))}
                        </ListGroup>
                    ) : (
                        <p>{t('no_appointments_for_this_day')}</p>
                    )}
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={() => setShowMoreModal(false)}>
                        {t('close')}
                    </Button>
                </Modal.Footer>
            </Modal>
        </Container>
    );
};

export default AppointmentsCalendar;