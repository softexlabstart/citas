import { useState, useEffect, useCallback } from 'react';
import {
    getOnboardingProgress,
    markOnboardingStep,
    dismissOnboarding,
    completeOnboarding,
    OnboardingProgress
} from '../api';

export const useOnboarding = () => {
    const [progress, setProgress] = useState<OnboardingProgress | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchProgress = useCallback(async () => {
        try {
            setLoading(true);
            const response = await getOnboardingProgress();
            setProgress(response.data);
            setError(null);
        } catch (err: any) {
            console.error('Error fetching onboarding progress:', err);
            setError(err?.response?.data?.message || 'Error al cargar el progreso');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchProgress();
    }, [fetchProgress]);

    const markStep = async (step: string) => {
        try {
            const response = await markOnboardingStep(step);
            setProgress(response.data);
            return { success: true };
        } catch (err: any) {
            console.error('Error marking step:', err);
            return { success: false, error: err?.response?.data?.error };
        }
    };

    const dismiss = async () => {
        try {
            const response = await dismissOnboarding();
            setProgress(response.data);
            return { success: true };
        } catch (err: any) {
            console.error('Error dismissing onboarding:', err);
            return { success: false, error: err?.response?.data?.error };
        }
    };

    const complete = async () => {
        try {
            const response = await completeOnboarding();
            setProgress(response.data);
            return { success: true };
        } catch (err: any) {
            console.error('Error completing onboarding:', err);
            return { success: false, error: err?.response?.data?.error };
        }
    };

    const shouldShowOnboarding = () => {
        if (!progress) return false;
        return !progress.is_completed && !progress.is_dismissed;
    };

    return {
        progress,
        loading,
        error,
        markStep,
        dismiss,
        complete,
        refresh: fetchProgress,
        shouldShowOnboarding: shouldShowOnboarding(),
    };
};
