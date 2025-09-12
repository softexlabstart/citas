import axios from 'axios';
import { Appointment } from './interfaces/Appointment';
import { Horario } from './interfaces/Horario';
import { RegisterUser } from './interfaces/User';
import { Service } from './interfaces/Service';
import { Recurso } from './interfaces/Recurso';
import { Sede } from './interfaces/Sede'; // Added Sede import

export interface PaginatedResponse<T> {
    count: number;
    next: string | null;
    previous: string | null;
    results: T[];
}

const API_URL = '/api';

const api = axios.create({
  baseURL: API_URL,
});

api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

export const setupInterceptors = (logout: (message?: string) => void) => {
    api.interceptors.response.use(
        (response) => response,
        (error) => {
            if (error.response && error.response.status === 401) {
                logout('Tu sesión ha expirado. Por favor, inicia sesión de nuevo.');
            }
            return Promise.reject(error);
        }
    );
};

// Funciones para Citas
export const getAppointments = (status?: string, page?: number, search?: string) => {
  let url = '/citas/citas/';
  const params = new URLSearchParams();
  if (status) {
    params.append('estado', status);
  }
  if (page) {
    params.append('page', String(page));
  }
  if (search) {
    params.append('search', search);
  }
  const queryString = params.toString();
  if (queryString) url += `?${queryString}`;
  return api.get<PaginatedResponse<Appointment>>(url);
};

export const getAllAppointments = (startDate?: string, endDate?: string) => {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  const queryString = params.toString();
  const url = `/citas/citas/all/${queryString ? `?${queryString}` : ''}`;
  return api.get<Appointment[]>(url);
};

export interface CreateAppointmentPayload {
    nombre: string;
    fecha: string;
    servicio_id: number;
    colaboradores_ids: number[];
    sede_id: number;
    estado: 'Pendiente';
}

export const addAppointment = (appointment: CreateAppointmentPayload) => api.post<Appointment>('/citas/citas/', appointment);
export const confirmAppointment = (id: number) => api.post(`/citas/citas/${id}/confirmar/`);
export const deleteAppointment = (id: number) => api.delete(`/citas/citas/${id}/`);
export const updateAppointment = (id: number, appointment: Partial<Appointment>) => api.patch(`/citas/citas/${id}/`, appointment);

// Funciones para Servicios
export const getServicios = (sedeId?: string) => {
    let url = '/citas/servicios/';
    if (sedeId) {
        url += `?sede_id=${sedeId}`;
    }
    return api.get<Service[]>(url);
};
export const addServicio = (servicio: Partial<Service>) => api.post<Service>('/citas/servicios/', servicio);
export const updateServicio = (id: number, servicio: Partial<Service>) => api.patch<Service>(`/citas/servicios/${id}/`, servicio);
export const deleteServicio = (id: number) => api.delete(`/citas/servicios/${id}/`);

// Funciones para Recursos
export const getRecursos = (sedeId?: string) => {
    let url = '/citas/recursos/';
    if (sedeId) {
        url += `?sede_id=${sedeId}`;
    }
    return api.get<Recurso[]>(url);
};
export const addRecurso = (recurso: Partial<Recurso>) => api.post<Recurso>('/citas/recursos/', recurso);
export const updateRecurso = (id: number, recurso: Partial<Recurso>) => api.patch<Recurso>(`/citas/recursos/${id}/`, recurso);
export const deleteRecurso = (id: number) => api.delete(`/citas/recursos/${id}/`);
export const getDisponibilidad = (fecha: string, recursoId: number, sedeId: string) => {
    const params = new URLSearchParams({
        fecha,
        recurso_id: String(recursoId),
        sede_id: sedeId,
    });
    return api.get(`/citas/disponibilidad/?${params.toString()}`);
};

// Funciones para Bloqueos (New)
export interface Bloqueo {
    id: number;
    recurso: Recurso;
    sede: Sede;
    motivo: string;
    fecha_inicio: string;
    fecha_fin: string;
}

