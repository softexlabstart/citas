import { useMemo } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { RoleType } from '../interfaces/Role';

export interface RolePermissions {
    // Role checks
    isOwner: boolean;
    isAdmin: boolean;
    isSedeAdmin: boolean;
    isColaborador: boolean;
    isCliente: boolean;

    // Combined checks
    isAdminOrHigher: boolean;
    isSedeAdminOrHigher: boolean;
    isColaboradorOrHigher: boolean;

    // Capabilities
    canManageUsers: boolean;
    canManageServices: boolean;
    canManageAppointments: boolean;
    canViewReports: boolean;
    canManageSedes: boolean;
    canAccessAllSedes: boolean;

    // Role info
    primaryRole: RoleType | null;
    allRoles: RoleType[];
    displayBadge: string | null;
}

/**
 * Hook that provides role-based permission checks for the current user
 */
export const useRolePermissions = (): RolePermissions => {
    const { user } = useAuth();

    return useMemo(() => {
        const perfil = user?.perfil;
        const primaryRole = perfil?.role || null;
        const additionalRoles = perfil?.additional_roles || [];
        const allRoles: RoleType[] = primaryRole
            ? [primaryRole, ...additionalRoles.filter((r): r is RoleType => r !== primaryRole)]
            : [];

        // Role checks
        const isOwner = allRoles.includes('owner');
        const isAdmin = allRoles.includes('admin');
        const isSedeAdmin = allRoles.includes('sede_admin');
        const isColaborador = allRoles.includes('colaborador');
        const isCliente = allRoles.includes('cliente');

        // Combined checks
        const isAdminOrHigher = isOwner || isAdmin;
        const isSedeAdminOrHigher = isAdminOrHigher || isSedeAdmin;
        const isColaboradorOrHigher = isSedeAdminOrHigher || isColaborador;

        // Capabilities based on roles
        const canManageUsers = isAdminOrHigher;
        const canManageServices = isSedeAdminOrHigher;
        const canManageAppointments = isColaboradorOrHigher;
        const canViewReports = isSedeAdminOrHigher;
        const canManageSedes = isAdminOrHigher;
        const canAccessAllSedes = isAdminOrHigher;

        return {
            // Role checks
            isOwner,
            isAdmin,
            isSedeAdmin,
            isColaborador,
            isCliente,

            // Combined checks
            isAdminOrHigher,
            isSedeAdminOrHigher,
            isColaboradorOrHigher,

            // Capabilities
            canManageUsers,
            canManageServices,
            canManageAppointments,
            canViewReports,
            canManageSedes,
            canAccessAllSedes,

            // Role info
            primaryRole,
            allRoles,
            displayBadge: perfil?.display_badge || null,
        };
    }, [user]);
};

/**
 * Hook that provides a function to check if user has a specific role
 */
export const useHasRole = () => {
    const { user } = useAuth();

    return (role: RoleType): boolean => {
        const perfil = user?.perfil;
        if (!perfil) return false;

        const allRoles = [
            perfil.role,
            ...(perfil.additional_roles || [])
        ].filter((r): r is RoleType => r !== null && r !== undefined);

        return allRoles.includes(role);
    };
};

/**
 * Hook that provides the default dashboard route based on user's primary role
 */
export const useDefaultDashboard = (): string => {
    const { user } = useAuth();
    const primaryRole = user?.perfil?.role;

    const dashboardMap: Record<RoleType, string> = {
        owner: '/',
        admin: '/',
        sede_admin: '/',
        colaborador: '/recurso-dashboard',
        cliente: '/',
    };

    return dashboardMap[primaryRole as RoleType] || '/user';
};
