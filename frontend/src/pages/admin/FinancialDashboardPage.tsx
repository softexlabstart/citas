import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Spinner, Alert, Form, Button } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { getFinancialSummary, FinancialSummary, getRecursos } from '../../api';
import { Recurso } from '../../interfaces/Recurso';
import {
    BarChart,
    Bar,
    PieChart,
    Pie,
    Cell,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer
} from 'recharts';
import './FinancialDashboardPage.css';

const FinancialDashboardPage: React.FC = () => {
    const { t } = useTranslation();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [data, setData] = useState<FinancialSummary | null>(null);

    // Date filters
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    // Colaborador filter
    const [colaboradores, setColaboradores] = useState<Recurso[]>([]);
    const [selectedColaborador, setSelectedColaborador] = useState<string>('');

    // Initialize default dates (last 30 days) and fetch data
    useEffect(() => {
        const loadInitialData = async () => {
            // Cargar colaboradores
            try {
                const response = await getRecursos();
                setColaboradores(response.data);
            } catch (err) {
                console.error('Error loading colaboradores:', err);
            }

            // Configurar fechas y cargar datos financieros
            const today = new Date();
            const thirtyDaysAgo = new Date(today);
            thirtyDaysAgo.setDate(today.getDate() - 30);

            const end = today.toISOString().split('T')[0];
            const start = thirtyDaysAgo.toISOString().split('T')[0];

            setEndDate(end);
            setStartDate(start);

            // Fetch data immediately with the calculated dates
            fetchDataWithDates(start, end, '');
        };

        loadInitialData();
    }, []);

    const fetchDataWithDates = async (start: string, end: string, colaboradorId: string) => {
        try {
            setLoading(true);
            setError(null);
            const response = await getFinancialSummary(start, end, colaboradorId || undefined);
            setData(response.data);
        } catch (err: any) {
            console.error('Error fetching financial summary:', err);
            if (err.response?.status === 403) {
                setError(t('no_permission_view_financial_data') || 'No tienes permisos para ver esta información.');
            } else {
                setError(t('error_loading_financial_summary') || 'Error al cargar el resumen financiero. Por favor, intenta de nuevo.');
            }
        } finally {
            setLoading(false);
        }
    };

    const fetchData = async () => {
        await fetchDataWithDates(startDate, endDate, selectedColaborador);
    };

    const handleGenerateReport = (e: React.FormEvent) => {
        e.preventDefault();
        if (startDate && endDate) {
            fetchData();
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

    // Colors for charts
    const COLORS = ['#198754', '#0dcaf0', '#ffc107', '#dc3545', '#6c757d'];
    const STATE_COLORS: Record<string, string> = {
        'Asistio': '#198754',
        'Pendiente': '#ffc107',
        'Confirmada': '#0dcaf0',
        'No Asistio': '#dc3545',
        'Cancelada': '#6c757d'
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
                <Button variant="primary" onClick={fetchData}>
                    {t('retry') || 'Reintentar'}
                </Button>
            </Container>
        );
    }

    if (!data) return null;

    // Prepare data for charts
    const pieChartData = data.citas_por_estado.map(item => ({
        name: item.estado,
        value: item.cantidad,
        porcentaje: item.porcentaje
    }));

    const barChartData = data.ingresos_por_servicio.map(item => ({
        name: item.servicio,
        ingresos: item.total_ingresos,
        citas: item.cantidad_citas
    }));

    // Custom label for pie chart
    const renderCustomizedLabel = (entry: any) => {
        return `${entry.porcentaje}%`;
    };

    return (
        <Container fluid className="financial-dashboard-page py-4">
            {/* Header */}
            <div className="d-flex justify-content-between align-items-center mb-4">
                <h2 className="mb-0 fw-bold">
                    📊 {t('financial_dashboard') || 'Dashboard Financiero'}
                </h2>
            </div>

            {/* Date Filters */}
            <Card className="mb-4 border-0 shadow-sm">
                <Card.Body>
                    <h5 className="mb-3 fw-semibold">
                        📅 {t('date_filters') || 'Filtros de Fecha'}
                    </h5>
                    <Form onSubmit={handleGenerateReport}>
                        <Row className="align-items-end mb-3">
                            <Col md={3}>
                                <Form.Group>
                                    <Form.Label className="fw-semibold">
                                        {t('start_date') || 'Fecha Inicio'}
                                    </Form.Label>
                                    <Form.Control
                                        type="date"
                                        value={startDate}
                                        onChange={(e) => setStartDate(e.target.value)}
                                        required
                                    />
                                </Form.Group>
                            </Col>
                            <Col md={3}>
                                <Form.Group>
                                    <Form.Label className="fw-semibold">
                                        {t('end_date') || 'Fecha Fin'}
                                    </Form.Label>
                                    <Form.Control
                                        type="date"
                                        value={endDate}
                                        onChange={(e) => setEndDate(e.target.value)}
                                        required
                                    />
                                </Form.Group>
                            </Col>
                            <Col md={3}>
                                <Form.Group>
                                    <Form.Label className="fw-semibold">
                                        {t('filter_by_resource') || 'Filtrar por Colaborador'}
                                    </Form.Label>
                                    <Form.Select
                                        value={selectedColaborador}
                                        onChange={(e) => setSelectedColaborador(e.target.value)}
                                    >
                                        <option value="">
                                            {t('all_resources') || 'Todos los colaboradores'}
                                        </option>
                                        {colaboradores.map((colaborador) => (
                                            <option key={colaborador.id} value={colaborador.id}>
                                                {colaborador.nombre}
                                            </option>
                                        ))}
                                    </Form.Select>
                                </Form.Group>
                            </Col>
                            <Col md={3}>
                                <Button
                                    variant="primary"
                                    type="submit"
                                    className="w-100 btn-generate-report"
                                >
                                    📈 {t('generate_report') || 'Generar Reporte'}
                                </Button>
                            </Col>
                        </Row>
                        <div className="mt-2">
                            <small className="text-muted">
                                {t('period') || 'Período'}: {new Date(data.periodo.inicio).toLocaleDateString('es-CO')} - {new Date(data.periodo.fin).toLocaleDateString('es-CO')}
                            </small>
                        </div>
                    </Form>
                </Card.Body>
            </Card>

            {/* KPI Cards */}
            <Row className="g-3 mb-4">
                <Col xs={12} md={6} lg={4}>
                    <Card className="kpi-card kpi-realized border-0 shadow-sm h-100">
                        <Card.Body>
                            <div className="d-flex justify-content-between align-items-start mb-2">
                                <div className="kpi-icon realized">💵</div>
                                <div className="kpi-trend text-success">
                                    <small>
                                        {data.total_citas > 0
                                            ? Math.round((data.citas_por_estado.find(c => c.estado === 'Asistio')?.cantidad || 0) / data.total_citas * 100)
                                            : 0}% {t('conversion') || 'conversión'}
                                    </small>
                                </div>
                            </div>
                            <h6 className="kpi-label mb-2">
                                {t('realized_income') || 'Ingresos Realizados'}
                            </h6>
                            <h3 className="kpi-value mb-1">
                                {formatCurrency(data.metricas_principales.ingresos_realizados)}
                            </h3>
                            <small className="text-muted">
                                {t('from_attended_appointments') || 'De citas asistidas'}
                            </small>
                        </Card.Body>
                    </Card>
                </Col>

                <Col xs={12} md={6} lg={4}>
                    <Card className="kpi-card kpi-projected border-0 shadow-sm h-100">
                        <Card.Body>
                            <div className="d-flex justify-content-between align-items-start mb-2">
                                <div className="kpi-icon projected">💰</div>
                                <div className="kpi-trend text-info">
                                    <small>
                                        {data.citas_por_estado.find(c => c.estado === 'Pendiente')?.cantidad || 0} + {' '}
                                        {data.citas_por_estado.find(c => c.estado === 'Confirmada')?.cantidad || 0} {t('appointments') || 'citas'}
                                    </small>
                                </div>
                            </div>
                            <h6 className="kpi-label mb-2">
                                {t('projected_income') || 'Ingresos Proyectados'}
                            </h6>
                            <h3 className="kpi-value mb-1">
                                {formatCurrency(data.metricas_principales.ingresos_proyectados)}
                            </h3>
                            <small className="text-muted">
                                {t('from_pending_confirmed') || 'De citas pendientes y confirmadas'}
                            </small>
                        </Card.Body>
                    </Card>
                </Col>

                <Col xs={12} md={12} lg={4}>
                    <Card className="kpi-card kpi-lost border-0 shadow-sm h-100">
                        <Card.Body>
                            <div className="d-flex justify-content-between align-items-start mb-2">
                                <div className="kpi-icon lost">🚫</div>
                                <div className="kpi-trend text-danger">
                                    <small>
                                        {data.citas_por_estado.find(c => c.estado === 'No Asistio')?.cantidad || 0} {t('no_shows') || 'inasistencias'}
                                    </small>
                                </div>
                            </div>
                            <h6 className="kpi-label mb-2">
                                {t('lost_income') || 'Ingresos Perdidos'}
                            </h6>
                            <h3 className="kpi-value mb-1">
                                {formatCurrency(data.metricas_principales.ingresos_perdidos)}
                            </h3>
                            <small className="text-muted">
                                {t('from_no_shows') || 'Por inasistencias'}
                            </small>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>

            {/* Charts Row */}
            <Row className="mb-4">
                {/* Bar Chart - Income by Service */}
                <Col lg={7} className="mb-4">
                    <Card className="border-0 shadow-sm h-100">
                        <Card.Header className="bg-white border-0 pt-4 px-4">
                            <h5 className="mb-0 fw-semibold">
                                📊 {t('income_by_service') || 'Ingresos por Servicio'}
                            </h5>
                            <small className="text-muted">
                                {t('top_10_services') || 'Top 10 servicios más rentables'}
                            </small>
                        </Card.Header>
                        <Card.Body className="px-4 pb-4">
                            {barChartData.length > 0 ? (
                                <ResponsiveContainer width="100%" height={350}>
                                    <BarChart
                                        data={barChartData}
                                        margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
                                    >
                                        <CartesianGrid strokeDasharray="3 3" stroke="#e9ecef" />
                                        <XAxis
                                            dataKey="name"
                                            angle={-45}
                                            textAnchor="end"
                                            height={100}
                                            style={{ fontSize: '12px' }}
                                        />
                                        <YAxis
                                            tickFormatter={(value: number) => `$${(value / 1000).toFixed(0)}K`}
                                            style={{ fontSize: '12px' }}
                                        />
                                        <Tooltip
                                            formatter={(value: any) => formatCurrency(value)}
                                            labelStyle={{ color: '#1d3557' }}
                                            contentStyle={{ borderRadius: '8px', border: '1px solid #e9ecef' }}
                                        />
                                        <Legend />
                                        <Bar
                                            dataKey="ingresos"
                                            fill="#457b9d"
                                            name={t('income') || 'Ingresos'}
                                            radius={[8, 8, 0, 0]}
                                        />
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="text-center py-5 text-muted">
                                    <div className="mb-2" style={{ fontSize: '2rem' }}>📊</div>
                                    <p className="mb-0">{t('no_service_data') || 'No hay datos de servicios en este período'}</p>
                                </div>
                            )}
                        </Card.Body>
                    </Card>
                </Col>

                {/* Pie Chart - Appointments by Status */}
                <Col lg={5} className="mb-4">
                    <Card className="border-0 shadow-sm h-100">
                        <Card.Header className="bg-white border-0 pt-4 px-4">
                            <h5 className="mb-0 fw-semibold">
                                🥧 {t('appointments_by_status') || 'Citas por Estado'}
                            </h5>
                            <small className="text-muted">
                                {t('distribution_by_status') || 'Distribución por estado'}
                            </small>
                        </Card.Header>
                        <Card.Body className="px-4 pb-4">
                            {pieChartData.length > 0 && data.total_citas > 0 ? (
                                <>
                                    <ResponsiveContainer width="100%" height={300}>
                                        <PieChart>
                                            <Pie
                                                data={pieChartData}
                                                cx="50%"
                                                cy="50%"
                                                labelLine={false}
                                                label={renderCustomizedLabel}
                                                outerRadius={100}
                                                fill="#8884d8"
                                                dataKey="value"
                                            >
                                                {pieChartData.map((entry, index) => (
                                                    <Cell
                                                        key={`cell-${index}`}
                                                        fill={STATE_COLORS[entry.name] || COLORS[index % COLORS.length]}
                                                    />
                                                ))}
                                            </Pie>
                                            <Tooltip
                                                formatter={(value: any, name: string, props: any) => [
                                                    `${value} citas (${props.payload.porcentaje}%)`,
                                                    name
                                                ]}
                                                contentStyle={{ borderRadius: '8px', border: '1px solid #e9ecef' }}
                                            />
                                            <Legend
                                                verticalAlign="bottom"
                                                height={36}
                                                iconType="circle"
                                            />
                                        </PieChart>
                                    </ResponsiveContainer>
                                    <div className="mt-3 text-center">
                                        <h4 className="mb-0">{data.total_citas}</h4>
                                        <small className="text-muted">
                                            {t('total_appointments') || 'Total de Citas'}
                                        </small>
                                    </div>
                                </>
                            ) : (
                                <div className="text-center py-5 text-muted">
                                    <div className="mb-2" style={{ fontSize: '2rem' }}>📅</div>
                                    <p className="mb-0">{t('no_appointments_data') || 'No hay datos de citas en este período'}</p>
                                </div>
                            )}
                        </Card.Body>
                    </Card>
                </Col>
            </Row>

            {/* Summary Card */}
            <Card className="summary-card border-0 shadow-lg">
                <Card.Body className="p-4">
                    <Row className="align-items-center">
                        <Col md={8}>
                            <h5 className="summary-label mb-2">
                                💎 {t('total_income_summary') || 'Total de Ingresos (Realizados + Proyectados)'}
                            </h5>
                            <h1 className="summary-amount mb-1">
                                {formatCurrency(data.metricas_principales.total_ingresos)}
                            </h1>
                            <p className="summary-description mb-0">
                                {t('based_on_appointments', { count: data.total_citas }) || `Basado en ${data.total_citas} citas en el período seleccionado`}
                            </p>
                        </Col>
                        <Col md={4} className="text-center">
                            <div className="summary-stats">
                                <div className="stat-item mb-2">
                                    <div className="stat-icon">✅</div>
                                    <div>
                                        <strong>{data.citas_por_estado.find(c => c.estado === 'Asistio')?.cantidad || 0}</strong>
                                        <small className="d-block text-muted">{t('attended') || 'Asistidas'}</small>
                                    </div>
                                </div>
                                <div className="stat-item">
                                    <div className="stat-icon">⏳</div>
                                    <div>
                                        <strong>
                                            {(data.citas_por_estado.find(c => c.estado === 'Pendiente')?.cantidad || 0) +
                                             (data.citas_por_estado.find(c => c.estado === 'Confirmada')?.cantidad || 0)}
                                        </strong>
                                        <small className="d-block text-muted">{t('pending') || 'Pendientes'}</small>
                                    </div>
                                </div>
                            </div>
                        </Col>
                    </Row>
                </Card.Body>
            </Card>
        </Container>
    );
};

export default FinancialDashboardPage;
