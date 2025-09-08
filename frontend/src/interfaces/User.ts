export interface Sede {
    id: number;
    nombre: string;
}

export interface PerfilUsuario {
    timezone: string;
    sede: number | null; // Assuming sede is just an ID here
    sedes_administradas: Sede[];
    is_sede_admin: boolean;
}

export interface User {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    is_staff: boolean;
    perfil: PerfilUsuario; // Add the perfil field
}

export interface RegisterUser extends Omit<User, 'id' | 'is_staff' | 'perfil'> {
    password: string;
    timezone: string;
}
