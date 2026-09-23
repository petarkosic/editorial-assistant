import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useDeleteRun, useRun, useSelectStories } from '../queries/runs';
import { Badge, Button, ProgressLine } from '../components/ui';
import { findingTitle, runLabel, scoreTone, statusTone } from './run-helpers';
import { StoryPanel } from './StoryPanel';
import styles from './RunDetail.module.css';

export function RunDetail() {
  const { id } = useParams<{ id: string }>();
  return <RunDetailForRun key={id} id={id} />;
}

function RunDetailForRun({ id }: { id: string | undefined }) {
  const { data: run, isLoading, isError } = useRun(id);
  const deleteRun = useDeleteRun();
  const selectStories = useSelectStories(id!);
  const navigate = useNavigate();
  const [scoreOpen, setScoreOpen] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [selectedStoryId, setSelectedStoryId] = useState<string | null>(null);

  if (isLoading) return <p role="status" className={styles.status}>Loading run…</p>;
  if (isError || !run) return <p role="alert" className={styles.status}>Could not load this run.</p>;

  const analysed = run.scout_report?.analyzed_articles ?? 0;
  const found = run.stories.length;
  const evaluation = run.scout_evaluation;

  const handleDelete = async () => {
    await deleteRun.mutateAsync(run.id);
    navigate('/');
  };

  function toggleSelected(storyId: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(storyId)) next.delete(storyId);
      else next.add(storyId);
      return next;
    });
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1>{runLabel(run)}</h1>
        <Badge tone={statusTone(run.status)}>{run.status}</Badge>
      </div>

      {run.status === 'scouting' ? (
        <div className={styles.status}>
          <ProgressLine
            messages={[
              'Scanning today’s headlines…',
              'Filtering for what matters…',
              'Weighing the shortlist…',
            ]}
          />
        </div>
      ) : null}
      {run.status === 'failed' && run.error ? (
        <p role="alert" className={styles.alert}>Scout failed: {run.error}</p>
      ) : null}

      <p className={styles.summary}>
        Analysed {analysed} {analysed === 1 ? 'article' : 'articles'} · {found}{' '}
        {found === 1 ? 'story' : 'stories'} found
      </p>

      {evaluation ? (
        <div className={styles.qualityBlock}>
          <button
            type="button"
            className={styles.scoreToggle}
            aria-expanded={scoreOpen}
            onClick={() => setScoreOpen((v) => !v)}
          >
            <span>Scout quality</span>
            <Badge tone={scoreTone(evaluation.overall_score)}>
              {evaluation.overall_score.toFixed(1)}/5
            </Badge>
            <svg
              className={styles.chevron}
              data-open={scoreOpen}
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M6 9l6 6 6-6" />
            </svg>
          </button>
          {scoreOpen ? (
            <div className={styles.scorecard}>
              <p className={styles.scorecardIntro}>
                Judges the scout's filtering across all {analysed} analysed
                articles, including which it correctly kept or excluded — its
                reasoning may reference articles that aren't in the story list
                below.
              </p>
              <ul>
                {evaluation.scores.map((s) => (
                  <li key={s.criterion}>
                    <strong>{s.criterion}</strong>: {s.score}/5 — {s.reasoning}
                  </li>
                ))}
              </ul>
              {evaluation.strengths.length > 0 ? (
                <p><strong>Strengths:</strong> {evaluation.strengths.join('; ')}</p>
              ) : null}
              {evaluation.weaknesses.length > 0 ? (
                <p><strong>Weaknesses:</strong> {evaluation.weaknesses.join('; ')}</p>
              ) : null}
              {evaluation.suggestions ? (
                <p><strong>Suggestions:</strong> {evaluation.suggestions}</p>
              ) : null}
            </div>
          ) : null}
        </div>
      ) : null}

      {run.status === 'scouting' ? null : found === 0 ? (
        <div className={styles.empty}>
          <p>No important stories in this run.</p>
          <Button variant="danger" onClick={handleDelete} isLoading={deleteRun.isPending}>
            Delete run
          </Button>
        </div>
      ) : (
        <div className={styles.layout} data-has-selection={selectedStoryId ? 'true' : 'false'}>
          <div className={styles.storiesPane}>
            {run.stories.some((s) => s.status === 'pending') ? (
              <div className={styles.bulkBar}>
                <span className={styles.bulkCount}>
                  <strong>{selectedIds.size}</strong> selected
                </span>
                <Button
                  size="sm"
                  disabled={selectedIds.size === 0 || selectStories.isPending}
                  isLoading={selectStories.isPending}
                  onClick={() =>
                    selectStories.mutate([...selectedIds], {
                      onSuccess: () => setSelectedIds(new Set()),
                    })
                  }
                >
                  Research {selectedIds.size} selected
                </Button>
              </div>
            ) : null}

            <ul className={styles.stories}>
              {run.stories.map((story) => (
                <li key={story.id} className={styles.storyRow}>
                  {story.status === 'pending' ? (
                    <input
                      type="checkbox"
                      className={styles.checkbox}
                      aria-label={findingTitle(story.finding)}
                      checked={selectedIds.has(story.id)}
                      onChange={() => toggleSelected(story.id)}
                    />
                  ) : (
                    <span className={styles.checkboxSpacer} aria-hidden="true" />
                  )}
                  <button
                    type="button"
                    className={styles.storyButton}
                    data-active={story.id === selectedStoryId}
                    onClick={() => setSelectedStoryId(story.id)}
                  >
                    <span
                      className={styles.storyTitle}
                      data-rejected={story.status === 'rejected'}
                    >
                      {findingTitle(story.finding)}
                    </span>
                    <Badge tone={statusTone(story.status)}>{story.status}</Badge>
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <aside className={styles.rightPanel}>
            {selectedStoryId ? (
              <>
                <button
                  type="button"
                  className={styles.backButton}
                  onClick={() => setSelectedStoryId(null)}
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M15 18l-6-6 6-6" />
                  </svg>
                  Stories
                </button>
                <StoryPanel runId={id!} storyId={selectedStoryId} />
              </>
            ) : (
              <p className={styles.pickHint}>Select a story to review it.</p>
            )}
          </aside>
        </div>
      )}
    </div>
  );
}
