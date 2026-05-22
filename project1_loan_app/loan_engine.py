"""
loan_engine.py
--------------
Loan decision engine combining:
  1. Hard rule-based filters (immediate reject/approve boundaries)
  2. Probability-based simulation for borderline cases

This is the core M&S component — the same inputs can yield
different outcomes on repeated runs, modeling real-world uncertainty.
"""

import random


# ── Hard rule thresholds ──────────────────────────────────────────────────────

MIN_CREDIT_SCORE   = 350       # Below this → instant reject
MIN_MONTHLY_INCOME = 500       # USD — below this → instant reject
MAX_LOAN_MULTIPLIER = 60       # Loan can't exceed 60× monthly income (5-yr cap)
AUTO_APPROVE_SCORE  = 780      # Above this + good DTI → near-certain approval


# ── Probability engine ────────────────────────────────────────────────────────

def compute_approval_probability(income: float,
                                  credit_score: int,
                                  loan_amount: float,
                                  duration_months: int) -> float:
    """
    Returns a float [0.0, 1.0] representing the simulated approval probability.

    Three weighted factors:
      - Credit score  (50%) — most important signal
      - Debt-to-income ratio (30%) — can they afford monthly payments?
      - Income level  (20%) — absolute earning capacity
    """

    # 1. Credit score component — normalised over 350–850 range
    credit_norm = (credit_score - 350) / (850 - 350)
    credit_norm = max(0.0, min(1.0, credit_norm))

    # 2. Debt-to-income ratio component
    #    Estimated monthly repayment (simple division, no interest model)
    monthly_payment = loan_amount / duration_months
    dti_ratio = monthly_payment / income          # e.g. 0.25 = 25 % of income
    # Score drops steeply once DTI exceeds ~35 %
    dti_score = max(0.0, 1.0 - (dti_ratio / 0.35))
    dti_score = min(1.0, dti_score)

    # 3. Income level component — saturates at $15,000 / month
    income_score = min(1.0, income / 15_000)

    # Weighted sum
    probability = (0.50 * credit_norm +
                   0.30 * dti_score   +
                   0.20 * income_score)

    return round(max(0.0, min(1.0, probability)), 4)


# ── Main evaluation function ──────────────────────────────────────────────────

def evaluate_loan(income: float,
                  credit_score: int,
                  loan_amount: float,
                  duration_months: int) -> dict:
    """
    Evaluate a loan application and return a result dictionary.

    Returns:
        {
            "decision":    "APPROVED" | "REJECTED" | "PENDING",
            "probability": float,
            "reason":      str,
            "monthly_est": float,   # estimated monthly payment
            "dti_ratio":   float,   # debt-to-income ratio
        }
    """

    monthly_est = round(loan_amount / duration_months, 2)
    dti_ratio   = round(monthly_est / income, 4) if income > 0 else 999

    # ── STAGE 1: Hard reject rules ─────────────────────────────────────────
    if credit_score < MIN_CREDIT_SCORE:
        return {
            "decision":    "REJECTED",
            "probability": 0.0,
            "reason":      f"Credit score ({credit_score}) is below the minimum threshold of {MIN_CREDIT_SCORE}.",
            "monthly_est": monthly_est,
            "dti_ratio":   dti_ratio,
        }

    if income < MIN_MONTHLY_INCOME:
        return {
            "decision":    "REJECTED",
            "probability": 0.0,
            "reason":      f"Monthly income (${income:,.0f}) is below the minimum of ${MIN_MONTHLY_INCOME:,}.",
            "monthly_est": monthly_est,
            "dti_ratio":   dti_ratio,
        }

    if loan_amount > income * MAX_LOAN_MULTIPLIER:
        max_allowed = income * MAX_LOAN_MULTIPLIER
        return {
            "decision":    "REJECTED",
            "probability": 0.0,
            "reason":      f"Loan amount (${loan_amount:,.0f}) exceeds maximum allowed (${max_allowed:,.0f} = 60× monthly income).",
            "monthly_est": monthly_est,
            "dti_ratio":   dti_ratio,
        }

    if dti_ratio > 0.60:
        return {
            "decision":    "REJECTED",
            "probability": 0.0,
            "reason":      f"Debt-to-income ratio ({dti_ratio:.1%}) is too high. Monthly payment would be {dti_ratio:.1%} of income.",
            "monthly_est": monthly_est,
            "dti_ratio":   dti_ratio,
        }

    # ── STAGE 2: Compute probability ──────────────────────────────────────
    prob = compute_approval_probability(income, credit_score, loan_amount, duration_months)

    # ── STAGE 3: Simulate decision ────────────────────────────────────────
    random_draw = random.random()
    approved    = random_draw <= prob

    decision = "APPROVED" if approved else "REJECTED"
    reason   = (
        f"Simulation approved the application. "
        f"Approval probability was {prob:.1%} — random draw: {random_draw:.4f}."
        if approved else
        f"Simulation rejected the application. "
        f"Approval probability was {prob:.1%} — random draw: {random_draw:.4f} exceeded threshold."
    )

    return {
        "decision":    decision,
        "probability": prob,
        "reason":      reason,
        "monthly_est": monthly_est,
        "dti_ratio":   dti_ratio,
    }