import {
	useEffect,
	useLayoutEffect,
	useRef,
	useState,
	type TextareaHTMLAttributes,
} from 'react';
import type { ArticleDraft, UpdateDraftBody } from '../api/runs';
import { Button, Field } from '../components/ui';
import styles from './DraftSection.module.css';

interface DraftEditorProps {
	draft: ArticleDraft;
	readableSources: string[];
	isSaving: boolean;
	error: string | null;
	onSave: (body: UpdateDraftBody) => void;
	onCancel: () => void;
	onDirtyChange?: (dirty: boolean) => void;
}

function sameList(a: string[], b: string[]): boolean {
	return a.length === b.length && a.every((value, i) => value === b[i]);
}

function sameSet(a: Set<string>, b: string[]): boolean {
	return a.size === b.length && b.every((value) => a.has(value));
}

function moveItem(list: string[], from: number, to: number): string[] {
	if (to < 0 || to >= list.length) return list;

	const next = [...list];
	[next[from], next[to]] = [next[to], next[from]];

	return next;
}

type TextareaSize = 'sm' | 'md' | 'lg';

interface AutoTextareaProps extends Omit<
	TextareaHTMLAttributes<HTMLTextAreaElement>,
	'value'
> {
	value: string;
	size: TextareaSize;
}

function AutoTextarea({ value, size, className, ...rest }: AutoTextareaProps) {
	const ref = useRef<HTMLTextAreaElement>(null);

	useLayoutEffect(() => {
		const el = ref.current;
		if (!el) return;

		el.style.height = 'auto';
		el.style.height = `${el.scrollHeight + (el.offsetHeight - el.clientHeight)}px`;
	}, [value]);

	return (
		<textarea
			ref={ref}
			value={value}
			className={`${styles.textarea} ${styles[size]} ${className ?? ''}`}
			{...rest}
		/>
	);
}

interface StringListEditorProps {
	id: string;
	label: string;
	items: string[];
	addLabel: string;
	onChange: (items: string[]) => void;
}

function StringListEditor({
	id,
	label,
	items,
	addLabel,
	onChange,
}: StringListEditorProps) {
	// Index of the row whose delete button was clicked once and is waiting for
	// a second click.
	const [armedIndex, setArmedIndex] = useState<number | null>(null);

	useEffect(() => {
		if (armedIndex === null) return;

		const timer = window.setTimeout(() => setArmedIndex(null), 3000);

		return () => window.clearTimeout(timer);
	}, [armedIndex]);

	const setItem = (index: number, value: string) =>
		onChange(items.map((item, i) => (i === index ? value : item)));

	const noun = label.toLowerCase();

	return (
		<fieldset className={styles.listGroup}>
			<legend className={styles.legend}>{label}s</legend>

			{items.map((item, i) => (
				<div key={i} className={styles.listItem}>
					<div className={styles.listRow}>
						{/* Fixed height, not auto-grow, so every row looks the same. */}
						<textarea
							id={`${id}-${i}`}
							aria-label={`${label} ${i + 1}`}
							className={`${styles.textarea} ${styles.row}`}
							value={item}
							onChange={(e) => setItem(i, e.target.value)}
						/>

						<div className={styles.rowActions}>
							<Button
								variant={armedIndex === i ? 'danger' : 'secondary'}
								size='sm'
								title={
									armedIndex === i
										? `Click again to delete this ${noun}`
										: `Delete ${noun}`
								}
								aria-label={`Delete ${label} ${i + 1}`}
								onBlur={() => setArmedIndex(null)}
								onClick={() => {
									if (armedIndex === i) {
										setArmedIndex(null);
										onChange(items.filter((_, idx) => idx !== i));
									} else {
										setArmedIndex(i);
									}
								}}
							>
								×
							</Button>
							<Button
								variant='secondary'
								size='sm'
								title={`Move ${noun} up`}
								aria-label={`Move ${label} ${i + 1} up`}
								disabled={i === 0}
								onClick={() => onChange(moveItem(items, i, i - 1))}
							>
								↑
							</Button>
							<Button
								variant='secondary'
								size='sm'
								title={`Move ${noun} down`}
								aria-label={`Move ${label} ${i + 1} down`}
								disabled={i === items.length - 1}
								onClick={() => onChange(moveItem(items, i, i + 1))}
							>
								↓
							</Button>
						</div>
					</div>

					{armedIndex === i ? (
						<p role='status' className={styles.deleteHint}>
							Click delete again to remove this {noun}.
						</p>
					) : null}
				</div>
			))}

			<Button
				variant='secondary'
				size='sm'
				onClick={() => onChange([...items, ''])}
			>
				{addLabel}
			</Button>
		</fieldset>
	);
}

