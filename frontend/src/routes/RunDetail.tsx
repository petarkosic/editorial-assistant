import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useDeleteRun, useRun } from '../queries/runs';
import { Badge, Button } from '../components/ui';
import { findingTitle, runLabel, scoreTone, statusTone } from './run-helpers';
import styles from './RunDetail.module.css';

export function RunDetail() {
	const { id } = useParams<{ id: string }>();
	const { data: run, isLoading, isError } = useRun(id);
	const deleteRun = useDeleteRun();
	const navigate = useNavigate();
	const [scoreOpen, setScoreOpen] = useState(false);

	if (isLoading) return <p role='status'>Loading run…</p>;
	if (isError || !run) return <p role='alert'>Could not load this run.</p>;

	const analysed = run.scout_report?.analyzed_articles ?? 0;
	const found = run.stories.length;
	const evaluation = run.scout_evaluation;

	const handleDelete = async () => {
		await deleteRun.mutateAsync(run.id);
		navigate('/');
	};

	return (
		<div>
			<div className={styles.header}>
				<h1>{runLabel(run)}</h1>
				<Badge tone={statusTone(run.status)}>{run.status}</Badge>
			</div>

			{run.status === 'scouting' ? (
				<p role='status'>Scouting in progress…</p>
			) : null}
			{run.status === 'failed' && run.error ? (
				<p role='alert'>Scout failed: {run.error}</p>
			) : null}

			<p className={styles.summary}>
				Analysed {analysed} {analysed === 1 ? 'article' : 'articles'} · {found}{' '}
				{found === 1 ? 'story' : 'stories'} found
			</p>

			{evaluation ? (
				<div>
					<button
						type='button'
						className={styles.scoreToggle}
						aria-expanded={scoreOpen}
						onClick={() => setScoreOpen((v) => !v)}
					>
						Scout quality
						<Badge tone={scoreTone(evaluation.overall_score)}>
							{evaluation.overall_score.toFixed(1)}/5
						</Badge>
					</button>
					{scoreOpen ? (
						<div className={styles.scorecard}>
							<ul>
								{evaluation.scores.map((s) => (
									<li key={s.criterion}>
										<strong>{s.criterion}</strong>: {s.score}/5 — {s.reasoning}
									</li>
								))}
							</ul>
							{evaluation.strengths.length > 0 ? (
								<p>
									<strong>Strengths:</strong> {evaluation.strengths.join('; ')}
								</p>
							) : null}
							{evaluation.weaknesses.length > 0 ? (
								<p>
									<strong>Weaknesses:</strong>{' '}
									{evaluation.weaknesses.join('; ')}
								</p>
							) : null}
							{evaluation.suggestions ? (
								<p>
									<strong>Suggestions:</strong> {evaluation.suggestions}
								</p>
							) : null}
						</div>
					) : null}
				</div>
			) : null}

			{found === 0 ? (
				<div className={styles.empty}>
					<p>No important stories in this run.</p>
					<Button
						variant='danger'
						onClick={handleDelete}
						isLoading={deleteRun.isPending}
					>
						Delete run
					</Button>
				</div>
			) : (
				<ul className={styles.stories}>
					{run.stories.map((story) => (
						<li key={story.id}>
							<button type='button' className={styles.storyButton}>
								<span>{findingTitle(story.finding)}</span>
								<Badge tone={statusTone(story.status)}>{story.status}</Badge>
							</button>
						</li>
					))}
				</ul>
			)}
		</div>
	);
}
