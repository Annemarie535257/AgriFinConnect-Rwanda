/**
 * API client for AgriFinConnect Rwanda backend.
 * Base URL: use Vite proxy /api in dev, or set VITE_API_URL in production.
 */
const API_BASE = import.meta.env.VITE_API_URL || '/api';

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };
  if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
    config.body = JSON.stringify(options.body);
  }
  const res = await fetch(url, config);
  if (!res.ok) {
    const err = new Error(res.statusText || 'API error');
    err.status = res.status;
    try {
      err.body = await res.json();
    } catch {
      err.body = await res.text();
    }
    throw err;
  }
  const contentType = res.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return res.json();
  }
  return res.text();
}

/** POST /api/eligibility — loan eligibility prediction (Model 1) */
export async function predictEligibility(payload) {
  return request('/eligibility/', { method: 'POST', body: payload });
}

/** POST /api/risk — default risk score (Model 2) */
export async function predictRisk(payload) {
  return request('/risk/', { method: 'POST', body: payload });
}

/** POST /api/recommend-amount — recommended loan amount (Model 3) */
export async function recommendLoanAmount(payload) {
  return request('/recommend-amount/', { method: 'POST', body: payload });
}

/** POST /api/chat — chatbot (multilingual) */
export async function chat(message, language = 'en') {
  return request('/chat/', { method: 'POST', body: { message, language } });
}
