import React, { createContext, ReactNode, useState, useEffect, useCallback, useContext, useRef } from 'react';
import { login as apiLogin, setupInterceptors, authenticateWithMagicLink } from '../api';
import { User } from '../interfaces/User';
import useIdleTimer from '../hooks/useIdleTimer';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// MULTI-TENANT: Interfaz para organizaciones
export interface Organization {
    id: number;
    nombre: string;
    slug: string;
    perfil_id: number;
}

interface AuthContextType {
    user: (User & { groups: string[] }) | null;
    organizations: Organization[] | null;
    selectedOrganization: Organization | null;
    login: (username: string, password: string) => Promise<{ needsOrgSelection: boolean }>;
    loginWithMagicLink: (token: string) => Promise<void>;
    logout: (message?: string) => void;
    updateUser: (updatedUser: Partial<User & { groups: string[] }>) => void;
    selectOrganization: (org: Organization) => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<(User & { groups: string[] }) | null>(null);
    const [organizations, setOrganizations] = useState<Organization[] | null>(null);
    const [selectedOrganization, setSelectedOrganization] = useState<Organization | null>(null);
    const logoutInProgressRef = useRef(false);

    const logout = useCallback((message?: string) => {
        // Prevent multiple logout calls
        if (!user || logoutInProgressRef.current) {
            return;
        }
        logoutInProgressRef.current = true;
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
        localStorage.removeItem('organizations');
        localStorage.removeItem('selectedOrganization');
        setUser(null);
        setOrganizations(null);
        setSelectedOrganization(null);
        if (message) {
            toast.info(message);
        }
        // Reset flag after a short delay to allow cleanup
        setTimeout(() => {
            logoutInProgressRef.current = false;
        }, 1000);
    }, [user]);

    const handleIdle = useCallback(() => {
        if (user) {
            logout('Tu sesión ha expirado por inactividad.');
        }
    }, [user, logout]);

    useIdleTimer(900000, handleIdle);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            const storedUser = localStorage.getItem('user');
            const storedOrganizations = localStorage.getItem('organizations');
            const storedSelectedOrganization = localStorage.getItem('selectedOrganization');

            if (storedUser) {
                setUser(JSON.parse(storedUser));
            }
            if (storedOrganizations) {
                setOrganizations(JSON.parse(storedOrganizations));
            }
            if (storedSelectedOrganization) {
                setSelectedOrganization(JSON.parse(storedSelectedOrganization));
            }
        }
    }, []);

    useEffect(() => {
        setupInterceptors(logout);
    }, [logout]);

    const login = async (username: string, password: string): Promise<{ needsOrgSelection: boolean }> => {
        const response = await apiLogin(username, password);

        localStorage.setItem('token', response.access);
        if (response.refresh) {
            localStorage.setItem('refreshToken', response.refresh);
        }

        // MULTI-TENANT: Verificar si el usuario tiene múltiples organizaciones
        if (response.organizations && response.organizations.length > 0) {
            // Usuario con múltiples organizaciones
            localStorage.setItem('organizations', JSON.stringify(response.organizations));
            localStorage.setItem('user', JSON.stringify(response.user));
            setOrganizations(response.organizations);
            setUser(response.user);
            return { needsOrgSelection: true };
        } else {
            // Usuario con una sola organización (flujo normal)
            localStorage.setItem('user', JSON.stringify(response.user));
            setUser(response.user);

            // CRITICAL FIX: Establecer selectedOrganization automáticamente
            // Esto NO afecta usuarios con múltiples orgs (se maneja arriba en línea 98-104)
            if (response.user.perfil?.organizacion) {
                const org = {
                    id: response.user.perfil.organizacion.id,
                    nombre: response.user.perfil.organizacion.nombre,
                    slug: response.user.perfil.organizacion.slug
                };
                localStorage.setItem('selectedOrganization', JSON.stringify(org));
                setSelectedOrganization(org);
            }

            return { needsOrgSelection: false };
        }
    };

    const selectOrganization = useCallback((org: Organization) => {
        setSelectedOrganization(org);
        localStorage.setItem('selectedOrganization', JSON.stringify(org));
    }, []);

    const loginWithMagicLink = async (token: string) => {
        const response = await authenticateWithMagicLink(token);
        localStorage.setItem('token', response.access);
        if (response.refresh) {
            localStorage.setItem('refreshToken', response.refresh);
        }
        localStorage.setItem('user', JSON.stringify(response.user));
        setUser(response.user);
    };

    const updateUser = useCallback((updatedUser: Partial<User & { groups: string[] }>) => {
        if (user) {
            const newUser = { ...user, ...updatedUser };
            setUser(newUser);
            localStorage.setItem('user', JSON.stringify(newUser));
        }
    }, [user]);

    return (
        <AuthContext.Provider value={{
            user,
            organizations,
            selectedOrganization,
            login,
            loginWithMagicLink,
            logout,
            updateUser,
            selectOrganization
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};