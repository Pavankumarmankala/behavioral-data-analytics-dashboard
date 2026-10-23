"""
Time series analysis over the 3+ year longitudinal span.

Aggregates behavioral records monthly, computes rolling averages and
a linear trend (SciPy linregress), and charts the longitudinal pattern.

Usage:
    python src/time_series_analysis.py
Outputs:
    outputs/tables/monthly_timeseries.csv
    outputs/charts/monthly_trend.png
    outputs/charts/monthly_completion_rate_trend.png
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "raw" / "behavioral_data.csv"
CHART_DIR = ROOT / "outputs" / "charts"
TABLE_DIR = ROOT / "outputs" / "tables"


def main() -> None:
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    df = df.sort_values("timestamp")

    monthly = (
        df.set_index("timestamp")
        .resample("M")
        .agg(
            sessions=("record_id", "count"),
            unique_users=("user_id", "nunique"),
            avg_session_duration_min=("session_duration_min", "mean"),
            avg_engagement_events=("engagement_events", "mean"),
            avg_session_score=("session_score", "mean"),
            completion_rate=("task_completed", "mean"),
        )
        .reset_index()
        .rename(columns={"timestamp": "month"})
    )
    monthly["sessions_3mo_rolling_avg"] = monthly["sessions"].rolling(3, min_periods=1).mean().round(2)
    monthly["completion_rate_3mo_rolling_avg"] = monthly["completion_rate"].rolling(3, min_periods=1).mean().round(4)
    monthly = monthly.round(4)
    monthly.to_csv(TABLE_DIR / "monthly_timeseries.csv", index=False)

    print(f"Monthly periods: {len(monthly)} ({monthly['month'].min().date()} to {monthly['month'].max().date()})")
    print(monthly.head(6).to_string(index=False))

    # Linear trend on monthly sessions
    x = range(len(monthly))
    slope, intercept, r_value, p_value, _ = stats.linregress(x, monthly["sessions"])
    print(f"\nTrend (sessions/month): slope={slope:.2f}, r={r_value:.3f}, p={p_value:.3e}")

    # Also trend on avg duration
    slope_d, _, r_d, p_d, _ = stats.linregress(x, monthly["avg_session_duration_min"])
    print(f"Trend (avg duration): slope={slope_d:.4f} min/month, r={r_d:.3f}, p={p_d:.3e}")

    # Yearly summary
    df["year"] = df["timestamp"].dt.year
    yearly = df.groupby("year").agg(
        sessions=("record_id", "count"),
        avg_session_duration_min=("session_duration_min", "mean"),
        completion_rate=("task_completed", "mean"),
    ).round(4)
    yearly.to_csv(TABLE_DIR / "yearly_summary.csv")
    print("\nYearly summary:")
    print(yearly)

    # Chart 1: Monthly sessions + rolling avg + trend line
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(monthly["month"], monthly["sessions"], label="Monthly sessions", color="#4C72B0", linewidth=1.6)
    ax.plot(monthly["month"], monthly["sessions_3mo_rolling_avg"], label="3-month rolling avg", color="#DD8452", linewidth=2)
    trend_line = [intercept + slope * i for i in x]
    ax.plot(monthly["month"], trend_line, label=f"Linear trend (slope {slope:.1f}/mo)", color="gray", linestyle="--")
    ax.set_xlabel("Month")
    ax.set_ylabel("Sessions")
    ax.set_title("Longitudinal Trend — Monthly Sessions (3+ Years)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(CHART_DIR / "monthly_trend.png", dpi=150)
    plt.close(fig)

    # Chart 2: Monthly completion rate
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(monthly["month"], monthly["completion_rate"] * 100, label="Completion rate (%)", color="#55A868", linewidth=1.6)
    ax.plot(monthly["month"], monthly["completion_rate_3mo_rolling_avg"] * 100, label="3-month rolling avg", color="#8172B2", linewidth=2)
    ax.set_xlabel("Month")
    ax.set_ylabel("Completion rate (%)")
    ax.set_title("Longitudinal Trend — Monthly Task Completion Rate")
    ax.legend()
    fig.tight_layout()
    fig.savefig(CHART_DIR / "monthly_completion_rate_trend.png", dpi=150)
    plt.close(fig)

    print(f"\nSaved monthly_timeseries.csv, yearly_summary.csv and 2 charts.")


if __name__ == "__main__":
    main()
