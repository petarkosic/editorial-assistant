import { useEffect, useRef, useState } from 'react';
import type { ArticleDraft, StoryDetail } from '../api/runs';
import { Badge, Button } from '../components/ui';
import { downloadMarkdown } from '../lib/draftMarkdown';
import {
	useApproveStory,
	useRejectStory,
	useUpdateDraft,
} from '../queries/runs';
import { DraftEditor } from './DraftEditor';
import { scoreTone } from './run-helpers';
import styles from './DraftSection.module.css';

interface DraftSectionProps {
	runId: string;
	storyId: string;
	story: StoryDetail;
	draft: ArticleDraft;
	onDirtyChange?: (dirty: boolean) => void;
}

export function DraftSection({
	runId,
	storyId,
	story,
	draft,
	onDirtyChange,
}: DraftSectionProps) {
	const approve = useApproveStory(runId, storyId);
	const reject = useRejectStory(runId, storyId);
	const update = useUpdateDraft(runId, storyId);
	const [editing, setEditing] = useState(false);
	const [scorecardOpen, setScorecardOpen] = useState(false);
	const wrapRef = useRef<HTMLDivElement>(null);

	// The Edit button sits at the bottom of the draft; without this the panel
	// stays scrolled down and the editor opens with its first fields off-screen.
	useEffect(() => {
		if (editing) {
			wrapRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
		}
	}, [editing]);

	const isApproved = story.status === 'approved';
	const evaluation = story.draft_evaluation;
	const readableSources = (story.research_brief?.sources ?? [])
		.filter((s) => s.fetch_status === 'ok')
		.map((s) => s.url);

	return (
		<div ref={wrapRef} className={styles.wrap}>
			<div className={styles.head}>
				<h3 className={styles.label}>Draft</h3>
				{draft.edited ? <Badge tone='info'>Edited</Badge> : null}
				{isApproved ? <Badge tone='success'>Approved</Badge> : null}
			</div>

			{editing ? (
				<DraftEditor
					draft={draft}
					readableSources={readableSources}
					onDirtyChange={onDirtyChange}
					isSaving={update.isPending}
					error={
						update.isError
							? "Couldn't save the draft. Check that every field is filled in and try again."
							: null
					}
					onSave={(body) =>
						update.mutate(body, { onSuccess: () => setEditing(false) })
					}
					onCancel={() => {
						update.reset();
						setEditing(false);
					}}
				/>
			) : (
				<>
					<article className={styles.article}>
						<h2 className={styles.headline}>{draft.headline}</h2>
						<p className={styles.lede}>{draft.lede}</p>
						{draft.body.map((paragraph, i) => (
							<p key={i}>{paragraph}</p>
						))}

						{draft.key_points.length > 0 ? (
							<>
								<h4 className={styles.subhead}>Key points</h4>
								<ul>
									{draft.key_points.map((point, i) => (
										<li key={i}>{point}</li>
									))}
								</ul>
							</>
						) : null}

						{draft.sources_cited.length > 0 ? (
							<>
								<h4 className={styles.subhead}>Sources</h4>
								<ul className={styles.sourceList}>
									{draft.sources_cited.map((url) => (
										<li key={url}>
											<a href={url} target='_blank' rel='noreferrer'>
												{url}
											</a>
										</li>
									))}
								</ul>
							</>
						) : null}
					</article>

					{evaluation ? (
						<div className={styles.scorecard}>
							<div className={styles.scoreRow}>
								<Badge tone={scoreTone(evaluation.overall_score)}>
									{evaluation.overall_score.toFixed(1)}/5
								</Badge>
								<span className={styles.muted}>
									Draft quality{draft.edited ? ' (scored before your edits)' : ''}
								</span>
								<Button
									variant='ghost'
									size='sm'
									aria-expanded={scorecardOpen}
									onClick={() => setScorecardOpen((v) => !v)}
								>
									{scorecardOpen ? 'Hide scorecard' : 'Show scorecard details'}
								</Button>
							</div>
							{scorecardOpen ? (
								<ul className={styles.reveal}>
									{evaluation.scores.map((s) => (
										<li key={s.criterion}>
											<strong>{s.criterion}</strong>: {s.score}/5 — {s.reasoning}
										</li>
									))}
								</ul>
							) : null}
						</div>
					) : null}

					{!isApproved ? (
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
					) : null}

					<div className={styles.secondaryActions}>
						{!isApproved ? (
							<Button variant='secondary' onClick={() => setEditing(true)}>
								<svg
									width='15'
									height='15'
									viewBox='0 0 24 24'
									fill='none'
									stroke='currentColor'
									strokeWidth='2'
									strokeLinecap='round'
									strokeLinejoin='round'
									aria-hidden='true'
								>
									<path d='M12 20h9' />
									<path d='M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z' />
								</svg>
								Edit draft
							</Button>
						) : null}
						<Button variant='secondary' onClick={() => downloadMarkdown(draft)}>
							<svg
								width='15'
								height='15'
								viewBox='0 0 24 24'
								fill='none'
								stroke='currentColor'
								strokeWidth='2'
								strokeLinecap='round'
								strokeLinejoin='round'
								aria-hidden='true'
							>
								<path d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4' />
								<path d='M7 10l5 5 5-5' />
								<path d='M12 15V3' />
							</svg>
							Download .md
						</Button>
					</div>
				</>
			)}
		</div>
	);
}
