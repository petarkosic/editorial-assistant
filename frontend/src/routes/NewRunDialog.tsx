import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { ApiError } from '../api/types';
import { useCreateRun } from '../queries/runs';
import { Button, Dialog, Field } from '../components/ui';
import styles from './NewRunDialog.module.css';

export const NEWS_CATEGORIES = [
	'WORLD',
	'NATION',
	'BUSINESS',
	'TECHNOLOGY',
	'ENTERTAINMENT',
	'SPORTS',
	'SCIENCE',
	'HEALTH',
] as const;

type Kind = 'top_stories' | 'category' | 'search';

interface Props {
	open: boolean;
	onOpenChange: (open: boolean) => void;
}

export function NewRunDialog({ open, onOpenChange }: Props) {
	const navigate = useNavigate();
	const createRun = useCreateRun();
	const [kind, setKind] = useState<Kind>('top_stories');
	const [category, setCategory] = useState<string>(NEWS_CATEGORIES[0]);
	const [term, setTerm] = useState('');
	const [error, setError] = useState<string | null>(null);

	const reset = () => {
		setKind('top_stories');
		setCategory(NEWS_CATEGORIES[0]);
		setTerm('');
		setError(null);
	};

	const handleOpenChange = (next: boolean) => {
		if (!next) reset();
		onOpenChange(next);
	};

	const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
		event.preventDefault();
		setError(null);

		let sourceQuery: string | null;
		if (kind === 'top_stories') {
			sourceQuery = null;
		} else if (kind === 'category') {
			sourceQuery = category;
		} else {
			sourceQuery = term.trim();
			if (!sourceQuery) {
				setError('Enter a search term');
				return;
			}
		}

		try {
			const run = await createRun.mutateAsync({
				source_kind: kind,
				source_query: sourceQuery,
			});
			handleOpenChange(false);
			navigate(`/runs/${run.id}`);
		} catch (err) {
			setError(
				err instanceof ApiError && typeof err.detail === 'string'
					? err.detail
					: 'Could not start the run. Try again.',
			);
		}
	};

	return (
		<Dialog
			open={open}
			onOpenChange={handleOpenChange}
			title='New run'
			description='Pick a source for the scout.'
		>
			<form className={styles.form} onSubmit={handleSubmit}>
				<div className={styles.choices} role='radiogroup' aria-label='Source'>
					<label className={styles.choice}>
						<input
							type='radio'
							name='source'
							checked={kind === 'top_stories'}
							onChange={() => setKind('top_stories')}
						/>
						<span className={styles.choiceText}>
							<span className={styles.choiceLabel}>Top stories</span>
							<span className={styles.choiceHint}>Whatever's leading right now</span>
						</span>
					</label>
					<label className={styles.choice}>
						<input
							type='radio'
							name='source'
							checked={kind === 'category'}
							onChange={() => setKind('category')}
						/>
						<span className={styles.choiceText}>
							<span className={styles.choiceLabel}>Category</span>
							<span className={styles.choiceHint}>World, business, tech, and more</span>
						</span>
					</label>
					<label className={styles.choice}>
						<input
							type='radio'
							name='source'
							checked={kind === 'search'}
							onChange={() => setKind('search')}
						/>
						<span className={styles.choiceText}>
							<span className={styles.choiceLabel}>Search</span>
							<span className={styles.choiceHint}>Scout a specific term</span>
						</span>
					</label>
				</div>

				{kind === 'category' ? (
					<Field label='Category' htmlFor='run-category'>
						<select
							id='run-category'
							className={styles.select}
							value={category}
							onChange={(e) => setCategory(e.target.value)}
						>
							{NEWS_CATEGORIES.map((c) => (
								<option key={c} value={c}>
									{c[0] + c.slice(1).toLowerCase()}
								</option>
							))}
						</select>
					</Field>
				) : null}

				{kind === 'search' ? (
					<Field label='Search term' htmlFor='run-term'>
						<input
							id='run-term'
							type='text'
							className={styles.input}
							value={term}
							onChange={(e) => setTerm(e.target.value)}
							placeholder='e.g. semiconductor export controls'
						/>
					</Field>
				) : null}

				{error ? (
					<div className={styles.error} role='alert'>
						{error}
					</div>
				) : null}

				<div className={styles.actions}>
					<Button type='submit' isLoading={createRun.isPending}>
						Start run
					</Button>
				</div>
			</form>
		</Dialog>
	);
}
