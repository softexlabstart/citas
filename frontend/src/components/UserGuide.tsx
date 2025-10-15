import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Accordion, Spinner, Alert, Badge } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { getGuideSections, GuideSection } from '../api';
import * as Icons from 'react-bootstrap-icons';

const UserGuide: React.FC = () => {
    const { t, i18n } = useTranslation();
    const [sections, setSections] = useState<GuideSection[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [groupedSections, setGroupedSections] = useState<Record<string, GuideSection[]>>({});

    useEffect(() => {
        const fetchSections = async () => {
            try {
                setLoading(true);
                const response = await getGuideSections(i18n.language);
                setSections(response.data);

                // Agrupar por categoría
                const grouped = response.data.reduce((acc, section) => {
                    if (!acc[section.category]) {
                        acc[section.category] = [];
                    }
                    acc[section.category].push(section);
                    return acc;
                }, {} as Record<string, GuideSection[]>);

                setGroupedSections(grouped);
                setError(null);
            } catch (err) {
                console.error('Error fetching guide sections:', err);
                setError('Error al cargar la guía de usuario');
            } finally {
                setLoading(false);
            }
        };

        fetchSections();
    }, [i18n.language]);

    const getIcon = (iconName: string) => {
        const IconComponent = (Icons as any)[iconName] || Icons.QuestionCircle;
        return <IconComponent className="me-2" />;
    };

    const getCategoryBadgeVariant = (category: string) => {
        switch (category) {
            case 'general': return 'primary';
            case 'usuarios': return 'success';
            case 'administradores': return 'warning';
            case 'colaboradores': return 'info';
            default: return 'secondary';
        }
    };

    if (loading) {
        return (
            <Container className="mt-5 text-center">
                <Spinner animation="border" role="status">
                    <span className="visually-hidden">Cargando...</span>
                </Spinner>
                <p className="mt-3">Cargando guía de usuario...</p>
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

    if (sections.length === 0) {
        return (
            <Container className="mt-5">
                <Alert variant="info">
                    No hay secciones de guía disponibles actualmente.
                </Alert>
            </Container>
        );
    }

    return (
        <Container className="mt-5">
            <Row className="justify-content-center">
                <Col md={10}>
                    <Card className="shadow-sm">
                        <Card.Header as="h2" className="text-center bg-primary text-white">
                            {t('user_guide_title')}
                        </Card.Header>
                        <Card.Body className="p-4">
                            <p className="lead text-center mb-4">
                                {t('user_guide_intro')}
                            </p>

                            {Object.keys(groupedSections).map((category, catIndex) => (
                                <div key={category} className="mb-4">
                                    <h4 className="mb-3">
                                        <Badge bg={getCategoryBadgeVariant(category)}>
                                            {groupedSections[category][0].category_display}
                                        </Badge>
                                    </h4>

                                    <Accordion defaultActiveKey={catIndex === 0 ? "0" : undefined}>
                                        {groupedSections[category].map((section, index) => (
                                            <Accordion.Item eventKey={String(index)} key={section.id}>
                                                <Accordion.Header>
                                                    {getIcon(section.icon)}
                                                    {section.title}
                                                </Accordion.Header>
                                                <Accordion.Body>
                                                    <div
                                                        dangerouslySetInnerHTML={{ __html: section.content }}
                                                        style={{ lineHeight: '1.6' }}
                                                    />
                                                    {section.video_url && (
                                                        <div className="mt-3">
                                                            <Alert variant="info">
                                                                <Icons.PlayCircle className="me-2" />
                                                                <a
                                                                    href={section.video_url}
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                >
                                                                    Ver video tutorial
                                                                </a>
                                                            </Alert>
                                                        </div>
                                                    )}
                                                </Accordion.Body>
                                            </Accordion.Item>
                                        ))}
                                    </Accordion>
                                </div>
                            ))}
                        </Card.Body>
                        <Card.Footer className="text-muted text-center">
                            {t('guide_footer')}
                            <div className="mt-2">
                                <small>
                                    <Icons.Tools className="me-1" />
                                    ¿Eres administrador?
                                    <a href="/admin/guide/guidesection/" target="_blank" rel="noopener noreferrer" className="ms-2">
                                        Editar guía desde el panel de administración
                                    </a>
                                </small>
                            </div>
                        </Card.Footer>
                    </Card>
                </Col>
            </Row>
        </Container>
    );
};

export default UserGuide;
