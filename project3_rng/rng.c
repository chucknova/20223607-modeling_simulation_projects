/*
 * rng.c
 * -----
 * Random Number Generator - Modeling & Simulation Project 3
 *
 * Algorithm: Linear Congruential Generator (LCG)
 *
 * Formula:
 *   X(n+1) = (a * X(n) + c) mod m
 *
 * Parameters used (from Numerical Recipes):
 *   m = 2^32  = 4294967296  (modulus)
 *   a = 1664525             (multiplier)
 *   c = 1013904223          (increment)
 *
 * These parameters satisfy the Hull-Dobell theorem for full-period LCGs,
 * meaning the generator cycles through all m values before repeating.
 *
 * The chi-square test checks whether the generated numbers are uniformly
 * distributed across k equal-width intervals (bins).
 *
 * Compile:  gcc rng.c -o rng -lm
 * Run:      ./rng [count] [seed] [bins]
 *           ./rng 1000 42 10
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

/* LCG parameters (Numerical Recipes) */
#define LCG_M  4294967296.0   /* 2^32 */
#define LCG_A  1664525
#define LCG_C  1013904223

/* Defaults */
#define DEFAULT_COUNT  1000
#define DEFAULT_BINS   10


/* ── LCG state ─────────────────────────────────────────────────────────────── */

static unsigned long lcg_state = 0;

void lcg_seed(unsigned long seed) {
    lcg_state = seed;
}

/* Returns next raw integer from the LCG */
unsigned long lcg_next_int(void) {
    lcg_state = (unsigned long)((LCG_A * (double)lcg_state + LCG_C));
    /* Keep within 32-bit range */
    lcg_state = lcg_state & 0xFFFFFFFF;
    return lcg_state;
}

/* Returns a uniform float in [0, 1) */
double lcg_next(void) {
    return lcg_next_int() / LCG_M;
}


/* ── Chi-square test ───────────────────────────────────────────────────────── */

/*
 * Chi-square goodness-of-fit test for uniformity.
 *
 * Divides [0, 1) into k equal bins and counts observed frequencies.
 * Expected frequency per bin = n / k.
 *
 * Test statistic: chi2 = sum((observed - expected)^2 / expected)
 *
 * Under H0 (uniform distribution), chi2 follows a chi-square distribution
 * with (k - 1) degrees of freedom.
 *
 * Critical value at alpha=0.05, df=(k-1) is looked up from a table.
 * If chi2 <= critical value, we fail to reject H0 (distribution appears uniform).
 */

/* Critical values at alpha=0.05 for df = 1..20 */
static const double CHI2_CRITICAL_005[] = {
    0.0,    /* placeholder for index 0 */
    3.841,  /* df=1  */
    5.991,  /* df=2  */
    7.815,  /* df=3  */
    9.488,  /* df=4  */
   11.070,  /* df=5  */
   12.592,  /* df=6  */
   14.067,  /* df=7  */
   15.507,  /* df=8  */
   16.919,  /* df=9  */
   18.307,  /* df=10 */
   19.675,  /* df=11 */
   21.026,  /* df=12 */
   22.362,  /* df=13 */
   23.685,  /* df=14 */
   24.996,  /* df=15 */
   26.296,  /* df=16 */
   27.587,  /* df=17 */
   28.869,  /* df=18 */
   30.144,  /* df=19 */
   31.410,  /* df=20 */
};

typedef struct {
    double  statistic;      /* computed chi-square statistic */
    int     degrees_of_freedom;
    double  critical_value; /* at alpha = 0.05 */
    int     reject_h0;      /* 1 = reject, 0 = fail to reject */
    int    *observed;        /* observed counts per bin */
    double  expected;       /* expected count per bin (same for all) */
    int     bins;
} ChiSquareResult;

ChiSquareResult chi_square_test(double *numbers, int n, int bins) {
    ChiSquareResult result;
    result.bins     = bins;
    result.expected = (double)n / bins;
    result.observed = (int *)calloc(bins, sizeof(int));

    /* Count observations in each bin */
    for (int i = 0; i < n; i++) {
        int bin = (int)(numbers[i] * bins);
        if (bin == bins) bin = bins - 1;  /* edge case: value exactly 1.0 */
        result.observed[bin]++;
    }

    /* Compute chi-square statistic */
    double chi2 = 0.0;
    for (int i = 0; i < bins; i++) {
        double diff = result.observed[i] - result.expected;
        chi2 += (diff * diff) / result.expected;
    }

    result.statistic          = chi2;
    result.degrees_of_freedom = bins - 1;

    /* Look up critical value (table covers df 1..20) */
    int df = result.degrees_of_freedom;
    if (df >= 1 && df <= 20) {
        result.critical_value = CHI2_CRITICAL_005[df];
    } else {
        /* Approximation for df > 20: chi2_crit ~ df * (1 - 2/(9*df) + 1.645*sqrt(2/(9*df)))^3 */
        double term = 1.0 - 2.0 / (9.0 * df) + 1.645 * sqrt(2.0 / (9.0 * df));
        result.critical_value = df * term * term * term;
    }

    result.reject_h0 = (result.statistic > result.critical_value) ? 1 : 0;

    return result;
}


/* ── Helpers ───────────────────────────────────────────────────────────────── */

void print_separator(int width) {
    for (int i = 0; i < width; i++) putchar('-');
    putchar('\n');
}

void print_header(const char *title) {
    printf("\n");
    print_separator(60);
    printf("  %s\n", title);
    print_separator(60);
}


/* ── Main ──────────────────────────────────────────────────────────────────── */

