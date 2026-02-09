import { useLanguage } from '../context/LanguageContext';
import './Dashboard.css';

export default function FarmerDashboard() {
  const { t } = useLanguage();

  return (
    <div className="dashboard-page">
      <h1 className="dashboard-page__title">{t('dashboard.farmerTitle')}</h1>
      <p className="dashboard-page__lead">{t('dashboard.farmerLead')}</p>
      <div className="dashboard-page__cards">
        <div className="dashboard-card">
          <h3 className="dashboard-card__title">{t('dashboard.applyLoan')}</h3>
          <p className="dashboard-card__desc">{t('dashboard.applyLoanDesc')}</p>
        </div>
        <div className="dashboard-card">
          <h3 className="dashboard-card__title">{t('dashboard.myApplications')}</h3>
          <p className="dashboard-card__desc">{t('dashboard.myApplicationsDesc')}</p>
        </div>
        <div className="dashboard-card">
          <h3 className="dashboard-card__title">{t('dashboard.chatbot')}</h3>
          <p className="dashboard-card__desc">{t('dashboard.chatbotDesc')}</p>
        </div>
      </div>
    </div>
  );
}
