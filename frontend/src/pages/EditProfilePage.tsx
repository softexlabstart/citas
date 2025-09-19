import React, { useEffect, useState } from 'react';
import { Container, Spinner, Alert, Button, Form } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import ClientForm from '../components/ClientForm';
import { useAuth } from '../contexts/AuthContext';
import { getPersonalData, deleteAccount, updateDataProcessingOptOut } from '../api'; // Corrected import
import { Client } from '../interfaces/Client';
import ConfirmationModal from '../components/ConfirmationModal'; // Import ConfirmationModal

const EditProfilePage: React.FC = () => {
    const { t } = useTranslation();
    const { user, logout } = useAuth(); // Get logout from useAuth
    const navigate = useNavigate();
    const [clientData, setClientData] = useState<Client | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showDeleteConfirmModal, setShowDeleteConfirmModal] = useState(false); // State for delete confirmation modal
    const [opposeDataProcessing, setOpposeDataProcessing] = useState(clientData?.data_processing_opt_out || false);

    useEffect(() => {
        if (clientData) {
            setOpposeDataProcessing(clientData.data_processing_opt_out || false);
        }
    }, [clientData]);

    const handleOpposeDataProcessingChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const newValue = event.target.checked;
        setOpposeDataProcessing(newValue);
        try {
            await updateDataProcessingOptOut(newValue);
            toast.success(t('data_processing_preference_updated'));
        } catch (err: any) {
            const errorMessage = err.response?.data?.detail || err.message || t('error_updating_data_processing_preference');
            toast.error(errorMessage);
            console.error('Error updating data processing preference:', err);
            setOpposeDataProcessing(!newValue); // Revert UI on error
        }
    };

    useEffect(() => {
        const fetchClientData = async () => {
            if (user && user.id) {
                try {
                    setLoading(true);
                    const response = await getPersonalData(); // Corrected API call
                    if (response.data) {
                        setClientData(response.data);
                    } else {
                        setError(t('error_fetching_profile'));
                        toast.error(t('error_fetching_profile'));
                    }
                } catch (err: any) {
                    const errorMessage = err.response?.data?.detail || err.message || t('error_fetching_profile');
                    setError(errorMessage);
                    toast.error(errorMessage);
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
        navigate(-1);
    };

    const handleCancel = () => {
        navigate(-1);
    };

    const handleDownloadData = async () => {
        try {
            const response = await getPersonalData();
            const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(response.data, null, 2));
            const downloadAnchorNode = document.createElement('a');
            downloadAnchorNode.setAttribute("href", dataStr);
            downloadAnchorNode.setAttribute("download", `personal_data_${user?.username || 'user'}.json`);
            document.body.appendChild(downloadAnchorNode);
            downloadAnchorNode.click();
            downloadAnchorNode.remove();
            toast.success(t('data_downloaded_successfully'));
        } catch (err: any) {
            const errorMessage = err.response?.data?.detail || err.message || t('error_downloading_data');
            toast.error(errorMessage);
            console.error('Error downloading personal data:', err);
        }
    };

    const handleDeleteAccount = () => {
        setShowDeleteConfirmModal(true);
    };

    const handleConfirmDeleteAccount = async () => {
        try {
            await deleteAccount();
            toast.success(t('account_deleted_successfully'));
            logout(); // Log out the user
            navigate('/login'); // Redirect to login page
        } catch (err: any) {
            const errorMessage = err.response?.data?.detail || err.message || t('error_deleting_account');
            toast.error(errorMessage);
            console.error('Error deleting account:', err);
        } finally {
            setShowDeleteConfirmModal(true); // Close the modal
        }
    };

    const handleCloseDeleteConfirmModal = () => {
        setShowDeleteConfirmModal(false);
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
            <div className="mt-3">
                <Form.Check
                    type="switch"
                    id="oppose-data-processing-switch"
                    label={t('oppose_data_processing')}
                    checked={opposeDataProcessing}
                    onChange={handleOpposeDataProcessingChange}
                    className="mb-3"
                />
            </div>
            <div className="mt-3 d-flex justify-content-between">
                <Button variant="secondary" onClick={handleDownloadData}>
                    {t('download_my_data')}
                </Button>
                <Button variant="danger" onClick={handleDeleteAccount}>
                    {t('delete_my_account')}
                </Button>
            </div>

            <ConfirmationModal
                isOpen={showDeleteConfirmModal}
                onClose={handleCloseDeleteConfirmModal}
                onConfirm={handleConfirmDeleteAccount}
                message={t('confirm_delete_account_message')}
                title={t('confirm_delete_account_title')}
            />
        </Container>
    );
};

export default EditProfilePage;