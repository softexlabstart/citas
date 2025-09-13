import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Table, Button, Form, Badge, Spinner, Modal, Alert, Pagination, InputGroup, Dropdown } from 'react-bootstrap';
import { toast } from 'react-toastify';
import { Appointment } from '../interfaces/Appointment';
import { getAppointments, confirmAppointment, deleteAppointment, updateAppointment, PaginatedResponse, CreateAppointmentPayload } from '../api';
import { useAuth } from '../hooks/useAuth';
import { useTranslation } from 'react-i18next';
import NewAppointmentModal from './NewAppointmentModal';
import { useApi } from '../hooks/useApi';
import { statusConfig, APPOINTMENT_STATUS } from '../constants/appointmentStatus';
import AppointmentTableSkeleton from './AppointmentTableSkeleton';
import { useDebounce } from '../hooks/useDebounce';
import { useLocation, useNavigate } from 'react-router-dom';

interface PrefillState {
    prefill: Partial<CreateAppointmentPayload> & { recurso_id: number };
}

const Appointments: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState(''); 
  const [processingId, setProcessingId] = useState<number | null>(null);
  const [showConfirmCancelModal, setShowConfirmCancelModal] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [showRescheduleModal, setShowRescheduleModal] = useState(false);
  const [showNewAppointmentModal, setShowNewAppointmentModal] = useState(false);
  const [reschedulingAppointment, setReschedulingAppointment] = useState<Appointment | null>(null);
  const [newDate, setNewDate] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearchTerm = useDebounce(searchTerm, 500); // 500ms delay
  const [currentPage, setCurrentPage] = useState(1);
  const { user } = useAuth();
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();

  const { data: paginatedData, loading, error, request: fetchAppointmentsApi } = useApi<PaginatedResponse<Appointment>, [string | undefined, number, string | undefined]>(getAppointments);
  // Hooks for mutations
  const { loading: isConfirming, request: confirmApi } = useApi(confirmAppointment);
  const { loading: isDeleting, request: deleteApi } = useApi(deleteAppointment);
  const { loading: isUpdating, request: updateApi } = useApi(updateAppointment);
  const isProcessing = isConfirming || isDeleting || isUpdating;

  useEffect(() => {
    if (user) {
      fetchAppointmentsApi(filterStatus || undefined, currentPage, debouncedSearchTerm || undefined);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, filterStatus, currentPage, debouncedSearchTerm]);

  useEffect(() => {
    const prefillState = location.state as PrefillState | null;
    if (prefillState?.prefill) {
        setShowNewAppointmentModal(true);
        // Clear the state from location so it doesn't trigger again on refresh
        navigate(location.pathname, { replace: true, state: null });
    }
  }, [location, navigate]);

  const handleConfirmAppointment = async (id: number) => {
    setProcessingId(id);
    const { success } = await confirmApi(id);
    if (success) {
      fetchAppointmentsApi(filterStatus || undefined, currentPage, debouncedSearchTerm || undefined);
      toast.success(t('appointment_confirmed_successfully'));
    } else {
      toast.error(t('error_confirming_appointment'));
    }
    setProcessingId(null);
  };

  const openConfirmCancelModal = (id: number) => {
    setDeletingId(id);
    setShowConfirmCancelModal(true);
  };

  const closeConfirmCancelModal = () => {
    setDeletingId(null);
    setShowConfirmCancelModal(false);
  };

  const handleDeleteAppointment = async () => {
    if (!deletingId) return;
    setProcessingId(deletingId);
    const { success } = await deleteApi(deletingId);
    if (success) {
      fetchAppointmentsApi(filterStatus || undefined, currentPage, debouncedSearchTerm || undefined);
      toast.success(t('appointment_cancelled_successfully'));
    } else {
      toast.error(t('error_cancelling_appointment'));
    }
    setProcessingId(null);
    closeConfirmCancelModal();
  };

  const handleRescheduleAppointment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reschedulingAppointment) return;

    setProcessingId(reschedulingAppointment.id);
    const { success } = await updateApi(reschedulingAppointment.id, { fecha: newDate });
    if (success) {
      fetchAppointmentsApi(filterStatus || undefined, currentPage, debouncedSearchTerm || undefined);
      setShowRescheduleModal(false);
      setReschedulingAppointment(null);
      toast.success(t('appointment_rescheduled_successfully'));
    } else {
      toast.error(t('error_rescheduling_appointment'));
    }
    setProcessingId(null);
  };

  const handleAppointmentAdded = () => {
    setFilterStatus(''); // Reset filter to show the new appointment
    setSearchTerm(''); // Reset search term
    if (currentPage === 1) {
      fetchAppointmentsApi(undefined, 1, undefined);
    } else {
      setCurrentPage(1);
    }
  };

  const openRescheduleModal = (appointment: Appointment) => {
    setReschedulingAppointment(appointment);
    setNewDate(appointment.fecha);
    setShowRescheduleModal(true);
  };

  const closeRescheduleModal = () => {
    setReschedulingAppointment(null);
    setShowRescheduleModal(false);
  };

  const getMinDateTime = () => {
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    return now.toISOString().slice(0, 16);
  };

  const renderPagination = () => {
    if (!paginatedData || paginatedData.count <= 10) return null;

    const totalPages = Math.ceil(paginatedData.count / 10);
    let items = [];
    // Simple pagination for now, can be extended with ellipsis for many pages
    for (let number = 1; number <= totalPages; number++) {
      items.push(
        <Pagination.Item key={number} active={number === currentPage} onClick={() => setCurrentPage(number)}>
          {number}
        </Pagination.Item>,
      );
    }

    return (
      <Pagination className="justify-content-center mt-3">
        <Pagination.Prev onClick={() => setCurrentPage(currentPage - 1)} disabled={!paginatedData.previous} />
        {items}
        <Pagination.Next onClick={() => setCurrentPage(currentPage + 1)} disabled={!paginatedData.next} />
      </Pagination>
    );
  };

  const appointments = paginatedData?.results || [];

  return (
    <Container className="mt-5 bg-white p-4 rounded shadow-sm">
      <Row>
        <Col xs={8}>
          <h2>{t('manage_appointments')}</h2>
        </Col>
        {user && !user.perfil?.is_sede_admin && !user.is_staff && (
          <Col xs={4} className="text-end">
            <Button onClick={() => setShowNewAppointmentModal(true)}>{t('schedule_new_appointment')}</Button>
          </Col>
        )}
      </Row>

          <Row className="mt-4">
            <Col> 
              <h3>{t('scheduled_appointments')}</h3>
              <Row>
                <Col md={8}>
                  <Form.Group className="mb-3">
                    <Form.Label>{t('search_by_client_name')}</Form.Label>
                    <Form.Control
                      type="text"
                      placeholder={t('enter_client_name')}
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                  </Form.Group>
                </Col>
                <Col md={4}>
                  <Form.Group className="mb-3">
                    <Form.Label>{t('filter_by_status')}</Form.Label>
                    <Form.Control
                      as="select"
                      value={filterStatus}
                      onChange={(e) => setFilterStatus(e.target.value)}
                    >
                      <option value="">{t('all')}</option>
                      <option value={APPOINTMENT_STATUS.PENDIENTE}>{t('pending')}</option>
                      <option value={APPOINTMENT_STATUS.CONFIRMADA}>{t('confirmed')}</option>
                      <option value={APPOINTMENT_STATUS.CANCELADA}>{t('cancelled')}</option>
                      <option value={APPOINTMENT_STATUS.ASISTIO}>{t('attended')}</option>
                      <option value={APPOINTMENT_STATUS.NO_ASISTIO}>{t('not_attended')}</option>
                    </Form.Control>
                  </Form.Group>
                </Col>
              </Row>
              {loading ? (
                <AppointmentTableSkeleton />
              ) : error ? (
                <Alert variant="danger">{t(error) || error}</Alert>
              ) : appointments.length > 0 ? (
                <div className="table-responsive">
                  <Table striped bordered hover>
                    <thead>
                      <tr>
                        <th>{t('id')}</th>
                        <th>{t('client_name')}</th>
                        <th>{t('date')}</th>
                        <th>{t('service')}</th>
                        <th>{t('sede_label')}</th>
                        <th>{t('status')}</th>
                        <th>{t('actions')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {appointments.map((appointment: Appointment) => {
                        const finalStateValues: string[] = [APPOINTMENT_STATUS.ASISTIO, APPOINTMENT_STATUS.CONFIRMADA, APPOINTMENT_STATUS.CANCELADA];
                        const isFinalState = finalStateValues.includes(appointment.estado);
                        return (
                          <tr key={appointment.id} className={appointment.estado === 'Confirmada' ? 'table-success' : appointment.estado === 'Cancelada' ? 'table-danger' : ''}>
                            <td>{appointment.id}</td>
                            <td>{appointment.nombre}</td>
                            <td>{new Date(appointment.fecha).toLocaleString()}</td>
                            <td>{appointment.servicio.nombre}</td>
                            <td>{appointment.sede.nombre}</td>
                            <td>
                              <Badge bg={statusConfig[appointment.estado]?.color || 'light'}>
                                {t(statusConfig[appointment.estado]?.key || appointment.estado.toLowerCase())}
                              </Badge>
                            </td>
                            <td>
                              <Dropdown>
                                <Dropdown.Toggle variant="secondary" size="sm" id={`dropdown-actions-${appointment.id}`} disabled={isProcessing && processingId === appointment.id}>
                                  {isProcessing && processingId === appointment.id ? <Spinner as="span" animation="border" size="sm" /> : t('actions')}
                                </Dropdown.Toggle>
                                <Dropdown.Menu>
                                  <Dropdown.Item onClick={() => handleConfirmAppointment(appointment.id)} disabled={appointment.estado !== APPOINTMENT_STATUS.PENDIENTE || isProcessing}>
                                    {t('confirm')}
                                  </Dropdown.Item>
                                  <Dropdown.Item onClick={() => openRescheduleModal(appointment)} disabled={isFinalState || isProcessing}>
                                    {t('reschedule')}
                                  </Dropdown.Item>
                                  <Dropdown.Item onClick={() => openConfirmCancelModal(appointment.id)} disabled={isFinalState || isProcessing} className="text-danger">
                                    {t('cancel')}
                                  </Dropdown.Item>
                                </Dropdown.Menu>
                              </Dropdown>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </Table>
                </div>
              ) : (
                <Alert variant="info" className="text-center mt-3">
                  {t('no_appointments_found')}
                </Alert>
              )}
              {renderPagination()}
            </Col>
          </Row>

      <Modal show={showRescheduleModal} onHide={closeRescheduleModal}>
        <Modal.Header closeButton>
          <Modal.Title>{t('reschedule_appointment_modal')}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {reschedulingAppointment && (
            <Form onSubmit={handleRescheduleAppointment}>
              <Form.Group className="mb-3">
                <Form.Label>{t('new_date_time_label')}</Form.Label>
                <Form.Control
                  type="datetime-local"
                  value={newDate}
                  min={getMinDateTime()}
                  onChange={(e) => setNewDate(e.target.value)}
                  required
                />
              </Form.Group>
              <Button variant="primary" type="submit" disabled={isProcessing || newDate === reschedulingAppointment.fecha}>
                {t('save_changes')}
              </Button>
            </Form>
          )}
        </Modal.Body>
      </Modal>

      <Modal show={showConfirmCancelModal} onHide={closeConfirmCancelModal} centered>
        <Modal.Header closeButton>
          <Modal.Title>{t('confirm_cancellation_title')}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {t('confirm_cancel_appointment')}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={closeConfirmCancelModal}>
            {t('no')}
          </Button>
          <Button variant="danger" onClick={handleDeleteAppointment} disabled={isProcessing}>
            {isProcessing && processingId === deletingId ? (
              <Spinner as="span" animation="border" size="sm" />
            ) : (
              t('yes_cancel')
            )}
          </Button>
        </Modal.Footer>
      </Modal>

      <NewAppointmentModal 
        show={showNewAppointmentModal}
        onHide={() => setShowNewAppointmentModal(false)}
        onAppointmentAdded={handleAppointmentAdded}
        prefillData={location.state?.prefill}
      />
    </Container>
  );
};

export default Appointments;