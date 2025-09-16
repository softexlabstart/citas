import React, { useState, useEffect } from 'react';
import { getRecursoAppointments, marcarAsistencia } from '../api';
import { Appointment } from '../interfaces/Appointment';
import { Table, Button, Badge, Modal, Form } from 'react-bootstrap';

const RecursoDashboard = () => {
    const [appointments, setAppointments] = useState<Appointment[]>([]);
    const [showModal, setShowModal] = useState(false);
    const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);
    const [comment, setComment] = useState('');

    useEffect(() => {
        const fetchAppointments = async () => {
            try {
                const response = await getRecursoAppointments();
                setAppointments(response.data);
            } catch (error) {
                console.error('Error fetching appointments:', error);
            }
        };

        fetchAppointments();
    }, []);

    const handleMarcarAsistencia = async (id: number, asistio: boolean, comentario?: string) => {
        try {
            const response = await marcarAsistencia(id, asistio, comentario);
            setAppointments(appointments.map(a => a.id === id ? response.data : a));
            setShowModal(false);
            setComment('');
        } catch (error) {
            console.error('Error updating appointment status:', error);
        }
    };

    const openModal = (appointment: Appointment) => {
        setSelectedAppointment(appointment);
        setShowModal(true);
    };

    const handleCloseModal = () => {
        setShowModal(false);
        setComment('');
    };

    return (
        <div>
            <h1>Panel de Recurso</h1>
            <div className="d-flex flex-wrap gap-4 mb-4">
                <a href="/reports" className="text-decoration-none">
                    <div className="card shadow-sm p-4 text-center dashboard-card-hover">
                        <h5>Informes</h5>
                        <p>Accede a los reportes de citas y servicios.</p>
                    </div>
                </a>
                <a href="/clients" className="text-decoration-none">
                    <div className="card shadow-sm p-4 text-center dashboard-card-hover">
                        <h5>Clientes</h5>
                        <p>Consulta y gestiona los clientes.</p>
                    </div>
                </a>
                <a href="/marketing" className="text-decoration-none">
                    <div className="card shadow-sm p-4 text-center dashboard-card-hover">
                        <h5>Marketing</h5>
                        <p>Envía campañas y comunicaciones.</p>
                    </div>
                </a>
            </div>
            <h2>Mis Citas</h2>
            <Table striped bordered hover responsive>
                <thead>
                    <tr>
                        <th>Cliente</th>
                        <th>Servicio</th>
                        <th>Fecha y Hora</th>
                        <th>Estado</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    {appointments.map(appointment => (
                        <tr key={appointment.id}>
                            <td>{appointment.nombre}</td>
                            <td>{appointment.servicio.nombre}</td>
                            <td>{new Date(appointment.fecha).toLocaleString()}</td>
                            <td>
                                <Badge bg={appointment.estado === 'Asistio' ? 'success' : appointment.estado === 'No Asistio' ? 'danger' : 'secondary'}>
                                    {appointment.estado}
                                </Badge>
                            </td>
                            <td>
                                {appointment.estado !== 'Asistio' && appointment.estado !== 'No Asistio' && appointment.estado !== 'Cancelada' && (
                                    <>
                                        <Button variant="success" size="sm" onClick={() => handleMarcarAsistencia(appointment.id, true)}>Asistió</Button>{' '}
                                        <Button variant="danger" size="sm" onClick={() => openModal(appointment)}>No Asistió</Button>
                                    </>
                                )}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </Table>

            <Modal show={showModal} onHide={handleCloseModal}>
                <Modal.Header closeButton>
                    <Modal.Title>Agregar Comentario</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form.Group>
                        <Form.Label>Comentario (opcional)</Form.Label>
                        <Form.Control as="textarea" rows={3} value={comment} onChange={(e) => setComment(e.target.value)} />
                    </Form.Group>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={handleCloseModal}>Cancelar</Button>
                    <Button variant="primary" onClick={() => handleMarcarAsistencia(selectedAppointment!.id, false, comment)}>Confirmar</Button>
                </Modal.Footer>
            </Modal>
        </div>
    );
};

export default RecursoDashboard;