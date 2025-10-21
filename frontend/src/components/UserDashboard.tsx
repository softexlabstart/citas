import React, { useEffect, useState } from 'react';
import { Card, Button, Alert, Modal } from 'react-bootstrap';
import { toast } from 'react-toastify';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { UserDashboardSummary, getClientById, deleteAccount } from '../api';
import { useAuth } from '../contexts/AuthContext';
import { Client } from '../interfaces/Client';

interface UserDashboardProps {
    data: UserDashboardSummary;
}

const UserDashboard: React.FC<UserDashboardProps> = ({ data }) => {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const [showDeleteConfirmModal, setShowDeleteConfirmModal] = useState(false);
    const { user } = useAuth();
    const [loading, setLoading] = useState(true);
    const [clientData, setClientData] = useState<Client | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchClientData = async () => {
            // Solo cargar datos de cliente si el usuario tiene rol 'cliente'
            if (user && user.id && user.perfil?.role === 'cliente') {
                setLoading(true);
                try {
                    const response = await getClientById(user.id);
                    if (response.data) {
                        setClientData(response.data);
                    } else {
                        setError(t('error_fetching_profile'));
                    }
                } catch (err: any) {
                    setError(err.message || t('error_fetching_profile'));
                } finally {
                    setLoading(false);
                }
            } else {
                // No es cliente, no necesita datos de cliente
                setLoading(false);
            }
        };
        fetchClientData();
    }, [user, t]); // Removed getClientById from dependency array

    return (
        <>
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

            <Card className="text-center shadow-sm mt-4">
                <Card.Header as="h4">{t('personal_data_management')}</Card.Header>
                <Card.Body>
                    <Button onClick={() => navigate('/profile/edit')} variant="info" className="me-2">
                        {t('edit_my_information')}
                    </Button>
                    <Button variant="warning" onClick={() => alert(t('request_opposition_sent'))} className="me-2"> {/* Placeholder for opposition logic */}
                        {t('oppose_data_processing')}
                    </Button>
                    <Button variant="danger" onClick={() => setShowDeleteConfirmModal(true)}>
                        {t('delete_my_account')}
                    </Button>
                </Card.Body>
            </Card>
            <Modal show={showDeleteConfirmModal} onHide={() => setShowDeleteConfirmModal(false)} centered>
                <Modal.Header closeButton>
                    <Modal.Title>{t('confirm_account_deletion')}</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <p>{t('are_you_sure_delete_account')}</p>
                    <Alert variant="warning">{t('account_deletion_warning')}</Alert>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={() => setShowDeleteConfirmModal(false)}>
                        {t('cancel')}
                    </Button>
                    <Button variant="danger" onClick={async () => {
                        try {
                            await deleteAccount();
                            toast.success(t('account_deleted_successfully'));
                            setShowDeleteConfirmModal(false);
                            // Assuming logout is available in AuthContext and clears user session
                            // You might need to adjust this based on your AuthContext implementation
                            // For now, we'll just navigate to home and let the token interceptor handle logout
                            navigate('/');
                        } catch (error) {
                            toast.error(t('error_deleting_account'));
                            setShowDeleteConfirmModal(false);
                        }
                    }}>
                        {t('delete_my_account')}
                    </Button>
                </Modal.Footer>
            </Modal>
        </>
    );
};

export default UserDashboard;