import { useLanguage } from '../context/LanguageContext';
import { HomeIcon } from './DashboardIcons';
import './DashboardTopBar.css';

export default function DashboardTopBar({ title, showSearch = true }) {
  const { t } = useLanguage();

  return (
    <header className="dashboard-topbar">
      <h1 className="dashboard-topbar__title">
        <HomeIcon className="dashboard-topbar__icon" />
        {title}
      </h1>
      {showSearch && (
        <input
          type="search"
          className="dashboard-topbar__search"
          placeholder={t('dashboard.search') || 'Search'}
          aria-label="Search"
        />
      )}
    </header>
  );
}
