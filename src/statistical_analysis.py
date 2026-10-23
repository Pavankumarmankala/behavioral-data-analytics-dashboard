"""
Statistical analysis: hypothesis testing, correlation, and 95% CIs.

Methods (SciPy + pandas), matching the resume description:
  - Independent-samples t-test (Welch's): session duration,
    Control vs Intervention
  - Chi-square test of independence: task completion vs group
  - Pearson correlation analysis across numeric behavioral variables
  - 95% confidence intervals for group means, the mean difference,
    and the overall completion rate (validated with 95% CIs)

Usage:
    python src/statistical_analysis.py
Outputs:
    outputs/tables/statistical_results.csv
    outputs/tables/correlation_matrix.csv
    outputs/tables/statistical_results.txt
"""

import math
from pathlib import Path

import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "raw" / "behavioral_data.csv"
TABLE_DIR = ROOT / "outputs" / "tables"

CORR_COLS = [
    "session_duration_min",
    "engagement_events",
    "pages_viewed",
    "clicks",
    "feature_usage_count",
    "session_score",
    "task_completed",
]


def mean_ci_95(series: pd.Series) -> tuple[float, float, float]:
    """Return (mean, ci_low, ci_high) using t-distribution, 95% CI."""
    n = len(series)
    mean = float(series.mean())
    sem = float(stats.sem(series))
    if n < 2 or sem == 0:
        return mean, mean, mean
    margin = float(stats.t.ppf(0.975, df=n - 1) * sem)
    return mean, mean - margin, mean + margin


def proportion_ci_95(successes: int, n: int) -> tuple[float, float, float]:
    """Wilson-style normal-approx 95% CI for a proportion."""
    if n == 0:
        return 0.0, 0.0, 0.0
    p = successes / n
    z = 1.96
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    margin = (z / denom) * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    return p, centre - margin, centre + margin


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    print(f"Loaded {len(df):,} records")

    lines: list[str] = []
    lines.append("Behavioral Data — Statistical Analysis Results")
    lines.append("=" * 60)
    lines.append(f"Records: {len(df):,}  |  Span: {df['timestamp'].min().date()} to {df['timestamp'].max().date()}")
    lines.append("")

    results_rows = []

    # --- 1. Welch's t-test: session duration by group ---
    control = df.loc[df["experimental_group"] == "Control", "session_duration_min"]
    intervention = df.loc[df["experimental_group"] == "Intervention", "session_duration_min"]
    t_stat, p_val = stats.ttest_ind(intervention, control, equal_var=False)

    c_mean, c_lo, c_hi = mean_ci_95(control)
    i_mean, i_lo, i_hi = mean_ci_95(intervention)
    diff = i_mean - c_mean
    # CI for difference (Welch)
    se_diff = math.sqrt(control.var(ddof=1) / len(control) + intervention.var(ddof=1) / len(intervention))
    # Welch-Satterthwaite df
    v1, v2 = control.var(ddof=1) / len(control), intervention.var(ddof=1) / len(intervention)
    welch_df = (v1 + v2) ** 2 / (v1**2 / (len(control) - 1) + v2**2 / (len(intervention) - 1))
    margin_diff = float(stats.t.ppf(0.975, df=welch_df) * se_diff)

    lines.append("1. Hypothesis Test — Session Duration (Welch's independent t-test)")
    lines.append(f"   Control:      n={len(control):,}, mean={c_mean:.2f} min, 95% CI [{c_lo:.2f}, {c_hi:.2f}]")
    lines.append(f"   Intervention: n={len(intervention):,}, mean={i_mean:.2f} min, 95% CI [{i_lo:.2f}, {i_hi:.2f}]")
    lines.append(f"   Difference (Intervention - Control): {diff:.2f} min, 95% CI [{diff - margin_diff:.2f}, {diff + margin_diff:.2f}]")
    lines.append(f"   t = {t_stat:.3f}, p = {p_val:.3e}  -> {'Significant' if p_val < 0.05 else 'Not significant'} at alpha=0.05")
    lines.append("")
    results_rows.append({"test": "t-test_session_duration_by_group", "statistic": t_stat, "p_value": p_val,
                         "effect_or_diff": diff, "ci_low": diff - margin_diff, "ci_high": diff + margin_diff,
                         "significant_0.05": bool(p_val < 0.05)})

    # --- 2. Chi-square: completion vs group ---
    contingency = pd.crosstab(df["experimental_group"], df["task_completed"])
    chi2, chi_p, chi_dof, _ = stats.chi2_contingency(contingency)
    lines.append("2. Hypothesis Test — Task Completion vs Group (Chi-square)")
    lines.append(f"   Contingency table:\n{contingency.to_string()}")
    lines.append(f"   chi2 = {chi2:.3f}, df = {chi_dof}, p = {chi_p:.3e}  -> {'Significant' if chi_p < 0.05 else 'Not significant'} at alpha=0.05")
    lines.append("")
    results_rows.append({"test": "chi-square_completion_by_group", "statistic": chi2, "p_value": chi_p,
                         "effect_or_diff": "", "ci_low": "", "ci_high": "", "significant_0.05": bool(chi_p < 0.05)})

    # Overall completion rate CI
    successes = int(df["task_completed"].sum())
    p_rate, p_lo, p_hi = proportion_ci_95(successes, len(df))
    lines.append(f"   Overall completion rate: {p_rate:.2%} , 95% CI [{p_lo:.2%}, {p_hi:.2%}]")
    for grp in ["Control", "Intervention"]:
        sub = df[df["experimental_group"] == grp]
        pr, lo, hi = proportion_ci_95(int(sub["task_completed"].sum()), len(sub))
        lines.append(f"   {grp} completion rate: {pr:.2%} , 95% CI [{lo:.2%}, {hi:.2%}]")
    lines.append("")

    # --- 3. Correlation analysis (Pearson) ---
    corr = df[CORR_COLS].corr(method="pearson").round(4)
    corr.to_csv(TABLE_DIR / "correlation_matrix.csv")
    lines.append("3. Correlation Analysis (Pearson r)")
    lines.append(corr.to_string())
    lines.append("")
    # Highlight key pairs with p-values
    key_pairs = [
        ("session_duration_min", "engagement_events"),
        ("session_duration_min", "task_completed"),
        ("engagement_events", "task_completed"),
        ("feature_usage_count", "task_completed"),
        ("session_duration_min", "session_score"),
    ]
    lines.append("   Key pairwise correlations:")
    for a, b in key_pairs:
        r, rp = stats.pearsonr(df[a], df[b])
        lines.append(f"   {a} vs {b}: r = {r:.3f}, p = {rp:.3e}")
        results_rows.append({"test": f"pearson_{a}_vs_{b}", "statistic": r, "p_value": rp,
                             "effect_or_diff": r, "ci_low": "", "ci_high": "", "significant_0.05": bool(rp < 0.05)})
    lines.append("")
    lines.append("All findings reported with 95% confidence intervals where applicable.")

    text = "\n".join(lines)
    print(text)
    (TABLE_DIR / "statistical_results.txt").write_text(text + "\n", encoding="utf-8")
    pd.DataFrame(results_rows).to_csv(TABLE_DIR / "statistical_results.csv", index=False)
    print(f"\nSaved: statistical_results.csv, statistical_results.txt, correlation_matrix.csv -> {TABLE_DIR}")


if __name__ == "__main__":
    main()
