import React, { useState, useEffect } from 'react';
import { Modal, Button, ProgressBar, Alert } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { useOnboarding } from '../hooks/useOnboarding';

interface WizardStep {
  key: string;
  title: string;
  description: string;
  icon: string;
  action?: () => void;
  actionLabel?: string;
  required: boolean;
}

interface OnboardingWizardProps {
  show: boolean;
  onHide: () => void;
}

const OnboardingWizard: React.FC<OnboardingWizardProps> = ({ show, onHide }) => {
  const navigate = useNavigate();
  const { progress, markStep, complete, dismiss, refresh } = useOnboarding();
  const [currentStep, setCurrentStep] = useState(0);
  const [isCompleting, setIsCompleting] = useState(false);

  const steps: WizardStep[] = [
    {
      key: 'has_created_service',
      title: 'Crea tu primer servicio',
      description: 'Define los servicios que ofreces a tus clientes. Esto es esencial para comenzar a recibir reservas.',
      icon: '🛠️',
      required: true,
      actionLabel: 'Ir a crear servicio',
      action: () => {
        onHide();
        navigate('/admin-settings');
      }
    },
    {
      key: 'has_added_collaborator',
      title: 'Agrega colaboradores',
      description: 'Invita a tu equipo para que gestionen las citas. Puedes asignar diferentes roles y permisos.',
      icon: '👥',
      required: false,
      actionLabel: 'Gestionar colaboradores',
      action: () => {
        onHide();
        navigate('/admin-settings');
      }
    },
    {
      key: 'has_completed_profile',
      title: 'Completa tu perfil',
      description: 'Agrega información de tu negocio, logotipo y datos de contacto para personalizar tu experiencia.',
      icon: '👤',
      required: false,
      actionLabel: 'Editar perfil',
      action: () => {
        onHide();
        navigate('/profile/edit');
      }
    },
    {
      key: 'has_viewed_public_link',
      title: 'Comparte tu enlace público',
      description: 'Obtén el enlace único para que tus clientes puedan agendar citas directamente.',
      icon: '🔗',
      required: false,
      actionLabel: 'Ver enlace público',
      action: () => {
        onHide();
        navigate('/marketing');
      }
    }
  ];

  useEffect(() => {
    if (show && progress) {
      // Encontrar el primer paso no completado
      const firstIncomplete = steps.findIndex(step => {
        const key = step.key as keyof typeof progress;
        return !progress[key];
      });
      if (firstIncomplete !== -1) {
        setCurrentStep(firstIncomplete);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [show, progress]);

  const currentStepData = steps[currentStep];
  const isStepCompleted = progress ? progress[currentStepData.key as keyof typeof progress] : false;
  const totalSteps = steps.length;
  const progressPercentage = progress?.completion_percentage || 0;

  const handleNext = () => {
    if (currentStep < totalSteps - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleMarkComplete = async () => {
    if (currentStepData && !isStepCompleted) {
      await markStep(currentStepData.key);
      await refresh();
    }
  };

  const handleSkipStep = () => {
    handleNext();
  };

  const handleFinish = async () => {
    setIsCompleting(true);
    await complete();
    setIsCompleting(false);
    onHide();
  };

  const handleDismiss = async () => {
    await dismiss();
    onHide();
  };

  const isLastStep = currentStep === totalSteps - 1;
  const canFinish = progress?.completion_percentage === 100;

  return (
    <Modal show={show} onHide={onHide} size="lg" centered backdrop="static">
      <Modal.Header closeButton>
        <Modal.Title>
          <span className="me-2">🚀</span>
          Bienvenido a tu sistema de citas
        </Modal.Title>
      </Modal.Header>

      <Modal.Body>
        {/* Progress bar */}
        <div className="mb-4">
          <div className="d-flex justify-content-between mb-2">
            <small className="text-muted">
              Paso {currentStep + 1} de {totalSteps}
            </small>
            <small className="text-muted">
              {progressPercentage}% completado
            </small>
          </div>
          <ProgressBar
            now={progressPercentage}
            variant={progressPercentage === 100 ? 'success' : 'primary'}
            style={{ height: '8px' }}
          />
        </div>

        {/* Current step content */}
        {currentStepData && (
          <div className="text-center py-4">
            <div style={{ fontSize: '4rem' }} className="mb-3">
              {currentStepData.icon}
            </div>

            <h4 className="mb-3">
              {currentStepData.title}
              {currentStepData.required && (
                <span className="badge bg-danger ms-2" style={{ fontSize: '0.7rem' }}>
                  Requerido
                </span>
              )}
            </h4>

            <p className="text-muted mb-4" style={{ fontSize: '1.1rem' }}>
              {currentStepData.description}
            </p>

            {isStepCompleted ? (
              <Alert variant="success" className="d-flex align-items-center justify-content-center">
                <span className="me-2">✅</span>
                <strong>Paso completado</strong>
              </Alert>
            ) : (
              <div className="d-grid gap-2">
                {currentStepData.action && (
                  <Button
                    variant="primary"
                    size="lg"
                    onClick={currentStepData.action}
                  >
                    {currentStepData.actionLabel}
                  </Button>
                )}

                <Button
                  variant="outline-success"
                  onClick={handleMarkComplete}
                >
                  ✓ Marcar como completado
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Step indicators */}
        <div className="d-flex justify-content-center gap-2 mt-4">
          {steps.map((step, index) => {
            const isCompleted = progress ? progress[step.key as keyof typeof progress] : false;
            return (
              <div
                key={step.key}
                style={{
                  width: '12px',
                  height: '12px',
                  borderRadius: '50%',
                  backgroundColor:
                    isCompleted ? '#28a745' :
                    index === currentStep ? '#007bff' :
                    '#dee2e6',
                  cursor: 'pointer',
                  transition: 'all 0.3s'
                }}
                onClick={() => setCurrentStep(index)}
                title={step.title}
              />
            );
          })}
        </div>
      </Modal.Body>

      <Modal.Footer className="d-flex justify-content-between">
        <div>
          <Button
            variant="link"
            className="text-muted"
            onClick={handleDismiss}
          >
            Omitir tutorial
          </Button>
        </div>

        <div className="d-flex gap-2">
          <Button
            variant="outline-secondary"
            onClick={handlePrevious}
            disabled={currentStep === 0}
          >
            ← Anterior
          </Button>

          {!currentStepData?.required && !isStepCompleted && (
            <Button
              variant="outline-secondary"
              onClick={handleSkipStep}
            >
              Saltar paso
            </Button>
          )}

          {!isLastStep ? (
            <Button
              variant="primary"
              onClick={handleNext}
            >
              Siguiente →
            </Button>
          ) : (
            <Button
              variant="success"
              onClick={handleFinish}
              disabled={!canFinish || isCompleting}
            >
              {isCompleting ? 'Finalizando...' : '🎉 Finalizar'}
            </Button>
          )}
        </div>
      </Modal.Footer>
    </Modal>
  );
};

export default OnboardingWizard;
