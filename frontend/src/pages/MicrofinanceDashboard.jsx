import { useLanguage } from '../context/LanguageContext';
import './Dashboard.css';

export default function MicrofinanceDashboard() {
  const { t } = useLanguage();

  return (
    <div className="dashboard-page">
      <h1 className="dashboard-page__title">{t('dashboard.microfinanceTitle')}</h1>
      <p className="dashboard-page__lead">{t('dashboard.microfinanceLead')}</p>
      <div className="dashboard-page__cards">
        <div className="dashboard-card">
          <h3 className="dashboard-card__title">{t('dashboard.reviewApplications')}</h3>
          <p className="dashboard-card__desc">{t('dashboard.reviewApplicationsDesc')}</p>
        </div>
        <div className="dashboard-card">
          <h3 className="dashboard-card__title">{t('dashboard.riskAssessment')}</h3>
          <p className="dashboard-card__desc">{t('dashboard.riskAssessmentDesc')}</p>
        </div>
        <div className="dashboard-card">
          <h3 className="dashboard-card__title">{t('dashboard.loanRecommendation')}</h3>
          <p className="dashboard-card__desc">{t('dashboard.loanRecommendationDesc')}</p>
        </div>
      </div>
    </div>
  );
}
