import React from 'react';
import { Card, Button, Alert } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { UserDashboardSummary } from '../api';

interface UserDashboardProps {
    data: UserDashboardSummary;
}

const UserDashboard: React.FC<UserDashboardProps> = ({ data }) => {
    const { t } = useTranslation();
    const navigate = useNavigate();

    return (
        <Card className="text-center shadow-sm">
            <Card.Header as="h4">{t('your_next_appointment')}</Card.Header>
            <Card.Body>
                {data.proxima_cita ? (
                    <>
                        <Card.Title className="fs-3">{data.proxima_cita.servicios.map(s => s.nombre).join(', ')}</Card.Title>
                        <Card.Text className="fs-5">
                            {new Date(data.proxima_cita.fecha).toLocaleDateString('es-ES', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                        </Card.Text>
                        <Card.Text className="fs-4 fw-bold">
                            {new Date(data.proxima_cita.fecha).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}
                        </Card.Text>
                        <p className="text-muted">{t('at_sede')} {data.proxima_cita.sede.nombre}</p>
                        <Button onClick={() => navigate('/appointments')} variant="primary">{t('manage_my_appointments')}</Button>
                    </>
                ) : (
                    <>
                        <Alert variant="info">{t('no_upcoming_appointments_user')}</Alert>
                        <Button onClick={() => navigate('/appointments')} variant="success" size="lg">{t('schedule_new_appointment')}</Button>
                    </>
                )}
            </Card.Body>
        </Card>
    );
};

export default UserDashboard;