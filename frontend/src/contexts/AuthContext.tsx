import React, { createContext, ReactNode, useState, useEffect, useCallback } from 'react';
import { login as apiLogin, setupInterceptors } from '../api';
import { User } from '../interfaces/User';
import useIdleTimer from '../hooks/useIdleTimer';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

interface AuthContextType {
    user: User | null;
    login: (username: string, password: string) => Promise<void>;
    logout: (message?: string) => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);

    const logout = useCallback((message?: string) => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setUser(null);
        if (message) {
            toast.info(message);
        }
    }, []);

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

    return (
        <AuthContext.Provider value={{ user, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};
