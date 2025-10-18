import React, { useEffect } from 'react';
import { Modal, Button, Spinner, Alert, Table, Card, Row, Col, Badge } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { useApi } from '../hooks/useApi';
import { getClientHistory } from '../api';
import { Client } from '../interfaces/Client';
import './ClientHistoryModal.css';

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
        <Modal show={show} onHide={onHide} size="xl" centered className="client-history-modal">
            <Modal.Header closeButton className="border-0 pb-0">
                <Modal.Title className="w-100">
                    <div className="d-flex align-items-center">
                        <div className="client-avatar me-3">
                            {client?.full_name?.charAt(0).toUpperCase()}
                        </div>
                        <div>
                            <h4 className="mb-0 fw-bold">{client?.full_name}</h4>
                            <small className="text-muted">{t('client_history') || 'Historial del Cliente'}</small>
                        </div>
                    </div>
                </Modal.Title>
            </Modal.Header>
            <Modal.Body style={{ maxHeight: '75vh', overflowY: 'auto' }} className="px-4">
                {loading && (
                    <div className="loading-container text-center py-5">
                        <Spinner animation="border" variant="primary" className="mb-3" />
                        <p className="text-muted">{t('loading')}...</p>
                    </div>
                )}
                {error && <Alert variant="danger" className="rounded-3">{error}</Alert>}
                {history && (
                    <div>
                        {/* LTV Card - Métrica Destacada con Gradiente */}
                        <div className="section-header mb-3">
                            <span className="section-icon">💰</span>
                            <h5 className="mb-0 fw-semibold">{t('financial_metrics') || 'Métricas Financieras'}</h5>
                        </div>
                        <Card className="ltv-card border-0 shadow-lg mb-4">
                            <Card.Body className="p-4">
                                <div className="d-flex justify-content-between align-items-center">
                                    <div>
                                        <p className="ltv-label mb-2">Ingresos Generados (LTV)</p>
                                        <h1 className="ltv-amount mb-1">{formatCurrency(history.stats.ltv || 0)}</h1>
                                        <p className="ltv-description mb-0">Total de servicios en citas asistidas</p>
                                    </div>
                                    <div className="ltv-icon">💵</div>
                                </div>
                            </Card.Body>
                        </Card>

                        {/* Estadísticas de Citas - Cards Mejorados */}
                        <div className="section-header mb-3">
                            <span className="section-icon">📊</span>
                            <h5 className="mb-0 fw-semibold">{t('appointment_stats') || 'Estadísticas de Citas'}</h5>
                        </div>
                        <Row className="g-3 mb-4">
                            <Col xs={6} lg={3}>
                                <Card className="stat-card stat-card-total h-100 border-0 shadow-sm">
                                    <Card.Body className="p-3">
                                        <div className="stat-icon mb-2">📅</div>
                                        <p className="stat-label mb-1">total</p>
                                        <h2 className="stat-value mb-0">{history.stats.total}</h2>
                                    </Card.Body>
                                </Card>
                            </Col>
                            <Col xs={6} lg={3}>
                                <Card className="stat-card stat-card-attended h-100 border-0 shadow-sm">
                                    <Card.Body className="p-3">
                                        <div className="stat-icon mb-2">✅</div>
                                        <p className="stat-label mb-1">Asistió</p>
                                        <h2 className="stat-value mb-0">{history.stats.asistidas}</h2>
                                    </Card.Body>
                                </Card>
                            </Col>
                            <Col xs={6} lg={3}>
                                <Card className="stat-card stat-card-canceled h-100 border-0 shadow-sm">
                                    <Card.Body className="p-3">
                                        <div className="stat-icon mb-2">❌</div>
                                        <p className="stat-label mb-1">canceladas</p>
                                        <h2 className="stat-value mb-0">{history.stats.canceladas}</h2>
                                    </Card.Body>
                                </Card>
                            </Col>
                            <Col xs={6} lg={3}>
                                <Card className="stat-card stat-card-missed h-100 border-0 shadow-sm">
                                    <Card.Body className="p-3">
                                        <div className="stat-icon mb-2">🚫</div>
                                        <p className="stat-label mb-1">No Asistió</p>
                                        <h2 className="stat-value mb-0">{history.stats.no_asistidas}</h2>
                                    </Card.Body>
                                </Card>
                            </Col>
                        </Row>

                        {/* Servicios Más Usados - Rediseñado */}
                        {history.servicios_mas_usados && history.servicios_mas_usados.length > 0 && (
                            <>
                                <div className="section-header mb-3">
                                    <span className="section-icon">🎯</span>
                                    <h5 className="mb-0 fw-semibold">{t('most_used_services') || 'Servicios Más Usados'}</h5>
                                </div>
                                <Card className="services-card border-0 shadow-sm mb-4">
                                    <Card.Body className="p-3">
                                        {history.servicios_mas_usados.map((servicio: any, index: number) => (
                                            <div
                                                key={index}
                                                className={`service-item d-flex justify-content-between align-items-center ${
                                                    index !== history.servicios_mas_usados.length - 1 ? 'mb-3 pb-3' : ''
                                                }`}
                                            >
                                                <div className="d-flex align-items-center">
                                                    <div className="service-rank me-3">{index + 1}</div>
                                                    <span className="service-name">{servicio.servicios__nombre || 'Sin servicio'}</span>
                                                </div>
                                                <Badge bg="primary" pill className="service-count px-3 py-2">
                                                    {servicio.count}
                                                </Badge>
                                            </div>
                                        ))}
                                    </Card.Body>
                                </Card>
                            </>
                        )}

                        {/* Historial de Citas - Tabla Mejorada */}
                        <div className="section-header mb-3">
                            <span className="section-icon">📋</span>
                            <h5 className="mb-0 fw-semibold">{t('appointment_history') || 'Historial de Citas'}</h5>
                        </div>
                        <Card className="history-table-card border-0 shadow-sm">
                            <div className="table-responsive">
                                <Table hover className="mb-0 history-table">
                                    <thead>
                                        <tr>
                                            <th>{t('date') || 'Fecha'}</th>
                                            <th>{t('service') || 'Servicio'}</th>
                                            <th className="text-center">{t('status') || 'Estado'}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {history.citas && history.citas.length > 0 ? (
                                            history.citas.map((cita: any) => (
                                                <tr key={cita.id}>
                                                    <td className="text-nowrap">
                                                        <div className="date-cell">
                                                            {new Date(cita.fecha).toLocaleDateString('es-CO', {
                                                                year: 'numeric',
                                                                month: 'short',
                                                                day: 'numeric'
                                                            })}
                                                            <small className="d-block text-muted">
                                                                {new Date(cita.fecha).toLocaleTimeString('es-CO', {
                                                                    hour: '2-digit',
                                                                    minute: '2-digit'
                                                                })}
                                                            </small>
                                                        </div>
                                                    </td>
                                                    <td>
                                                        <div className="service-cell">
                                                            {cita.servicios && cita.servicios.length > 0
                                                                ? cita.servicios.map((s: any) => s.nombre).join(', ')
                                                                : <span className="text-muted">Sin servicio</span>}
                                                        </div>
                                                    </td>
                                                    <td className="text-center">
                                                        <Badge
                                                            bg={
                                                                cita.estado === 'Asistio' ? 'success' :
                                                                cita.estado === 'Cancelada' ? 'danger' :
                                                                cita.estado === 'No Asistio' ? 'warning' :
                                                                cita.estado === 'Confirmada' ? 'info' :
                                                                'secondary'
                                                            }
                                                            className="status-badge px-3 py-2"
                                                        >
                                                            {t(cita.estado) || cita.estado}
                                                        </Badge>
                                                    </td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan={3} className="text-center py-5">
                                                    <div className="text-muted">
                                                        <div className="mb-2" style={{ fontSize: '2rem' }}>📅</div>
                                                        <p className="mb-0">No hay citas registradas</p>
                                                    </div>
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </Table>
                            </div>
                        </Card>
                    </div>
                )}
            </Modal.Body>
            <Modal.Footer className="border-0 pt-0">
                <Button variant="light" onClick={onHide} className="px-4 py-2 btn-close-modal">
                    {t('close') || 'Cerrar'}
                </Button>
            </Modal.Footer>
        </Modal>
    );
};

export default ClientHistoryModal;
