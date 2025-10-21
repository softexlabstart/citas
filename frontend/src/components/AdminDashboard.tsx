import React from 'react';
import { Row, Col, Card, ListGroup, Badge } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { BarChart, People, Megaphone } from 'react-bootstrap-icons';
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
                    <Link to="/reports" className="text-decoration-none">
                        <Card className="text-center shadow-sm h-100 card-hover">
                            <Card.Body>
                                <BarChart size={40} className="text-primary mb-2" />
                                <Card.Title>{t('reports')}</Card.Title>
                                <Card.Text>{t('reports_description')}</Card.Text>
                            </Card.Body>
                        </Card>
                    </Link>
                </Col>
                <Col md={4}>
                    <Link to="/clients" className="text-decoration-none">
                        <Card className="text-center shadow-sm h-100 card-hover">
                            <Card.Body>
                                <People size={40} className="text-warning mb-2" />
                                <Card.Title>{t('clients')}</Card.Title>
                                <Card.Text>{t('clients_description')}</Card.Text>
                            </Card.Body>
                        </Card>
                    </Link>
                </Col>
                <Col md={4}>
                    <Link to="/marketing" className="text-decoration-none">
                        <Card className="text-center shadow-sm h-100 card-hover">
                            <Card.Body>
                                <Megaphone size={40} className="text-success mb-2" />
                                <Card.Title>{t('marketing')}</Card.Title>
                                <Card.Text>{t('marketing_description')}</Card.Text>
                            </Card.Body>
                        </Card>
                    </Link>
                </Col>
            </Row>

            <Card className="shadow-sm">
                <Card.Header as="h5">{t('upcoming_appointments')}</Card.Header>
                <ListGroup variant="flush">
                    {data.proximas_citas && data.proximas_citas.length > 0 ? (
                        data.proximas_citas.map(cita => (
                            <ListGroup.Item key={cita.id} className="d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>{cita.nombre}</strong> - {cita.servicios.map(s => s.nombre).join(', ')}
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