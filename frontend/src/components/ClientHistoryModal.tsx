import React, { useEffect } from 'react';
import { Modal, Button, Spinner, Alert, Table, Card, Row, Col } from 'react-bootstrap';
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

    // Formatear número como moneda colombiana (COP)
    const formatCurrency = (amount: number): string => {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    };

    return (
        <Modal show={show} onHide={onHide} size="xl" centered>
            <Modal.Header closeButton>
                <Modal.Title>{t('client_history')} - {client?.full_name}</Modal.Title>
            </Modal.Header>
            <Modal.Body style={{ maxHeight: '80vh', overflowY: 'auto' }}>
                {loading && (
                    <div className="text-center py-5">
                        <Spinner animation="border" variant="primary" />
                        <p className="mt-3">{t('loading')}...</p>
                    </div>
                )}
                {error && <Alert variant="danger">{error}</Alert>}
                {history && (
                    <div>
                        {/* LTV Card - Métrica Destacada */}
                        <h5 className="mb-3">💰 {t('financial_metrics') || 'Métricas Financieras'}</h5>
                        <Card bg="success" text="white" className="shadow mb-4">
                            <Card.Body>
                                <div className="d-flex justify-content-between align-items-center">
                                    <div>
                                        <h6 className="mb-1 text-white-50">Ingresos Generados (LTV)</h6>
                                        <h2 className="mb-0 fw-bold">{formatCurrency(history.stats.ltv || 0)}</h2>
                                        <small className="text-white-50">Total de servicios en citas asistidas</small>
                                    </div>
                                    <div style={{ fontSize: '3.5rem', opacity: 0.25 }}>💵</div>
                                </div>
                            </Card.Body>
                        </Card>

                        {/* Estadísticas de Citas */}
                        <h5 className="mb-3">📊 {t('appointment_stats') || 'Estadísticas de Citas'}</h5>
                        <Row className="mb-4">
                            <Col md={6} lg={3} className="mb-3">
                                <Card className="h-100 shadow-sm border-primary">
                                    <Card.Body className="text-center">
                                        <div style={{ fontSize: '2rem' }}>📅</div>
                                        <h6 className="text-muted mb-1">{t('total') || 'Total'}</h6>
                                        <h3 className="mb-0 fw-bold text-primary">{history.stats.total}</h3>
                                    </Card.Body>
                                </Card>
                            </Col>
                            <Col md={6} lg={3} className="mb-3">
                                <Card className="h-100 shadow-sm border-success">
                                    <Card.Body className="text-center">
                                        <div style={{ fontSize: '2rem' }}>✅</div>
                                        <h6 className="text-muted mb-1">{t('attended') || 'Asistidas'}</h6>
                                        <h3 className="mb-0 fw-bold text-success">{history.stats.asistidas}</h3>
                                    </Card.Body>
                                </Card>
                            </Col>
                            <Col md={6} lg={3} className="mb-3">
                                <Card className="h-100 shadow-sm border-danger">
                                    <Card.Body className="text-center">
                                        <div style={{ fontSize: '2rem' }}>❌</div>
                                        <h6 className="text-muted mb-1">{t('canceled') || 'Canceladas'}</h6>
                                        <h3 className="mb-0 fw-bold text-danger">{history.stats.canceladas}</h3>
                                    </Card.Body>
                                </Card>
                            </Col>
                            <Col md={6} lg={3} className="mb-3">
                                <Card className="h-100 shadow-sm border-warning">
                                    <Card.Body className="text-center">
                                        <div style={{ fontSize: '2rem' }}>🚫</div>
                                        <h6 className="text-muted mb-1">{t('not_attended') || 'No Asistidas'}</h6>
                                        <h3 className="mb-0 fw-bold text-warning">{history.stats.no_asistidas}</h3>
                                    </Card.Body>
                                </Card>
                            </Col>
                        </Row>

                        {/* Servicios Más Usados */}
                        {history.servicios_mas_usados && history.servicios_mas_usados.length > 0 && (
                            <>
                                <h5 className="mb-3">🎯 {t('most_used_services') || 'Servicios Más Usados'}</h5>
                                <Card className="mb-4 shadow-sm">
                                    <Card.Body>
                                        {history.servicios_mas_usados.map((servicio: any, index: number) => (
                                            <div
                                                key={index}
                                                className={`d-flex justify-content-between align-items-center ${index !== history.servicios_mas_usados.length - 1 ? 'mb-2 pb-2 border-bottom' : ''}`}
                                            >
                                                <span className="fw-bold">{servicio.servicios__nombre || 'Sin servicio'}</span>
                                                <span className="badge bg-primary rounded-pill">{servicio.count} {t('times') || 'veces'}</span>
                                            </div>
                                        ))}
                                        {history.servicios_mas_usados.length === 0 && (
                                            <p className="text-muted text-center mb-0">No hay servicios registrados</p>
                                        )}
                                    </Card.Body>
                                </Card>
                            </>
                        )}

                        {/* Historial de Citas */}
                        <h5 className="mb-3">📋 {t('appointment_history') || 'Historial de Citas'}</h5>
                        <div className="table-responsive">
                            <Table striped bordered hover>
                                <thead className="table-light">
                                    <tr>
                                        <th>{t('date') || 'Fecha'}</th>
                                        <th>{t('service') || 'Servicio'}</th>
                                        <th>{t('status') || 'Estado'}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {history.citas && history.citas.length > 0 ? (
                                        history.citas.map((cita: any) => (
                                            <tr key={cita.id}>
                                                <td>{new Date(cita.fecha).toLocaleString('es-CO')}</td>
                                                <td>
                                                    {cita.servicios && cita.servicios.length > 0
                                                        ? cita.servicios.map((s: any) => s.nombre).join(', ')
                                                        : 'Sin servicio'}
                                                </td>
                                                <td>
                                                    <span className={`badge ${
                                                        cita.estado === 'Asistio' ? 'bg-success' :
                                                        cita.estado === 'Cancelada' ? 'bg-danger' :
                                                        cita.estado === 'No Asistio' ? 'bg-warning' :
                                                        cita.estado === 'Confirmada' ? 'bg-info' :
                                                        'bg-secondary'
                                                    }`}>
                                                        {t(cita.estado) || cita.estado}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan={3} className="text-center text-muted">
                                                No hay citas registradas
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </Table>
                        </div>
                    </div>
                )}
            </Modal.Body>
            <Modal.Footer>
                <Button variant="secondary" onClick={onHide}>
                    {t('close') || 'Cerrar'}
                </Button>
            </Modal.Footer>
        </Modal>
    );
};

export default ClientHistoryModal;
