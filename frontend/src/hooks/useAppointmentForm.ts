import { useState, useEffect, useMemo } from 'react';
import { Sede } from '../interfaces/Sede';
import { Service } from '../interfaces/Service';
import { Recurso } from '../interfaces/Recurso';
import { getSedes, getServicios, getRecursos } from '../api';
import { useApi } from './useApi';
import { useAuth } from './useAuth';

export const useAppointmentForm = (organizacionSlug?: string) => {
    // State for selected values
    const [selectedSede, setSelectedSede] = useState('');
    const [selectedRecurso, setSelectedRecurso] = useState('');
    const { user } = useAuth();

    // API hooks for data fetching
    const { data: sedes, loading: loadingSedes, error: errorSedes, request: fetchSedes } = useApi<Sede[], [string?]>(getSedes);
    const { data: servicios, loading: loadingServicios, error: errorServicios, request: fetchServicios } = useApi<Service[], [string]>(getServicios);
    const { data: recursos, loading: loadingRecursos, error: errorRecursos, request: fetchRecursos } = useApi<Recurso[], [string]>(getRecursos);

    // Fetch sedes on initial mount, optionally filtered by organization
    useEffect(() => {
        fetchSedes(organizacionSlug);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [organizacionSlug]);

    // Load initial services if user has multiple sedes (without sede selection)
    useEffect(() => {
        if (user?.perfil?.sedes && user.perfil.sedes.length > 1 && !selectedSede) {
            // User has multiple sedes and hasn't selected one yet - load all services
            fetchServicios('');
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user]);

    // Fetch servicios and recursos when a sede is selected
    useEffect(() => {
        // Reset selections when sede changes
        setSelectedRecurso('');

        if (selectedSede) {
            fetchServicios(selectedSede);
            fetchRecursos(selectedSede);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedSede]);

    // Check if user has multiple sedes
    const hasMultipleSedes = user?.perfil?.sedes && user.perfil.sedes.length > 1;

    return {
        sedes: sedes || [],
        // Show servicios if sede is selected OR if user has multiple sedes (showing all)
        servicios: useMemo(() => {
            if (selectedSede) return servicios || [];
            if (hasMultipleSedes) return servicios || [];
            return [];
        }, [selectedSede, servicios, hasMultipleSedes]),
        recursos: useMemo(() => (selectedSede ? recursos || [] : []), [selectedSede, recursos]),
        selectedSede,
        selectedRecurso,
        loadingSedes,
        loadingServicios,
        loadingRecursos,
        error: errorSedes || errorServicios || errorRecursos,
        setSelectedSede,
        setSelectedRecurso
    };
};