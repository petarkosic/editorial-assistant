import { useOutletContext } from 'react-router-dom';
import { Button } from '../components/ui';
import styles from './RunsIndex.module.css';

interface RunsLayoutContext {
  openNewRun: () => void;
  hasRuns: boolean;
}

export function RunsIndex() {
  const { openNewRun, hasRuns } = useOutletContext<RunsLayoutContext>();

  return (
    <div className={styles.wrap}>
      <div className={styles.icon} aria-hidden="true">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
        </svg>
      </div>
      {hasRuns ? (
        <>
          <h1>No run selected</h1>
          <p>Pick a run from the list, or start a new one with &ldquo;New run&rdquo;.</p>
        </>
      ) : (
        <>
          <h1>No runs yet</h1>
          <p>Start a run to have the scout find today&rsquo;s important stories.</p>
          <Button onClick={openNewRun} className={styles.cta}>
            New run
          </Button>
        </>
      )}
    </div>
  );
}
