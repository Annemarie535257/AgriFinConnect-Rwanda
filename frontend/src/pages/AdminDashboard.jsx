import { useLanguage } from '../context/LanguageContext';
import './Dashboard.css';

export default function AdminDashboard() {
  const { t } = useLanguage();

  return (
    <div className="dashboard-page">
      <h1 className="dashboard-page__title">{t('dashboard.adminTitle')}</h1>
      <p className="dashboard-page__lead">{t('dashboard.adminLead')}</p>
      <div className="dashboard-page__cards">
        <div className="dashboard-card">
          <h3 className="dashboard-card__title">{t('dashboard.users')}</h3>
          <p className="dashboard-card__desc">{t('dashboard.usersDesc')}</p>
        </div>
        <div className="dashboard-card">
          <h3 className="dashboard-card__title">{t('dashboard.reports')}</h3>
          <p className="dashboard-card__desc">{t('dashboard.reportsDesc')}</p>
        </div>
        <div className="dashboard-card">
          <h3 className="dashboard-card__title">{t('dashboard.settings')}</h3>
          <p className="dashboard-card__desc">{t('dashboard.settingsDesc')}</p>
        </div>
      </div>
    </div>
  );
}
