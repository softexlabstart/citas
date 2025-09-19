import React from 'react';
import { Modal } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import NewAppointmentForm from './NewAppointmentForm';
import { CreateAppointmentPayload } from '../api';

interface NewAppointmentModalProps {
    show: boolean;
    onHide: () => void;
    onAppointmentAdded: () => void;
    prefillData?: Partial<CreateAppointmentPayload> & { recurso_id: number, servicios_ids: number[] };
}

const NewAppointmentModal: React.FC<NewAppointmentModalProps> = ({ show, onHide, onAppointmentAdded, prefillData }) => {
    const { t } = useTranslation();

    const handleFormSuccess = () => {
        onAppointmentAdded();
        onHide(); // Close the modal after successful submission
    };

    return (
        <Modal show={show} onHide={onHide} size="lg" centered>
            <Modal.Header closeButton>
                <Modal.Title>{t('schedule_new_appointment')}</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                <NewAppointmentForm onAppointmentAdded={handleFormSuccess} prefillData={prefillData} />
            </Modal.Body>
        </Modal>
    );
};

export default NewAppointmentModal;