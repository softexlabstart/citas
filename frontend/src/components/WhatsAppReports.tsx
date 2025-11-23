import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Table, Badge, Spinner, Alert, Form } from 'react-bootstrap';
import { Chart as ChartJS, ArcElement, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, LineElement, PointElement } from 'chart.js';
import { Pie, Bar, Line } from 'react-chartjs-2';
import { getWhatsAppReportsSummary, getWhatsAppRecentMessages, getWhatsAppDeliveryPerformance } from '../api';

// Registrar componentes de Chart.js
ChartJS.register(ArcElement, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, LineElement, PointElement);

const WhatsAppReports: React.FC = () => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [days, setDays] = useState(30);
    
    // Estados para datos
    const [summary, setSummary] = useState<any>(null);
    const [recentMessages, setRecentMessages] = useState<any[]>([]);
    const [performance, setPerformance] = useState<any[]>([]);

    const fetchData = async () => {
        setLoading(true);
        setError(null);

        try {
            // Fetch summary
            const summaryRes = await getWhatsAppReportsSummary(days);
            setSummary(summaryRes.data);

            // Fetch recent messages
            const messagesRes = await getWhatsAppRecentMessages(50);
            setRecentMessages(messagesRes.data.messages);

            // Fetch performance
            const perfRes = await getWhatsAppDeliveryPerformance(days);
            setPerformance(perfRes.data.performance);

        } catch (err: any) {
            console.error('Error fetching WhatsApp reports:', err);
            setError('Error al cargar los reportes de WhatsApp');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [days]);

    const getStatusBadge = (status: string) => {
        const statusConfig: Record<string, { variant: string; label: string }> = {
            'pending': { variant: 'secondary', label: 'Pendiente' },
            'sent': { variant: 'info', label: 'Enviado' },
            'delivered': { variant: 'success', label: 'Entregado' },
            'failed': { variant: 'danger', label: 'Fallido' },
            'read': { variant: 'primary', label: 'Leído' }
        };
        
        const config = statusConfig[status] || { variant: 'secondary', label: status };
        return <Badge bg={config.variant}>{config.label}</Badge>;
    };

    const getMessageTypeLabel = (type: string) => {
        const types: Record<string, string> = {
            'confirmation': 'Confirmación',
            'reminder_24h': 'Recordatorio 24h',
            'reminder_1h': 'Recordatorio 1h',
            'cancellation': 'Cancelación'
        };
        return types[type] || type;
    };

    if (loading) {
        return (
            <Container className="mt-5 text-center">
                <Spinner animation="border" />
                <p className="mt-3">Cargando reportes...</p>
            </Container>
        );
    }

    if (error) {
        return (
            <Container className="mt-5">
                <Alert variant="danger">{error}</Alert>
            </Container>
        );
    }

    // Datos para gráfico de pastel (por estado)
    const statusPieData = {
        labels: Object.keys(summary?.by_status || {}).map(s => {
            const labels: Record<string, string> = {
                'pending': 'Pendiente',
                'sent': 'Enviado',
                'delivered': 'Entregado',
                'failed': 'Fallido'
            };
            return labels[s] || s;
        }),
        datasets: [{
            data: Object.values(summary?.by_status || {}),
            backgroundColor: [
                '#6c757d', // pending
                '#17a2b8', // sent
                '#28a745', // delivered
                '#dc3545'  // failed
            ]
        }]
    };

    // Datos para gráfico de barras (por tipo)
    const typeBarData = {
        labels: Object.keys(summary?.by_type || {}).map(t => getMessageTypeLabel(t)),
        datasets: [{
            label: 'Mensajes',
            data: Object.values(summary?.by_type || {}),
            backgroundColor: '#007bff'
        }]
    };

    // Datos para gráfico de línea (tendencia diaria)
    const dailyLineData = {
        labels: summary?.daily_stats?.map((d: any) => new Date(d.date).toLocaleDateString('es-CO', { month: 'short', day: 'numeric' })) || [],
        datasets: [
            {
                label: 'Entregados',
                data: summary?.daily_stats?.map((d: any) => d.delivered) || [],
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                tension: 0.4
            },
            {
                label: 'Fallidos',
                data: summary?.daily_stats?.map((d: any) => d.failed) || [],
                borderColor: '#dc3545',
                backgroundColor: 'rgba(220, 53, 69, 0.1)',
                tension: 0.4
            }
        ]
    };

    return (
        <Container className="mt-4">
            <Row className="mb-4">
                <Col>
                    <h2>📊 Reportes de WhatsApp</h2>
                    <p className="text-muted">Organización: {summary?.organization}</p>
                </Col>
                <Col md="auto">
                    <Form.Group>
                        <Form.Label>Período</Form.Label>
                        <Form.Select value={days} onChange={(e) => setDays(Number(e.target.value))}>
                            <option value="7">Últimos 7 días</option>
                            <option value="30">Últimos 30 días</option>
                            <option value="60">Últimos 60 días</option>
                            <option value="90">Últimos 90 días</option>
                        </Form.Select>
                    </Form.Group>
                </Col>
            </Row>

            {/* Tarjetas de resumen */}
            <Row className="mb-4">
                <Col md={3}>
                    <Card className="text-center">
                        <Card.Body>
                            <h6 className="text-muted">Total Mensajes</h6>
                            <h2>{summary?.total_messages || 0}</h2>
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={3}>
                    <Card className="text-center border-success">
                        <Card.Body>
                            <h6 className="text-muted">Tasa de Entrega</h6>
                            <h2 className="text-success">{summary?.delivery_rate || 0}%</h2>
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={3}>
                    <Card className="text-center border-danger">
                        <Card.Body>
                            <h6 className="text-muted">Tasa de Fallo</h6>
                            <h2 className="text-danger">{summary?.failed_rate || 0}%</h2>
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={3}>
                    <Card className="text-center">
                        <Card.Body>
                            <h6 className="text-muted">Período</h6>
                            <h2>{summary?.period_days || 0} días</h2>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>

            {/* Gráficos */}
            <Row className="mb-4">
                <Col md={4}>
                    <Card>
                        <Card.Header>Distribución por Estado</Card.Header>
                        <Card.Body>
                            <Pie data={statusPieData} />
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={8}>
                    <Card>
                        <Card.Header>Tendencia Diaria (Últimos 7 días)</Card.Header>
                        <Card.Body>
                            <Line data={dailyLineData} options={{ responsive: true, maintainAspectRatio: true }} />
                        </Card.Body>
                    </Card>
                </Col>
            </Row>

            <Row className="mb-4">
                <Col md={6}>
                    <Card>
                        <Card.Header>Mensajes por Tipo</Card.Header>
                        <Card.Body>
                            <Bar data={typeBarData} options={{ responsive: true }} />
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={6}>
                    <Card>
                        <Card.Header>Rendimiento por Tipo</Card.Header>
                        <Card.Body>
                            <Table striped hover size="sm">
                                <thead>
                                    <tr>
                                        <th>Tipo</th>
                                        <th>Total</th>
                                        <th>Entrega %</th>
                                        <th>Fallo %</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {performance.map((perf: any, idx: number) => (
                                        <tr key={idx}>
                                            <td>{perf.label}</td>
                                            <td>{perf.total}</td>
                                            <td className="text-success">{perf.delivery_rate}%</td>
                                            <td className="text-danger">{perf.failure_rate}%</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </Table>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>

            {/* Mensajes recientes */}
            <Row>
                <Col>
                    <Card>
                        <Card.Header>Mensajes Recientes</Card.Header>
                        <Card.Body>
                            <Table striped hover responsive>
                                <thead>
                                    <tr>
                                        <th>Fecha</th>
                                        <th>Tipo</th>
                                        <th>Cliente</th>
                                        <th>Teléfono</th>
                                        <th>Estado</th>
                                        <th>Cita ID</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {recentMessages.map((msg: any) => (
                                        <tr key={msg.id}>
                                            <td>{new Date(msg.created_at).toLocaleString('es-CO')}</td>
                                            <td>{getMessageTypeLabel(msg.message_type)}</td>
                                            <td>{msg.recipient_name}</td>
                                            <td className="text-muted">{msg.recipient_phone}</td>
                                            <td>{getStatusBadge(msg.status)}</td>
                                            <td>
                                                {msg.cita_id && (
                                                    <a href={`#/appointments?cita=${msg.cita_id}`}>#{msg.cita_id}</a>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </Table>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </Container>
    );
};

export default WhatsAppReports;
