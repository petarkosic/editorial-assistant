import styles from './ProgressLine.module.css';

export interface ProgressLineProps {
	messages: [string, string, string];
}

/** Indeterminate progress indicator: a sweeping bar plus CSS-only cycling captions. */
export function ProgressLine({ messages }: ProgressLineProps) {
	return (
		<div className={styles.wrap} role='status'>
			<div className={styles.bar}>
				<div className={styles.sweep} />
			</div>
			<div className={styles.captions}>
				{messages.map((message, i) => (
					<span
						key={message}
						className={styles.caption}
						style={{ animationDelay: `${i * 2.6}s` }}
					>
						{message}
					</span>
				))}
			</div>
		</div>
	);
}
