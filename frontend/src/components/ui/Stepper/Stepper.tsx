import styles from './Stepper.module.css';

export interface StepperStep {
  id: string;
  label: string;
}

export interface StepperProps {
  steps: StepperStep[];
  currentStepId: string;
  /** 'success': every step is done. 'danger': the current step failed or was rejected. */
  outcome?: 'success' | 'danger';
}

export function Stepper({ steps, currentStepId, outcome }: StepperProps) {
  const currentIndex = steps.findIndex((s) => s.id === currentStepId);
  return (
    <ol className={styles.list}>
      {steps.map((step, index) => {
        const isCurrent = step.id === currentStepId;
        const isComplete =
          outcome === 'success' || (currentIndex >= 0 && index < currentIndex);
        const isFailed = outcome === 'danger' && isCurrent;
        return (
          <li
            key={step.id}
            className={styles.step}
            aria-current={isCurrent ? 'step' : undefined}
            data-complete={isComplete ? 'true' : undefined}
            data-outcome={outcome === 'success' ? 'success' : isFailed ? 'danger' : undefined}
          >
            <span className={styles.dot} aria-hidden="true">
              {isComplete ? '✓' : isFailed ? '✕' : index + 1}
            </span>
            {step.label}
          </li>
        );
      })}
    </ol>
  );
}
