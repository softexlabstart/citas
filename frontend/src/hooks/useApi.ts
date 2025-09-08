import { useState, useCallback } from 'react';

interface UseApiState<T> {
    data: T | null;
    error: string | null;
    loading: boolean;
}

export const useApi = <T, P extends any[]>(apiFunc: (...args: P) => Promise<{ data: T }>) => {
    const [state, setState] = useState<UseApiState<T>>({
        data: null,
        error: null,
        loading: false,
    });

    const request = useCallback(async (...args: P): Promise<{ success: boolean; data?: T; error?: string }> => {
        setState((prevState) => ({ ...prevState, loading: true, error: null }));
        try {
            const response = await apiFunc(...args);
            setState({ data: response.data, loading: false, error: null });
            return { success: true, data: response.data };
        } catch (err: any) {
            const errorMessage = err.response?.data?.detail || err.message || 'An unexpected error occurred.';
            setState({ data: null, loading: false, error: errorMessage });
            return { success: false, error: errorMessage };
        }
    }, [apiFunc]);

    return { ...state, request };
};