int main(int argc, char *argv[]) {

    /* Parse arguments */
    int count = (argc > 1) ? atoi(argv[1]) : DEFAULT_COUNT;
    unsigned long seed = (argc > 2) ? (unsigned long)atol(argv[2]) : (unsigned long)time(NULL);
    int bins  = (argc > 3) ? atoi(argv[3]) : DEFAULT_BINS;

    if (count <= 0) { fprintf(stderr, "Error: count must be > 0\n"); return 1; }
    if (bins  <= 1) { fprintf(stderr, "Error: bins must be > 1\n");  return 1; }
    if (bins  > 20) { fprintf(stderr, "Error: bins must be <= 20 (chi-square table limit)\n"); return 1; }
    if (count < bins * 5) {
        fprintf(stderr,
            "Warning: count (%d) is small relative to bins (%d). "
            "Chi-square test requires at least 5 expected per bin (need >= %d).\n",
            count, bins, bins * 5);
    }

    /* Seed the generator */
    lcg_seed(seed);

    /* Generate numbers */
    double *numbers = (double *)malloc(count * sizeof(double));
    if (!numbers) { fprintf(stderr, "Error: memory allocation failed\n"); return 1; }

    for (int i = 0; i < count; i++) {
        numbers[i] = lcg_next();
    }

    /* ── Print configuration ───────────────────────────────────────────────── */

    print_header("LCG Random Number Generator");
    printf("  Algorithm   : Linear Congruential Generator (LCG)\n");
    printf("  Formula     : X(n+1) = (a * X(n) + c) mod m\n");
    printf("  Multiplier  : a = %d\n",    LCG_A);
    printf("  Increment   : c = %d\n",    LCG_C);
    printf("  Modulus     : m = 2^32 = 4294967296\n");
    printf("  Seed        : %lu\n",       seed);
    printf("  Count       : %d\n",        count);
    printf("  Bins        : %d\n",        bins);

    /* ── Print sample output ───────────────────────────────────────────────── */

    print_header("Sample Output (first 20 numbers)");
    printf("  %-6s  %-20s  %s\n", "Index", "Raw (unsigned int)", "Normalized [0, 1)");
    print_separator(60);

    lcg_seed(seed);   /* re-seed to show the sequence from the start */
    int show = (count < 20) ? count : 20;
    for (int i = 0; i < show; i++) {
        unsigned long raw = lcg_next_int();
        double norm = raw / LCG_M;
        printf("  %-6d  %-20lu  %.10f\n", i + 1, raw, norm);
    }
    if (count > 20) {
        printf("  ... (%d more numbers generated)\n", count - 20);
    }

    /* ── Descriptive statistics ────────────────────────────────────────────── */

    double sum = 0.0, sum_sq = 0.0;
    double min_val = numbers[0], max_val = numbers[0];

    for (int i = 0; i < count; i++) {
        sum    += numbers[i];
        sum_sq += numbers[i] * numbers[i];
        if (numbers[i] < min_val) min_val = numbers[i];
        if (numbers[i] > max_val) max_val = numbers[i];
    }

    double mean     = sum / count;
    double variance = (sum_sq / count) - (mean * mean);
    double std_dev  = sqrt(variance);

    /* Theoretical values for U(0,1): mean=0.5, variance=1/12, std=0.2887 */

    print_header("Descriptive Statistics");
    printf("  %-25s  %-12s  %s\n", "Metric", "Simulated", "Theoretical U(0,1)");
    print_separator(60);
    printf("  %-25s  %-12.6f  %.6f\n", "Mean",              mean,    0.5);
    printf("  %-25s  %-12.6f  %.6f\n", "Variance",          variance, 1.0/12.0);
    printf("  %-25s  %-12.6f  %.6f\n", "Std deviation",     std_dev,  sqrt(1.0/12.0));
    printf("  %-25s  %-12.6f  %.6f\n", "Min",               min_val,  0.0);
    printf("  %-25s  %-12.6f  %.6f\n", "Max",               max_val,  1.0);

    /* ── Chi-square test ───────────────────────────────────────────────────── */

    ChiSquareResult cs = chi_square_test(numbers, count, bins);

    print_header("Chi-Square Uniformity Test");
    printf("  Null hypothesis (H0): numbers are uniformly distributed\n\n");
    printf("  %-20s  %s\n", "Bin", "Observed    Expected");
    print_separator(60);
    for (int i = 0; i < bins; i++) {
        printf("  [%.2f, %.2f)%-9s  %-12d  %.2f\n",
               (double)i / bins,
               (double)(i + 1) / bins,
               "",
               cs.observed[i],
               cs.expected);
    }
    print_separator(60);
    printf("\n");
    printf("  Chi-square statistic : %.4f\n",  cs.statistic);
    printf("  Degrees of freedom   : %d\n",    cs.degrees_of_freedom);
    printf("  Critical value       : %.3f  (alpha = 0.05)\n", cs.critical_value);
    printf("\n");

    if (!cs.reject_h0) {
        printf("  Result: PASS\n");
        printf("  The statistic (%.4f) does not exceed the critical value (%.3f).\n",
               cs.statistic, cs.critical_value);
        printf("  There is no significant evidence against uniformity.\n");
    } else {
        printf("  Result: FAIL\n");
        printf("  The statistic (%.4f) exceeds the critical value (%.3f).\n",
               cs.statistic, cs.critical_value);
        printf("  The distribution does not appear to be uniform at the 5%% significance level.\n");
    }

    printf("\n");
    print_separator(60);
    printf("\n");

    /* Cleanup */
    free(numbers);
    free(cs.observed);

    return 0;
}