export function DraftEditor({
	draft,
	readableSources,
	isSaving,
	error,
	onSave,
	onCancel,
	onDirtyChange,
}: DraftEditorProps) {
	const [headline, setHeadline] = useState(draft.headline);
	const [lede, setLede] = useState(draft.lede);
	const [body, setBody] = useState(draft.body);
	const [keyPoints, setKeyPoints] = useState(draft.key_points);
	const [cited, setCited] = useState(() => new Set(draft.sources_cited));

	const dirty =
		headline !== draft.headline ||
		lede !== draft.lede ||
		!sameList(body, draft.body) ||
		!sameList(keyPoints, draft.key_points) ||
		!sameSet(cited, draft.sources_cited);

	useEffect(() => {
		onDirtyChange?.(dirty);
	}, [dirty, onDirtyChange]);

	// Leaving edit mode (save, cancel, or the panel going away) is never "dirty".
	useEffect(() => () => onDirtyChange?.(false), [onDirtyChange]);

	const cleanBody = body.map((p) => p.trim()).filter(Boolean);
	const canSave =
		headline.trim() !== '' && lede.trim() !== '' && cleanBody.length > 0;

	const toggleSource = (url: string) =>
		setCited((prev) => {
			const next = new Set(prev);
			if (next.has(url)) next.delete(url);
			else next.add(url);

			return next;
		});

	const handleSave = () =>
		onSave({
			headline: headline.trim(),
			lede: lede.trim(),
			body: cleanBody,
			key_points: keyPoints.map((p) => p.trim()).filter(Boolean),
			sources_cited: readableSources.filter((url) => cited.has(url)),
		});

	return (
		<div className={styles.editor}>
			<Field label='Headline' htmlFor='draft-headline'>
				<AutoTextarea
					id='draft-headline'
					size='sm'
					value={headline}
					onChange={(e) => setHeadline(e.target.value)}
				/>
			</Field>

			<Field label='Lede' htmlFor='draft-lede'>
				<AutoTextarea
					id='draft-lede'
					size='md'
					value={lede}
					onChange={(e) => setLede(e.target.value)}
				/>
			</Field>

			<StringListEditor
				id='draft-key-point'
				label='Key point'
				items={keyPoints}
				addLabel='Add key point'
				onChange={setKeyPoints}
			/>

			<fieldset className={styles.listGroup}>
				<legend className={styles.legend}>Sources cited</legend>
				{readableSources.length === 0 ? (
					<p className={styles.muted}>No sources were read for this story.</p>
				) : (
					readableSources.map((url, i) => (
						<label
							key={url}
							className={styles.sourceChoice}
							htmlFor={`draft-source-${i}`}
						>
							<input
								id={`draft-source-${i}`}
								type='checkbox'
								checked={cited.has(url)}
								onChange={() => toggleSource(url)}
							/>
							<span>{url}</span>
						</label>
					))
				)}
			</fieldset>

			<StringListEditor
				id='draft-body'
				label='Paragraph'
				items={body}
				addLabel='Add paragraph'
				onChange={setBody}
			/>

			{error ? (
				<p role='alert' className={styles.error}>
					{error}
				</p>
			) : null}

			<div className={styles.actions}>
				<Button onClick={handleSave} isLoading={isSaving} disabled={!canSave}>
					Save changes
				</Button>
				<Button variant='secondary' onClick={onCancel} disabled={isSaving}>
					Cancel
				</Button>
			</div>
		</div>
	);
}
