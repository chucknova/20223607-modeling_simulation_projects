"""
app.py
------
M/M/1 Queue Simulation - Modeling & Simulation Project 2
Built with Streamlit

Run with:
    streamlit run app.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd

from queue_engine import simulate_mm1

st.set_page_config(
    page_title="M/M/1 Queue Simulation",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stButton > button { width: 100%; border-radius: 6px; font-weight: 500; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; }
    .metric-label { font-size: 0.78rem; font-weight: 600;
                    text-transform: uppercase; letter-spacing: 0.05em;
                    color: #6b7280; }
    .section-label { font-size: 0.85rem; font-weight: 600;
                     text-transform: uppercase; letter-spacing: 0.05em;
                     color: #6b7280; margin-bottom: 0.4rem; }
    table { width: 100%; }
</style>
""", unsafe_allow_html=True)


# Sidebar — simulation parameters

with st.sidebar:
    st.title("Queue Simulation")
    st.caption("M/M/1 Model — Modeling & Simulation Project")
    st.divider()

    st.markdown("**Simulation Parameters**")

    arrival_rate = st.number_input(
        "Arrival rate (lambda)",
        min_value=0.1, max_value=100.0,
        value=4.0, step=0.5,
        help="Average number of customers arriving per unit time",
    )

    service_rate = st.number_input(
        "Service rate (mu)",
        min_value=0.1, max_value=100.0,
        value=6.0, step=0.5,
        help="Average number of customers the server can handle per unit time",
    )

    num_customers = st.slider(
        "Number of customers",
        min_value=10, max_value=1000,
        value=200, step=10,
    )

    use_seed = st.checkbox("Fix random seed (reproducible results)", value=False)
    seed_val = None
    if use_seed:
        seed_val = st.number_input("Seed value", min_value=0, value=42, step=1)

    st.divider()

    rho = arrival_rate / service_rate
    if rho >= 1:
        st.error(
            f"Traffic intensity (rho) = {rho:.2f}. "
            "The system is unstable — the server cannot keep up with arrivals. "
            "Increase the service rate or decrease the arrival rate."
        )
    else:
        st.success(f"Traffic intensity (rho) = {rho:.2f}. System is stable.")

    run = st.button("Run Simulation", width="stretch")

    st.divider()
    st.markdown("**Model notes**")
    st.markdown("""
    - Arrivals are Poisson distributed
    - Service times are exponentially distributed
    - Single server, FIFO, infinite queue capacity
    - Theoretical values use steady-state M/M/1 formulas
    """)


# Main area

st.title("M/M/1 Queue Simulation")

