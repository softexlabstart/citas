import React, { useState } from 'react';
import { Row, Col, Form, Button, Card, Spinner, Alert, Table } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import { useApi } from '../hooks/useApi';
import { getSedeSummaryReport } from '../api';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

interface SedeReportItem {
    sede_id: number;
    sede_nombre: string;
    total_citas: number;
    ingresos: number;
    estados: { [key: string]: number };
}

interface SedeReportData {
    reporte_por_sede: SedeReportItem[];
    ingresos_totales: number;
    resumen_servicios: any[];
    resumen_recursos: any[];
}

const SedeReport: React.FC = () => {
    const { t } = useTranslation();

    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    const { data: reportData, loading, error, request: fetchReport } = useApi<SedeReportData, [string, string]>(getSedeSummaryReport);

    const handleGenerateReport = () => {
        if (!startDate || !endDate) {
            toast.warn(t('select_start_and_end_date'));
            return;
        }
        fetchReport(startDate, endDate);
    };

    const generateChartData = () => {
        if (!reportData?.reporte_por_sede) return null;

        const labels = reportData.reporte_por_sede.map(item => item.sede_nombre);
        const totalCitasData = reportData.reporte_por_sede.map(item => item.total_citas);
        const ingresosData = reportData.reporte_por_sede.map(item => item.ingresos);

        return {
            labels,
            datasets: [
                {
                    label: t('total_appointments'),
                    data: totalCitasData,
                    backgroundColor: 'rgba(54, 162, 235, 0.6)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1,
                },
                {
                    label: t('revenue'),
                    data: ingresosData,
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1,
                },
            ],
        };
    };
    
    const chartOptions = {
        responsive: true,
        plugins: {
            legend: {
                position: 'top' as const,
            },
            title: {
                display: true,
                text: t('appointments_and_revenue_by_sede'),
            },
        },
    };

    return (
        <Card className="p-4 rounded shadow-sm">
            <Card.Body>
                <Form>
                    <Row>
                        <Col md={6}>
                            <Form.Group className="mb-3">
                                <Form.Label>{t('start_date')}</Form.Label>
                                <Form.Control type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} required />
                            </Form.Group>
                        </Col>
                        <Col md={6}>
                            <Form.Group className="mb-3">
                                <Form.Label>{t('end_date')}</Form.Label>
                                <Form.Control type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} required />
                            </Form.Group>
                        </Col>
                    </Row>
                    <div className="mt-2 d-flex justify-content-end">
                        <Button variant="primary" onClick={handleGenerateReport} disabled={loading || !startDate || !endDate}>
                            {loading ? <Spinner size="sm" /> : t('generate_report')}
                        </Button>
                    </div>
                </Form>

                {error && <Alert variant="danger" className="mt-4">{t(error) || error}</Alert>}

                {reportData && !loading && (
                    <div className="mt-4">
                        <Row>
                            <Col>
                                <h4 className="mb-3">{t('report_results')}</h4>
                            </Col>
                            <Col>
                                <Alert variant="success" className="text-center">
                                    <h5>{t('total_revenue')}: <strong>${(reportData.ingresos_totales || 0).toFixed(2)}</strong></h5>
                                </Alert>
                            </Col>
                        </Row>
                        <div style={{ position: 'relative', height: '400px', marginBottom: '2rem' }}>
                            <Bar options={chartOptions} data={generateChartData()!} />
                        </div>
                        <h5 className="mt-5">{t('detailed_data')}</h5>
                        <Table striped bordered hover responsive className="mt-3">
                            <thead><tr><th>{t('sede_label')}</th><th>{t('total_appointments')}</th><th>{t('attended')}</th><th>{t('revenue')}</th></tr></thead>
                            <tbody>{reportData.reporte_por_sede.map(item => (<tr key={item.sede_id}><td>{item.sede_nombre}</td><td>{item.total_citas}</td><td>{item.estados.Asistio || 0}</td><td>${(item.ingresos || 0).toFixed(2)}</td></tr>))}</tbody>
                        </Table>

                        <Row className="mt-5">
                            <Col md={6}>
                                <h5>{t('services_summary')}</h5>
                                <Table striped bordered hover responsive size="sm">
                                    <thead><tr><th>{t('service')}</th><th>{t('count')}</th></tr></thead>
                                    <tbody>{reportData.resumen_servicios.map((item, index) => (<tr key={index}><td>{item.servicio__nombre}</td><td>{item.count}</td></tr>))}</tbody>
                                </Table>
                            </Col>
                            <Col md={6}>
                                <h5>{t('resources_summary')}</h5>
                                <Table striped bordered hover responsive size="sm">
                                    <thead><tr><th>{t('resource_label')}</th><th>{t('count')}</th></tr></thead>
                                    <tbody>{reportData.resumen_recursos.map((item, index) => (<tr key={index}><td>{item.colaboradores__nombre}</td><td>{item.count}</td></tr>))}</tbody>
                                </Table>
                            </Col>
                        </Row>
                    </div>
                )}
            </Card.Body>
        </Card>
    );
};

export default SedeReport;