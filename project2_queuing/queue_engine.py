"""
queue_engine.py
---------------
M/M/1 Queue Simulation Engine

Model assumptions:
  - Arrivals follow a Poisson process (inter-arrival times are exponentially distributed)
  - Service times are exponentially distributed
  - Single server, infinite queue capacity, FIFO discipline

Kendall notation: M/M/1
"""

import random
import math


def simulate_mm1(arrival_rate: float,
                 service_rate: float,
                 num_customers: int,
                 seed: int = None) -> dict:
    """
    Run an M/M/1 queue simulation.

    Parameters
    ----------
    arrival_rate   : Average number of arrivals per unit time (lambda)
    service_rate   : Average number of customers served per unit time (mu)
    num_customers  : Number of customers to simulate
    seed           : Random seed for reproducibility (optional)

    Returns
    -------
    A dict containing the event log and all computed performance metrics.
    """

    if seed is not None:
        random.seed(seed)

    # Each record: customer_id, arrival_time, service_start, service_end,
    #              wait_time, service_time, time_in_system
    log = []

    clock         = 0.0   # simulation clock
    server_free_at = 0.0  # when the server becomes available next

    for customer_id in range(1, num_customers + 1):
        # Generate inter-arrival time ~ Exp(lambda)
        inter_arrival = random.expovariate(arrival_rate)
        clock += inter_arrival

        arrival_time = clock

        # Customer starts service when server is free or immediately if idle
        service_start = max(arrival_time, server_free_at)

        # Generate service time ~ Exp(mu)
        service_time = random.expovariate(service_rate)

        service_end  = service_start + service_time
        server_free_at = service_end

        wait_time      = service_start - arrival_time
        time_in_system = service_end  - arrival_time

        log.append({
            "customer_id":     customer_id,
            "arrival_time":    round(arrival_time,    4),
            "service_start":   round(service_start,   4),
            "service_end":     round(service_end,     4),
            "wait_time":       round(wait_time,       4),
            "service_time":    round(service_time,    4),
            "time_in_system":  round(time_in_system,  4),
        })

    # ── Compute simulation metrics ────────────────────────────────────────────

    total_wait        = sum(r["wait_time"]      for r in log)
    total_service     = sum(r["service_time"]   for r in log)
    total_in_system   = sum(r["time_in_system"] for r in log)
    total_sim_time    = log[-1]["service_end"] if log else 0

    avg_wait          = total_wait      / num_customers
    avg_service       = total_service   / num_customers
    avg_time_system   = total_in_system / num_customers
    server_busy_time  = total_service
    utilization       = server_busy_time / total_sim_time if total_sim_time > 0 else 0

    # Customers who had to wait at all
    num_waited        = sum(1 for r in log if r["wait_time"] > 0)
    pct_waited        = num_waited / num_customers

    # Approximate average queue length via Little's Law: Lq = lambda_eff * Wq
    # Use effective arrival rate from simulation
    effective_lambda  = num_customers / total_sim_time if total_sim_time > 0 else 0
    avg_queue_length  = effective_lambda * avg_wait
    avg_num_system    = effective_lambda * avg_time_system

    # ── Theoretical (steady-state) values ────────────────────────────────────
    # Valid only when rho = lambda/mu < 1

    rho = arrival_rate / service_rate  # traffic intensity

    if rho < 1:
        theory_utilization   = rho
        theory_avg_wait      = rho / (service_rate * (1 - rho))
        theory_avg_queue_len = rho ** 2 / (1 - rho)
        theory_avg_system    = 1 / (service_rate * (1 - rho))
        theory_avg_num_sys   = rho / (1 - rho)
        theory_valid         = True
    else:
        # Unstable system — queue grows without bound
        theory_utilization   = None
        theory_avg_wait      = None
        theory_avg_queue_len = None
        theory_avg_system    = None
        theory_avg_num_sys   = None
        theory_valid         = False

    # ── Queue length over time (sampled at each arrival) ──────────────────────
    # Reconstruct queue depth at each arrival moment
    queue_over_time = []
    for r in log:
        # At the moment this customer arrived, count how many are still in the system
        t = r["arrival_time"]
        in_system = sum(
            1 for other in log
            if other["arrival_time"] <= t < other["service_end"]
        )
        queue_over_time.append({
            "customer": r["customer_id"],
            "time":     r["arrival_time"],
            "in_system": in_system,
        })

    return {
        # Raw event log
        "log": log,

        # Simulation metrics
        "num_customers":    num_customers,
        "total_sim_time":   round(total_sim_time,   4),
        "avg_wait":         round(avg_wait,         4),
        "avg_service":      round(avg_service,      4),
        "avg_time_system":  round(avg_time_system,  4),
        "utilization":      round(utilization,      4),
        "avg_queue_length": round(avg_queue_length, 4),
        "avg_num_system":   round(avg_num_system,   4),
        "num_waited":       num_waited,
        "pct_waited":       round(pct_waited,       4),
        "effective_lambda": round(effective_lambda, 4),

        # Theoretical values
        "rho":                    round(rho, 4),
        "theory_valid":           theory_valid,
        "theory_utilization":     round(theory_utilization, 4)   if theory_valid else None,
        "theory_avg_wait":        round(theory_avg_wait, 4)      if theory_valid else None,
        "theory_avg_queue_len":   round(theory_avg_queue_len, 4) if theory_valid else None,
        "theory_avg_system":      round(theory_avg_system, 4)    if theory_valid else None,
        "theory_avg_num_sys":     round(theory_avg_num_sys, 4)   if theory_valid else None,

        # Queue length trace
        "queue_over_time": queue_over_time,
    }