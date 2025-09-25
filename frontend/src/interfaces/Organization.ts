// Interfaces para el sistema multi-tenant
export interface Organizacion {
    id: number;
    nombre: string;
}

export interface SedeDetail {
    id: number;
    nombre: string;
    direccion: string;
    telefono: string;
}

export interface MultiTenantRegistrationData {
    // Datos del usuario
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    password: string;
    
    // Datos de la organización
    organizacion_nombre: string;
    
    // Datos de la sede principal
    sede_nombre: string;
    sede_direccion?: string;
    sede_telefono?: string;
    
    // Datos del perfil
    telefono?: string;
    ciudad?: string;
    barrio?: string;
    genero?: 'M' | 'F' | 'O';
    fecha_nacimiento?: string;
    timezone?: string;
}

export interface InvitationData {
    email: string;
    first_name: string;
    last_name: string;
    role: 'admin' | 'sede_admin' | 'colaborador';
    sede_id?: number;
    message?: string;
}

export interface OrganizationInfo {
    organizacion: Organizacion;
    sedes: SedeDetail[];
    user_role: 'super_admin' | 'sede_admin' | 'member';
}

export interface OrganizationMember {
    id: number;
    username: string;
    first_name: string;
    last_name: string;
    email: string;
    perfil: {
        sede: SedeDetail | null;
        sedes_administradas: SedeDetail[];
        is_sede_admin: boolean;
    };
}

export interface OrganizationMembersResponse {
    miembros: OrganizationMember[];
    total: number;
}
