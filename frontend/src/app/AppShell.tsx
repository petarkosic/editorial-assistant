import { Link, Outlet } from 'react-router-dom';
import styles from './AppShell.module.css';

export function AppShell() {
	return (
		<div className={styles.shell}>
			<header className={styles.header}>
				<span className={styles.brand}>Editorial Assistant</span>
				<nav className={styles.nav}>
					<Link to='/'>Runs</Link>
				</nav>
			</header>
			<main className={styles.main}>
				<Outlet />
			</main>
		</div>
	);
}
