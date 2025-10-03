import React, { useState, useEffect } from 'react';
import { Table, Spinner, Alert, Button, Modal } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import { useApi } from '../hooks/useApi';
import { Client } from '../interfaces/Client';
import { getClients, deleteClient } from '../api';
import ClientForm from './ClientForm';
import ClientHistoryModal from './ClientHistoryModal';
import ConfirmationModal from './ConfirmationModal'; // Import ConfirmationModal
import { useAuth } from '../hooks/useAuth';


const Clients: React.FC = () => {
    const { t } = useTranslation();
    const { user } = useAuth();
    const { data: clients, loading, error, request: fetchClients, setData: setClients } = useApi(getClients);
    const { loading: deleteLoading, error: deleteError, request: callDeleteClient } = useApi(deleteClient);
    const [showModal, setShowModal] = useState(false);
    const [editingClient, setEditingClient] = useState<Client | null>(null);
    const [showHistoryModal, setShowHistoryModal] = useState(false);
    const [selectedClient, setSelectedClient] = useState<Client | null>(null);
    const [showConfirmModal, setShowConfirmModal] = useState(false); // State for confirmation modal visibility
    const [clientToDeleteId, setClientToDeleteId] = useState<number | null>(null); // State for client ID to delete

    const handleDeleteClient = (clientId: number) => {
        setClientToDeleteId(clientId);
        setShowConfirmModal(true);
    };

    const handleConfirmDelete = async () => {
        if (clientToDeleteId) {
            const { success } = await callDeleteClient(clientToDeleteId);
            if (success) {
                toast.success(t('client_deleted_successfully'));
                fetchClients(); // Refresh client list
            } else if (deleteError) {
                toast.error(t('error_deleting_client') + ": " + deleteError);
            }
            setClientToDeleteId(null);
            setShowConfirmModal(false);
        }
    };

    const handleCloseConfirmModal = () => {
        setClientToDeleteId(null);
        setShowConfirmModal(false);
    };

    useEffect(() => {
        console.log('🔍 Clients - Usuario actual:', {
            username: user?.username,
            is_staff: user?.is_staff,
            is_sede_admin: user?.perfil?.is_sede_admin,
            sedes_administradas: user?.perfil?.sedes_administradas,
            organizacion: user?.perfil?.organizacion
        });
        fetchClients();
    }, [fetchClients]);

    const handleAddClient = () => {
        setEditingClient(null);
        setShowModal(true);
    };

    const handleEditClient = (client: Client) => {
        setEditingClient(client);
        setShowModal(true);
    };

    const handleShowHistory = (client: Client) => {
        setSelectedClient(client);
        setShowHistoryModal(true);
    };

    const handleCloseModal = () => {
        setShowModal(false);
        setEditingClient(null);
    };

    const handleSuccess = (updatedClient?: Client) => {
        if (updatedClient) {
            setClients(
                clients
                    ? clients.map((client) =>
                          client.id === updatedClient.id ? updatedClient : client
                      )
                    : []
            );
        } else {
            fetchClients();
        }
        handleCloseModal();
    };

    return (
        <div>
            <div className="d-flex justify-content-between align-items-center mb-3">
                <h2>{t('clients')}</h2>
                <Button variant="primary" onClick={handleAddClient}>
                    {t('add_client')}
                </Button>
            </div>
            
            {loading && <Spinner animation="border" />}
            {error && <Alert variant="danger">{error}</Alert>}

            {/* Debug info */}
            {!loading && clients && clients.length === 0 && (
                <Alert variant="warning">
                    No se encontraron clientes.
                    {user?.perfil?.is_sede_admin && !user?.is_staff && (
                        <div className="mt-2">
                            <strong>Nota para Admin de Sede:</strong> Solo verás clientes de tu organización.
                            <br />
                            Organización: {user?.perfil?.organizacion ? 'Asignada' : 'No asignada'}
                            <br />
                            Sedes administradas: {user?.perfil?.sedes_administradas?.length || 0}
                        </div>
                    )}
                </Alert>
            )}

            {clients && clients.length > 0 && (
                <Table striped bordered hover responsive>
                    <thead>
                        <tr>
                            <th>{t('full_name')}</th>
                            <th>{t('email')}</th>
                            <th>{t('phone')}</th>
                            <th>{t('city')}</th>
                            <th>{t('neighborhood')}</th>
                            <th>{t('gender')}</th>
                            <th>{t('age')}</th>
                            <th>{t('actions')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {clients.map((client) => (
                            <tr key={client.id}>
                                <td>{client.full_name}</td>
                                <td>{client.email}</td>
                                <td>{client.telefono}</td>
                                <td>{client.ciudad}</td>
                                <td>{client.barrio}</td>
                                <td>{client.genero}</td>
                                <td>{client.age}</td>
                                <td>
                                    <Button variant="info" size="sm" onClick={() => handleEditClient(client)} className="me-2">
                                        {t('edit')}
                                    </Button>
                                    <Button variant="secondary" size="sm" onClick={() => handleShowHistory(client)} className="me-2">
                                        {t('history')}
                                    </Button>
                                    <Button variant="danger" size="sm" onClick={() => handleDeleteClient(client.id)}>
                                        {t('delete')}
                                    </Button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </Table>
            )}

            {/* Client Form Modal */}
            <Modal show={showModal} onHide={handleCloseModal} size="lg" centered>
                <Modal.Header closeButton>
                    <Modal.Title>{editingClient ? t('edit_client') : t('add_client')}</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <ClientForm client={editingClient} onSuccess={handleSuccess} onCancel={handleCloseModal} />
                </Modal.Body>
            </Modal>

            {/* Client History Modal */}
            <ClientHistoryModal client={selectedClient} show={showHistoryModal} onHide={() => setShowHistoryModal(false)} />

            {/* Confirmation Modal for deleting client */}
            <ConfirmationModal
                isOpen={showConfirmModal}
                onClose={handleCloseConfirmModal}
                onConfirm={handleConfirmDelete}
                message={t('confirm_delete_client')}
                title={t('confirm_deletion')}
            />
        </div>
    );
};

export default Clients;
