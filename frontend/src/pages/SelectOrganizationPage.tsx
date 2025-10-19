import React from 'react';
import { Container, Row, Col, Card } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { useAuth, Organization } from '../contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import './SelectOrganizationPage.css';

const SelectOrganizationPage: React.FC = () => {
    const { organizations, selectOrganization } = useAuth();
    const navigate = useNavigate();
    const { t } = useTranslation();

    // Si no hay organizaciones, redirigir al login
    React.useEffect(() => {
        if (!organizations || organizations.length === 0) {
            navigate('/login');
        }
    }, [organizations, navigate]);

    const handleSelectOrganization = (org: Organization) => {
        selectOrganization(org);
        navigate('/');
    };

    if (!organizations) {
        return null;
    }

    return (
        <Container className="select-organization-page">
            <Row className="justify-content-center mt-5">
                <Col md={8} lg={6}>
                    <div className="text-center mb-4">
                        <h2 className="mb-2">{t('select_organization') || 'Selecciona una Organización'}</h2>
                        <p className="text-muted">
                            {t('select_organization_description') || 'Tienes acceso a múltiples organizaciones. Selecciona la que deseas gestionar.'}
                        </p>
                    </div>

                    <Row>
                        {organizations.map((org) => (
                            <Col key={org.id} xs={12} className="mb-3">
                                <Card
                                    className="organization-card"
                                    onClick={() => handleSelectOrganization(org)}
                                    style={{ cursor: 'pointer' }}
                                >
                                    <Card.Body className="d-flex align-items-center">
                                        <div className="organization-icon me-3">
                                            <i className="bi bi-building" style={{ fontSize: '2rem' }}></i>
                                        </div>
                                        <div className="flex-grow-1">
                                            <h5 className="mb-1">{org.nombre}</h5>
                                            <small className="text-muted">{org.slug}</small>
                                        </div>
                                        <div>
                                            <i className="bi bi-chevron-right text-muted"></i>
                                        </div>
                                    </Card.Body>
                                </Card>
                            </Col>
                        ))}
                    </Row>
                </Col>
            </Row>
        </Container>
    );
};

export default SelectOrganizationPage;
