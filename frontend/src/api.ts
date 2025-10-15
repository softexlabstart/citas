import axios from 'axios';
import { Appointment } from './interfaces/Appointment';
import { Horario } from './interfaces/Horario';
import { RegisterUser } from './interfaces/User';
import { Service } from './interfaces/Service';
import { Recurso } from './interfaces/Recurso';
import { Sede } from './interfaces/Sede'; // Added Sede import
import { Client } from './interfaces/Client';
import { 
    MultiTenantRegistrationData, 
    InvitationData, 
    OrganizationInfo, 
    OrganizationMembersResponse 
} from './interfaces/Organization';

export interface PaginatedResponse<T> {
    count: number;
    next: string | null;
    previous: string | null;
    results: T[];
}

const API_URL = process.env.REACT_APP_API_URL;
// IMPORTANT: In production, REACT_APP_API_URL should always be an HTTPS endpoint
// to ensure data encryption in transit.
const api = axios.create({
  baseURL: API_URL,
});

api.interceptors.request.use(
    (config: any) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error: any) => {
        return Promise.reject(error);
    }
);

export const setupInterceptors = (logout: (message?: string) => void) => {
    api.interceptors.response.use(
        (response: any) => response,
        (error: any) => {
            if (error.response && error.response.status === 401) {
                logout('Tu sesión ha expirado. Por favor, inicia sesión de nuevo.');
            }
            return Promise.reject(error);
        }
    );
};

// Funciones para Citas
export const getAppointments = (status?: string, page?: number, search?: string) => {
  let url = '/api/citas/citas/';
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
  const url = `/api/citas/citas/all/${queryString ? `?${queryString}` : ''}`;
  return api.get<Appointment[]>(url);
};

export interface CreateAppointmentPayload {
    nombre: string;
    fecha: string;
    servicios_ids: number[];
    colaboradores_ids: number[];
    sede_id: number;
    estado: 'Pendiente';
}

export const addAppointment = (appointment: CreateAppointmentPayload) => api.post<Appointment>('/api/citas/citas/', appointment);
export const confirmAppointment = (id: number) => api.post(`/api/citas/citas/${id}/confirmar/`);
export const deleteAppointment = (id: number) => api.delete(`/api/citas/citas/${id}/`);
export const updateAppointment = (id: number, appointment: Partial<Appointment>) => api.patch(`/api/citas/citas/${id}/`, appointment);

// Funciones para Servicios
export const getServicios = (sedeId?: string) => {
    let url = '/api/citas/servicios/';
    if (sedeId) {
        url += `?sede_id=${sedeId}`;
    }
    return api.get<Service[]>(url);
};
export const addServicio = (servicio: Partial<Service>) => api.post<Service>('/api/citas/servicios/', servicio);
export const updateServicio = (id: number, servicio: Partial<Service>) => api.patch<Service>(`/api/citas/servicios/${id}/`, servicio);
export const deleteServicio = (id: number) => api.delete(`/api/citas/servicios/${id}/`);

// Funciones para Recursos
export const getRecursos = (sedeId?: string) => {
    let url = '/api/citas/recursos/';
    if (sedeId) {
        url += `?sede_id=${sedeId}`;
    }
    return api.get<Recurso[]>(url);
};
export const addRecurso = (recurso: Partial<Recurso>) => api.post<Recurso>('/api/citas/recursos/', recurso);
export const updateRecurso = (id: number, recurso: Partial<Recurso>) => api.patch<Recurso>(`/api/citas/recursos/${id}/`, recurso);
export const deleteRecurso = (id: number) => api.delete(`/api/citas/recursos/${id}/`);
export const getDisponibilidad = (fecha: string, recursoId: number, sedeId: string, servicioIds: string[]) => {
    const params = new URLSearchParams({
        fecha,
        recurso_id: String(recursoId),
        sede_id: sedeId,
        servicio_ids: servicioIds.join(','),
    });
    return api.get(`/api/citas/disponibilidad/?${params.toString()}`);
};

// Funciones para Bloqueos (New)
export interface Bloqueo {
    id: number;
    colaborador: Recurso;
    sede: Sede;
    motivo: string;
    fecha_inicio: string;
    fecha_fin: string;
}

