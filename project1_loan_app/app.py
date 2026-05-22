"""
app.py
------
Loan Application System - Modeling & Simulation Project
Built with Streamlit + SQLite

Run with:
    streamlit run app.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import time

from loan_engine import evaluate_loan
from loan_db import (
    init_db,
    save_application,
    fetch_all_applications,
    fetch_stats,
    clear_all_applications,
)

st.set_page_config(
    page_title="Loan Application System",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        border-radius: 6px;
        font-weight: 500;
    }
    [data-testid="stMetricValue"] { font-size: 2rem !important; }
    .section-label {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #6b7280;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# Sidebar

with st.sidebar:
    st.title("Loan System")
    st.caption("Modeling & Simulation Project")
    st.divider()

    page = st.radio(
        "Navigation",
        ["Apply", "History", "Statistics"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("**How decisions are made**")
    st.markdown("""
    1. Hard rules check minimum thresholds
    2. A weighted score is calculated from credit, income, and debt-to-income ratio
    3. A random draw is made against that score — the same inputs can produce different results
    """)


# Page: Apply

if page == "Apply":
    st.title("Loan Application")
    st.write("Enter the applicant details below. The system will run a simulated lending decision.")
    st.divider()

    with st.form("loan_form", clear_on_submit=False):

        st.markdown('<p class="section-label">Personal Information</p>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            applicant_name = st.text_input("Full Name", placeholder="e.g. John Doe")
        with col2:
            purpose = st.selectbox(
                "Loan Purpose",
                ["Home Purchase", "Car Purchase", "Education",
                 "Business", "Medical", "Personal", "Debt Consolidation"],
            )

        st.markdown('<p class="section-label">Financial Details</p>', unsafe_allow_html=True)
        col3, col4 = st.columns(2)
        with col3:
            income = st.number_input(
                "Monthly Income (USD)",
                min_value=0.0, max_value=500_000.0,
                step=100.0, value=3000.0,
                help="Gross monthly income before taxes",
            )
        with col4:
            credit_score = st.slider(
                "Credit Score",
                min_value=300, max_value=850,
                value=650, step=1,
                help="FICO credit score (300-850)",
            )

        st.markdown('<p class="section-label">Loan Details</p>', unsafe_allow_html=True)
        col5, col6 = st.columns(2)
        with col5:
            loan_amount = st.number_input(
                "Loan Amount (USD)",
                min_value=100.0, max_value=5_000_000.0,
                step=500.0, value=10_000.0,
            )
        with col6:
            duration_months = st.select_slider(
                "Loan Duration",
                options=[6, 12, 18, 24, 36, 48, 60, 72, 84, 96, 120],
                value=36,
                format_func=lambda x: f"{x} months ({x//12} yr)" if x >= 12 else f"{x} months",
            )

        submitted = st.form_submit_button("Submit Application", width="stretch")

    if submitted:
        if not applicant_name.strip():
            st.error("Please enter the applicant's name.")
        elif loan_amount <= 0:
            st.error("Loan amount must be greater than zero.")
        else:
            with st.spinner("Processing application..."):
                time.sleep(1.0)
                result = evaluate_loan(income, credit_score, loan_amount, duration_months)
                save_application(
                    applicant_name.strip(), income, credit_score,
                    loan_amount, duration_months, purpose, result,
                )

            st.divider()
            st.subheader("Decision")

            if result["decision"] == "APPROVED":
                st.success(f"Approved — {applicant_name.strip()}, your loan application has been approved.")
            else:
                st.error(f"Rejected — {applicant_name.strip()}, your loan application was not approved.")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Decision",         result["decision"])
            c2.metric("Approval Chance",  f"{result['probability']:.1%}")
            c3.metric("Monthly Payment",  f"${result['monthly_est']:,.2f}")
            c4.metric("Debt-to-Income",   f"{result['dti_ratio']:.1%}")

            st.info(f"Reason: {result['reason']}")
            st.caption(
                "Note: This system uses probabilistic simulation. The same application "
                "may receive a different outcome on resubmission if the score is borderline."
            )


# Page: History

elif page == "History":
    st.title("Application History")

    records = fetch_all_applications()

    if not records:
        st.info("No applications on record. Submit one from the Apply page.")
    else:
        col1, _ = st.columns([1, 3])
        with col1:
            filter_decision = st.selectbox("Filter by decision", ["All", "APPROVED", "REJECTED"])

        df = pd.DataFrame(records)

        df["income"]       = df["income"].map("${:,.0f}".format)
        df["loan_amount"]  = df["loan_amount"].map("${:,.0f}".format)
        df["monthly_est"]  = df["monthly_est"].map("${:,.2f}".format)
        df["probability"]  = df["probability"].map("{:.1%}".format)
        df["dti_ratio"]    = df["dti_ratio"].map("{:.1%}".format)

        display_cols = {
            "id":              "ID",
            "applied_at":      "Date and Time",
            "applicant_name":  "Applicant",
            "purpose":         "Purpose",
            "income":          "Monthly Income",
            "credit_score":    "Credit Score",
            "loan_amount":     "Loan Amount",
            "duration_months": "Duration (months)",
            "monthly_est":     "Est. Monthly Payment",
            "dti_ratio":       "DTI Ratio",
            "probability":     "Approval Chance",
            "decision":        "Decision",
        }

        df_display = df[list(display_cols.keys())].rename(columns=display_cols)

        if filter_decision != "All":
            df_display = df_display[df_display["Decision"] == filter_decision]

        def style_decision(val):
            if val == "APPROVED":
                return "background-color: #d1fae5; color: #065f46; font-weight: bold"
            elif val == "REJECTED":
                return "background-color: #fee2e2; color: #991b1b; font-weight: bold"
            return ""

        styled = df_display.style.applymap(style_decision, subset=["Decision"])
        st.dataframe(styled, width="stretch", hide_index=True)
        st.caption(f"{len(df_display)} record(s) shown.")

        with st.expander("Clear all records"):
            st.warning("This will permanently delete all application records and cannot be undone.")
            if st.button("Delete all records", type="primary"):
                clear_all_applications()
                st.success("All records have been deleted.")
                st.rerun()


# Page: Statistics

elif page == "Statistics":
    st.title("Statistics")

    stats = fetch_stats()
    records = fetch_all_applications()

    if not stats or stats.get("total", 0) == 0:
        st.info("No data available. Submit some applications first.")
    else:
        total         = stats["total"]
        approved      = stats["approved"] or 0
        rejected      = stats["rejected"] or 0
        approval_rate = approved / total if total > 0 else 0

        st.subheader("Summary")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Applications", total)
        m2.metric("Approved",           approved)
        m3.metric("Rejected",           rejected)
        m4.metric("Approval Rate",      f"{approval_rate:.1%}")
        m5.metric("Average Loan",       f"${stats['avg_loan']:,.0f}")

        st.divider()

        df = pd.DataFrame(records)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Decision Breakdown**")
            decision_counts = df["decision"].value_counts().reset_index()
            decision_counts.columns = ["Decision", "Count"]
            st.bar_chart(decision_counts.set_index("Decision"))

        with col2:
            st.markdown("**Credit Score Distribution**")
            st.bar_chart(
                df["credit_score"]
                  .value_counts(bins=10, sort=False)
                  .rename("Count")
            )

        st.divider()

        col3, col4 = st.columns(2)
        with col3:
            st.markdown("**Loan Amount Distribution**")
            st.bar_chart(
                df["loan_amount"]
                  .value_counts(bins=8, sort=False)
                  .rename("Count")
            )

        with col4:
            st.markdown("**Approval Chance Distribution**")
            st.bar_chart(
                df["probability"]
                  .value_counts(bins=10, sort=False)
                  .rename("Count")
            )

        st.divider()

        st.subheader("Averages by Decision")
        avg_table = (
            df.groupby("decision")
              .agg(
                  Count=("id", "count"),
                  Avg_Income=("income", "mean"),
                  Avg_Credit=("credit_score", "mean"),
                  Avg_Loan=("loan_amount", "mean"),
                  Avg_Prob=("probability", "mean"),
              )
              .round(2)
              .reset_index()
        )
        avg_table.columns = ["Decision", "Count", "Avg Income",
                              "Avg Credit Score", "Avg Loan Amount", "Avg Approval Chance"]
        avg_table["Avg Income"]          = avg_table["Avg Income"].map("${:,.0f}".format)
        avg_table["Avg Loan Amount"]     = avg_table["Avg Loan Amount"].map("${:,.0f}".format)
        avg_table["Avg Approval Chance"] = avg_table["Avg Approval Chance"].map("{:.1%}".format)

        st.dataframe(avg_table, width="stretch", hide_index=True)