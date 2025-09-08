import React, { useState, useEffect } from 'react';
import { Container, Tabs, Tab, Table, Button, Modal, Form, Row, Col, Spinner, InputGroup, Alert } from 'react-bootstrap';
import BlocksManager from './BlocksManager';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import { useApi } from '../hooks/useApi';
import { getServicios, addServicio, updateServicio, deleteServicio, getRecursos, addRecurso, updateRecurso, deleteRecurso, getSedes } from '../api';
import { Service } from '../interfaces/Service';
import { Recurso } from '../interfaces/Recurso';
import { Sede } from '../interfaces/Sede';
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';

// Define extended interfaces locally to avoid modifying shared interface files.
// This acknowledges that for this admin component, we expect more detailed data from the API.
interface ServiceWithDetails extends Service {
    sede: Sede;
    precio: number;
    metadata?: { [key: string]: any };
}

interface RecursoWithDetails extends Recurso {
    sede: Sede;
    metadata?: { [key: string]: any };
}

type MetadataPair = { key: string; value: string };

const AdminSettings: React.FC = () => {
    const { t } = useTranslation();
    const { user } = useAuth();
    const navigate = useNavigate();

    // Authorization check
    useEffect(() => {
        if (user === null) return; // Wait until user state is resolved
        if (!user || (!user.is_staff && !user.perfil?.is_sede_admin)) {
            toast.error("No tienes permiso para acceder a esta página.");
            navigate('/');
        }
    }, [user, navigate]);

    // API Hooks
    const { data: servicios, loading: loadingServicios, request: fetchServicios } = useApi<ServiceWithDetails[], [string | undefined]>(getServicios as any);
    const { data: recursos, loading: loadingRecursos, request: fetchRecursos } = useApi<RecursoWithDetails[], [string | undefined]>(getRecursos as any);
    const { data: sedes, request: fetchSedes } = useApi<Sede[], []>(getSedes);

    // State for modals and forms
    const [showModal, setShowModal] = useState(false);
    const [modalType, setModalType] = useState<'service' | 'resource' | null>(null);
    const [editingItem, setEditingItem] = useState<ServiceWithDetails | RecursoWithDetails | null>(null);
    const [formData, setFormData] = useState<any>({});
    const [metadata, setMetadata] = useState<MetadataPair[]>([]);
    const [processing, setProcessing] = useState(false);

    useEffect(() => {
        fetchServicios(undefined);
        fetchRecursos(undefined);
        fetchSedes();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const handleOpenModal = (type: 'service' | 'resource', item: ServiceWithDetails | RecursoWithDetails | null = null) => {
        setModalType(type);
        setEditingItem(item);
        if (item) {
            setFormData({ ...item });
            const meta = item.metadata ? Object.entries(item.metadata).map(([key, value]) => ({ key, value: String(value) })) : [];
            setMetadata(meta);
        } else {
            setFormData(type === 'service' ? { nombre: '', descripcion: '', duracion_estimada: 30, precio: 0.00, sede: '' } : { nombre: '', descripcion: '', sede: '' });
            setMetadata([]);
        }
        setShowModal(true);
    };

    const handleCloseModal = () => {
        setShowModal(false);
        setModalType(null);
        setEditingItem(null);
        setFormData({});
        setMetadata([]);
    };

    const handleMetadataChange = (index: number, field: 'key' | 'value', value: string) => {
        const newMetadata = [...metadata];
        newMetadata[index][field] = value;
        setMetadata(newMetadata);
    };

    const addMetadataField = () => {
        setMetadata([...metadata, { key: '', value: '' }]);
    };

    const removeMetadataField = (index: number) => {
        const newMetadata = metadata.filter((_, i) => i !== index);
        setMetadata(newMetadata);
    };

    const handleFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setProcessing(true);

        const finalMetadata = metadata.reduce((acc, pair) => {
            if (pair.key) {
                acc[pair.key] = pair.value;
            }
            return acc;
        }, {} as { [key: string]: any });

        const payload = { ...formData, metadata: finalMetadata, sede_id: Number(formData.sede?.id || formData.sede) };
        // The 'sede' object is not needed in the payload, only 'sede_id'
        delete payload.sede;

        let success = false;
        try {
            if (modalType === 'service') {
                await (editingItem ? updateServicio(editingItem.id, payload) : addServicio(payload));
                fetchServicios(undefined);
            } else if (modalType === 'resource') {
                await (editingItem ? updateRecurso(editingItem.id, payload) : addRecurso(payload));
                fetchRecursos(undefined);
            }
            success = true;
        } catch (err: any) {
            toast.error(err.response?.data?.detail || t('unexpected_error'));
        }

        if (success) {
            toast.success(editingItem ? t('item_updated_successfully') : t('item_created_successfully'));
            handleCloseModal();
        }
        setProcessing(false);
    };
    
    const handleDelete = async (type: 'service' | 'resource', id: number) => {
        if (window.confirm(t('confirm_delete_item'))) {
            try {
                if (type === 'service') {
                    await deleteServicio(id);
                    fetchServicios(undefined);
                } else if (type === 'resource') {
                    await deleteRecurso(id);
                    fetchRecursos(undefined);
                }
                toast.success(t('item_deleted_successfully'));
            } catch (err: any) {
                toast.error(err.response?.data?.detail || t('unexpected_error'));
            }
        }
    };

    if (!user || (!user.is_staff && !user.perfil?.is_sede_admin)) {
        return <Container className="mt-5"><Alert variant="danger">Acceso denegado. No tienes permiso para ver esta página.</Alert></Container>;
    }

    return (
        <Container className="mt-5">
            <h2>{t('admin_settings')}</h2>
            <Tabs defaultActiveKey="services" id="admin-settings-tabs" className="mb-3">
                <Tab eventKey="services" title={t('manage_services')}>
                    <Button className="mb-3" onClick={() => handleOpenModal('service')}>{t('new_service')}</Button>
                    <Table striped bordered hover responsive>
                        <thead><tr><th>{t('name')}</th><th>{t('description')}</th><th>{t('duration')}</th><th>{t('price')}</th><th>{t('sede_label')}</th><th>{t('actions')}</th></tr></thead>
                        <tbody>
                            {loadingServicios ? (<tr><td colSpan={6} className="text-center"><Spinner animation="border" /></td></tr>) : (
                                servicios?.map(s => (<tr key={s.id}><td>{s.nombre}</td><td>{s.descripcion}</td><td>{s.duracion_estimada} min</td><td>${(Number(s.precio) || 0).toFixed(2)}</td><td>{s.sede.nombre}</td><td><Button variant="warning" size="sm" onClick={() => handleOpenModal('service', s)}>{t('edit')}</Button>{' '}<Button variant="danger" size="sm" onClick={() => handleDelete('service', s.id)}>{t('delete')}</Button></td></tr>))
                            )}
                        </tbody>
                    </Table>
                </Tab>
                <Tab eventKey="resources" title={t('manage_resources')}>
                    <Button className="mb-3" onClick={() => handleOpenModal('resource')}>{t('new_resource')}</Button>
                    <Table striped bordered hover responsive>
                        <thead><tr><th>{t('name')}</th><th>{t('description')}</th><th>{t('sede_label')}</th><th>{t('actions')}</th></tr></thead>
                        <tbody>
                            {loadingRecursos ? (<tr><td colSpan={4} className="text-center"><Spinner animation="border" /></td></tr>) : (
                                recursos?.map(r => (<tr key={r.id}><td>{r.nombre}</td><td>{r.descripcion}</td><td>{r.sede.nombre}</td><td><Button variant="warning" size="sm" onClick={() => handleOpenModal('resource', r)}>{t('edit')}</Button>{' '}<Button variant="danger" size="sm" onClick={() => handleDelete('resource', r.id)}>{t('delete')}</Button></td></tr>))
                            )}
                        </tbody>
                    </Table>
                </Tab>
                <Tab eventKey="blocks" title={t('manage_blocks')}>
                    <BlocksManager />
                </Tab>
            </Tabs>

            <Modal show={showModal} onHide={handleCloseModal} size="lg">
                <Form onSubmit={handleSubmit}>
                    <Modal.Header closeButton><Modal.Title>{editingItem ? t('edit') : t('new')}{' '}{modalType === 'service' ? t('service') : t('resource')}</Modal.Title></Modal.Header>
                    <Modal.Body>
                        <Form.Group className="mb-3"><Form.Label>{t('name')}</Form.Label><Form.Control type="text" name="nombre" value={formData.nombre || ''} onChange={handleFormChange} required /></Form.Group>
                        <Form.Group className="mb-3"><Form.Label>{t('description')}</Form.Label><Form.Control as="textarea" name="descripcion" value={formData.descripcion || ''} onChange={handleFormChange} /></Form.Group>
                        {modalType === 'service' && (<Form.Group className="mb-3"><Form.Label>{t('duration')}</Form.Label><Form.Control type="number" name="duracion_estimada" value={formData.duracion_estimada || 30} onChange={handleFormChange} required /></Form.Group>)}
                        {modalType === 'service' && (<Form.Group className="mb-3"><Form.Label>{t('price')}</Form.Label><Form.Control type="number" name="precio" value={formData.precio || '0.00'} onChange={handleFormChange} step="0.01" required /></Form.Group>)}
                        <Form.Group className="mb-3"><Form.Label>{t('sede_label')}</Form.Label><Form.Control as="select" name="sede" value={formData.sede?.id || formData.sede || ''} onChange={handleFormChange} required><option value="">{t('select_sede')}</option>{sedes?.map(s => <option key={s.id} value={s.id}>{s.nombre}</option>)}</Form.Control></Form.Group>
                        <hr />
                        <h5>{t('metadata')}</h5>
                        {metadata.map((pair, index) => (
                            <Row key={index} className="mb-2">
                                <Col>
                                    <InputGroup>
                                        <Form.Control type="text" placeholder={t('key')} value={pair.key} onChange={(e) => handleMetadataChange(index, 'key', e.target.value)} />
                                        <Form.Control type="text" placeholder={t('value')} value={pair.value} onChange={(e) => handleMetadataChange(index, 'value', e.target.value)} />
                                        <Button variant="outline-danger" onClick={() => removeMetadataField(index)}>X</Button>
                                    </InputGroup>
                                </Col>
                            </Row>
                        ))}
                        <Button variant="outline-secondary" size="sm" onClick={addMetadataField}>{t('add_field')}</Button>
                    </Modal.Body>
                    <Modal.Footer>
                        <Button variant="secondary" onClick={handleCloseModal}>{t('close')}</Button>
                        <Button variant="primary" type="submit" disabled={processing}>{processing ? <Spinner size="sm" /> : t('save_changes')}</Button>
                    </Modal.Footer>
                </Form>
            </Modal>
        </Container>
    );
};

export default AdminSettings;