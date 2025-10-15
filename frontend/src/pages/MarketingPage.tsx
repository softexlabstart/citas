import React, { useState, useEffect } from 'react';
import { Container, Form, Button, Spinner, Alert, Card } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import { useApi } from '../hooks/useApi';
import { sendMarketingEmail, getClients } from '../api';
import { Client } from '../interfaces/Client';

const MarketingPage: React.FC = () => {
    const { t } = useTranslation();
    const [subject, setSubject] = useState('');
    const [message, setMessage] = useState('');
    const [clients, setClients] = useState<Client[]>([]);
    const [selectedClientEmails, setSelectedClientEmails] = useState<string[]>([]);
    const [selectAll, setSelectAll] = useState(false);
    const [consentFilter, setConsentFilter] = useState<string>('all');
    const { loading, error, request: doSendEmail } = useApi(sendMarketingEmail);
    const { request: fetchClientsApi } = useApi(getClients);

    useEffect(() => {
        const fetchClients = async () => {
            try {
                const filterParam = consentFilter === 'all' ? undefined : consentFilter;
                const response = await fetchClientsApi(filterParam);
                // Assuming getClients returns PaginatedResponse<Client>
                // Adjust if getClients returns Client[] directly
                type PaginatedResponse<T> = { results: T[] };
                const data = response.data as Client[] | PaginatedResponse<Client>;
                if (Array.isArray(data)) {
                    setClients(data);
                } else if ('results' in data && Array.isArray(data.results)) {
                    setClients(data.results);
                } else {
                    setClients([]);
                }
                // Reset selection when filter changes
                setSelectedClientEmails([]);
                setSelectAll(false);
            } catch (err) {
                console.error('Error fetching clients:', err);
                toast.error(t('error_fetching_clients'));
            }
        };
        fetchClients();
    }, [t, fetchClientsApi, consentFilter]);

    const handleClientSelect = (email: string) => {
        setSelectedClientEmails((prevSelected) =>
            prevSelected.includes(email)
                ? prevSelected.filter((e) => e !== email)
                : [...prevSelected, email]
        );
    };

    const handleSelectAll = () => {
        if (selectAll) {
            setSelectedClientEmails([]);
        } else {
            setSelectedClientEmails(clients.map((client) => client.email));
        }
        setSelectAll(!selectAll);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!subject || !message) {
            toast.error(t('subject_and_message_required'));
            return;
        }

        const { success, error: apiError } = await doSendEmail({
            subject,
            message,
            recipient_emails: selectedClientEmails.length > 0 ? selectedClientEmails : undefined,
        });

        if (success) {
            toast.success(t('email_sent_successfully'));
            setSubject('');
            setMessage('');
            setSelectedClientEmails([]); // Clear selection after sending
            setSelectAll(false);
        } else {
            toast.error(t('error_sending_email') + (apiError ? `: ${apiError}` : ''));
        }
    };

    return (
        <Container className="mt-5">
            <h2>{t('marketing_email')}</h2>
            <p>{t('marketing_email_description')}</p>
            <Form onSubmit={handleSubmit}>
                <Form.Group className="mb-3" controlId="subject">
                    <Form.Label>{t('subject')}</Form.Label>
                    <Form.Control
                        type="text"
                        value={subject}
                        onChange={(e) => setSubject(e.target.value)}
                        required
                    />
                </Form.Group>

                <Form.Group className="mb-3" controlId="message">
                    <Form.Label>{t('message')}</Form.Label>
                    <Form.Control
                        as="textarea"
                        rows={10}
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        required
                    />
                </Form.Group>

                <Card className="mb-3">
                    <Card.Header>
                        <div className="d-flex justify-content-between align-items-center">
                            <span>{t('select_recipients')}</span>
                            <Form.Select
                                value={consentFilter}
                                onChange={(e) => setConsentFilter(e.target.value)}
                                style={{ width: 'auto', marginLeft: '10px' }}
                                size="sm"
                            >
                                <option value="all">Todos los clientes</option>
                                <option value="true">Con consentimiento ✓</option>
                                <option value="false">Sin consentimiento ✗</option>
                            </Form.Select>
                        </div>
                    </Card.Header>
                    <Card.Body style={{ maxHeight: '300px', overflowY: 'auto' }}>
                        <Form.Check
                            type="checkbox"
                            id="selectAllClients"
                            label={t('select_all_clients')}
                            checked={selectAll}
                            onChange={handleSelectAll}
                            className="mb-2"
                        />
                        {clients.length === 0 ? (
                            <p className="text-muted text-center">No hay clientes con este filtro</p>
                        ) : (
                            clients.map((client) => (
                                <Form.Check
                                    type="checkbox"
                                    id={`client-${client.id}`}
                                    key={client.id}
                                    label={
                                        <span>
                                            {client.first_name} {client.last_name} ({client.email})
                                            {client.has_consented_data_processing ? (
                                                <span className="text-success ms-2" title="Aceptó políticas">✓</span>
                                            ) : (
                                                <span className="text-warning ms-2" title="No aceptó políticas">⚠</span>
                                            )}
                                        </span>
                                    }
                                    checked={selectedClientEmails.includes(client.email)}
                                    onChange={() => handleClientSelect(client.email)}
                                />
                            ))
                        )}
                    </Card.Body>
                </Card>

                {error && <Alert variant="danger">{error}</Alert>}

                <Button variant="primary" type="submit" disabled={loading}>
                    {loading ? <Spinner as="span" animation="border" size="sm" /> : t('send_email')}
                </Button>
            </Form>
        </Container>
    );
};

export default MarketingPage;
