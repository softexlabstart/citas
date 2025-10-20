import React, { useState, useEffect } from 'react';
import { getOrganizationInfo, getOrganizationMembers, sendInvitation } from '../api';
import { OrganizationInfo, OrganizationMembersResponse, InvitationData } from '../interfaces/Organization';
import { Container, Row, Col, Card, Button, Alert, Modal, Form, Table, Badge, Tabs, Tab } from 'react-bootstrap';
import { Building, People, Plus, Envelope, GeoAlt, Phone } from 'react-bootstrap-icons';
import { useTranslation } from 'react-i18next';

const OrganizationPage: React.FC = () => {
    const { t } = useTranslation();
    const [organizationInfo, setOrganizationInfo] = useState<OrganizationInfo | null>(null);
    const [members, setMembers] = useState<OrganizationMembersResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showInviteModal, setShowInviteModal] = useState(false);
    const [inviteData, setInviteData] = useState<InvitationData>({
        email: '',
        first_name: '',
        last_name: '',
        role: 'colaborador',
        message: ''
    });

    useEffect(() => {
        loadOrganizationData();
    }, []);

    const loadOrganizationData = async () => {
        try {
            setLoading(true);
            const [orgInfo, membersData] = await Promise.all([
                getOrganizationInfo(),
                getOrganizationMembers()
            ]);
            setOrganizationInfo(orgInfo.data);
            setMembers(membersData.data);
        } catch (error: any) {
            setError('Error al cargar la información de la organización');
            console.error('Failed to load organization data', error);
        } finally {
            setLoading(false);
        }
    };

    const handleInviteSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            // Agregar organization_id al payload de invitación
            const invitationPayload = {
                ...inviteData,
                organization_id: organizationInfo?.organizacion.id
            };
            await sendInvitation(invitationPayload);
            setShowInviteModal(false);
            setInviteData({
                email: '',
                first_name: '',
                last_name: '',
                role: 'colaborador',
                message: ''
            });
            // Recargar datos
            loadOrganizationData();
        } catch (error: any) {
            setError('Error al enviar la invitación');
            console.error('Failed to send invitation', error);
        }
    };

    const getRoleBadge = (isSedeAdmin: boolean, isStaff: boolean) => {
        if (isStaff) return <Badge bg="danger">Super Admin</Badge>;
        if (isSedeAdmin) return <Badge bg="warning">Admin Sede</Badge>;
        return <Badge bg="secondary">Miembro</Badge>;
    };

    if (loading) {
        return (
            <Container className="py-5">
                <div className="text-center">
                    <div className="spinner-border" role="status">
                        <span className="visually-hidden">Cargando...</span>
                    </div>
                </div>
            </Container>
        );
    }

    if (error) {
        return (
            <Container className="py-5">
                <Alert variant="danger">{error}</Alert>
            </Container>
        );
    }

    return (
        <Container className="py-4">
            <Row className="mb-4">
                <Col>
                    <h1 className="h2">
                        <Building className="me-2" />
                        {organizationInfo?.organizacion.nombre}
                    </h1>
                    <p className="text-muted">Gestiona tu organización y miembros</p>
                </Col>
            </Row>

            <Tabs defaultActiveKey="info" className="mb-4">
                <Tab eventKey="info" title="Información">
                    <Row className="mt-3">
                        <Col md={6}>
                            <Card>
                                <Card.Header>
                                    <h5 className="mb-0">Información de la Organización</h5>
                                </Card.Header>
                                <Card.Body>
                                    <p><strong>Nombre:</strong> {organizationInfo?.organizacion.nombre}</p>
                                    <p><strong>Tu rol:</strong> {getRoleBadge(false, false)}</p>
                                </Card.Body>
                            </Card>
                        </Col>
                        <Col md={6}>
                            <Card>
                                <Card.Header>
                                    <h5 className="mb-0">Sedes</h5>
                                </Card.Header>
                                <Card.Body>
                                    {organizationInfo?.sedes.map((sede) => (
                                        <div key={sede.id} className="mb-2">
                                            <div className="d-flex align-items-center">
                                                <GeoAlt className="me-2" />
                                                <div>
                                                    <strong>{sede.nombre}</strong>
                                                    {sede.direccion && <div className="text-muted small">{sede.direccion}</div>}
                                                    {sede.telefono && <div className="text-muted small">{sede.telefono}</div>}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </Card.Body>
                            </Card>
                        </Col>
                    </Row>
                </Tab>

                <Tab eventKey="members" title="Miembros">
                    <Row className="mt-3">
                        <Col>
                            <Card>
                                <Card.Header className="d-flex justify-content-between align-items-center">
                                    <h5 className="mb-0">
                                        <People className="me-2" />
                                        Miembros ({members?.total || 0})
                                    </h5>
                                    <Button 
                                        variant="primary" 
                                        size="sm"
                                        onClick={() => setShowInviteModal(true)}
                                    >
                                        <Plus className="me-1" />
                                        Invitar
                                    </Button>
                                </Card.Header>
                                <Card.Body>
                                    <Table responsive>
                                        <thead>
                                            <tr>
                                                <th>Usuario</th>
                                                <th>Email</th>
                                                <th>Sede</th>
                                                <th>Rol</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {members?.miembros.map((member) => (
                                                <tr key={member.id}>
                                                    <td>
                                                        <div>
                                                            <strong>{member.first_name} {member.last_name}</strong>
                                                            <div className="text-muted small">@{member.username}</div>
                                                        </div>
                                                    </td>
                                                    <td>{member.email}</td>
                                                    <td>{member.perfil.sede?.nombre || 'Sin sede'}</td>
                                                    <td>{getRoleBadge(member.perfil.is_sede_admin, false)}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </Table>
                                </Card.Body>
                            </Card>
                        </Col>
                    </Row>
                </Tab>
            </Tabs>

            {/* Modal de Invitación */}
            <Modal show={showInviteModal} onHide={() => setShowInviteModal(false)} size="lg">
                <Modal.Header closeButton>
                    <Modal.Title>
                        <Envelope className="me-2" />
                        Invitar Nuevo Miembro
                    </Modal.Title>
                </Modal.Header>
                <Form onSubmit={handleInviteSubmit}>
                    <Modal.Body>
                        <Row>
                            <Col md={6}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Email</Form.Label>
                                    <Form.Control
                                        type="email"
                                        value={inviteData.email}
                                        onChange={(e) => setInviteData(prev => ({ ...prev, email: e.target.value }))}
                                        required
                                    />
                                </Form.Group>
                            </Col>
                            <Col md={6}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Rol</Form.Label>
                                    <Form.Select
                                        value={inviteData.role}
                                        onChange={(e) => setInviteData(prev => ({ ...prev, role: e.target.value as any }))}
                                    >
                                        <option value="colaborador">Colaborador</option>
                                        <option value="sede_admin">Administrador de Sede</option>
                                        <option value="admin">Administrador</option>
                                    </Form.Select>
                                </Form.Group>
                            </Col>
                        </Row>
                        <Row>
                            <Col md={6}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Nombre</Form.Label>
                                    <Form.Control
                                        type="text"
                                        value={inviteData.first_name}
                                        onChange={(e) => setInviteData(prev => ({ ...prev, first_name: e.target.value }))}
                                        required
                                    />
                                </Form.Group>
                            </Col>
                            <Col md={6}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Apellido</Form.Label>
                                    <Form.Control
                                        type="text"
                                        value={inviteData.last_name}
                                        onChange={(e) => setInviteData(prev => ({ ...prev, last_name: e.target.value }))}
                                        required
                                    />
                                </Form.Group>
                            </Col>
                        </Row>
                        <Form.Group className="mb-3">
                            <Form.Label>Mensaje (opcional)</Form.Label>
                            <Form.Control
                                as="textarea"
                                rows={3}
                                value={inviteData.message}
                                onChange={(e) => setInviteData(prev => ({ ...prev, message: e.target.value }))}
                                placeholder="Mensaje personalizado para la invitación..."
                            />
                        </Form.Group>
                    </Modal.Body>
                    <Modal.Footer>
                        <Button variant="secondary" onClick={() => setShowInviteModal(false)}>
                            Cancelar
                        </Button>
                        <Button variant="primary" type="submit">
                            <Envelope className="me-1" />
                            Enviar Invitación
                        </Button>
                    </Modal.Footer>
                </Form>
            </Modal>
        </Container>
    );
};

export default OrganizationPage;
