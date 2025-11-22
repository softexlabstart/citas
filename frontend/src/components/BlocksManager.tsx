import React, { useState, useEffect, useMemo } from 'react';
import { Table, Button, Form, Row, Col, Spinner, Alert, Card, Modal, Badge } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import { useApi } from '../hooks/useApi';
import { getRecursos, getBloqueos, addBloqueo, deleteBloqueo, Bloqueo, CreateBloqueoPayload } from '../api';
import { Recurso } from '../interfaces/Recurso';
import { Sede } from '../interfaces/Sede';

// Define an extended interface to include nested sede details from the API response.
interface RecursoWithDetails extends Recurso {
    sede: Sede;
}

const BlocksManager: React.FC = () => {
    const { t } = useTranslation();

    // API Hooks
    const { data: recursos, request: fetchRecursos } = useApi<RecursoWithDetails[], [string | undefined]>(getRecursos as any);
    const { data: bloqueos, loading, error, request: fetchBloqueos } = useApi<Bloqueo[], [string | undefined]>(getBloqueos);
    const { loading: isCreating, request: createBloqueo } = useApi<Bloqueo, [CreateBloqueoPayload]>(addBloqueo);
    const { loading: isDeleting, request: removeBloqueo } = useApi<any, [number]>(deleteBloqueo);

    // Form State
    const [formData, setFormData] = useState({
        colaborador_id: '',
        sede_id: '',
        motivo: '',
        fecha_inicio: '',
        fecha_fin: '',
    });
    const [processingId, setProcessingId] = useState<number | null>(null);
    const [showDeleteConfirmModal, setShowDeleteConfirmModal] = useState(false);
    const [deletingBlockId, setDeletingBlockId] = useState<number | null>(null);

    useEffect(() => {
        fetchRecursos(undefined);
        fetchBloqueos(undefined);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const { activeBlocks, pastBlocks } = useMemo(() => {
        const now = new Date();
        const active: Bloqueo[] = [];
        const past: Bloqueo[] = [];

        bloqueos?.forEach(b => {
            if (new Date(b.fecha_fin) > now) {
                active.push(b);
            } else {
                past.push(b);
            }
        });

        return { activeBlocks: active, pastBlocks: past };
    }, [bloqueos]);

    const handleFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        
        if (name === 'colaborador_id') {
            const selectedRecurso = recursos?.find(r => r.id === Number(value));
            // When a resource is selected, also update the corresponding sede_id atomically
            setFormData(prev => ({
                ...prev,
                colaborador_id: value,
                sede_id: selectedRecurso ? String(selectedRecurso.sede.id) : ''
            }));
        } else {
            setFormData(prev => ({ ...prev, [name]: value }));
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.colaborador_id || !formData.motivo || !formData.fecha_inicio || !formData.fecha_fin || !formData.sede_id) {
            toast.warn(t('please_fill_all_fields'));
            return;
        }

        const payload: CreateBloqueoPayload = {
            ...formData,
            colaborador_id: Number(formData.colaborador_id),
            sede_id: Number(formData.sede_id),
        };

        const { success, error: apiError } = await createBloqueo(payload);
        if (success) {
            toast.success(t('block_created_successfully'));
            fetchBloqueos(undefined);
            setFormData({ colaborador_id: '', sede_id: '', motivo: '', fecha_inicio: '', fecha_fin: '' });
        } else {
            toast.error(apiError || t('unexpected_error'));
        }
    };

    const handleDelete = (id: number) => {
        setDeletingBlockId(id);
        setShowDeleteConfirmModal(true);
    };

    const confirmDelete = async () => {
        if (!deletingBlockId) return;
        setProcessingId(deletingBlockId);
        const { success, error: apiError } = await removeBloqueo(deletingBlockId);
        if (success) {
            toast.success(t('block_deleted_successfully'));
            fetchBloqueos(undefined);
        } else {
            toast.error(apiError || t('unexpected_error'));
        }
        setProcessingId(null);
        setShowDeleteConfirmModal(false);
        setDeletingBlockId(null);
    };

    return (
        <>
            <Card className="p-4 rounded shadow-sm">
                <Card.Body>
                    <h4 className="mb-3">{t('new_block')}</h4>
                    <Form onSubmit={handleSubmit}>
                        <Row>
                            <Col md={6}>
                                <Form.Group className="mb-3">
                                    <Form.Label>{t('resource_label')}</Form.Label>
                                    <Form.Control as="select" name="colaborador_id" value={formData.colaborador_id} onChange={handleFormChange} required>
                                        <option value="">{t('select_resource')}</option>
                                        {recursos?.map(r => <option key={r.id} value={r.id}>{r.nombre} ({r.sede.nombre})</option>)}
                                    </Form.Control>
                                </Form.Group>
                            </Col>
                            <Col md={6}>
                                <Form.Group className="mb-3">
                                    <Form.Label>{t('reason')}</Form.Label>
                                    <Form.Control type="text" name="motivo" value={formData.motivo} onChange={handleFormChange} required />
                                </Form.Group>
                            </Col>
                        </Row>
                        <Row>
                            <Col md={6}>
                                <Form.Group className="mb-3">
                                    <Form.Label>{t('start_datetime')}</Form.Label>
                                    <Form.Control type="datetime-local" name="fecha_inicio" value={formData.fecha_inicio} onChange={handleFormChange} required />
                                </Form.Group>
                            </Col>
                            <Col md={6}>
                                <Form.Group className="mb-3">
                                    <Form.Label>{t('end_datetime')}</Form.Label>
                                    <Form.Control type="datetime-local" name="fecha_fin" value={formData.fecha_fin} onChange={handleFormChange} required />
                                </Form.Group>
                            </Col>
                        </Row>
                        <div className="d-flex justify-content-end">
                            <Button type="submit" disabled={isCreating}>{isCreating ? <Spinner size="sm" /> : t('add_block')}</Button>
                        </div>
                    </Form>

                    <hr className="my-4" />

                    <div className="d-flex justify-content-between align-items-center mb-3">
                        <h4 className="mb-0">{t('active_blocks')}</h4>
                        <Badge bg="primary" pill>{activeBlocks?.length || 0} activos</Badge>
                    </div>
                    {loading && <div className="text-center py-4"><Spinner animation="border" /></div>}
                    {error && <Alert variant="danger">{t(error)}</Alert>}
                    {!loading && activeBlocks && activeBlocks.length === 0 && (
                        <Alert variant="info">
                            <i className="bi bi-info-circle me-2"></i>
                            No hay bloqueos activos en este momento
                        </Alert>
                    )}
                    {!loading && activeBlocks && activeBlocks.length > 0 && (
                        <Table striped bordered hover responsive>
                            <thead>
                                <tr>
                                    <th>{t('resource_label')}</th>
                                    <th>{t('reason')}</th>
                                    <th>{t('start_datetime')}</th>
                                    <th>{t('end_datetime')}</th>
                                    <th>Estado</th>
                                    <th>{t('actions')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {activeBlocks.map(b => {
                                    const now = new Date();
                                    const start = new Date(b.fecha_inicio);
                                    const isActive = start <= now;
                                    return (
                                        <tr key={b.id} className={isActive ? 'table-warning' : ''}>
                                            <td>{b.colaborador?.nombre}</td>
                                            <td>{b.motivo}</td>
                                            <td>{new Date(b.fecha_inicio).toLocaleString()}</td>
                                            <td>{new Date(b.fecha_fin).toLocaleString()}</td>
                                            <td>
                                                {isActive ? (
                                                    <Badge bg="warning" text="dark">
                                                        <i className="bi bi-clock-fill me-1"></i>
                                                        En curso
                                                    </Badge>
                                                ) : (
                                                    <Badge bg="secondary">
                                                        <i className="bi bi-calendar-event me-1"></i>
                                                        Programado
                                                    </Badge>
                                                )}
                                            </td>
                                            <td>
                                                <Button
                                                    variant="danger"
                                                    size="sm"
                                                    onClick={() => handleDelete(b.id)}
                                                    disabled={isDeleting && processingId === b.id}
                                                >
                                                    {isDeleting && processingId === b.id ? <Spinner size="sm" /> : t('delete')}
                                                </Button>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </Table>
                    )}

                    <hr className="my-4" />

                    <h4 className="mb-3">{t('past_blocks')}</h4>
                    <Table striped bordered hover responsive>
                        <thead><tr><th>{t('resource_label')}</th><th>{t('reason')}</th><th>{t('start_datetime')}</th><th>{t('end_datetime')}</th><th>{t('actions')}</th></tr></thead>
                        <tbody>{pastBlocks?.map(b => (<tr key={b.id} className="table-secondary text-muted"><td>{b.colaborador?.nombre}</td><td>{b.motivo}</td><td>{new Date(b.fecha_inicio).toLocaleString()}</td><td>{new Date(b.fecha_fin).toLocaleString()}</td><td><Button variant="danger" size="sm" onClick={() => handleDelete(b.id)} disabled={isDeleting && processingId === b.id}>{isDeleting && processingId === b.id ? <Spinner size="sm" /> : t('delete')}</Button></td></tr>))}</tbody>
                    </Table>
                </Card.Body>
            </Card>

            <Modal show={showDeleteConfirmModal} onHide={() => setShowDeleteConfirmModal(false)} centered>
                <Modal.Header closeButton>
                    <Modal.Title>{t('confirm_delete_block_title')}</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    {t('confirm_delete_block_body')}
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={() => setShowDeleteConfirmModal(false)}>
                        {t('no')}
                    </Button>
                    <Button variant="danger" onClick={confirmDelete} disabled={isDeleting}>
                        {isDeleting ? (
                            <Spinner as="span" animation="border" size="sm" />
                        ) : (
                            t('yes_delete')
                        )}
                    </Button>
                </Modal.Footer>
            </Modal>
        </>
    );
};

export default BlocksManager;