import React, { createContext, ReactNode, useState, useEffect, useCallback, useContext, useRef } from 'react';
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
    updateUser: (updatedUser: Partial<User & { groups: string[] }>) => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<(User & { groups: string[] }) | null>(null);
    const logoutInProgressRef = useRef(false);

    const logout = useCallback((message?: string) => {
        // Prevent multiple logout calls
        if (!user || logoutInProgressRef.current) {
            return;
        }
        logoutInProgressRef.current = true;
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setUser(null);
        if (message) {
            toast.info(message);
        }
        // Reset flag after a short delay to allow cleanup
        setTimeout(() => {
            logoutInProgressRef.current = false;
        }, 1000);
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

    const updateUser = useCallback((updatedUser: Partial<User & { groups: string[] }>) => {
        if (user) {
            const newUser = { ...user, ...updatedUser };
            setUser(newUser);
            localStorage.setItem('user', JSON.stringify(newUser));
        }
    }, [user]);

    return (
        <AuthContext.Provider value={{ user, login, loginWithMagicLink, logout, updateUser }}>
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