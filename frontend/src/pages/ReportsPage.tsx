import React from 'react';
import { Container, Tabs, Tab } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import AppointmentsReport from '../components/AppointmentsReport';
import SedeReport from '../components/SedeReport';

const ReportsPage: React.FC = () => {
    const { t } = useTranslation();

    return (
        <Container className="mt-5">
            <h2 className="mb-4 text-center">{t('reports')}</h2>
            <Tabs defaultActiveKey="appointments" id="reports-tabs" className="mb-4" variant="pills" justify>
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