import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { useRuns } from '../queries/runs';
import { relativeTime } from '../lib/relativeTime';
import { Button } from '../components/ui';
import { NewRunDialog } from './NewRunDialog';
import { runLabel, statusTone } from './run-helpers';
import styles from './RunsLayout.module.css';

export function RunsLayout() {
	const { data: runs, isLoading } = useRuns();
	const [dialogOpen, setDialogOpen] = useState(false);

	return (
		<div className={styles.layout}>
			<aside className={styles.rail}>
				<div className={styles.railHead}>
					<h2>Runs</h2>
					<Button size='sm' onClick={() => setDialogOpen(true)}>
						New run
					</Button>
				</div>

				{isLoading ? (
					<p className={styles.empty}>Loading…</p>
				) : (runs ?? []).length === 0 ? (
					<p className={styles.empty}>No runs yet.</p>
				) : (
					<ul className={styles.list}>
						{(runs ?? []).map((run) => (
							<li key={run.id}>
								<NavLink
									to={`/runs/${run.id}`}
									className={({ isActive }) =>
										`${styles.link} ${isActive ? styles.linkActive : ''}`
									}
								>
									<span
										className={styles.dot}
										data-tone={statusTone(run.status)}
										aria-hidden='true'
									/>
									<span className={styles.meta}>
										<span>{runLabel(run)}</span>
										<span className={styles.time}>
											{relativeTime(run.created_at)}
										</span>
									</span>
								</NavLink>
							</li>
						))}
					</ul>
				)}
			</aside>

			<section>
				<Outlet />
			</section>

			<NewRunDialog open={dialogOpen} onOpenChange={setDialogOpen} />
		</div>
	);
}