export interface CreateBloqueoPayload {
    colaborador_id: number;
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
    return api.get<Bloqueo[]>(`/api/citas/bloqueos/${queryString ? `?${queryString}` : ''}`);
};
export const addBloqueo = (bloqueo: CreateBloqueoPayload) => api.post<Bloqueo>('/api/citas/bloqueos/', bloqueo);
export const deleteBloqueo = (id: number) => api.delete(`/api/citas/bloqueos/${id}/`);

// Funciones para Disponibilidad Inteligente (New)
export interface NextAvailableSlot {
    recurso: {
        id: number;
        nombre: string;
    };
    start: string;
    end: string;
}

export const getNextAvailableSlots = (servicioIds: string[], sedeId: string) => {
    const params = new URLSearchParams({
        servicio_ids: servicioIds.join(','),
        sede_id: sedeId
    });
    return api.get<NextAvailableSlot[]>(`/api/citas/next-availability/?${params.toString()}`);
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

export const getDashboardSummary = () => api.get<DashboardSummary>('/api/citas/dashboard/summary/');

// Funciones para Sedes (New section)
export const getSedes = (organizacionSlug?: string) => {
    const params = organizacionSlug ? `?organizacion_slug=${organizacionSlug}` : '';
    return api.get<Sede[]>(`/api/organizacion/sedes/${params}`);
};

// Funciones para Reportes
export const getAppointmentsReport = (startDate: string, endDate: string, servicioIds?: string[], recursoId?: string) => {
    const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
    });
    if (servicioIds && servicioIds.length > 0) {
        params.append('servicio_ids', servicioIds.join(','));
    }
    if (recursoId) {
        params.append('recurso_id', recursoId);
    }
    return api.get(`/api/citas/reports/appointments/?${params.toString()}`);
};

export const getSedeSummaryReport = (startDate: string, endDate: string) => {
    const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
    });
    return api.get(`/api/citas/reports/sede_summary/?${params.toString()}`);
};

export const downloadAppointmentsReportCSV = (startDate: string, endDate: string, servicioIds?: string[], recursoId?: string) => {
    const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
    });
    if (servicioIds && servicioIds.length > 0) {
        params.append('servicio_ids', servicioIds.join(','));
    }
    if (recursoId) {
        params.append('recurso_id', recursoId);
    }
    params.append('export', 'csv'); // Use 'export' to avoid conflict with DRF's 'format'
    // Important: set responseType to 'blob' to handle file download
    return api.get(`/api/citas/reports/appointments/?${params.toString()}`, { responseType: 'blob' });
};


// Funciones para Autenticación
export const login = async (username: string, password: string) => {
    const response = await api.post('/api/token/', { username, password });
    const token = response.data.access;
    const userResponse = await api.get('/api/auth/user/', {
        headers: { Authorization: `Bearer ${token}` }
    });
    return { ...response.data, user: userResponse.data };
};

export const register = async (user: RegisterUser) => {
    const response = await api.post('/api/register/', user);
    return response.data;
};

export const updateUserProfile = (userData: Partial<Client>) => api.patch<Client>('/api/auth/user/', userData);

// Funciones para Zonas Horarias
export const getTimezones = () => api.get<string[]>('/api/timezones/');

// Funciones para Horarios
export const getHorarios = () => api.get<Horario[]>('/api/citas/horarios/');
export const addHorario = (horario: Horario) => api.post('/api/citas/horarios/', horario);
export const updateHorario = (id: number, horario: Horario) => api.patch(`/api/citas/horarios/${id}/`, horario);
export const deleteHorario = (id: number) => api.delete(`/api/citas/horarios/${id}/`);

// Funciones para Recurso Dashboard
export const getRecursoAppointments = () => api.get<Appointment[]>('/api/citas/recurso-citas/');
export const marcarAsistencia = (id: number, asistio: boolean, comentario?: string) => api.post(`/api/citas/recurso-citas/${id}/marcar_asistencia/`, { asistio, comentario });

// Funciones para Clientes
export const getClients = (consentFilter?: string) => {
    const params = new URLSearchParams();
    if (consentFilter) {
        params.append('consent', consentFilter);
    }
    params.append('_', new Date().getTime().toString()); // Cache buster
    return api.get<Client[]>(`/api/clients/?${params.toString()}`);
};
export const getClientById = (id: number) => api.get<Client>(`/api/clients/${id}/`); // Added for fetching single client
export const createClient = (clientData: Partial<Client>) => api.post<Client>('/api/clients/', clientData);
export const updateClient = (id: number, clientData: Partial<Client>) => api.patch<Client>(`/api/clients/${id}/`, clientData);
export const deleteClient = (id: number) => api.delete(`/api/clients/${id}/`);
export const getClientHistory = (id: number) => api.get(`/api/clients/${id}/history/`);

