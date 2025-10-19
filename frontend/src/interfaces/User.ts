export interface Sede {
    id: number;
    nombre: string;
}

export interface Organizacion {
    id: number;
    nombre: string;
    slug: string;
}

export interface PerfilUsuario {
    timezone: string;
    sede: number | null; // Assuming sede is just an ID here
    sedes: Sede[]; // Multiple sedes that the user has access to
    sedes_administradas: Sede[];
    is_sede_admin: boolean;
    organizacion?: Organizacion | null; // Organización del usuario
    telefono?: string;
    ciudad?: string;
    barrio?: string;
    genero?: string;
    fecha_nacimiento?: string | null;
    has_consented_data_processing?: boolean;
    data_processing_opt_out?: boolean;
    // New Role System Fields
    role?: 'owner' | 'admin' | 'sede_admin' | 'colaborador' | 'cliente';
    additional_roles?: string[];
    display_badge?: string;
    is_active?: boolean;
    permissions?: Record<string, boolean>;
}

export interface User {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    is_staff: boolean;
    is_superuser: boolean;
    perfil: PerfilUsuario; // Add the perfil field
    groups: string[];
}

export interface RegisterUser extends Omit<User, 'id' | 'is_staff' | 'perfil' | 'groups' | 'is_superuser'> {
    password: string;
    timezone: string;
    has_consented_data_processing: boolean; // Added for registration consent
}
