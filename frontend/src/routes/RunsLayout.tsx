import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { useRuns } from '../queries/runs';
import { relativeTime } from '../lib/relativeTime';
import { useMediaQuery } from '../hooks/useMediaQuery';
import { Button } from '../components/ui';
import { NewRunDialog } from './NewRunDialog';
import { runLabel, statusTone } from './run-helpers';
import styles from './RunsLayout.module.css';

const MOBILE_QUERY = '(max-width: 860px)';

export function RunsLayout() {
	const { data: runs, isLoading } = useRuns();
	const [dialogOpen, setDialogOpen] = useState(false);
	const [railOpen, setRailOpen] = useState(false);
	const [collapsed, setCollapsed] = useState(false);
	const isMobile = useMediaQuery(MOBILE_QUERY);
	const showMini = collapsed && !isMobile;

	const openNewRun = () => {
		setDialogOpen(true);
		setRailOpen(false);
	};

	return (
		<div className={styles.layout}>
			<div className={styles.topbar}>
				<button
					type="button"
					className={styles.menuButton}
					aria-label="Toggle runs menu"
					aria-expanded={railOpen}
					onClick={() => setRailOpen((v) => !v)}
				>
					<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
						<path d="M4 7h16M4 12h16M4 17h16" />
					</svg>
				</button>
				<span className={styles.topbarBrand}>Editorial Assistant</span>
			</div>

			{railOpen ? (
				<button
					type="button"
					className={styles.backdrop}
					aria-label="Close runs menu"
					onClick={() => setRailOpen(false)}
				/>
			) : null}

			<aside className={styles.rail} data-open={railOpen} data-collapsed={showMini}>
				{showMini ? (
					<div className={styles.railMini}>
						<span className={styles.mark} aria-hidden="true">
							<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
								<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
								<path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
							</svg>
						</span>

						<button
							type="button"
							className={styles.railToggle}
							aria-label="Expand runs sidebar"
							onClick={() => setCollapsed(false)}
						>
							<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
								<path d="M9 6l6 6-6 6" />
							</svg>
						</button>

						<button
							type="button"
							className={styles.miniNewRun}
							aria-label="New run"
							onClick={openNewRun}
						>
							<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
								<path d="M12 5v14M5 12h14" />
							</svg>
						</button>

						<div className={styles.miniDivider} />

						<div className={styles.miniList}>
							{(runs ?? []).map((run) => (
								<NavLink
									key={run.id}
									to={`/runs/${run.id}`}
									title={runLabel(run)}
									onClick={() => setRailOpen(false)}
									className={({ isActive }) =>
										`${styles.miniLink} ${isActive ? styles.linkActive : ''}`
									}
								>
									<span
										className={styles.dot}
										data-tone={statusTone(run.status)}
										aria-hidden="true"
									/>
								</NavLink>
							))}
						</div>
					</div>
				) : (
					<div className={styles.railInner}>
						<div className={styles.brandRow}>
							<span className={styles.mark} aria-hidden="true">
								<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
									<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
									<path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
								</svg>
							</span>
							<span className={styles.brand}>Editorial Assistant</span>
							<button
								type="button"
								className={styles.railToggle}
								aria-label="Collapse runs sidebar"
								onClick={() => setCollapsed(true)}
							>
								<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
									<path d="M15 6l-6 6 6 6" />
								</svg>
							</button>
						</div>

						<div className={styles.railHead}>
							<h2>Runs</h2>
							<Button size="sm" onClick={openNewRun}>
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
											onClick={() => setRailOpen(false)}
											className={({ isActive }) =>
												`${styles.link} ${isActive ? styles.linkActive : ''}`
											}
										>
											<span
												className={styles.dot}
												data-tone={statusTone(run.status)}
												aria-hidden="true"
											/>
											<span className={styles.meta}>
												<span className={styles.title}>{runLabel(run)}</span>
												<span className={styles.time}>
													{relativeTime(run.created_at)}
												</span>
											</span>
										</NavLink>
									</li>
								))}
							</ul>
						)}
					</div>
				)}
			</aside>

			<section className={styles.content}>
				<Outlet
					context={{
						openNewRun,
						hasRuns: (runs ?? []).length > 0,
					}}
				/>
			</section>

			<NewRunDialog open={dialogOpen} onOpenChange={setDialogOpen} />
		</div>
	);
}