if not run:
    st.write(
        "Set the parameters in the sidebar and click **Run Simulation** to begin. "
        "The simulation generates a sequence of customer arrivals and service events, "
        "then reports performance metrics and compares them against theoretical values."
    )
    st.divider()
    st.markdown("**What is M/M/1?**")
    st.write(
        "M/M/1 is the simplest queuing model. The first M means Markovian (exponential) "
        "inter-arrival times. The second M means Markovian service times. "
        "The 1 means a single server. It is the foundation of queuing theory and is used "
        "to model systems like bank tellers, call centers, and network routers."
    )
    st.markdown("**Key formulas**")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        | Symbol | Meaning |
        |--------|---------|
        | λ (lambda) | Arrival rate |
        | μ (mu) | Service rate |
        | ρ = λ/μ | Traffic intensity (utilization) |
        """)
    with col2:
        st.markdown("""
        | Formula | Description |
        |---------|-------------|
        | Wq = ρ / (μ(1−ρ)) | Avg wait time in queue |
        | Lq = ρ² / (1−ρ) | Avg queue length |
        | W = 1 / (μ(1−ρ)) | Avg time in system |
        | L = ρ / (1−ρ) | Avg number in system |
        """)

else:
    with st.spinner("Running simulation..."):
        results = simulate_mm1(
            arrival_rate=arrival_rate,
            service_rate=service_rate,
            num_customers=num_customers,
            seed=seed_val if use_seed else None,
        )

    # ── Summary metrics ───────────────────────────────────────────────────────

    st.subheader("Results")
    st.caption(
        f"Simulated {results['num_customers']} customers over "
        f"{results['total_sim_time']:.2f} time units. "
        f"Effective arrival rate: {results['effective_lambda']:.3f} per unit time."
    )

    st.divider()

    st.markdown("**Simulated vs Theoretical**")
    st.write(
        "The table below compares what the simulation produced against the analytical "
        "steady-state values from M/M/1 theory. They should be close but not identical — "
        "the simulation is a finite sample, the theory assumes infinite time."
    )

    th = results

    comparison_data = {
        "Metric": [
            "Server utilization",
            "Average wait time (Wq)",
            "Average queue length (Lq)",
            "Average time in system (W)",
            "Average number in system (L)",
        ],
        "Simulated": [
            f"{th['utilization']:.4f}",
            f"{th['avg_wait']:.4f}",
            f"{th['avg_queue_length']:.4f}",
            f"{th['avg_time_system']:.4f}",
            f"{th['avg_num_system']:.4f}",
        ],
        "Theoretical": [
            f"{th['theory_utilization']:.4f}"  if th["theory_valid"] else "N/A (unstable)",
            f"{th['theory_avg_wait']:.4f}"     if th["theory_valid"] else "N/A",
            f"{th['theory_avg_queue_len']:.4f}" if th["theory_valid"] else "N/A",
            f"{th['theory_avg_system']:.4f}"   if th["theory_valid"] else "N/A",
            f"{th['theory_avg_num_sys']:.4f}"  if th["theory_valid"] else "N/A",
        ],
    }

    st.dataframe(
        pd.DataFrame(comparison_data),
        width="stretch",
        hide_index=True,
    )

    st.divider()

    # ── Metric cards ──────────────────────────────────────────────────────────

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Customers Simulated", results["num_customers"])
    c2.metric("Server Utilization",  f"{results['utilization']:.1%}")
    c3.metric("Avg Wait Time",       f"{results['avg_wait']:.3f}")
    c4.metric("Avg Queue Length",    f"{results['avg_queue_length']:.3f}")
    c5.metric("Customers Who Waited", f"{results['pct_waited']:.1%}")

    st.divider()

    # ── Queue length over time ─────────────────────────────────────────────────

    st.subheader("Queue Length Over Time")
    st.write("Number of customers in the system at each arrival point during the simulation.")

    queue_df = pd.DataFrame(results["queue_over_time"])
    st.line_chart(queue_df.set_index("time")["in_system"], width="stretch")

    st.divider()

    # ── Wait time distribution ─────────────────────────────────────────────────

    st.subheader("Wait Time Distribution")
    st.write(
        f"{results['pct_waited']:.1%} of customers had to wait. "
        "The histogram below shows how wait times were distributed across all customers."
    )

    wait_series = pd.Series([r["wait_time"] for r in results["log"]], name="Wait Time")
    wait_bins   = wait_series.value_counts(bins=20, sort=False).rename("Count")
    st.bar_chart(wait_bins, width="stretch")

    st.divider()

    # ── Event log ─────────────────────────────────────────────────────────────

    st.subheader("Event Log")
    st.write("Full record of every customer that passed through the system.")

    log_df = pd.DataFrame(results["log"])
    log_df.columns = [
        "Customer", "Arrival Time", "Service Start",
        "Service End", "Wait Time", "Service Time", "Time in System"
    ]

    filter_waited = st.checkbox("Show only customers who waited")
    if filter_waited:
        log_df = log_df[log_df["Wait Time"] > 0]

    st.dataframe(log_df, width="stretch", hide_index=True)
    st.caption(f"{len(log_df)} records shown.")