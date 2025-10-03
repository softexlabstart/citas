import React, { createContext, ReactNode, useState, useEffect, useCallback, useContext } from 'react';
import { login as apiLogin, setupInterceptors, authenticateWithMagicLink } from '../api';
import { User } from '../interfaces/User';
import useIdleTimer from '../hooks/useIdleTimer';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

interface AuthContextType {
    user: (User & { groups: string[] }) | null;
    login: (username: string, password: string) => Promise<void>;
    loginWithMagicLink: (token: string) => Promise<void>;
    logout: (message?: string) => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<(User & { groups: string[] }) | null>(null);

    const logout = useCallback((message?: string) => {
        // Prevent multiple logout calls
        if (!user) {
            return;
        }
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setUser(null);
        if (message) {
            toast.info(message);
        }
    }, [user]); // Add user to dependency array

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
            if (storedUser) {
                setUser(JSON.parse(storedUser));
            }
        }
    }, []);

    useEffect(() => {
        setupInterceptors(logout);
    }, [logout]);

    const login = async (username: string, password: string) => {
        const response = await apiLogin(username, password);
        localStorage.setItem('token', response.access);
        localStorage.setItem('user', JSON.stringify(response.user));
        setUser(response.user);
    };

    const loginWithMagicLink = async (token: string) => {
        const response = await authenticateWithMagicLink(token);
        localStorage.setItem('token', response.access);
        localStorage.setItem('user', JSON.stringify(response.user));
        setUser(response.user);
    };

    return (
        <AuthContext.Provider value={{ user, login, loginWithMagicLink, logout }}>
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