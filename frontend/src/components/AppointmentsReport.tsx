import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Form, Button, Card, Spinner, Alert, Table } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import { useApi } from '../hooks/useApi';
import { getServicios, getRecursos, getAppointmentsReport, downloadAppointmentsReportCSV } from '../api';
import { Service } from '../interfaces/Service';
import { Recurso } from '../interfaces/Recurso';
import { statusConfig } from '../constants/appointmentStatus';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Pie } from 'react-chartjs-2';
ChartJS.register(ArcElement, Tooltip, Legend);

interface ReportData {
    [key: string]: number;
}

// Define a consistent color map for appointment statuses to ensure visual distinction in charts.
const statusColorMap: { [key: string]: string } = {
    'Pendiente': '#ffc107', // Bootstrap 'warning'
    'Confirmada': '#198754', // Bootstrap 'success'
    'Cancelada': '#dc3545', // Bootstrap 'danger'
    'Asistio': '#0dcaf0',   // Bootstrap 'info'
    'No Asistio': '#6c757d', // Bootstrap 'secondary'
};

const AppointmentsReport: React.FC = () => {
    const { t } = useTranslation();

    // Form state
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [servicioIds, setServicioIds] = useState<string[]>([]);
    const [recursoId, setRecursoId] = useState('');
    const [isExporting, setIsExporting] = useState(false);

    // API hooks
    const { data: servicios, loading: loadingServicios, request: fetchServicios } = useApi<Service[], []>(getServicios);
    const { data: recursos, loading: loadingRecursos, request: fetchRecursos } = useApi<Recurso[], []>(getRecursos);
    const { data: reportData, loading: loadingReport, error: reportError, request: fetchReport } = useApi<ReportData, [string, string, string[] | undefined, string | undefined]>(getAppointmentsReport);

    useEffect(() => {
        fetchServicios();
        fetchRecursos();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const handleGenerateReport = () => {
        if (!startDate || !endDate) {
            toast.warn(t('select_start_and_end_date'));
            return;
        }
        fetchReport(startDate, endDate, servicioIds.length > 0 ? servicioIds : undefined, recursoId || undefined);
    };

    const handleExportCSV = async () => {
        if (!startDate || !endDate) {
            toast.warn(t('select_start_and_end_date'));
            return;
        }
        setIsExporting(true);
        try {
            const response = await downloadAppointmentsReportCSV(startDate, endDate, servicioIds.length > 0 ? servicioIds : undefined, recursoId || undefined);
            const blob = new Blob([response.data], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'reporte_citas.csv';
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            toast.success(t('report_exported_successfully'));
        } catch (error) {
            toast.error(t('error_exporting_report'));
        } finally {
            setIsExporting(false);
        }
    };

    const handleServiceChange = (serviceId: string) => {
        setServicioIds(prev =>
            prev.includes(serviceId)
                ? prev.filter(id => id !== serviceId)
                : [...prev, serviceId]
        );
    };

    const generateChartData = () => {
        if (!reportData) return null;

        const labels = Object.keys(reportData).map(status => t(statusConfig[status as keyof typeof statusConfig]?.key || status.toLowerCase()));
        const data = Object.values(reportData);
        const backgroundColors = Object.keys(reportData).map(status => statusColorMap[status] || '#cccccc');

        return {
            labels,
            datasets: [
                {
                    label: t('count'),
                    data,
                    backgroundColor: backgroundColors,
                    borderColor: backgroundColors.map(color => `${color}B3`), // Add some transparency to border
                    borderWidth: 1,
                },
            ],
        };
    };

    const isLoadingFilters = loadingServicios || loadingRecursos;

    return (
        <Card className="p-4 rounded shadow-sm">
            <Card.Body>
                    <h4 className="mb-3">{t('filter_criteria')}</h4>
                    
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
                        <Row>
                            <Col md={6}>
                                <Form.Group className="mb-3">
                                    <Form.Label>{t('service')} ({t('optional')})</Form.Label>
                                    {isLoadingFilters ? (
                                        <Spinner animation="border" size="sm" />
                                    ) : (
                                        servicios?.map(s => (
                                            <Form.Check
                                                type="checkbox"
                                                key={s.id}
                                                id={`service-filter-${s.id}`}
                                                label={s.nombre}
                                                checked={servicioIds.includes(String(s.id))}
                                                onChange={() => handleServiceChange(String(s.id))}
                                            />
                                        ))
                                    )}
                                </Form.Group>
                            </Col>
                            <Col md={6}>
                                <Form.Group className="mb-3">
                                    <Form.Label>{t('resource_label')} ({t('optional')})</Form.Label>
                                    <Form.Control as="select" value={recursoId} onChange={(e) => setRecursoId(e.target.value)} disabled={isLoadingFilters}>
                                        <option value="">{t('all_resources')}</option>
                                        {recursos?.map(r => <option key={r.id} value={r.id}>{r.nombre}</option>)}
                                    </Form.Control>
                                </Form.Group>
                            </Col>
                        </Row>
                        <div className="mt-4 d-flex justify-content-end gap-2">
                            <Button variant="primary" onClick={handleGenerateReport} disabled={loadingReport || !startDate || !endDate}>
                                {loadingReport ? <Spinner size="sm" /> : t('generate_report')}
                            </Button>
                            <Button variant="outline-success" onClick={handleExportCSV} disabled={isExporting || !startDate || !endDate}>
                                {isExporting ? <Spinner size="sm" /> : t('export_to_csv')}
                            </Button>
                        </div>
                    </Form>

                    {reportError && <Alert variant="danger" className="mt-4">{t(reportError) || reportError}</Alert>}

                    {reportData && !loadingReport && (
                        <div className="mt-4">
                            <h4 className="mb-3">{t('report_results')}</h4>
                            <Row>
                                <Col md={8}>
                                    <Table striped bordered hover>
                                        <thead><tr><th>{t('status')}</th><th>{t('count')}</th></tr></thead>
                                        <tbody>
                                            {Object.entries(reportData).map(([status, count]) => (<tr key={status}><td>{t(statusConfig[status as keyof typeof statusConfig]?.key || status.toLowerCase())}</td><td>{count}</td></tr>))}
                                        </tbody>
                                    </Table>
                                </Col>
                                <Col md={4}>
                                    <div style={{ position: 'relative', height: '300px' }}>
                                        <Pie data={generateChartData()!} options={{ maintainAspectRatio: false, responsive: true }} />
                                    </div>
                                </Col>
                            </Row>
                        </div>
                    )}
                </Card.Body>
        </Card>
    );
};

export default AppointmentsReport;