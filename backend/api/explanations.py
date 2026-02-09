"""
Human-readable explanations for ML API responses.
Uses payload features and model output to describe what the result means.
"""


def _num(payload, key, default=0):
    try:
        v = payload.get(key, default)
        return float(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def _str(payload, key, default=""):
    v = payload.get(key, default)
    return str(v).strip() if v is not None else default


def eligibility_reason(payload, approved):
    """
    Build a short reason for approval or denial based on the application features.
    """
    income = _num(payload, "AnnualIncome", 60000)
    credit = _num(payload, "CreditScore", 620)
    loan_amt = _num(payload, "LoanAmount", 20000)
    dti = _num(payload, "DebtToIncomeRatio", 0.35)
    employment = _str(payload, "EmploymentStatus", "Employed")
    prev_defaults = _num(payload, "PreviousLoanDefaults", 0)
    bankruptcy = _num(payload, "BankruptcyHistory", 0)
    payment_hist = _num(payload, "PaymentHistory", 25)

    reasons = []
    if approved:
        if credit >= 650:
            reasons.append("strong credit score ({}).".format(int(credit)))
        elif credit >= 600:
            reasons.append("acceptable credit score ({}).".format(int(credit)))
        if income >= 50000 and loan_amt > 0 and (income / 12) > loan_amt / 48:
            reasons.append("income supports the requested loan amount and repayment.")
        if dti <= 0.40:
            reasons.append("manageable debt-to-income ratio ({:.0%}).".format(dti))
        if employment == "Employed":
            reasons.append("stable employment status.")
        if prev_defaults == 0:
            reasons.append("no previous loan defaults.")
        if bankruptcy == 0:
            reasons.append("no bankruptcy history.")
        if payment_hist >= 20:
            reasons.append("good payment history.")
        if not reasons:
            reasons.append("your overall profile meets the eligibility criteria.")
        return "Approved: The application was approved based on " + " ".join(reasons)
    else:
        if credit < 600:
            reasons.append("credit score ({}).".format(int(credit)))
        if dti > 0.45:
            reasons.append("high debt-to-income ratio ({:.0%}).".format(dti))
        if prev_defaults > 0:
            reasons.append("previous loan default(s).")
        if bankruptcy > 0:
            reasons.append("bankruptcy history.")
        if employment == "Unemployed":
            reasons.append("employment status.")
        if income < 30000 and loan_amt > 10000:
            reasons.append("income may be insufficient for the requested amount.")
        if payment_hist < 15:
            reasons.append("limited or weak payment history.")
        if not reasons:
            reasons.append("the combined risk factors in your profile.")
        return "Denied: The application was not approved primarily due to " + ", ".join(reasons)


def risk_score_description(risk_score):
    """
    Return interpretation and description of what the risk score means.
    Higher score = higher default risk. Typical range from model is roughly 30–70+.
    """
    score = float(risk_score)
    if score < 35:
        band = "Low risk"
        interpretation = (
            "The score indicates a lower likelihood of default. "
            "Lenders may offer more favorable terms for applications in this range."
        )
    elif score < 55:
        band = "Moderate risk"
        interpretation = (
            "The score indicates a moderate level of default risk. "
            "Lenders may apply standard terms or request additional assurance."
        )
    else:
        band = "Higher risk"
        interpretation = (
            "The score indicates a higher likelihood of default. "
            "Lenders may require stronger guarantees or offer different terms."
        )

    description = (
        "Risk score: {:.1f}. "
        "This is a relative measure of default risk (higher number = higher risk). "
        "Interpretation: {} — {}"
    ).format(score, band, interpretation)

    return {
        "interpretation": band,
        "description": description,
        "score_meaning": (
            "Scores are typically in a range where lower values (e.g. below 40) indicate lower default risk "
            "and higher values (e.g. above 55) indicate higher default risk. "
            "The exact scale depends on the model training data."
        ),
    }


def recommend_amount_explanation(payload, recommended_amount):
    """
    Explain why this loan amount was recommended based on the main features.
    """
    income = _num(payload, "AnnualIncome", 60000)
    credit = _num(payload, "CreditScore", 620)
    dti = _num(payload, "DebtToIncomeRatio", 0.35)
    net_worth = _num(payload, "NetWorth", 30000)
    savings = _num(payload, "SavingsAccountBalance", 5000)
    employment = _str(payload, "EmploymentStatus", "Employed")
    loan_duration = _num(payload, "LoanDuration", 48)

    factors = []
    if income > 0:
        factors.append(
            "your annual income ({} RWF)".format(int(income))
        )
    factors.append(
        "your credit score ({})".format(int(credit))
    )
    factors.append(
        "your debt-to-income ratio ({:.0%})".format(dti)
    )
    if net_worth > 0:
        factors.append(
            "your net worth ({} RWF)".format(int(net_worth))
        )
    if savings > 0:
        factors.append(
            "savings and reserves ({} RWF)".format(int(savings))
        )
    factors.append(
        "employment status ({})".format(employment)
    )
    if loan_duration > 0:
        factors.append(
            "requested loan duration ({} months)".format(int(loan_duration))
        )

    explanation = (
        "The recommended amount of {:.0f} RWF is based on your profile: {}. "
        "The model considers these and other application features to suggest a loan amount "
        "that aligns with typical approvals for similar profiles while respecting affordability and risk."
    ).format(float(recommended_amount), ", ".join(factors))

    return {
        "explanation": explanation,
        "basis": "The recommendation is driven by income, credit score, debt burden, assets, employment, and loan term from your application.",
    }
