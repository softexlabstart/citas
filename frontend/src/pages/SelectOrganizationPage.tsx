import React from 'react';
import { Container, Row, Col, Card, Badge } from 'react-bootstrap';
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

    // Generar colores aleatorios pero consistentes basados en el ID
    const getOrgColor = (id: number) => {
        const colors = [
            { bg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', shadow: 'rgba(102, 126, 234, 0.4)' },
            { bg: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', shadow: 'rgba(240, 147, 251, 0.4)' },
            { bg: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', shadow: 'rgba(79, 172, 254, 0.4)' },
            { bg: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)', shadow: 'rgba(67, 233, 123, 0.4)' },
            { bg: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)', shadow: 'rgba(250, 112, 154, 0.4)' },
            { bg: 'linear-gradient(135deg, #30cfd0 0%, #330867 100%)', shadow: 'rgba(48, 207, 208, 0.4)' },
            { bg: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)', shadow: 'rgba(168, 237, 234, 0.4)' },
            { bg: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)', shadow: 'rgba(255, 154, 158, 0.4)' }
        ];
        return colors[id % colors.length];
    };

    return (
        <div className="select-organization-page">
            {/* Animated Background */}
            <div className="animated-background">
                <div className="circle-1"></div>
                <div className="circle-2"></div>
                <div className="circle-3"></div>
            </div>

            <Container className="content-wrapper">
                <Row className="justify-content-center">
                    <Col md={10} lg={8} xl={7}>
                        {/* Header */}
                        <div className="page-header">
                            <div className="header-icon">
                                <i className="bi bi-buildings"></i>
                            </div>
                            <h1 className="page-title">
                                {t('select_organization') || 'Selecciona tu Organización'}
                            </h1>
                            <p className="page-subtitle">
                                {t('select_organization_description') ||
                                 'Tienes acceso a múltiples organizaciones. Elige una para comenzar.'}
                            </p>
                            <div className="organizations-count">
                                <Badge bg="light" text="dark" className="px-3 py-2">
                                    {organizations.length} {organizations.length === 1 ? 'organización' : 'organizaciones'} disponibles
                                </Badge>
                            </div>
                        </div>

                        {/* Organizations Grid */}
                        <Row className="organizations-grid">
                            {organizations.map((org) => {
                                const orgColor = getOrgColor(org.id);
                                return (
                                    <Col key={org.id} xs={12} md={6} className="mb-4">
                                        <Card
                                            className="organization-card"
                                            onClick={() => handleSelectOrganization(org)}
                                            style={{
                                                cursor: 'pointer',
                                                '--card-shadow-color': orgColor.shadow
                                            } as React.CSSProperties}
                                        >
                                            <div className="card-glow" style={{ background: orgColor.bg }}></div>
                                            <Card.Body>
                                                <div className="card-content">
                                                    <div
                                                        className="organization-icon"
                                                        style={{ background: orgColor.bg }}
                                                    >
                                                        <i className="bi bi-building"></i>
                                                    </div>
                                                    <div className="organization-info">
                                                        <h3 className="organization-name">{org.nombre}</h3>
                                                        <p className="organization-slug">
                                                            <i className="bi bi-link-45deg me-1"></i>
                                                            {org.slug}
                                                        </p>
                                                    </div>
                                                    <div className="card-arrow">
                                                        <i className="bi bi-arrow-right"></i>
                                                    </div>
                                                </div>
                                            </Card.Body>
                                        </Card>
                                    </Col>
                                );
                            })}
                        </Row>

                        {/* Footer */}
                        <div className="page-footer">
                            <p className="footer-text">
                                <i className="bi bi-shield-check me-2"></i>
                                Tus datos están protegidos y seguros
                            </p>
                        </div>
                    </Col>
                </Row>
            </Container>
        </div>
    );
};

export default SelectOrganizationPage;
