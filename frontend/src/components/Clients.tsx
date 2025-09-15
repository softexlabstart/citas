import React, { useState, useEffect } from 'react';
import { Table, Spinner, Alert } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { useApi } from '../hooks/useApi';
import { Client } from '../interfaces/Client';
import { getClients } from '../api';

const Clients: React.FC = () => {
    const { t } = useTranslation();
    const { data: clients, loading, error, request: fetchClients } = useApi(getClients);

    useEffect(() => {
        fetchClients();
    }, [fetchClients]);

    return (
        <div>
            <h2>{t('clients')}</h2>
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
                            </tr>
                        ))}
                    </tbody>
                </Table>
            )}
        </div>
    );
};

export default Clients;
