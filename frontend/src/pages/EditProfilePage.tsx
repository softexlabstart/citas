import React, { useEffect, useState } from 'react';
import { Container, Spinner, Alert, Button, Form, Row, Col } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { useAuth } from '../contexts/AuthContext';
import { getPersonalData, deleteAccount, updateDataProcessingOptOut, updateUserProfile } from '../api';
import { Client } from '../interfaces/Client';
import ConfirmationModal from '../components/ConfirmationModal';

export const EditProfilePage: React.FC = () => {
    const { t } = useTranslation();
    const { user, logout, updateUser } = useAuth();
    const navigate = useNavigate();
    const [clientData, setClientData] = useState<Client | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showDeleteConfirmModal, setShowDeleteConfirmModal] = useState(false);
    const [showOpposeConfirmModal, setShowOpposeConfirmModal] = useState(false);
    const [opposeDataProcessing, setOpposeDataProcessing] = useState(false); // Initialized to false, will be updated by useEffect

    // Form states
    const [username, setUsername] = useState('');
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [email, setEmail] = useState('');
    const [telefono, setTelefono] = useState('');
    const [ciudad, setCiudad] = useState('');
    const [barrio, setBarrio] = useState('');
    const [genero, setGenero] = useState('');
    const [fechaNacimiento, setFechaNacimiento] = useState('');

    // Effect to load client data and initialize form states
    useEffect(() => {
        const fetchClientData = async () => {
            if (user && user.id) {
                try {
                    setLoading(true);
                    const response = await getPersonalData();
                    if (response.data) {
                        setClientData(response.data);
                        // Initialize form states from fetched data
                        setUsername(response.data.username || '');
                        setFirstName(response.data.first_name || '');
                        setLastName(response.data.last_name || '');
                        setEmail(response.data.email || '');
                        setTelefono(response.data.telefono || '');
                        setCiudad(response.data.ciudad || '');
                        setBarrio(response.data.barrio || '');
                        setGenero(response.data.genero || '');
                        setFechaNacimiento(response.data.fecha_nacimiento || '');
                        setOpposeDataProcessing(response.data.data_processing_opt_out || false);
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
    }, [user, t]); // Depend on user and t

    const handleOpposeSwitchClick = (e: React.MouseEvent<HTMLInputElement>) => {
        e.preventDefault();
        setShowOpposeConfirmModal(true);
    };

    const handleConfirmOpposeDataProcessing = async () => {
        const newValue = !opposeDataProcessing;
        setOpposeDataProcessing(newValue);
        try {
            await updateDataProcessingOptOut(newValue);
            // Update the user context with the new preference
            if (user?.perfil) {
                updateUser({
                    perfil: {
                        ...user.perfil,
                        data_processing_opt_out: newValue
                    }
                });
            }
            toast.success(t('data_processing_preference_updated'));
        } catch (err: any) {
            const errorMessage = err.response?.data?.detail || err.message || t('error_updating_data_processing_preference');
            toast.error(errorMessage);
            console.error('Error updating data processing preference:', err);
            setOpposeDataProcessing(!newValue); // Revert UI on error
        } finally {
            setShowOpposeConfirmModal(false);
        }
    };

    const handleCloseOpposeConfirmModal = () => {
        setShowOpposeConfirmModal(false);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true); // Set loading true for form submission
        try {
            const updatedData: Partial<Client> = {
                first_name: firstName,
                last_name: lastName,
                email,
                telefono,
                ciudad,
                barrio,
                genero,
                fecha_nacimiento: fechaNacimiento,
            };
            await updateUserProfile(updatedData);
            toast.success(t('profile_updated_successfully'));
            navigate(-1); // Navigate back after successful update
        } catch (err: any) {
            const errorMessage = err.response?.data?.detail || err.message || t('error_updating_profile');
            toast.error(errorMessage);
            setError(errorMessage);
            console.error('Error updating profile:', err);
        } finally {
            setLoading(false); // Set loading false after submission attempt
        }
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
            setShowDeleteConfirmModal(false); // Close the modal
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
            <h2>{t('editar perfil')}</h2>
            <Form onSubmit={handleSubmit}>
                <Row>
                    <Col md={6}>
                        <Form.Group className="mb-3">
                            <Form.Label>{t('username')}</Form.Label>
                            <Form.Control type="text" value={username} disabled />
                        </Form.Group>
                    </Col>
                    <Col md={6}>
                        <Form.Group className="mb-3">
                            <Form.Label>{t('email')}</Form.Label>
                            <Form.Control type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
                        </Form.Group>
                    </Col>
                </Row>

                <Row>
                    <Col md={6}>
                        <Form.Group className="mb-3">
                            <Form.Label>{t('first_name')}</Form.Label>
                            <Form.Control type="text" value={firstName} onChange={(e) => setFirstName(e.target.value)} />
                        </Form.Group>
                    </Col>
                    <Col md={6}>
                        <Form.Group className="mb-3">
                            <Form.Label>{t('last_name')}</Form.Label>
                            <Form.Control type="text" value={lastName} onChange={(e) => setLastName(e.target.value)} />
                        </Form.Group>
                    </Col>
                </Row>
                <Button variant="primary" type="submit" className="mt-3">
                    {t('save_changes')}
                </Button>
                <Button variant="secondary" onClick={handleCancel} className="mt-3 ms-2">
                    {t('cancel')}
                </Button>
            </Form>

            <hr />

            <div className="mt-4">
                <h4>{t('data_management')}</h4>
                <p>{t('download_your_data_description')}</p>
                <Button variant="info" onClick={handleDownloadData}>
                    {t('download_my_data')}
                </Button>
            </div>

            <div className="mt-4">
                <Form.Group className="mb-3">
                    <Form.Check
                        type="switch"
                        id="oppose-data-processing-switch"
                        label={t('oppose_data_processing')}
                        checked={opposeDataProcessing}
                        onClick={handleOpposeSwitchClick}
                        onChange={() => {}} // Empty onChange to satisfy React warning for controlled components
                    />
                </Form.Group>
            </div>

            <div className="mt-5 border-top pt-4">
                <h4>{t('delete_account')}</h4>
                <p>{t('delete_account_warning')}</p>
                <Button variant="danger" onClick={handleDeleteAccount}>
                    {t('delete_my_account')}
                </Button>
            </div>

            <ConfirmationModal
                isOpen={showDeleteConfirmModal}
                onClose={handleCloseDeleteConfirmModal}
                onConfirm={handleConfirmDeleteAccount}
                title={t('confirm_account_deletion')}
                message={t('are_you_sure_you_want_to_delete_account')}
            />

            <ConfirmationModal
                isOpen={showOpposeConfirmModal}
                onClose={handleCloseOpposeConfirmModal}
                onConfirm={handleConfirmOpposeDataProcessing}
                title={t('confirm_data_processing_opposition')}
                message={t('are_you_sure_you_want_to_change_data_processing')}
            />
        </Container>
    );
};