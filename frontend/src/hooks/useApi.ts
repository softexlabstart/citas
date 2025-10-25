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
            // Extraer mensaje de error del backend
            let errorMessage = 'An unexpected error occurred.';

            if (err.response?.data) {
                const errorData = err.response.data;

                // Caso 1: Error simple con campo "detail"
                if (errorData.detail) {
                    errorMessage = errorData.detail;
                }
                // Caso 2: Error simple con campo "error"
                else if (errorData.error) {
                    errorMessage = errorData.error;
                }
                // Caso 3: Errores de validación de Django (formato: {campo: ["mensaje"]})
                else if (typeof errorData === 'object') {
                    const messages: string[] = [];
                    for (const [, fieldErrors] of Object.entries(errorData)) {
                        if (Array.isArray(fieldErrors)) {
                            messages.push(...fieldErrors);
                        } else if (typeof fieldErrors === 'string') {
                            messages.push(fieldErrors);
                        }
                    }
                    if (messages.length > 0) {
                        errorMessage = messages.join('. ');
                    }
                }
                // Caso 4: String directo
                else if (typeof errorData === 'string') {
                    errorMessage = errorData;
                }
            }
            // Fallback al mensaje de error de Axios
            else if (err.message) {
                errorMessage = err.message;
            }

            setState({ data: null, loading: false, error: errorMessage });
            return { success: false, error: errorMessage };
        }
    }, [apiFunc]);

    const setData = (data: T) => {
        setState(prevState => ({ ...prevState, data }));
    };

    return { ...state, request, setData };
};