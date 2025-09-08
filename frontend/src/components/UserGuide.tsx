import React from 'react';
import { Container, Row, Col, Card, Accordion } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';

const UserGuide: React.FC = () => {
    const { t } = useTranslation();

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

                            <Accordion defaultActiveKey="0" alwaysOpen>
                                <Accordion.Item eventKey="0">
                                    <Accordion.Header>{t('guide_section_1_title')}</Accordion.Header>
                                    <Accordion.Body>
                                        <p>{t('guide_section_1_p1')}</p>
                                        <ol>
                                            <li>{t('guide_section_1_step1')}</li>
                                            <li>{t('guide_section_1_step2')}</li>
                                            <li>{t('guide_section_1_step3')}</li>
                                        </ol>
                                        <p>{t('guide_section_1_p2')}</p>
                                        {/* Puedes añadir una imagen de ejemplo aquí */}
                                        {/* <img src="/path/to/services-screenshot.png" alt="Gestionar Servicios" className="img-fluid rounded mt-2" /> */}
                                    </Accordion.Body>
                                </Accordion.Item>

                                <Accordion.Item eventKey="1">
                                    <Accordion.Header>{t('guide_section_2_title')}</Accordion.Header>
                                    <Accordion.Body>
                                        <p>{t('guide_section_2_p1')}</p>
                                        <p>{t('guide_section_2_p2')}</p>
                                        <ul>
                                            <li><strong>{t('pending')}:</strong> {t('guide_status_pending')}</li>
                                            <li><strong>{t('confirmed')}:</strong> {t('guide_status_confirmed')}</li>
                                            <li><strong>{t('cancelled')}:</strong> {t('guide_status_cancelled')}</li>
                                        </ul>
                                        <p>{t('guide_section_2_p3')}</p>
                                    </Accordion.Body>
                                </Accordion.Item>

                                <Accordion.Item eventKey="2">
                                    <Accordion.Header>{t('guide_section_3_title')}</Accordion.Header>
                                    <Accordion.Body>
                                        <p>{t('guide_section_3_p1')}</p>
                                        <p>{t('guide_section_3_p2')}</p>
                                        <p>{t('guide_section_3_p3')}</p>
                                    </Accordion.Body>
                                </Accordion.Item>

                                <Accordion.Item eventKey="3">
                                    <Accordion.Header>{t('guide_section_4_title')}</Accordion.Header>
                                    <Accordion.Body>
                                        <p>{t('guide_section_4_p1')}</p>
                                        <ol>
                                            <li>{t('guide_section_4_step1')}</li>
                                            <li>{t('guide_section_4_step2')}</li>
                                            <li>{t('guide_section_4_step3')}</li>
                                        </ol>
                                        <p>{t('guide_section_4_p2')}</p>
                                    </Accordion.Body>
                                </Accordion.Item>
                            </Accordion>

                        </Card.Body>
                        <Card.Footer className="text-muted text-center">
                            {t('guide_footer')}
                        </Card.Footer>
                    </Card>
                </Col>
            </Row>
        </Container>
    );
};

export default UserGuide;
