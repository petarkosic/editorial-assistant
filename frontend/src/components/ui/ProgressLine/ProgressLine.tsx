import { useEffect, useState } from 'react';
import styles from './ProgressLine.module.css';

export interface ProgressLineProps {
	messages: string[];
	/** How long each message stays on screen, in ms. */
	intervalMs?: number;
	/** Shuffle the message order once on mount, then cycle through it. */
	randomize?: boolean;
}

function shuffled<T>(items: T[]): T[] {
	const copy = [...items];

	for (let i = copy.length - 1; i > 0; i--) {
		const j = Math.floor(Math.random() * (i + 1));
		[copy[i], copy[j]] = [copy[j], copy[i]];
	}

	return copy;
}

/** Indeterminate progress indicator: a slowly cycling caption with a text shimmer. */
export function ProgressLine({
	messages,
	intervalMs = 3400,
	randomize = true,
}: ProgressLineProps) {
	const [order] = useState(() => (randomize ? shuffled(messages) : messages));
	const [index, setIndex] = useState(0);

	useEffect(() => {
		if (order.length <= 1) return;

		const id = window.setInterval(() => {
			setIndex((i) => (i + 1) % order.length);
		}, intervalMs);

		return () => window.clearInterval(id);
	}, [order.length, intervalMs]);

	return (
		<div className={styles.wrap} role='status'>
			<div className={styles.captions}>
				<span key={index} className={styles.caption}>
					{order[index]}
				</span>
			</div>
		</div>
	);
}
