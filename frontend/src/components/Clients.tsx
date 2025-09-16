import React, { useState, useEffect } from 'react';
import { Table, Spinner, Alert, Button, Modal } from 'react-bootstrap'; // Added Button and Modal
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify'; // Added toast import
import { useApi } from '../hooks/useApi';
import { Client } from '../interfaces/Client';
import { getClients, deleteClient } from '../api';
import ClientHistoryModal from './ClientHistoryModal'; // Import ClientHistoryModal

const Clients: React.FC = () => {
    const { t } = useTranslation();
    const { data: clients, loading, error, request: fetchClients, setData: setClients } = useApi(getClients);
    const { loading: deleteLoading, error: deleteError, request: callDeleteClient } = useApi(deleteClient);
    const [showModal, setShowModal] = useState(false); // State for modal visibility
    const [editingClient, setEditingClient] = useState<Client | null>(null); // State for client being edited
    const [showHistoryModal, setShowHistoryModal] = useState(false);
    const [selectedClient, setSelectedClient] = useState<Client | null>(null);

    const handleDeleteClient = async (clientId: number) => {
        if (window.confirm(t('confirm_delete_client'))) {
            const { success } = await callDeleteClient(clientId);
            if (success) {
                toast.success(t('client_deleted_successfully'));
                fetchClients(); // Refresh client list
            } else if (deleteError) {
                toast.error(t('error_deleting_client') + ": " + deleteError);
            }
        }
    };

    useEffect(() => {
        fetchClients();
    }, [fetchClients]);

    const handleAddClient = () => {
        setEditingClient(null); // Clear any previous editing state
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
        setEditingClient(null); // Clear editing state on close
    };

    const handleSuccess = (updatedClient?: Client) => {
        if (updatedClient) {
            // Update existing client in the list
            setClients(
                clients
                    ? clients.map((client) =>
                          client.id === updatedClient.id ? updatedClient : client
                      )
                    : []
            );
        } else {
            // New client was added, so we need to refetch the whole list
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
            {clients && (
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
                            <th>{t('actions')}</th> {/* Added actions column */}
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
        </div>
    );
};

export default Clients;
