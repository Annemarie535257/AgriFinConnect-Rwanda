import { useLanguage } from '../context/LanguageContext';
import './OurServicesSection.css';

const SERVICES = [
  { key: 'card1', icon: '📊', label: 'Loan eligibility' },
  { key: 'card2', icon: '📈', label: 'Default risk' },
  { key: 'card3', icon: '💰', label: 'Loan recommendation' },
  { key: 'card4', icon: '💬', label: 'Multilingual chatbot' },
];

export default function OurServicesSection() {
  const { t } = useLanguage();

  return (
    <section id="our-services" className="our-services landing-section" aria-labelledby="our-services-heading" style={{ animationDelay: '0.15s' }}>
      <div className="our-services__inner">
        <h2 id="our-services-heading" className="our-services__title">
          {t('services.title')}
        </h2>
        <p className="our-services__lead">{t('services.introLead')}</p>
        <div className="our-services__grid">
          <div className="our-services__items">
            {SERVICES.map(({ key, icon, label }) => (
              <div key={key} className="our-services__item">
                <span className="our-services__icon" aria-hidden="true">
                  {icon}
                </span>
                <h3 className="our-services__item-title">{t(`${key}.title`)}</h3>
                <p className="our-services__item-desc">{t(`${key}.desc`)}</p>
              </div>
            ))}
          </div>
          <div className="our-services__visual">
            <div className="our-services__image-wrap">
              <img
                src="/download (3).jpeg"
                alt=""
                loading="lazy"
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
