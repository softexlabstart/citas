import React, { useState, useEffect } from 'react';
import { getRecursoAppointments, marcarAsistencia } from '../api';
import { Appointment } from '../interfaces/Appointment';
import { Table, Button, Badge } from 'react-bootstrap';

const RecursoDashboard = () => {
    const [appointments, setAppointments] = useState<Appointment[]>([]);

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

    const handleMarcarAsistencia = async (id: number, asistio: boolean) => {
        try {
            const response = await marcarAsistencia(id, asistio);
            setAppointments(appointments.map(a => a.id === id ? response.data : a));
        } catch (error) {
            console.error('Error updating appointment status:', error);
        }
    };

    return (
        <div>
            <h1>Mis Citas</h1>
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
                                {appointment.estado !== 'Asistio' && appointment.estado !== 'No Asistio' && (
                                    <>
                                        <Button variant="success" size="sm" onClick={() => handleMarcarAsistencia(appointment.id, true)}>Asistió</Button>{' '}
                                        <Button variant="danger" size="sm" onClick={() => handleMarcarAsistencia(appointment.id, false)}>No Asistió</Button>
                                    </>
                                )}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </Table>
        </div>
    );
};

export default RecursoDashboard;
