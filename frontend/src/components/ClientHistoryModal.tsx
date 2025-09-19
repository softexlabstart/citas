import React, { useEffect } from 'react';
import { Modal, Button, Spinner, Alert, Table, ListGroup } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { useApi } from '../hooks/useApi';
import { getClientHistory } from '../api';
import { Client } from '../interfaces/Client';

interface ClientHistoryModalProps {
    client: Client | null;
    show: boolean;
    onHide: () => void;
}

const ClientHistoryModal: React.FC<ClientHistoryModalProps> = ({ client, show, onHide }) => {
    const { t } = useTranslation();
    const { data: history, loading, error, request: fetchHistory } = useApi(getClientHistory);

    useEffect(() => {
        if (client && show) {
            fetchHistory(client.id);
        }
    }, [client, show, fetchHistory]);

    return (
        <Modal show={show} onHide={onHide} size="lg" centered>
            <Modal.Header closeButton>
                <Modal.Title>{t('client_history')} - {client?.full_name}</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                {loading && <Spinner animation="border" />}
                {error && <Alert variant="danger">{error}</Alert>}
                {history && (
                    <div>
                        <h4>{t('appointment_stats')}</h4>
                        <ListGroup horizontal className="mb-3">
                            <ListGroup.Item><strong>{t('total')}:</strong> {history.stats.total}</ListGroup.Item>
                            <ListGroup.Item><strong>{t('attended')}:</strong> {history.stats.asistidas}</ListGroup.Item>
                            <ListGroup.Item><strong>{t('canceled')}:</strong> {history.stats.canceladas}</ListGroup.Item>
                            <ListGroup.Item><strong>{t('not_attended')}:</strong> {history.stats.no_asistidas}</ListGroup.Item>
                        </ListGroup>

                        <h4>{t('most_used_services')}</h4>
                        <ListGroup className="mb-3">
                            {history.servicios_mas_usados.map((servicio: any, index: number) => (
                                <ListGroup.Item key={index}>
                                    {servicio.servicio__nombre}: {servicio.count} {t('times')}
                                </ListGroup.Item>
                            ))}
                        </ListGroup>

                        <h4>{t('appointment_history')}</h4>
                        <Table striped bordered hover responsive>
                            <thead>
                                <tr>
                                    <th>{t('date')}</th>
                                    <th>{t('service')}</th>
                                    <th>{t('status')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {history.citas.map((cita: any) => (
                                    <tr key={cita.id}>
                                        <td>{new Date(cita.fecha).toLocaleString()}</td>
                                        <td>{cita.servicios.map((s: any) => s.nombre).join(', ')}</td>
                                        <td>{t(cita.estado)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </Table>
                    </div>
                )}
            </Modal.Body>
            <Modal.Footer>
                <Button variant="secondary" onClick={onHide}>
                    {t('close')}
                </Button>
            </Modal.Footer>
        </Modal>
    );
};

export default ClientHistoryModal;