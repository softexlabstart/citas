import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Spinner, Alert, Form, Button, Table, Badge } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { getFinancialSummary, FinancialSummary } from '../api';
import './FinancialDashboard.css';

const FinancialDashboard: React.FC = () => {
    const { t } = useTranslation();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [data, setData] = useState<FinancialSummary | null>(null);

    // Date filters
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    // Initialize default dates (last 30 days)
    useEffect(() => {
        const today = new Date();
        const thirtyDaysAgo = new Date(today);
        thirtyDaysAgo.setDate(today.getDate() - 30);

        setEndDate(today.toISOString().split('T')[0]);
        setStartDate(thirtyDaysAgo.toISOString().split('T')[0]);
    }, []);

    // Fetch data when dates change
    useEffect(() => {
        if (startDate && endDate) {
            fetchData();
        }
    }, [startDate, endDate]);

    const fetchData = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await getFinancialSummary(startDate, endDate);
            setData(response.data);
        } catch (err: any) {
            console.error('Error fetching financial summary:', err);
            if (err.response?.status === 403) {
                setError('No tienes permisos para ver esta información.');
            } else {
                setError('Error al cargar el resumen financiero. Por favor, intenta de nuevo.');
            }
        } finally {
            setLoading(false);
        }
    };

    const formatCurrency = (amount: number): string => {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    };

    const handleApplyFilters = (e: React.FormEvent) => {
        e.preventDefault();
        fetchData();
    };

    // Calculate percentages for visual bars
    const getPercentageWidth = (value: number, total: number): number => {
        if (total === 0) return 0;
        return (value / total) * 100;
    };

    if (loading) {
        return (
            <Container className="py-5 text-center">
                <Spinner animation="border" variant="primary" />
                <p className="mt-3">{t('loading')}...</p>
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

    if (!data) return null;

    const totalIngresos = data.metricas_principales.ingresos_realizados +
        data.metricas_principales.ingresos_proyectados;

    return (
        <Container fluid className="financial-dashboard py-4">
            <div className="d-flex justify-content-between align-items-center mb-4">
                <h2 className="mb-0 fw-bold">Dashboard Financiero</h2>
            </div>

            {/* Date Filters */}
            <Card className="mb-4 border-0 shadow-sm">
                <Card.Body>
                    <Form onSubmit={handleApplyFilters}>
                        <Row className="align-items-end">
                            <Col md={5}>
                                <Form.Group>
                                    <Form.Label className="fw-semibold">Fecha Inicio</Form.Label>
                                    <Form.Control
                                        type="date"
                                        value={startDate}
                                        onChange={(e) => setStartDate(e.target.value)}
                                        required
                                    />
                                </Form.Group>
                            </Col>
                            <Col md={5}>
                                <Form.Group>
                                    <Form.Label className="fw-semibold">Fecha Fin</Form.Label>
                                    <Form.Control
                                        type="date"
                                        value={endDate}
                                        onChange={(e) => setEndDate(e.target.value)}
                                        required
                                    />
                                </Form.Group>
                            </Col>
                            <Col md={2}>
                                <Button variant="primary" type="submit" className="w-100">
                                    Aplicar
                                </Button>
                            </Col>
                        </Row>
                    </Form>
                    <div className="mt-2">
                        <small className="text-muted">
                            Período: {new Date(data.periodo.inicio).toLocaleDateString('es-CO')} - {new Date(data.periodo.fin).toLocaleDateString('es-CO')}
                        </small>
                    </div>
                </Card.Body>
            </Card>

            {/* Main Metrics Cards */}
            <Row className="g-3 mb-4">
                <Col xs={12} md={6} lg={3}>
                    <Card className="metric-card metric-card-realized border-0 shadow-sm h-100">
                        <Card.Body>
                            <div className="metric-icon mb-2">💵</div>
                            <h6 className="metric-label mb-2">Ingresos Realizados</h6>
                            <h3 className="metric-value mb-0">
                                {formatCurrency(data.metricas_principales.ingresos_realizados)}
                            </h3>
                            <div className="progress mt-2" style={{ height: '4px' }}>
                                <div
                                    className="progress-bar bg-success"
                                    style={{
                                        width: `${getPercentageWidth(
                                            data.metricas_principales.ingresos_realizados,
                                            totalIngresos
                                        )}%`
                                    }}
                                ></div>
                            </div>
                        </Card.Body>
                    </Card>
                </Col>
                <Col xs={12} md={6} lg={3}>
                    <Card className="metric-card metric-card-projected border-0 shadow-sm h-100">
                        <Card.Body>
                            <div className="metric-icon mb-2">💰</div>
                            <h6 className="metric-label mb-2">Ingresos Proyectados</h6>
                            <h3 className="metric-value mb-0">
                                {formatCurrency(data.metricas_principales.ingresos_proyectados)}
                            </h3>
                            <div className="progress mt-2" style={{ height: '4px' }}>
                                <div
                                    className="progress-bar bg-info"
                                    style={{
                                        width: `${getPercentageWidth(
                                            data.metricas_principales.ingresos_proyectados,
                                            totalIngresos
                                        )}%`
                                    }}
                                ></div>
                            </div>
                        </Card.Body>
                    </Card>
                </Col>
                <Col xs={12} md={6} lg={3}>
                    <Card className="metric-card metric-card-lost border-0 shadow-sm h-100">
                        <Card.Body>
                            <div className="metric-icon mb-2">🚫</div>
                            <h6 className="metric-label mb-2">Ingresos Perdidos</h6>
                            <h3 className="metric-value mb-0">
                                {formatCurrency(data.metricas_principales.ingresos_perdidos)}
                            </h3>
                            <small className="text-muted">Por no asistencia</small>
                        </Card.Body>
                    </Card>
                </Col>
                <Col xs={12} md={6} lg={3}>
                    <Card className="metric-card metric-card-canceled border-0 shadow-sm h-100">
                        <Card.Body>
                            <div className="metric-icon mb-2">❌</div>
                            <h6 className="metric-label mb-2">Ingresos Cancelados</h6>
                            <h3 className="metric-value mb-0">
                                {formatCurrency(data.metricas_principales.ingresos_cancelados)}
                            </h3>
                            <small className="text-muted">Por cancelaciones</small>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>

            {/* Total Summary Card */}
            <Card className="total-card border-0 shadow-lg mb-4">
                <Card.Body className="p-4">
                    <Row className="align-items-center">
                        <Col md={8}>
                            <h5 className="total-label mb-2">Total de Ingresos (Realizados + Proyectados)</h5>
                            <h1 className="total-amount mb-1">
                                {formatCurrency(data.metricas_principales.total_ingresos)}
                            </h1>
                            <p className="total-description mb-0">
                                Basado en {data.total_citas} citas en el período seleccionado
                            </p>
                        </Col>
                        <Col md={4} className="text-center">
                            <div className="total-icon">📊</div>
                        </Col>
                    </Row>
                </Card.Body>
            </Card>

            <Row>
                {/* Appointments by Status */}
                <Col lg={6} className="mb-4">
                    <Card className="border-0 shadow-sm h-100">
                        <Card.Header className="bg-white border-0 pt-4 px-4">
                            <h5 className="mb-0 fw-semibold">📋 Citas por Estado</h5>
                        </Card.Header>
                        <Card.Body className="px-4 pb-4">
                            <div className="appointments-chart">
                                {data.citas_por_estado.map((item, index) => (
                                    <div key={index} className="appointment-status-item mb-3">
                                        <div className="d-flex justify-content-between align-items-center mb-1">
                                            <span className="fw-semibold">{item.estado}</span>
                                            <div>
                                                <Badge bg="secondary" className="me-2">{item.cantidad}</Badge>
                                                <span className="text-muted">{item.porcentaje}%</span>
                                            </div>
                                        </div>
                                        <div className="progress" style={{ height: '8px' }}>
                                            <div
                                                className={`progress-bar ${
                                                    item.estado === 'Asistio' ? 'bg-success' :
                                                    item.estado === 'Pendiente' ? 'bg-warning' :
                                                    item.estado === 'Confirmada' ? 'bg-info' :
                                                    item.estado === 'No Asistio' ? 'bg-danger' :
                                                    'bg-secondary'
                                                }`}
                                                style={{ width: `${item.porcentaje}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </Card.Body>
                    </Card>
                </Col>

                {/* Top Services by Revenue */}
                <Col lg={6} className="mb-4">
                    <Card className="border-0 shadow-sm h-100">
                        <Card.Header className="bg-white border-0 pt-4 px-4">
                            <h5 className="mb-0 fw-semibold">🎯 Top 10 Servicios por Ingresos</h5>
                        </Card.Header>
                        <Card.Body className="px-4 pb-4">
                            {data.ingresos_por_servicio.length > 0 ? (
                                <div className="table-responsive">
                                    <Table hover className="mb-0 services-table">
                                        <thead>
                                            <tr>
                                                <th>#</th>
                                                <th>Servicio</th>
                                                <th className="text-end">Citas</th>
                                                <th className="text-end">Ingresos</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {data.ingresos_por_servicio.map((item, index) => (
                                                <tr key={index}>
                                                    <td>
                                                        <div className="service-rank">{index + 1}</div>
                                                    </td>
                                                    <td className="fw-semibold">{item.servicio}</td>
                                                    <td className="text-end">
                                                        <Badge bg="primary" pill>{item.cantidad_citas}</Badge>
                                                    </td>
                                                    <td className="text-end fw-bold text-success">
                                                        {formatCurrency(item.total_ingresos)}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </Table>
                                </div>
                            ) : (
                                <div className="text-center py-5 text-muted">
                                    <div className="mb-2" style={{ fontSize: '2rem' }}>📊</div>
                                    <p className="mb-0">No hay datos de servicios en este período</p>
                                </div>
                            )}
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </Container>
    );
};

export default FinancialDashboard;