export interface CreateBloqueoPayload {
    recurso_id: number;
    sede_id: number;
    motivo: string;
    fecha_inicio: string;
    fecha_fin: string;
}

export const getBloqueos = (sedeId?: string, startDate?: string, endDate?: string) => {
    const params = new URLSearchParams();
    if (sedeId) params.append('sede_id', sedeId);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    const queryString = params.toString();
    return api.get<Bloqueo[]>(`/citas/bloqueos/${queryString ? `?${queryString}` : ''}`);
};
export const addBloqueo = (bloqueo: CreateBloqueoPayload) => api.post<Bloqueo>('/citas/bloqueos/', bloqueo);
export const deleteBloqueo = (id: number) => api.delete(`/citas/bloqueos/${id}/`);

// Funciones para Disponibilidad Inteligente (New)
export interface NextAvailableSlot {
    recurso: {
        id: number;
        nombre: string;
    };
    start: string;
    end: string;
}

export const getNextAvailableSlots = (servicioId: string, sedeId: string) => {
    const params = new URLSearchParams({ servicio_id: servicioId, sede_id: sedeId });
    return api.get<NextAvailableSlot[]>(`/citas/next-availability/?${params.toString()}`);
};

// Funciones para Dashboard (New)
export interface AdminDashboardSummary {
    citas_hoy: number;
    pendientes_confirmacion: number;
    ingresos_mes: number;
    proximas_citas: Appointment[];
}

export interface UserDashboardSummary {
    proxima_cita: Appointment | null;
}

export type DashboardSummary = AdminDashboardSummary | UserDashboardSummary;

export const getDashboardSummary = () => api.get<DashboardSummary>('/citas/dashboard/summary/');

// Funciones para Sedes (New section)
export const getSedes = () => api.get<Sede[]>('/organizacion/sedes/');

// Funciones para Reportes
export const getAppointmentsReport = (startDate: string, endDate: string, servicioId?: string, recursoId?: string) => {
    const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
    });
    if (servicioId) {
        params.append('servicio_id', servicioId);
    }
    if (recursoId) {
        params.append('recurso_id', recursoId);
    }
    return api.get(`/citas/reports/appointments/?${params.toString()}`);
};

export const getSedeSummaryReport = (startDate: string, endDate: string) => {
    const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
    });
    return api.get(`/citas/reports/sede_summary/?${params.toString()}`);
};

export const downloadAppointmentsReportCSV = (startDate: string, endDate: string, servicioId?: string, recursoId?: string) => {
    const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
    });
    if (servicioId) {
        params.append('servicio_id', servicioId);
    }
    if (recursoId) {
        params.append('recurso_id', recursoId);
    }
    params.append('export', 'csv'); // Use 'export' to avoid conflict with DRF's 'format'
    // Important: set responseType to 'blob' to handle file download
    return api.get(`/citas/reports/appointments/?${params.toString()}`, { responseType: 'blob' });
};


// Funciones para Autenticación
export const login = async (username: string, password: string) => {
    const response = await api.post('/token/', { username, password });
    const token = response.data.access;
    const userResponse = await api.get('/auth/user/', {
        headers: { Authorization: `Bearer ${token}` }
    });
    return { ...response.data, user: userResponse.data };
};

export const register = async (user: RegisterUser) => {
    const response = await api.post('/register/', user);
    return response.data;
};

// Funciones para Zonas Horarias
export const getTimezones = () => api.get<string[]>('/timezones/');

// Funciones para Horarios
export const getHorarios = () => api.get<Horario[]>('/citas/horarios/');
export const addHorario = (horario: Horario) => api.post('/citas/horarios/', horario);
export const updateHorario = (id: number, horario: Horario) => api.patch(`/citas/horarios/${id}/`, horario);
export const deleteHorario = (id: number) => api.delete(`/citas/horarios/${id}/`);

// Funciones para Recurso Dashboard
export const getRecursoAppointments = () => api.get<Appointment[]>('/citas/recurso-citas/');
export const marcarAsistencia = (id: number, asistio: boolean) => api.post(`/citas/recurso-citas/${id}/marcar_asistencia/`, { asistio });
