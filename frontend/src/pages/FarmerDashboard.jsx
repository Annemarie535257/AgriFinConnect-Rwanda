import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import {
  getFarmerProfile,
  updateFarmerProfile,
  getFarmerApplications,
  submitFarmerApplication,
  getFarmerLoans,
  getFarmerRepayments,
  predictEligibility,
  predictRisk,
  recommendLoanAmount,
} from '../api/client';
import FloatingChatbot from '../components/FloatingChatbot';
import DashboardTopBar from '../components/DashboardTopBar';
import './Dashboard.css';
import './FarmerDashboard.css';

const EMPLOYMENT_OPTIONS = ['Employed', 'Self-Employed', 'Unemployed'];
const EDUCATION_OPTIONS = ['High School', 'Associate', 'Bachelor', 'Master'];
const MARITAL_OPTIONS = ['Single', 'Married', 'Divorced'];
const PURPOSE_OPTIONS = ['Other', 'Education', 'Home', 'Debt Consolidation'];

/** Map farmer form to ML model API payload (PascalCase) */
function formToMlPayload(form) {
  return {
    Age: Number(form.age) || 35,
    AnnualIncome: Number(form.annual_income) || 600000,
    CreditScore: Number(form.credit_score) || 600,
    LoanAmount: Number(form.loan_amount_requested) || 200000,
    LoanDuration: Number(form.loan_duration_months) || 24,
    EmploymentStatus: form.employment_status || 'Self-Employed',
    EducationLevel: form.education_level || 'High School',
    MaritalStatus: form.marital_status || 'Married',
    LoanPurpose: form.loan_purpose || 'Other',
    DebtToIncomeRatio: 0.35,
  };
}

