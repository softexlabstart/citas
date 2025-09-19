import React, { useState, useEffect } from 'react';
import { Form, Button, Spinner, Alert, Modal, ListGroup } from 'react-bootstrap';
import { toast } from 'react-toastify';
import { useTranslation } from 'react-i18next';
import { getDisponibilidad, addAppointment, getNextAvailableSlots, NextAvailableSlot } from '../api';
import { CreateAppointmentPayload } from '../api';
import { useApi } from '../hooks/useApi';
import { useAppointmentForm } from '../hooks/useAppointmentForm';
import { useAuth } from '../hooks/useAuth';

interface NewAppointmentFormProps {
  onAppointmentAdded: () => void;
  prefillData?: Partial<CreateAppointmentPayload> & { recurso_id: number, servicios_ids?: number[] };
}

const NewAppointmentForm: React.FC<NewAppointmentFormProps> = ({ onAppointmentAdded, prefillData }) => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const {
    sedes,
    servicios,
    recursos,
    selectedSede,
    selectedRecurso,
    loadingSedes,
    loadingServicios,
    loadingRecursos,
    error: formDependencyError,
    setSelectedSede,
    setSelectedRecurso,
  } = useAppointmentForm();

  const [selectedServicios, setSelectedServicios] = useState<string[]>([]);

  const { data: availability, loading: slotsLoading, request: fetchAvailableSlots, error: availabilityError } = useApi<{ disponibilidad: any[] }, [string, number, string, string[]]>(getDisponibilidad);
  const { loading: isSubmitting, request: submitAppointment, error: submitError } = useApi(addAppointment);
  const { data: nextAvailable, loading: nextAvailableLoading, request: fetchNextAvailable, error: nextAvailableError } = useApi<NextAvailableSlot[], [string[], string]>(getNextAvailableSlots);

  const [date, setDate] = useState('');
  const [selectedSlot, setSelectedSlot] = useState('');
  const [showNextAvailableModal, setShowNextAvailableModal] = useState(false);

  useEffect(() => {
    if (prefillData) {
      setSelectedSede(String(prefillData.sede_id));
      // The useEffect in useAppointmentForm will fetch servicios and recursos.
      // We need to wait for them to be loaded before setting the other fields.
    }
  }, [prefillData, setSelectedSede]);

  useEffect(() => {
    // This effect runs when the prefill data is available AND the dependent dropdowns have been loaded.
    if (prefillData && servicios.length > 0 && recursos.length > 0) {
      if (prefillData.servicios_ids) {
        setSelectedServicios(prefillData.servicios_ids.map(String));
      }
      setSelectedRecurso(String(prefillData.recurso_id));
      setDate(prefillData.fecha?.split('T')[0] || '');
      setSelectedSlot(prefillData.fecha || '');
    }
  }, [prefillData, servicios, recursos, setSelectedRecurso]);

  const availableSlots = availability?.disponibilidad.filter(slot => slot.status === 'disponible') || [];

  useEffect(() => {
    if (date && selectedRecurso && selectedSede && selectedServicios.length > 0) {
      fetchAvailableSlots(date, parseInt(selectedRecurso, 10), selectedSede, selectedServicios);
    }
  }, [date, selectedRecurso, selectedSede, selectedServicios, fetchAvailableSlots]);

  const handleFindNextAvailable = () => {
    if (selectedServicios.length > 0 && selectedSede) {
      fetchNextAvailable(selectedServicios, selectedSede);
      setShowNextAvailableModal(true);
    }
  };

  const handleServiceChange = (serviceId: string) => {
    setSelectedServicios(prev =>
      prev.includes(serviceId)
        ? prev.filter(id => id !== serviceId)
        : [...prev, serviceId]
    );
  };

  const handleSelectNextAvailable = (slot: NextAvailableSlot) => {
    setDate(slot.start.split('T')[0]);
    setSelectedRecurso(String(slot.recurso.id));
    setSelectedSlot(slot.start);
    setShowNextAvailableModal(false);
  };

  const resetForm = () => {
    setDate('');
    setSelectedSede('');
    setSelectedServicios([]);
    setSelectedRecurso('');
    setSelectedSlot('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      toast.error(t('you_must_be_logged_in'));
      return;
    }
    const newAppointment = {
      nombre: user.username,
      fecha: selectedSlot,
      servicios_ids: selectedServicios.map(id => parseInt(id, 10)),
      colaboradores_ids: [parseInt(selectedRecurso)],
      sede_id: parseInt(selectedSede),
      estado: 'Pendiente' as const,
    };

    const { success, error } = await submitAppointment(newAppointment);

    if (success) {
      toast.success(t('appointment_added_successfully'));
      resetForm();
      onAppointmentAdded();
    } else {
      const errorMessages = Object.values(error || {}).flat().join(' ');
      toast.error(errorMessages || t('error_adding_appointment'));
    }
  };

  if (loadingSedes) {
    return <Spinner animation="border" />;
  }

  return (
    <>
      <Form onSubmit={handleSubmit}>
        <h3>{t('schedule_new_appointment')}</h3>
        {(formDependencyError || availabilityError || submitError || nextAvailableError) && (
          <Alert variant="danger">{t('error_processing_request')}</Alert>
        )}

        <Form.Group className="mb-3">
          <Form.Label>{t('sede_label')}</Form.Label>
          <Form.Control as="select" value={selectedSede} onChange={(e) => setSelectedSede(e.target.value)} required>
            <option value="">{t('select_sede')}</option>
            {sedes.map((sede) => (
              <option key={sede.id} value={sede.id}>{sede.nombre}</option>
            ))}
          </Form.Control>
        </Form.Group>

        <Form.Group className="mb-3">
          <Form.Label>{t('service_label')}</Form.Label>
          {loadingServicios && <Spinner animation="border" size="sm" />}
          {!selectedSede || loadingServicios ? (
            <p>{t('select_sede_first')}</p>
          ) : (
            servicios.map((service) => (
              <Form.Check
                type="checkbox"
                key={service.id}
                id={`service-${service.id}`}
                label={service.nombre}
                checked={selectedServicios.includes(String(service.id))}
                onChange={() => handleServiceChange(String(service.id))}
              />
            ))
          )}
        </Form.Group>

        <Form.Group className="mb-3">
          <Form.Label>{t('resource_label')}</Form.Label>
          {loadingRecursos && <Spinner animation="border" size="sm" />}
          <Form.Control as="select" value={selectedRecurso} onChange={(e) => setSelectedRecurso(e.target.value)} required disabled={!selectedSede || loadingRecursos}>
            <option value="">{t('select_resource')}</option>
            {recursos.map((resource) => (
              <option key={resource.id} value={resource.id}>{resource.nombre}</option>
            ))}
          </Form.Control>
        </Form.Group>

        <Form.Group className="mb-3">
          <Form.Label>{t('date_label')}</Form.Label>
          <Form.Control type="date" value={date} min={new Date().toISOString().split('T')[0]} onChange={(e) => { setDate(e.target.value); setSelectedSlot(''); }} required disabled={!selectedSede || selectedServicios.length === 0 || !selectedRecurso} />
        </Form.Group>

        <Button variant="info" onClick={handleFindNextAvailable} disabled={selectedServicios.length === 0 || !selectedSede || nextAvailableLoading}>
          {nextAvailableLoading ? t('searching') : t('find_next_available')}
        </Button>

        {date && selectedRecurso && (
          <Form.Group className="mb-3">
            <Form.Label>{t('available_time')}</Form.Label>
            {slotsLoading && <Spinner animation="border" size="sm" />}
            {!slotsLoading && availableSlots.length > 0 ? (
              <Form.Control as="select" value={selectedSlot} onChange={(e) => setSelectedSlot(e.target.value)} required>
                <option value="">{t('select_time')}</option>
                {availableSlots.map((slot, index) => (
                  <option key={index} value={slot.start}>{new Date(slot.start).toLocaleTimeString()}</option>
                ))}
              </Form.Control>
            ) : (
              !slotsLoading && <p className="text-muted">{t('no_available_slots')}</p>
            )}
          </Form.Group>
        )}

        <Button variant="primary" type="submit" disabled={!selectedSlot || isSubmitting} className="mt-3">
          {isSubmitting ? <><Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" /> {t('scheduling')}</> : t('schedule_appointment')}
        </Button>
      </Form>

      <Modal show={showNextAvailableModal} onHide={() => setShowNextAvailableModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>{t('next_available_slots')}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {nextAvailableLoading && <Spinner animation="border" />}
          {nextAvailableError && <Alert variant="danger">{t('error_finding_slots')}</Alert>}
          {nextAvailable && nextAvailable.length > 0 ? (
            <ListGroup>
              {nextAvailable.map((slot, index) => (
                <ListGroup.Item key={index} action onClick={() => handleSelectNextAvailable(slot)}>
                  {new Date(slot.start).toLocaleString()} - {slot.recurso.nombre}
                </ListGroup.Item>
              ))}
            </ListGroup>
          ) : (
            !nextAvailableLoading && <p>{t('no_upcoming_availability')}</p>
          )}
        </Modal.Body>
      </Modal>
    </>
  );
};

export default NewAppointmentForm;