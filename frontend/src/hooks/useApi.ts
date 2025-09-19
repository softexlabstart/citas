import { useState, useCallback } from 'react';
import { AxiosResponse } from 'axios';

interface UseApiState<T> {
    data: T | null;
    error: string | null;
    loading: boolean;
}

export const useApi = <T, P extends any[]>(apiFunc: (...args: P) => Promise<{ data: T } | AxiosResponse<T>>) => {
    const [state, setState] = useState<UseApiState<T>>({
        data: null,
        error: null,
        loading: false,
    });

    const request = useCallback(async (...args: P): Promise<{ success: boolean; data?: T; error?: string }> => {
        setState((prevState) => ({ ...prevState, loading: true, error: null }));
        try {
            const response = await apiFunc(...args);
            // Check if response is an AxiosResponse or a direct data object
            const data = (response as AxiosResponse<T>).data !== undefined ? (response as AxiosResponse<T>).data : (response as { data: T }).data;
            setState({ data: data, loading: false, error: null });
            return { success: true, data: data };
        } catch (err: any) {
            const errorMessage = err.response?.data?.detail || err.message || 'An unexpected error occurred.';
            setState({ data: null, loading: false, error: errorMessage });
            return { success: false, error: errorMessage };
        }
    }, [apiFunc]);

    const setData = (data: T) => {
        setState(prevState => ({ ...prevState, data }));
    };

    return { ...state, request, setData };
};