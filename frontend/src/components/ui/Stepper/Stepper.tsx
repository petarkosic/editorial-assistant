import styles from './Stepper.module.css';

export interface StepperStep {
  id: string;
  label: string;
}

export interface StepperProps {
  steps: StepperStep[];
  currentStepId: string;
}

export function Stepper({ steps, currentStepId }: StepperProps) {
  const currentIndex = steps.findIndex((s) => s.id === currentStepId);
  return (
    <ol className={styles.list}>
      {steps.map((step, index) => {
        const isCurrent = step.id === currentStepId;
        const isComplete = currentIndex >= 0 && index < currentIndex;
        return (
          <li
            key={step.id}
            className={styles.step}
            aria-current={isCurrent ? 'step' : undefined}
            data-complete={isComplete ? 'true' : undefined}
          >
            <span className={styles.dot} aria-hidden="true">
              {isComplete ? '✓' : index + 1}
            </span>
            {step.label}
          </li>
        );
      })}
    </ol>
  );
}
