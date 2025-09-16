import React, { useState } from 'react';
import { Container, Form, Button, Spinner, Alert } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import { useApi } from '../hooks/useApi';
import { sendMarketingEmail } from '../api';

const MarketingPage: React.FC = () => {
    const { t } = useTranslation();
    const [subject, setSubject] = useState('');
    const [message, setMessage] = useState('');
    const { loading, error, request: doSendEmail } = useApi(sendMarketingEmail);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!subject || !message) {
            toast.error(t('subject_and_message_required'));
            return;
        }

        const { success, error: apiError } = await doSendEmail({ subject, message });

        if (success) {
            toast.success(t('email_sent_successfully'));
            setSubject('');
            setMessage('');
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

                {error && <Alert variant="danger">{error}</Alert>}

                <Button variant="primary" type="submit" disabled={loading}>
                    {loading ? <Spinner as="span" animation="border" size="sm" /> : t('send_email')}
                </Button>
            </Form>
        </Container>
    );
};

export default MarketingPage;
