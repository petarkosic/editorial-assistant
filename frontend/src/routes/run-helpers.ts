import type { BadgeProps } from '../components/ui';

export function runLabel(run: {
	source_kind: string;
	source_query: string | null;
}): string {
	if (run.source_kind === 'top_stories') return 'Top stories';
	if (run.source_kind === 'category')
		return `Category: ${run.source_query ?? ''}`.trim();

	return `Search: ${run.source_query ?? ''}`.trim();
}

export function findingTitle(finding: { original_title?: unknown }): string {
	const title = finding.original_title;

	return typeof title === 'string' && title.trim() !== ''
		? title
		: 'Untitled story';
}

type Tone = NonNullable<BadgeProps['tone']>;

export function statusTone(status: string): Tone {
	if (status === 'failed' || status === 'rejected') return 'danger';
	if (status === 'done' || status === 'approved') return 'success';
	if (
		status === 'scouting' ||
		status === 'in_progress' ||
		status === 'researching' ||
		status === 'synthesizing'
	) {
		return 'info';
	}
	if (
		status === 'research_ready' ||
		status === 'draft_ready' ||
		status === 'selecting'
	)
		return 'warning';

	return 'neutral';
}

export function scoreTone(score: number): 'success' | 'warning' | 'danger' {
	if (score >= 4) return 'success';
	if (score >= 3) return 'warning';

	return 'danger';
}
