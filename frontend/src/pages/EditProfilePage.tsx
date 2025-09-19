import React, { useEffect, useState } from 'react';
import { Container, Spinner, Alert } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import ClientForm from '../components/ClientForm';
import { useAuth } from '../contexts/AuthContext';
import { getClientById } from '../api'; // Assuming an API call to get client by ID
import { Client } from '../interfaces/Client';

const EditProfilePage: React.FC = () => {
    const { t } = useTranslation();
    const { user } = useAuth();
    const navigate = useNavigate();
    const [clientData, setClientData] = useState<Client | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchClientData = async () => {
            if (user && user.id) {
                try {
                    setLoading(true);
                    const response = await getClientById(user.id);
                    if (response.success && response.data) {
                        setClientData(response.data);
                    } else {
                        setError(response.error || t('error_fetching_profile'));
                        toast.error(response.error || t('error_fetching_profile'));
                    }
                } catch (err) {
                    setError(t('error_fetching_profile'));
                    toast.error(t('error_fetching_profile'));
                } finally {
                    setLoading(false);
                }
            } else {
                setError(t('user_not_logged_in'));
                setLoading(false);
            }
        };

        fetchClientData();
    }, [user, t]);

    const handleSuccess = () => {
        toast.success(t('profile_updated_successfully'));
        navigate(-1); // Go back to the previous page (e.g., UserDashboard)
    };

    const handleCancel = () => {
        navigate(-1); // Go back to the previous page
    };

    if (loading) {
        return (
            <Container className="mt-5 text-center">
                <Spinner animation="border" role="status">
                    <span className="visually-hidden">{t('loading')}...</span>
                </Spinner>
            </Container>
        );
    }

    if (error) {
        return (
            <Container className="mt-5">
                <Alert variant="danger">{error}</Alert>
            </Container>
        );
    }

    if (!clientData) {
        return (
            <Container className="mt-5">
                <Alert variant="warning">{t('no_profile_data_found')}</Alert>
            </Container>
        );
    }

    return (
        <Container className="mt-5">
            <h2>{t('edit_profile')}</h2>
            <ClientForm client={clientData} onSuccess={handleSuccess} onCancel={handleCancel} />
        </Container>
    );
};

export default EditProfilePage;
