import { useState, useEffect, useMemo } from 'react';
import { Sede } from '../interfaces/Sede';
import { Service } from '../interfaces/Service';
import { Recurso } from '../interfaces/Recurso';
import { getSedes, getServicios, getRecursos } from '../api';
import { useApi } from './useApi';

export const useAppointmentForm = () => {
    // State for selected values
    const [selectedSede, setSelectedSede] = useState('');
    const [selectedRecurso, setSelectedRecurso] = useState('');

    // API hooks for data fetching
    const { data: sedes, loading: loadingSedes, error: errorSedes, request: fetchSedes } = useApi<Sede[], []>(getSedes);
    const { data: servicios, loading: loadingServicios, error: errorServicios, request: fetchServicios } = useApi<Service[], [string]>(getServicios);
    const { data: recursos, loading: loadingRecursos, error: errorRecursos, request: fetchRecursos } = useApi<Recurso[], [string]>(getRecursos);

    // Fetch sedes on initial mount
    useEffect(() => {
        fetchSedes();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

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

    return {
        sedes: sedes || [],
        // Memoize to prevent re-rendering if the sede is not selected
        servicios: useMemo(() => (selectedSede ? servicios || [] : []), [selectedSede, servicios]),
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