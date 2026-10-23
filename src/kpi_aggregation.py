"""
KPI aggregation — dashboard-ready tables for the Power BI layer.

Produces the exact tables that dax/measures.dax and the Power BI data
model (see README) consume: overall KPIs, KPIs by group, by cohort,
by segment, and by month.

Usage:
    python src/kpi_aggregation.py
Outputs:
    outputs/tables/kpi_overall.csv
    outputs/tables/kpi_by_group.csv
    outputs/tables/kpi_by_cohort.csv
    outputs/tables/kpi_by_segment.csv
    outputs/tables/kpi_monthly.csv
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "raw" / "behavioral_data.csv"
TABLE_DIR = ROOT / "outputs" / "tables"


def kpi_block(df: pd.DataFrame) -> dict:
    return {
        "total_sessions": int(len(df)),
        "unique_users": int(df["user_id"].nunique()),
        "avg_session_duration_min": round(float(df["session_duration_min"].mean()), 2),
        "median_session_duration_min": round(float(df["session_duration_min"].median()), 2),
        "total_engagement_events": int(df["engagement_events"].sum()),
        "avg_engagement_events": round(float(df["engagement_events"].mean()), 2),
        "total_pages_viewed": int(df["pages_viewed"].sum()),
        "total_clicks": int(df["clicks"].sum()),
        "avg_feature_usage_count": round(float(df["feature_usage_count"].mean()), 2),
        "avg_session_score": round(float(df["session_score"].mean()), 2),
        "completed_sessions": int(df["task_completed"].sum()),
        "completion_rate_pct": round(float(df["task_completed"].mean() * 100), 2),
        "sessions_per_user": round(len(df) / df["user_id"].nunique(), 2) if df["user_id"].nunique() else 0,
    }


def grouped(df: pd.DataFrame, col: str) -> pd.DataFrame:
    rows = []
    for key, sub in df.groupby(col):
        row = {col: key}
        row.update(kpi_block(sub))
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    print(f"Loaded {len(df):,} records for KPI aggregation")

    overall = pd.DataFrame([kpi_block(df)])
    overall.to_csv(TABLE_DIR / "kpi_overall.csv", index=False)
    print("kpi_overall:")
    print(overall.to_string(index=False))

    grouped(df, "experimental_group").to_csv(TABLE_DIR / "kpi_by_group.csv", index=False)
    grouped(df, "cohort").to_csv(TABLE_DIR / "kpi_by_cohort.csv", index=False)
    grouped(df, "user_segment").to_csv(TABLE_DIR / "kpi_by_segment.csv", index=False)

    df["month"] = df["timestamp"].dt.to_period("M").dt.to_timestamp()
    monthly_rows = []
    for month, sub in df.groupby("month"):
        row = {"month": month.date().isoformat()}
        row.update(kpi_block(sub))
        monthly_rows.append(row)
    pd.DataFrame(monthly_rows).to_csv(TABLE_DIR / "kpi_monthly.csv", index=False)

    print("Saved: kpi_overall.csv, kpi_by_group.csv, kpi_by_cohort.csv, kpi_by_segment.csv, kpi_monthly.csv")


if __name__ == "__main__":
    main()
