import React, { useState, useEffect } from 'react';
import { Table, Button, Form, Row, Col, Spinner, Alert, Card } from 'react-bootstrap';
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

    useEffect(() => {
        fetchRecursos(undefined);
        fetchBloqueos(undefined);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

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

        const { success } = await createBloqueo(payload);
        if (success) {
            toast.success(t('block_created_successfully'));
            fetchBloqueos(undefined);
            setFormData({ colaborador_id: '', sede_id: '', motivo: '', fecha_inicio: '', fecha_fin: '' });
        } else {
            toast.error(t('unexpected_error'));
        }
    };

    const handleDelete = async (id: number) => {
        if (window.confirm(t('confirm_delete_block'))) {
            setProcessingId(id);
            const { success } = await removeBloqueo(id);
            if (success) {
                toast.success(t('block_deleted_successfully'));
                fetchBloqueos(undefined);
            } else {
                toast.error(t('unexpected_error'));
            }
            setProcessingId(null);
        }
    };

    return (
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

                <h4 className="mb-3">{t('existing_blocks')}</h4>
                {loading && <Spinner animation="border" />}
                {error && <Alert variant="danger">{t(error)}</Alert>}
                <Table striped bordered hover responsive>
                    <thead><tr><th>{t('resource_label')}</th><th>{t('reason')}</th><th>{t('start_datetime')}</th><th>{t('end_datetime')}</th><th>{t('actions')}</th></tr></thead>
                    <tbody>{bloqueos?.map(b => (<tr key={b.id}><td>{b.recurso.nombre}</td><td>{b.motivo}</td><td>{new Date(b.fecha_inicio).toLocaleString()}</td><td>{new Date(b.fecha_fin).toLocaleString()}</td><td><Button variant="danger" size="sm" onClick={() => handleDelete(b.id)} disabled={isDeleting && processingId === b.id}>{isDeleting && processingId === b.id ? <Spinner size="sm" /> : t('delete')}</Button></td></tr>))}</tbody>
                </Table>
            </Card.Body>
        </Card>
    );
};

export default BlocksManager;