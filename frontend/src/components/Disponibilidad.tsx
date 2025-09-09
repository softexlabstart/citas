import React, { useState, useEffect } from 'react';
import { getSedes, getServicios, getNextAvailableSlots, NextAvailableSlot } from '../api';
import { Sede } from '../interfaces/Sede';
import { Service } from '../interfaces/Service';
import { Form, Button, Container, Row, Col, Card, Spinner, Alert, ListGroup } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import { useApi } from '../hooks/useApi';
import { useNavigate } from 'react-router-dom';
import { CalendarPlus } from 'react-bootstrap-icons';

const Disponibilidad: React.FC = () => {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const [selectedSede, setSelectedSede] = useState<string>('');
    const [selectedServicio, setSelectedServicio] = useState<string>('');

    const { data: sedes, loading: loadingSedes, request: fetchSedes } = useApi<Sede[], []>(getSedes);
    const { data: servicios, loading: loadingServicios, request: fetchServicios } = useApi<Service[], [string]>(getServicios);
    const { data: availableSlots, loading: loadingAvailability, error: errorAvailability, request: fetchNextSlots } = useApi<NextAvailableSlot[], [string, string]>(getNextAvailableSlots);

    useEffect(() => {
        fetchSedes();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        if (selectedSede) {
            fetchServicios(selectedSede);
            setSelectedServicio(''); // Reset selected service when sede changes
        }
    }, [selectedSede, fetchServicios]);

    const handleSearch = () => {
        if (!selectedSede || !selectedServicio) {
            toast.warn(t('select_sede_and_service'));
            return;
        }
        fetchNextSlots(selectedServicio, selectedSede);
    };

    const handleScheduleClick = (slot: NextAvailableSlot) => {
        navigate('/appointments', {
            state: {
                prefill: {
                    nombre: '', // Explicitly set name as empty for the user to fill
                    sede_id: selectedSede,
                    servicio_id: selectedServicio,
                    recurso_id: slot.recurso.id,
                    fecha: slot.start,
                }
            }
        });
    };

    const anyError = errorAvailability;

    return (
        <Container className="mt-4">
            <Row className="justify-content-md-center">
                <Col md={8}>
                    <Card className="p-4 rounded shadow-sm">
                        <Card.Body>
                            <Card.Title className="text-center mb-4">{t('find_next_appointment')}</Card.Title>
                            {anyError && <Alert variant="danger">{t(anyError) || anyError}</Alert>}
                            <Form>
                                <Form.Group className="mb-3">
                                    <Form.Label>{t('sede_label')}</Form.Label>
                                    {loadingSedes && <Spinner animation="border" size="sm" />}
                                    <Form.Control
                                        as="select"
                                        value={selectedSede}
                                        onChange={(e) => setSelectedSede(e.target.value)}
                                        disabled={loadingSedes}
                                    >
                                        <option value="">{t('select_sede')}</option>
                                        {sedes?.map((sede) => (
                                            <option key={sede.id} value={sede.id}>
                                                {sede.nombre}
                                            </option>
                                        ))}
                                    </Form.Control>
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>{t('service_label')}</Form.Label>
                                    {loadingServicios && <Spinner animation="border" size="sm" />}
                                    <Form.Control
                                        as="select"
                                        value={selectedServicio}
                                        onChange={(e) => setSelectedServicio(e.target.value)}
                                        disabled={!selectedSede || loadingServicios}
                                    >
                                        <option value="">{t('select_service')}</option>
                                        {servicios?.map((service) => (
                                            <option key={service.id} value={service.id}>
                                                {service.nombre}
                                            </option>
                                        ))}
                                    </Form.Control>
                                </Form.Group>

                                <div className="d-grid">
                                    <Button variant="primary" onClick={handleSearch} disabled={loadingAvailability || !selectedSede || !selectedServicio}>
                                        {loadingAvailability ? <Spinner as="span" animation="border" size="sm" /> : t('search_next_availability')}
                                    </Button>
                                </div>
                            </Form>

                            {availableSlots && !loadingAvailability && (
                                <>
                                    <h5 className="mt-4">{t('next_available_slots')}:</h5>
                                    {availableSlots.length > 0 ? (
                                        <ListGroup>
                                            {availableSlots.map((slot, index) => (
                                                <ListGroup.Item key={index} className="d-flex justify-content-between align-items-center">
                                                    <div>
                                                        <strong>{new Date(slot.start).toLocaleString('es-ES', { dateStyle: 'full', timeStyle: 'short' })}</strong>
                                                        <br />
                                                        <small className="text-muted">{t('with_resource')} {slot.recurso.nombre}</small>
                                                    </div>
                                                    <Button variant="outline-success" size="sm" onClick={() => handleScheduleClick(slot)}>
                                                        <CalendarPlus className="me-1" /> {t('schedule')}
                                                    </Button>
                                                </ListGroup.Item>
                                            ))}
                                        </ListGroup>
                                    ) : (
                                        <Alert variant="info" className="mt-3">{t('no_available_slots_for_service')}</Alert>
                                    )}
                                </>
                            )}
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </Container>
    );
};

export default Disponibilidad;