export default function FarmerDashboard() {
  const { t } = useLanguage();
  const [searchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'apply';
  const [profile, setProfile] = useState(null);
  const [applications, setApplications] = useState([]);
  const [loans, setLoans] = useState([]);
  const [repayments, setRepayments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [modelLoading, setModelLoading] = useState(null); // 'eligibility' | 'risk' | 'recommend' | null
  const [modelResults, setModelResults] = useState({ eligibility: null, risk: null, recommend: null });

  // Form state for loan application
  const [form, setForm] = useState({
    age: 35,
    annual_income: 600000,
    credit_score: 600,
    loan_amount_requested: 200000,
    loan_duration_months: 24,
    employment_status: 'Self-Employed',
    education_level: 'High School',
    marital_status: 'Married',
    loan_purpose: 'Other',
  });

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [profileRes, appsRes, loansRes, repayRes] = await Promise.all([
        getFarmerProfile().catch(() => null),
        getFarmerApplications().catch(() => ({ applications: [] })),
        getFarmerLoans().catch(() => ({ loans: [] })),
        getFarmerRepayments().catch(() => ({ repayments: [] })),
      ]);
      if (profileRes) setProfile(profileRes);
      if (appsRes?.applications) setApplications(appsRes.applications);
      if (loansRes?.loans) setLoans(loansRes.loans);
      if (repayRes?.repayments) setRepayments(repayRes.repayments);
    } catch (err) {
      setError(err.body?.error || err.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSubmitApplication = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      await submitFarmerApplication(form);
      setSuccess(t('farmer.applicationSubmitted') || 'Application submitted successfully!');
      setModelResults({ eligibility: null, risk: null, recommend: null });
      setForm({
        age: 35,
        annual_income: 600000,
        credit_score: 600,
        loan_amount_requested: 200000,
        loan_duration_months: 24,
        employment_status: 'Self-Employed',
        education_level: 'High School',
        marital_status: 'Married',
        loan_purpose: 'Other',
      });
      fetchData();
    } catch (err) {
      setError(err.body?.error || err.message || 'Failed to submit application');
    } finally {
      setLoading(false);
    }
  };

  const handleCheckEligibility = async () => {
    setModelLoading('eligibility');
    setModelResults((r) => ({ ...r, eligibility: null }));
    try {
      const data = await predictEligibility(formToMlPayload(form));
      setModelResults((r) => ({ ...r, eligibility: data }));
    } catch (err) {
      setModelResults((r) => ({ ...r, eligibility: { error: err.body?.error || err.message || 'Model unavailable' } }));
    } finally {
      setModelLoading(null);
    }
  };

  const handleCheckRisk = async () => {
    setModelLoading('risk');
    setModelResults((r) => ({ ...r, risk: null }));
    try {
      const data = await predictRisk(formToMlPayload(form));
      setModelResults((r) => ({ ...r, risk: data }));
    } catch (err) {
      setModelResults((r) => ({ ...r, risk: { error: err.body?.error || err.message || 'Model unavailable' } }));
    } finally {
      setModelLoading(null);
    }
  };

  const handleGetRecommendation = async () => {
    setModelLoading('recommend');
    setModelResults((r) => ({ ...r, recommend: null }));
    try {
      const data = await recommendLoanAmount(formToMlPayload(form));
      setModelResults((r) => ({ ...r, recommend: data }));
    } catch (err) {
      setModelResults((r) => ({ ...r, recommend: { error: err.body?.error || err.message || 'Model unavailable' } }));
    } finally {
      setModelLoading(null);
    }
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const data = {
      location: fd.get('location') || '',
      phone: fd.get('phone') || '',
      cooperative_name: fd.get('cooperative_name') || '',
    };
    setLoading(true);
    setError(null);
    try {
      const res = await updateFarmerProfile(data);
      setProfile(res);
      setSuccess(t('farmer.profileUpdated') || 'Profile updated');
    } catch (err) {
      setError(err.body?.error || err.message || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const pendingCount = applications.filter((a) => a.status === 'pending').length;
  const approvedCount = applications.filter((a) => a.status === 'approved').length;

  return (
    <div className="dashboard-page farmer-dashboard">
      <DashboardTopBar title={t('dashboard.farmerTitle')} />
      <div className="dashboard-content">
        {error && <div className="farmer-dashboard__message farmer-dashboard__message--error">{error}</div>}
        {success && <div className="farmer-dashboard__message farmer-dashboard__message--success">{success}</div>}
        {loading && (
          <div className="farmer-dashboard__loading" aria-live="polite">
            {t('getStarted.submitting') || 'Loading…'}
          </div>
        )}

        {activeTab === 'apply' && (
        <>
          <div className="dashboard-grid" style={{ marginBottom: '1.5rem' }}>
            <div className="dashboard-card">
              <h3 className="dashboard-card__title">{t('dashboard.myApplications')}</h3>
              <div className="dashboard-donut" style={{ background: `conic-gradient(var(--color-primary) ${(applications.length ? (approvedCount / applications.length) * 100 : 0)}%, #e8eaed 0)` }}>
                <span className="dashboard-donut__inner">{applications.length}</span>
              </div>
              <span className="dashboard-card__label">{t('farmer.totalApplications') || 'Total applications'}</span>
            </div>
            <div className="dashboard-card">
              <h3 className="dashboard-card__title">{t('farmer.myLoans') || 'My loans'}</h3>
              <div className="dashboard-card__value">{loans.length}</div>
              <span className="dashboard-card__label">{t('farmer.activeLoans') || 'Active loans'}</span>
            </div>
            <div className="dashboard-card">
              <h3 className="dashboard-card__title">{t('farmer.repayments') || 'Repayments'}</h3>
              <div className="dashboard-card__value">{repayments.filter((r) => r.status === 'paid').length}/{repayments.length}</div>
              <span className="dashboard-card__label">{t('farmer.paid') || 'Paid'}</span>
            </div>
          </div>
        <section className="farmer-dashboard__section" aria-labelledby="apply-heading">
          <h2 id="apply-heading" className="farmer-dashboard__section-title">{t('dashboard.applyLoan')}</h2>
          <form className="farmer-dashboard__form" onSubmit={handleSubmitApplication}>
            <div className="farmer-dashboard__form-row">
              <label>
                <span>{t('card1.age')}</span>
                <input
                  type="number"
                  min={18}
                  max={100}
                  value={form.age}
                  onChange={(e) => setForm({ ...form, age: parseInt(e.target.value, 10) || 35 })}
                />
              </label>
              <label>
                <span>{t('card1.annualIncome')}</span>
                <input
                  type="number"
                  min={0}
                  value={form.annual_income}
                  onChange={(e) => setForm({ ...form, annual_income: parseInt(e.target.value, 10) || 0 })}
                />
              </label>
            </div>
            <div className="farmer-dashboard__form-row">
              <label>
                <span>{t('card1.creditScore')}</span>
                <input
                  type="number"
                  min={300}
                  max={850}
                  value={form.credit_score}
                  onChange={(e) => setForm({ ...form, credit_score: parseInt(e.target.value, 10) || 600 })}
                />
              </label>
              <label>
                <span>{t('card1.loanAmount')}</span>
                <input
                  type="number"
                  min={0}
                  value={form.loan_amount_requested}
                  onChange={(e) => setForm({ ...form, loan_amount_requested: parseInt(e.target.value, 10) || 0 })}
                />
              </label>
            </div>
            <div className="farmer-dashboard__form-row">
              <label>
                <span>{t('card1.loanDuration')}</span>
                <input
                  type="number"
                  min={6}
                  max={84}
                  value={form.loan_duration_months}
                  onChange={(e) => setForm({ ...form, loan_duration_months: parseInt(e.target.value, 10) || 24 })}
                />
              </label>
              <label>
                <span>{t('card1.employment')}</span>
                <select
                  value={form.employment_status}
                  onChange={(e) => setForm({ ...form, employment_status: e.target.value })}
                >
                  {EMPLOYMENT_OPTIONS.map((o) => (
                    <option key={o} value={o}>{o}</option>
                  ))}
                </select>
              </label>
            </div>
            <div className="farmer-dashboard__form-row">
              <label>
                <span>{t('card1.education')}</span>
                <select
                  value={form.education_level}
                  onChange={(e) => setForm({ ...form, education_level: e.target.value })}
                >
                  {EDUCATION_OPTIONS.map((o) => (
                    <option key={o} value={o}>{o}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>{t('farmer.maritalStatus') || 'Marital status'}</span>
                <select
                  value={form.marital_status}
                  onChange={(e) => setForm({ ...form, marital_status: e.target.value })}
                >
                  {MARITAL_OPTIONS.map((o) => (
                    <option key={o} value={o}>{o}</option>
                  ))}
                </select>
              </label>
            </div>
            <div className="farmer-dashboard__form-row">
              <label>
                <span>{t('farmer.loanPurpose') || 'Loan purpose'}</span>
                <select
                  value={form.loan_purpose}
                  onChange={(e) => setForm({ ...form, loan_purpose: e.target.value })}
                >
                  {PURPOSE_OPTIONS.map((o) => (
                    <option key={o} value={o}>{o}</option>
                  ))}
                </select>
              </label>
            </div>

            {/* ML model preview - runs before submit */}
            <div className="farmer-dashboard__model-section">
              <h3 className="farmer-dashboard__model-title">AI model preview</h3>
              <p className="farmer-dashboard__model-hint">Check eligibility, risk score, and recommended amount before submitting your application.</p>
              <div className="farmer-dashboard__model-buttons">
                <button
                  type="button"
                  className="farmer-dashboard__model-btn"
                  onClick={handleCheckEligibility}
                  disabled={loading || !!modelLoading}
                >
                  {modelLoading === 'eligibility' ? (t('card1.checking') || 'Checking…') : t('card1.submit') || 'Check eligibility'}
                </button>
                <button
                  type="button"
                  className="farmer-dashboard__model-btn"
                  onClick={handleCheckRisk}
                  disabled={loading || !!modelLoading}
                >
                  {modelLoading === 'risk' ? (t('card2.assessing') || 'Assessing…') : t('card2.submit') || 'Get risk score'}
                </button>
                <button
                  type="button"
                  className="farmer-dashboard__model-btn"
                  onClick={handleGetRecommendation}
                  disabled={loading || !!modelLoading}
                >
                  {modelLoading === 'recommend' ? (t('getStarted.submitting') || 'Loading…') : (t('card3.submit') || 'Get recommended amount')}
                </button>
              </div>
              {(modelResults.eligibility || modelResults.risk || modelResults.recommend) && (
                <div className="farmer-dashboard__model-results">
                  {modelResults.eligibility && (
                    <div className="farmer-dashboard__model-card">
                      <strong>{t('card1.title')}</strong>
                      {modelResults.eligibility.error ? (
                        <span className="farmer-dashboard__model-error">{modelResults.eligibility.error}</span>
                      ) : (
                        <span className={modelResults.eligibility.approved ? 'farmer-dashboard__model-ok' : 'farmer-dashboard__model-warn'}>
                          {modelResults.eligibility.approved ? t('card1.approved') : t('card1.denied')}
                          {modelResults.eligibility.reason && ` — ${modelResults.eligibility.reason}`}
                        </span>
                      )}
                    </div>
                  )}
                  {modelResults.risk && (
                    <div className="farmer-dashboard__model-card">
                      <strong>{t('card2.title')}</strong>
                      {modelResults.risk.error ? (
                        <span className="farmer-dashboard__model-error">{modelResults.risk.error}</span>
                      ) : (
                        <span>
                          {t('card2.riskScore')}: {Number(modelResults.risk.risk_score ?? modelResults.risk.score).toFixed(2)}
                          {modelResults.risk.interpretation && ` — ${modelResults.risk.interpretation}`}
                        </span>
                      )}
                    </div>
                  )}
                  {modelResults.recommend && (
                    <div className="farmer-dashboard__model-card">
                      <strong>{t('card3.title') || 'Loan recommendation'}</strong>
                      {modelResults.recommend.error ? (
                        <span className="farmer-dashboard__model-error">{modelResults.recommend.error}</span>
                      ) : (
                        <div>
                          <span className="farmer-dashboard__model-ok">
                            Recommended: RWF {Number(modelResults.recommend.recommended_amount ?? modelResults.recommend.recommendedAmount ?? modelResults.recommend.amount).toLocaleString()}
                          </span>
                          <button
                            type="button"
                            className="farmer-dashboard__model-btn farmer-dashboard__model-btn--small"
                            onClick={() => {
                              const amt = modelResults.recommend.recommended_amount ?? modelResults.recommend.recommendedAmount ?? modelResults.recommend.amount;
                              if (amt != null) setForm((f) => ({ ...f, loan_amount_requested: Number(amt) }));
                            }}
                          >
                            Use this amount
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            <button type="submit" className="farmer-dashboard__submit" disabled={loading}>
              {loading ? t('getStarted.submitting') : t('farmer.submitApplication') || 'Submit application'}
            </button>
          </form>
        </section>
        </>
        )}

        {activeTab === 'applications' && (
        <section className="farmer-dashboard__section" aria-labelledby="apps-heading">
          <h2 id="apps-heading" className="farmer-dashboard__section-title">{t('dashboard.myApplications')}</h2>
          {applications.length === 0 ? (
            <p className="farmer-dashboard__empty">{t('farmer.noApplications') || 'No applications yet.'}</p>
          ) : (
            <div className="farmer-dashboard__list">
              {applications.map((app) => (
                <div key={app.id} className="farmer-dashboard__card">
                  <div className="farmer-dashboard__card-row">
                    <strong>#{app.id}</strong>
                    <span className={`farmer-dashboard__status farmer-dashboard__status--${app.status}`}>{app.status}</span>
                  </div>
                  <p>Amount: RWF {Number(app.loan_amount_requested).toLocaleString()} · {app.loan_duration_months} months</p>
                  {app.eligibility_approved != null && (
                    <p>Eligibility: {app.eligibility_approved ? t('card1.approved') : t('card1.denied')}</p>
                  )}
                  {app.risk_score != null && <p>Risk score: {app.risk_score?.toFixed(2)}</p>}
                  {app.recommended_amount != null && (
                    <p>Recommended: RWF {Number(app.recommended_amount).toLocaleString()}</p>
                  )}
                  <p className="farmer-dashboard__date">{new Date(app.created_at).toLocaleDateString()}</p>
                </div>
              ))}
            </div>
          )}
        </section>
        )}

        {activeTab === 'loans' && (
        <section className="farmer-dashboard__section" aria-labelledby="loans-heading">
          <h2 id="loans-heading" className="farmer-dashboard__section-title">{t('farmer.myLoans') || 'My loans'}</h2>
          {loans.length === 0 ? (
            <p className="farmer-dashboard__empty">{t('farmer.noLoans') || 'No approved loans yet.'}</p>
          ) : (
            <div className="farmer-dashboard__list">
              {loans.map((loan) => (
                <div key={loan.id} className="farmer-dashboard__card">
                  <p><strong>Loan #{loan.id}</strong></p>
                  <p>Amount: RWF {Number(loan.amount).toLocaleString()}</p>
                  <p>Duration: {loan.duration_months} months · Monthly: RWF {Number(loan.monthly_payment).toLocaleString()}</p>
                  <p className="farmer-dashboard__date">{new Date(loan.created_at).toLocaleDateString()}</p>
                </div>
              ))}
            </div>
          )}
        </section>
        )}

        {activeTab === 'repayments' && (
        <section className="farmer-dashboard__section" aria-labelledby="rep-heading">
          <h2 id="rep-heading" className="farmer-dashboard__section-title">{t('farmer.repayments') || 'Repayments'}</h2>
          {repayments.length === 0 ? (
            <p className="farmer-dashboard__empty">{t('farmer.noRepayments') || 'No repayments yet.'}</p>
          ) : (
            <div className="farmer-dashboard__list">
              {repayments.map((r) => (
                <div key={r.id} className="farmer-dashboard__card farmer-dashboard__card--small">
                  <span>RWF {Number(r.amount).toLocaleString()}</span>
                  <span>Due: {r.due_date}</span>
                  <span className={`farmer-dashboard__status farmer-dashboard__status--${r.status}`}>{r.status}</span>
                </div>
              ))}
            </div>
          )}
        </section>
        )}

        {activeTab === 'profile' && (
        <section className="farmer-dashboard__section" aria-labelledby="profile-heading">
          <h2 id="profile-heading" className="farmer-dashboard__section-title">{t('farmer.profile') || 'Profile'}</h2>
          <form className="farmer-dashboard__form" onSubmit={handleUpdateProfile}>
            <label>
              <span>{t('farmer.location') || 'Location'}</span>
              <input name="location" defaultValue={profile?.location || ''} placeholder="e.g. Kigali" />
            </label>
            <label>
              <span>{t('farmer.phone') || 'Phone'}</span>
              <input name="phone" type="tel" defaultValue={profile?.phone || ''} placeholder="+250 788 000 000" />
            </label>
            <label>
              <span>{t('farmer.cooperative') || 'Cooperative name'}</span>
              <input name="cooperative_name" defaultValue={profile?.cooperative_name || ''} placeholder="Optional" />
            </label>
            <button type="submit" className="farmer-dashboard__submit" disabled={loading}>
              {t('farmer.saveProfile') || 'Save profile'}
            </button>
          </form>
        </section>
        )}
      </div>
      <FloatingChatbot />
    </div>
  );
}
