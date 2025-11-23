import React, { useState, useEffect } from 'react';
import { Form, Button, Spinner, Alert, Modal, ListGroup } from 'react-bootstrap';
import { toast } from 'react-toastify';
import { useTranslation } from 'react-i18next';
import { getDisponibilidad, addAppointment, getNextAvailableSlots, NextAvailableSlot, getClients } from '../api';
import { CreateAppointmentPayload } from '../api';
import { useApi } from '../hooks/useApi';
import { useAppointmentForm } from '../hooks/useAppointmentForm';
import { useAuth } from '../hooks/useAuth';
import MultiSelectDropdown from './MultiSelectDropdown';
import { Client } from '../interfaces/Client';

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
  const [selectedClientId, setSelectedClientId] = useState<string>('');
  const [isColaboradorOrAdmin, setIsColaboradorOrAdmin] = useState(false);
  const [emailCliente, setEmailCliente] = useState<string>('');
  const [telefonoCliente, setTelefonoCliente] = useState<string>('');

  const { data: availability, loading: slotsLoading, request: fetchAvailableSlots, error: availabilityError } = useApi<{ disponibilidad: any[] }, [string, number, string, string[]]>(getDisponibilidad);
  const { loading: isSubmitting, request: submitAppointment, error: submitError } = useApi(addAppointment);
  const { data: nextAvailable, loading: nextAvailableLoading, request: fetchNextAvailable, error: nextAvailableError } = useApi<NextAvailableSlot[], [string[], string]>(getNextAvailableSlots);
  const { data: clients, loading: loadingClients, request: fetchClients } = useApi<Client[], []>(getClients);

  const [date, setDate] = useState('');
  const [selectedSlot, setSelectedSlot] = useState('');
  const [showNextAvailableModal, setShowNextAvailableModal] = useState(false);
  const [searchDays, setSearchDays] = useState(90);

  useEffect(() => {
    // NUEVO SISTEMA DE ROLES: Verificar si el usuario es colaborador o admin
    if (user) {
      const isAdmin = user.is_staff || user.is_superuser;
      const isSedeAdmin = user.perfil?.sedes_administradas?.length > 0;
      const isColaborador = user.perfil?.role === 'colaborador';
      // Un usuario tiene permisos especiales si es admin, sede admin, o colaborador
      const hasSpecialRole = isAdmin || isSedeAdmin || isColaborador;

      if (hasSpecialRole) {
        setIsColaboradorOrAdmin(true);
        fetchClients(); // Cargar clientes si es colaborador/admin
      }
    }
  }, [user, fetchClients]);

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

  const handleFindNextAvailable = (days: number = searchDays) => {
    if (selectedServicios.length > 0 && selectedSede) {
      fetchNextAvailable(selectedServicios, selectedSede, days, 10);
      setShowNextAvailableModal(true);
    }
  };

  const handleExtendSearch = () => {
    const newDays = searchDays + 60; // Extender 60 días más
    setSearchDays(newDays);
    handleFindNextAvailable(newDays);
  };

  const handleServiciosChange = (selected: string[]) => {
    setSelectedServicios(selected);
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
    setSelectedClientId('');
    setEmailCliente('');
    setTelefonoCliente('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      toast.error(t('you_must_be_logged_in'));
      return;
    }

    // Construir el payload base
    const newAppointment: any = {
      nombre: user.username,
      fecha: selectedSlot,
      servicios_ids: selectedServicios.map(id => parseInt(id, 10)),
      colaboradores_ids: [parseInt(selectedRecurso)],
      sede_id: parseInt(selectedSede),
      estado: 'Pendiente' as const,
    };

    // Si es colaborador/admin y seleccionó un cliente, agregar user_id y datos del cliente
    if (isColaboradorOrAdmin && selectedClientId) {
      newAppointment.user_id = parseInt(selectedClientId, 10);
      // Actualizar el nombre y datos de contacto con el del cliente seleccionado
      const selectedClient = clients?.find(c => c.id === parseInt(selectedClientId, 10));
      if (selectedClient) {
        newAppointment.nombre = selectedClient.username;
        newAppointment.email_cliente = selectedClient.email;
        newAppointment.telefono_cliente = selectedClient.telefono;
      }
    } else {
      // Si NO es colaborador/admin, usar los datos ingresados en el formulario
      // O si es colaborador/admin pero NO seleccionó cliente, usar los datos del usuario actual
      newAppointment.email_cliente = emailCliente || user.email;
      newAppointment.telefono_cliente = telefonoCliente || user.perfil?.telefono || '';
    }

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

        {/* Campos de contacto - Solo para usuarios regulares o colaboradores sin cliente seleccionado */}
        {(!isColaboradorOrAdmin || !selectedClientId) && (
          <>
            <Form.Group className="mb-3">
              <Form.Label>Email {!isColaboradorOrAdmin && <span className="text-danger">*</span>}</Form.Label>
              <Form.Control
                type="email"
                value={emailCliente}
                onChange={(e) => setEmailCliente(e.target.value)}
                placeholder={user?.email || "tu@email.com"}
                required={!isColaboradorOrAdmin}
              />
              <Form.Text className="text-muted">
                Usaremos este email para enviarte notificaciones sobre tu cita
              </Form.Text>
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Teléfono (WhatsApp) {!isColaboradorOrAdmin && <span className="text-danger">*</span>}</Form.Label>
              <Form.Control
                type="tel"
                value={telefonoCliente}
                onChange={(e) => setTelefonoCliente(e.target.value)}
                placeholder="+57 300 123 4567"
                required={!isColaboradorOrAdmin}
              />
              <Form.Text className="text-muted">
                Incluye el código de país (ej: +57 para Colombia). Recibirás recordatorios por WhatsApp.
              </Form.Text>
            </Form.Group>
          </>
        )}

        {/* Selector de cliente - Solo para colaboradores y admins */}
        {isColaboradorOrAdmin && (
          <Form.Group className="mb-3">
            <Form.Label>Cliente {selectedClientId ? '' : '(Opcional - déjalo vacío para crear cita a tu nombre)'}</Form.Label>
            {loadingClients ? (
              <Spinner animation="border" size="sm" />
            ) : (
              <Form.Control
                as="select"
                value={selectedClientId}
                onChange={(e) => setSelectedClientId(e.target.value)}
              >
                <option value="">-- Crear cita a mi nombre --</option>
                {clients?.map((client) => (
                  <option key={client.id} value={client.id}>
                    {client.full_name || client.username} ({client.email})
                  </option>
                ))}
              </Form.Control>
            )}
          </Form.Group>
        )}

        <Form.Group className="mb-3">
          {!selectedSede || loadingServicios ? (
            <>
              <Form.Label>{t('service_label')}</Form.Label>
              {loadingServicios && <Spinner animation="border" size="sm" />}
              {!selectedSede && <p className="text-muted">{t('select_sede_first')}</p>}
            </>
          ) : (
            <MultiSelectDropdown
              options={servicios.map(s => ({
                id: s.id,
                nombre: s.nombre,
                descripcion: s.descripcion
              }))}
              selected={selectedServicios}
              onChange={handleServiciosChange}
              label={t('service_label')}
              placeholder={t('select_services') || 'Seleccionar servicios'}
              isLoading={loadingServicios}
              disabled={!selectedSede}
              searchPlaceholder={t('search_services') || 'Buscar servicios...'}
              showDescriptions={true}
            />
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
            {slotsLoading ? (
              <div className="text-center p-3">
                <Spinner animation="border" size="sm" className="me-2" />
                <span className="text-muted">{t('loading_available_slots') || 'Cargando horarios disponibles...'}</span>
              </div>
            ) : availableSlots.length > 0 ? (
              <Form.Control as="select" value={selectedSlot} onChange={(e) => setSelectedSlot(e.target.value)} required>
                <option value="">{t('select_time')}</option>
                {availableSlots.map((slot, index) => (
                  <option key={index} value={slot.start}>{new Date(slot.start).toLocaleTimeString()}</option>
                ))}
              </Form.Control>
            ) : (
              <p className="text-muted">{t('no_available_slots')}</p>
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
          {nextAvailableLoading && (
            <div className="text-center p-3">
              <Spinner animation="border" />
              <p className="mt-2">Buscando disponibilidad en los próximos {searchDays} días...</p>
            </div>
          )}
          {nextAvailableError && <Alert variant="danger">{t('error_finding_slots')}</Alert>}
          {nextAvailable && nextAvailable.length > 0 ? (
            <>
              <Alert variant="info">
                Se encontraron {nextAvailable.length} horarios disponibles en los próximos {searchDays} días
              </Alert>
              <ListGroup>
                {nextAvailable.map((slot, index) => (
                  <ListGroup.Item key={index} action onClick={() => handleSelectNextAvailable(slot)}>
                    <strong>{new Date(slot.start).toLocaleDateString('es-CO', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</strong>
                    <br />
                    {new Date(slot.start).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })} - {slot.recurso.nombre}
                  </ListGroup.Item>
                ))}
              </ListGroup>
            </>
          ) : (
            !nextAvailableLoading && (
              <>
                <Alert variant="warning">
                  <strong>No hay disponibilidad en los próximos {searchDays} días</strong>
                  <p className="mb-0 mt-2">
                    {searchDays < 180 ?
                      'Puedes ampliar la búsqueda para encontrar fechas más adelante.' :
                      'Por favor, contacta directamente con la sede para coordinar una cita.'}
                  </p>
                </Alert>
                {searchDays < 180 && (
                  <div className="text-center">
                    <Button variant="primary" onClick={handleExtendSearch} disabled={nextAvailableLoading}>
                      Buscar en los próximos {searchDays + 60} días
                    </Button>
                  </div>
                )}
              </>
            )
          )}
        </Modal.Body>
      </Modal>
    </>
  );
};

export default NewAppointmentForm;