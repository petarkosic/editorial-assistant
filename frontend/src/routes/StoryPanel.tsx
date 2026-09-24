import { useState } from 'react';
import {
	Badge,
	Button,
	ProgressLine,
	Stepper,
	type StepperStep,
} from '../components/ui';
import {
	useApproveStory,
	useRejectStory,
	useRetryStory,
	useSelectStories,
	useStory,
} from '../queries/runs';
import {
	RESEARCHING_MESSAGES,
	SYNTHESIZING_MESSAGES,
} from '../lib/progressMessages';
import { findingTitle, scoreTone } from './run-helpers';
import styles from './StoryPanel.module.css';

const STEPS: StepperStep[] = [
	{ id: 'scout', label: 'Scout' },
	{ id: 'research', label: 'Research' },
	{ id: 'synthesis', label: 'Synthesis' },
];

function currentStepId(status: string): string {
	if (status === 'pending') return 'scout';
	if (
		status === 'synthesizing' ||
		status === 'draft_ready' ||
		status === 'approved'
	) {
		return 'synthesis';
	}
	return 'research';
}

export function StoryPanel({
	runId,
	storyId,
}: {
	runId: string;
	storyId: string;
}) {
	const { data: story, isLoading } = useStory(runId, storyId);
	const approve = useApproveStory(runId, storyId);
	const reject = useRejectStory(runId, storyId);
	const retry = useRetryStory(runId, storyId);
	const selectOne = useSelectStories(runId);
	const [scorecardOpen, setScorecardOpen] = useState(false);

	if (isLoading || !story) {
		return <div className={styles.panel}>Loading…</div>;
	}

	return (
		<div className={styles.panel}>
			<Stepper steps={STEPS} currentStepId={currentStepId(story.status)} />

			<section>
				<h2 className={styles.title}>{findingTitle(story.finding)}</h2>
				<p className={styles.summaryText}>{story.finding.summary}</p>
				{story.finding.reasoning ? (
					<p className={styles.reasoning}>{story.finding.reasoning}</p>
				) : null}
				<a
					className={styles.sourceLink}
					href={story.finding.original_link}
					target='_blank'
					rel='noreferrer'
				>
					Read the original article
					<svg
						width='11'
						height='11'
						viewBox='0 0 24 24'
						fill='none'
						stroke='currentColor'
						strokeWidth='2.5'
						strokeLinecap='round'
						strokeLinejoin='round'
					>
						<path d='M7 17L17 7M7 7h10v10' />
					</svg>
				</a>
			</section>

			{story.status === 'pending' && (
				<div>
					<Button
						onClick={() => selectOne.mutate([storyId])}
						isLoading={selectOne.isPending}
					>
						Research this story
					</Button>
				</div>
			)}

			{story.status === 'researching' && (
				<ProgressLine messages={RESEARCHING_MESSAGES} />
			)}

			{story.status === 'failed' && (
				<div>
					<p role='alert'>{story.error}</p>
					<Button onClick={() => retry.mutate()} isLoading={retry.isPending}>
						Retry
					</Button>
				</div>
			)}

			{story.status === 'research_ready' && story.research_brief && (
				<>
					<section>
						<h3>Background</h3>
						<p>{story.research_brief.background}</p>
					</section>

					<section>
						<h3>Key facts</h3>
						<ul>
							{story.research_brief.key_facts.map((fact, i) => (
								<li key={i}>{fact}</li>
							))}
						</ul>
					</section>

					<section>
						<h3>Open questions</h3>
						<ul>
							{story.research_brief.open_questions.map((q, i) => (
								<li key={i}>{q}</li>
							))}
						</ul>
					</section>

					{story.research_brief.fact_check_flags.length > 0 && (
						<section>
							<h3>Fact-check flags</h3>
							{story.research_brief.fact_check_flags.map((flag, i) => (
								<div key={i} className={styles.flag}>
									<svg
										width='15'
										height='15'
										viewBox='0 0 24 24'
										fill='none'
										stroke='currentColor'
										strokeWidth='2.5'
										strokeLinecap='round'
										strokeLinejoin='round'
										className={styles.flagIcon}
									>
										<path d='M12 9v4M12 17h.01M10.29 3.86l-8.18 14.14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.89-2.99L13.71 3.86a2 2 0 0 0-3.42 0z' />
									</svg>
									<span>{flag}</span>
								</div>
							))}
						</section>
					)}

					<section>
						<h3>Sources</h3>
						{story.research_brief.sources.map((source) => (
							<div key={source.url} className={styles.sourceRow}>
								<span>{source.url}</span>
								<Badge
									tone={source.fetch_status === 'ok' ? 'success' : 'warning'}
								>
									{source.fetch_status}
								</Badge>
							</div>
						))}
					</section>

					{story.research_evaluation && (
						<section>
							<div className={styles.scoreRow}>
								<Badge
									tone={scoreTone(story.research_evaluation.overall_score)}
								>
									{story.research_evaluation.overall_score.toFixed(1)}/5
								</Badge>
								<Button
									variant='ghost'
									size='sm'
									aria-expanded={scorecardOpen}
									onClick={() => setScorecardOpen((v) => !v)}
								>
									{scorecardOpen ? 'Hide scorecard' : 'Show scorecard details'}
								</Button>
							</div>
							{scorecardOpen && (
								<ul className={styles.reveal}>
									{story.research_evaluation.scores.map((s) => (
										<li key={s.criterion}>
											<strong>{s.criterion}</strong>: {s.score}/5 —{' '}
											{s.reasoning}
										</li>
									))}
								</ul>
							)}
						</section>
					)}

					<div className={styles.actions}>
						<Button
							onClick={() => approve.mutate()}
							isLoading={approve.isPending}
						>
							Approve
						</Button>
						<Button
							variant='secondary'
							onClick={() => reject.mutate()}
							isLoading={reject.isPending}
						>
							Reject
						</Button>
					</div>
				</>
			)}

			{story.status === 'synthesizing' && (
				<ProgressLine messages={SYNTHESIZING_MESSAGES} />
			)}

			{['rejected', 'draft_ready', 'approved'].includes(story.status) && (
				<p>Status: {story.status}</p>
			)}
		</div>
	);
}
