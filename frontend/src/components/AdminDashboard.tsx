import React from 'react';
import { Row, Col, Card, ListGroup, Badge } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { CalendarCheck, ClockHistory, CashCoin } from 'react-bootstrap-icons';
import { AdminDashboardSummary } from '../api';
import { statusConfig } from '../constants/appointmentStatus';

interface AdminDashboardProps {
    data: AdminDashboardSummary;
}

const AdminDashboard: React.FC<AdminDashboardProps> = ({ data }) => {
    const { t } = useTranslation();

    return (
        <>
            <Row className="mb-4">
                <Col md={4}>
                    <Card className="text-center shadow-sm h-100">
                        <Card.Body>
                            <CalendarCheck size={40} className="text-primary mb-2" />
                            <Card.Title>{t('appointments_today')}</Card.Title>
                            <Card.Text className="fs-2 fw-bold">{data.citas_hoy}</Card.Text>
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={4}>
                    <Card className="text-center shadow-sm h-100">
                        <Card.Body>
                            <ClockHistory size={40} className="text-warning mb-2" />
                            <Card.Title>{t('pending_confirmation')}</Card.Title>
                            <Card.Text className="fs-2 fw-bold">{data.pendientes_confirmacion}</Card.Text>
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={4}>
                    <Card className="text-center shadow-sm h-100">
                        <Card.Body>
                            <CashCoin size={40} className="text-success mb-2" />
                            <Card.Title>{t('revenue_this_month')}</Card.Title>
                            <Card.Text className="fs-2 fw-bold">${(data.ingresos_mes || 0).toFixed(2)}</Card.Text>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>

            <Card className="shadow-sm">
                <Card.Header as="h5">{t('upcoming_appointments')}</Card.Header>
                <ListGroup variant="flush">
                    {data.proximas_citas.length > 0 ? (
                        data.proximas_citas.map(cita => (
                            <ListGroup.Item key={cita.id} className="d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>{cita.nombre}</strong> - {cita.servicio.nombre}
                                    <br />
                                    <small className="text-muted">{new Date(cita.fecha).toLocaleString()}</small>
                                </div>
                                <Badge bg={statusConfig[cita.estado]?.color || 'light'}>{t(statusConfig[cita.estado]?.key || cita.estado.toLowerCase())}</Badge>
                            </ListGroup.Item>
                        ))
                    ) : (
                        <ListGroup.Item>{t('no_upcoming_appointments')}</ListGroup.Item>
                    )}
                </ListGroup>
                <Card.Footer className="text-center">
                    <Link to="/appointments">{t('view_all_appointments')}</Link>
                </Card.Footer>
            </Card>
        </>
    );
};

export default AdminDashboard;