// Funciones para Marketing
export const sendMarketingEmail = (data: { subject: string; message: string; recipient_emails?: string[] }) => api.post('/api/marketing/send-email/', data);

// Funciones para Gestión de Datos Personales (New)
export const getPersonalData = () => api.get<any>('/api/auth/user/personal-data/');
export const deleteAccount = () => api.delete('/api/auth/user/delete-account/'); // New function for deleting account

export const updateDataProcessingOptOut = (optOutStatus: boolean) => api.patch('/api/auth/user/', { perfil: { data_processing_opt_out: optOutStatus } });

// Funciones para Sistema Multi-Tenant (New)
export const registerWithOrganization = async (data: MultiTenantRegistrationData) => {
    const response = await api.post('/api/usuarios/register-organization/', data);
    return response.data;
};

export const getOrganizationInfo = () => api.get<OrganizationInfo>('/api/usuarios/organization/');

export const getOrganizationMembers = (sedeId?: number) => {
    const params = new URLSearchParams();
    if (sedeId) {
        params.append('sede_id', String(sedeId));
    }
    const queryString = params.toString();
    return api.get<OrganizationMembersResponse>(`/api/usuarios/organization/members/${queryString ? `?${queryString}` : ''}`);
};

export const sendInvitation = (invitation: InvitationData) => api.post('/api/usuarios/organization/invite/', invitation);

// Funciones para Organizacion
export const createOrganization = (nombre: string) => api.post('/api/organizacion/organizaciones/', { nombre });

// Funciones para Magic Link (Autenticación sin Contraseña)
export const requestMagicLink = async (email: string) => {
    const response = await api.post('/api/auth/request-history-link/', { email });
    return response.data;
};

export const authenticateWithMagicLink = async (token: string) => {
    const response = await api.post('/api/auth/access-history-with-token/', { token });
    return response.data;
};

// Funciones para Password Reset (Recuperación de Contraseña)
export const requestPasswordReset = async (email: string) => {
    const response = await api.post('/api/auth/request-password-reset/', { email });
    return response.data;
};

export const confirmPasswordReset = async (token: string, new_password: string) => {
    const response = await api.post('/api/auth/confirm-password-reset/', { token, new_password });
    return response.data;
};

// Funciones para Guía de Usuario
export interface GuideSection {
    id: number;
    title: string;
    slug: string;
    content: string;
    category: string;
    category_display: string;
    order: number;
    icon: string;
    language: string;
    language_display: string;
    video_url?: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export const getGuideSections = (language?: string, category?: string) => {
    const params = new URLSearchParams();
    if (language) params.append('language', language);
    if (category) params.append('category', category);
    return api.get<GuideSection[]>(`/api/guide/sections/?${params.toString()}`);
};

// Funciones para Onboarding
export interface OnboardingProgress {
    id: number;
    user: number;
    user_email: string;
    user_name: string;
    has_created_service: boolean;
    has_added_collaborator: boolean;
    has_viewed_public_link: boolean;
    has_completed_profile: boolean;
    is_completed: boolean;
    is_dismissed: boolean;
    completion_percentage: number;
    pending_steps: string[];
    created_at: string;
    updated_at: string;
    completed_at?: string;
}

export const getOnboardingProgress = () => api.get<OnboardingProgress>('/api/onboarding/progress/');
export const markOnboardingStep = (step: string) => api.post('/api/onboarding/progress/mark_step/', { step });
export const dismissOnboarding = () => api.post('/api/onboarding/progress/dismiss/');
export const completeOnboarding = () => api.post('/api/onboarding/progress/complete/');
export const resetOnboarding = () => api.post('/api/onboarding/progress/reset/');

// Funciones para Reservas Públicas (Invitados)
export interface PublicBookingData {
    nombre: string;
    email_cliente: string;
    telefono_cliente: string;
    fecha: string;
    servicios_ids: number[];
    colaboradores_ids: number[];
    sede_id: number;
    comentario?: string;
}

export const createPublicBooking = async (bookingData: PublicBookingData) => {
    const response = await api.post('/api/citas/public-booking/', bookingData);
    return response.data;
};
