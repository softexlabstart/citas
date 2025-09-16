import React, { useState, useEffect } from 'react';
import { Form, Button, Spinner, Alert, Row, Col } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import { useApi } from '../hooks/useApi';
import { Client } from '../interfaces/Client';
import { getClients, createClient, updateClient } from '../api'; // Assuming getClients is used for fetching existing data

interface ClientFormProps {
    client?: Client | null; // Optional: if editing an existing client
    onSuccess: (updatedClient?: Client) => void;
    onCancel: () => void;
}

const ClientForm: React.FC<ClientFormProps> = ({ client, onSuccess, onCancel }) => {
    const { t } = useTranslation();
    const [username, setUsername] = useState(client?.username || '');
    const [firstName, setFirstName] = useState(client?.first_name || '');
    const [lastName, setLastName] = useState(client?.last_name || '');
    const [email, setEmail] = useState(client?.email || '');
    const [telefono, setTelefono] = useState(client?.telefono || '');
    const [ciudad, setCiudad] = useState(client?.ciudad || '');
    const [barrio, setBarrio] = useState(client?.barrio || '');
    const [genero, setGenero] = useState(client?.genero || '');
    const [fechaNacimiento, setFechaNacimiento] = useState(client?.fecha_nacimiento || '');

        const { loading: createLoading, error: createError, request: callCreateClient } = useApi(createClient);
    const { loading: updateLoading, error: updateError, request: callUpdateClient } = useApi(updateClient);

    const loading = createLoading || updateLoading;
    const error = createError || updateError;

    useEffect(() => {
        if (client) {
            setUsername(client.username);
            setFirstName(client.first_name);
            setLastName(client.last_name);
            setEmail(client.email);
            setTelefono(client.telefono);
            setCiudad(client.ciudad);
            setBarrio(client.barrio);
            setGenero(client.genero);
            setFechaNacimiento(client.fecha_nacimiento);
        }
    }, [client]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        const clientData = {
            username,
            first_name: firstName,
            last_name: lastName,
            email,
            perfil: {
                telefono,
                ciudad,
                barrio,
                genero,
                fecha_nacimiento: fechaNacimiento,
            },
        };

        if (client) {
            // Update existing client
            const result = await callUpdateClient(client.id, clientData);
            if (result.success && result.data) {
                toast.success(t('client_saved_successfully'));
                onSuccess(result.data);
            } else if (result.error) {
                toast.error(t('error_saving_client') + ": " + result.error);
            }
        } else {
            // Create new client
            const result = await callCreateClient(clientData);
            if (result.success) {
                toast.success(t('client_saved_successfully'));
                onSuccess();
            } else if (result.error) {
                toast.error(t('error_saving_client') + ": " + result.error);
            }
        }
    };

    return (
        <Form onSubmit={handleSubmit}>
            {error && <Alert variant="danger">{t('error_saving_client')}: {error}</Alert>}

            <Row>
                <Col md={6}>
                    <Form.Group className="mb-3">
                        <Form.Label>{t('username')}</Form.Label>
                        <Form.Control type="text" value={username} onChange={(e) => setUsername(e.target.value)} required />
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

            <Row>
                <Col md={6}>
                    <Form.Group className="mb-3">
                        <Form.Label>{t('phone')}</Form.Label>
                        <Form.Control type="text" value={telefono} onChange={(e) => setTelefono(e.target.value)} />
                    </Form.Group>
                </Col>
                <Col md={6}>
                    <Form.Group className="mb-3">
                        <Form.Label>{t('city')}</Form.Label>
                        <Form.Control type="text" value={ciudad} onChange={(e) => setCiudad(e.target.value)} />
                    </Form.Group>
                </Col>
            </Row>

            <Row>
                <Col md={6}>
                    <Form.Group className="mb-3">
                        <Form.Label>{t('neighborhood')}</Form.Label>
                        <Form.Control type="text" value={barrio} onChange={(e) => setBarrio(e.target.value)} />
                    </Form.Group>
                </Col>
                <Col md={6}>
                    <Form.Group className="mb-3">
                        <Form.Label>{t('gender')}</Form.Label>
                        <Form.Control as="select" value={genero} onChange={(e) => setGenero(e.target.value)}>
                            <option value="">{t('select_gender')}</option>
                            <option value="M">{t('male')}</option>
                            <option value="F">{t('female')}</option>
                            <option value="O">{t('other')}</option>
                        </Form.Control>
                    </Form.Group>
                </Col>
            </Row>

            <Row>
                <Col md={6}>
                    <Form.Group className="mb-3">
                        <Form.Label>{t('date_of_birth')}</Form.Label>
                        <Form.Control type="date" value={fechaNacimiento} onChange={(e) => setFechaNacimiento(e.target.value)} />
                    </Form.Group>
                </Col>
            </Row>

            <div className="d-flex justify-content-end mt-3">
                <Button variant="secondary" onClick={onCancel} className="me-2">
                    {t('cancel')}
                </Button>
                <Button variant="primary" type="submit" disabled={loading}>
                    {loading ? <Spinner as="span" animation="border" size="sm" /> : t('save')}
                </Button>
            </div>
        </Form>
    );
};

export default ClientForm;
