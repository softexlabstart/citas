import React from 'react';
import { Container, Tabs, Tab } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import AppointmentsReport from '../components/AppointmentsReport';
import SedeReport from '../components/SedeReport';
import FinancialDashboardPage from './admin/FinancialDashboardPage';

const ReportsPage: React.FC = () => {
    const { t } = useTranslation();

    return (
        <Container fluid className="mt-4">
            <h2 className="mb-4 text-center">{t('reports')}</h2>
            <Tabs defaultActiveKey="financial" id="reports-tabs" className="mb-4" variant="pills" justify>
                <Tab eventKey="financial" title={t('financial_dashboard') || 'Dashboard Financiero'}>
                    <FinancialDashboardPage />
                </Tab>
                <Tab eventKey="appointments" title={t('appointments_report')}>
                    <AppointmentsReport />
                </Tab>
                <Tab eventKey="sedes" title={t('sede_summary_report')}>
                    <SedeReport />
                </Tab>
            </Tabs>
        </Container>
    );
};

export default ReportsPage;