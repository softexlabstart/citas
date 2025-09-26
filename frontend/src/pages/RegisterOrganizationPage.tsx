import React, { useState } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert, Spinner } from 'react-bootstrap';
import { Building } from 'react-bootstrap-icons';
import { useTranslation } from 'react-i18next';
import { useApi } from '../hooks/useApi';
import { createOrganization } from '../api';
import { toast } from 'react-toastify';

const RegisterOrganizationPage: React.FC = () => {
    const { t } = useTranslation();
    const [nombre, setNombre] = useState('');
    const { loading, error, request: doCreateOrganization } = useApi(createOrganization);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!nombre.trim()) {
            toast.error('El nombre de la organización no puede estar vacío.');
            return;
        }

        const { success, data, error: apiError } = await doCreateOrganization(nombre);

        if (success) {
            toast.success(`Organización "${nombre}" creada exitosamente.`);
            setNombre(''); // Clear form on success
        } else {
            // Handle potential nested error messages from Django REST Framework
            const errorMessage = (apiError as any)?.nombre?.[0] || apiError || 'Ocurrió un error al crear la organización.';
            if (errorMessage.includes('already exists')) {
                toast.error('Ya existe una organización con este nombre.');
            } else {
                toast.error(errorMessage);
            }
        }
    };

    return (
        <Container>
            <Row className="justify-content-center mt-5">
                <Col md={8} lg={6}>
                    <Card className="shadow-sm">
                        <Card.Body className="p-4">
                            <h2 className="text-center mb-4">
                                <Building className="me-2" />
                                {t('create_new_organization')}
                            </h2>
                            <p className="text-center text-muted mb-4">
                                {t('create_organization_description')}
                            </p>
                            <Form onSubmit={handleSubmit}>
                                {error && <Alert variant="danger">{error}</Alert>}
                                <Form.Group className="mb-3" controlId="formOrganizationName">
                                    <Form.Label>{t('organization_name')}</Form.Label>
                                    <Form.Control
                                        type="text"
                                        placeholder={t('enter_name')}
                                        value={nombre}
                                        onChange={(e) => setNombre(e.target.value)}
                                        required
                                        disabled={loading}
                                    />
                                </Form.Group>

                                <div className="d-grid mt-4">
                                    <Button variant="primary" type="submit" disabled={loading}>
                                        {loading ? (
                                            <>
                                                <Spinner
                                                    as="span"
                                                    animation="border"
                                                    size="sm"
                                                    role="status"
                                                    aria-hidden="true"
                                                />
                                                <span className="ms-2">{t('creating')}...</span>
                                            </>
                                        ) : (
                                            t('create_organization')
                                        )}
                                    </Button>
                                </div>
                            </Form>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </Container>
    );
};

export default RegisterOrganizationPage;