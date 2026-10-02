import type { ArticleDraft } from '../api/runs';

export function draftToMarkdown(draft: ArticleDraft): string {
	const parts = [`# ${draft.headline}`, `**${draft.lede}**`, ...draft.body];

	if (draft.key_points.length > 0) {
		parts.push('## Key points', draft.key_points.map((p) => `- ${p}`).join('\n'));
	}

	if (draft.sources_cited.length > 0) {
		parts.push('## Sources', draft.sources_cited.map((u) => `- ${u}`).join('\n'));
	}

	return `${parts.join('\n\n')}\n`;
}

export function draftFilename(draft: ArticleDraft): string {
	const slug = draft.headline
		.toLowerCase()
		.replace(/[^a-z0-9]+/g, '-')
		.replace(/^-+|-+$/g, '')
		.slice(0, 60);

	return `${slug || 'article'}.md`;
}

export function downloadMarkdown(draft: ArticleDraft): void {
	const url = URL.createObjectURL(
		new Blob([draftToMarkdown(draft)], { type: 'text/markdown;charset=utf-8' }),
	);
	const link = document.createElement('a');
	link.href = url;
	link.download = draftFilename(draft);
	link.click();
	URL.revokeObjectURL(url);
}
