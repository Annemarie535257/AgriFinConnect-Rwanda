import { Outlet, Link, useLocation } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import './DashboardLayout.css';

const DASHBOARD_LINKS = [
  { path: '/dashboard/farmer', key: 'farmers' },
  { path: '/dashboard/microfinance', key: 'microfinances' },
  { path: '/dashboard/admin', key: 'admin' },
];

export default function DashboardLayout() {
  const { t } = useLanguage();
  const location = useLocation();

  return (
    <div className="dashboard-layout">
      <aside className="dashboard-sidebar">
        <Link to="/" className="dashboard-sidebar__logo">
          <img src="/logo (3).png" alt="AgriFinConnect Rwanda" className="dashboard-sidebar__logo-img" />
        </Link>
        <nav className="dashboard-sidebar__nav" aria-label="Dashboard navigation">
          {DASHBOARD_LINKS.map(({ path, key }) => (
            <Link
              key={path}
              to={path}
              className={`dashboard-sidebar__link ${location.pathname === path ? 'dashboard-sidebar__link--active' : ''}`}
            >
              {t(`getStarted.${key}`)}
            </Link>
          ))}
        </nav>
        <Link to="/" className="dashboard-sidebar__home">
          {t('nav.home')}
        </Link>
      </aside>
      <main className="dashboard-main">
        <Outlet />
      </main>
    </div>
  );
}
