// Role System Interfaces for Multi-Tenant SaaS

export type RoleType = 'owner' | 'admin' | 'sede_admin' | 'colaborador' | 'cliente';

export interface RoleChoice {
    value: RoleType;
    label: string;
    emoji: string;
    description: string;
}

export const ROLE_CHOICES: RoleChoice[] = [
    {
        value: 'owner',
        label: 'Propietario',
        emoji: '👑',
        description: 'Dueño de la organización con acceso total'
    },
    {
        value: 'admin',
        label: 'Administrador',
        emoji: '🔴',
        description: 'Administrador global con acceso a todas las sedes'
    },
    {
        value: 'sede_admin',
        label: 'Admin de Sede',
        emoji: '🟠',
        description: 'Administrador de sedes específicas'
    },
    {
        value: 'colaborador',
        label: 'Colaborador',
        emoji: '🟢',
        description: 'Empleado que atiende citas'
    },
    {
        value: 'cliente',
        label: 'Cliente',
        emoji: '🔵',
        description: 'Usuario final que agenda citas'
    }
];

export interface CreateUserPayload {
    email: string;
    first_name: string;
    last_name: string;
    password: string;
    role: RoleType;
    additional_roles?: RoleType[];
    sede_principal_id?: number;
    sedes_trabajo_ids?: number[];
    sedes_administradas_ids?: number[];
    permissions?: Record<string, boolean>;
}

export interface UserWithRoles {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
    role: RoleType;
    additional_roles: RoleType[];
    display_badge: string;
    accessible_sedes: number;
    is_active: boolean;
}

export interface UserOrganization {
    id: number;
    nombre: string;
    slug: string;
    role: RoleType;
    all_roles: RoleType[];
    display_badge: string;
}

export interface UserOrganizationsResponse {
    count: number;
    organizations: UserOrganization[];
}
