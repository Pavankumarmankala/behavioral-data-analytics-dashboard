"""
Exploratory Data Analysis (EDA) for the behavioral dataset.

Produces distribution charts, group-comparison charts, and summary
tables using pandas and matplotlib.

Usage:
    python src/eda.py
Inputs:
    data/raw/behavioral_data.csv
Outputs:
    outputs/charts/*.png
    outputs/tables/descriptive_stats.csv
    outputs/tables/group_summary.csv
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "raw" / "behavioral_data.csv"
CHART_DIR = ROOT / "outputs" / "charts"
TABLE_DIR = ROOT / "outputs" / "tables"

NUMERIC_COLS = [
    "session_duration_min",
    "engagement_events",
    "pages_viewed",
    "clicks",
    "feature_usage_count",
    "session_score",
    "task_completed",
]


def main() -> None:
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    print(f"Loaded {len(df):,} records, {df['timestamp'].min().date()} to {df['timestamp'].max().date()}")

    # --- Descriptive statistics ---
    desc = df[NUMERIC_COLS].describe().T
    desc.to_csv(TABLE_DIR / "descriptive_stats.csv")
    print(f"Saved descriptive_stats.csv ({len(desc)} metrics)")

    # --- Group summary ---
    group_summary = (
        df.groupby("experimental_group")
        .agg(
            sessions=("record_id", "count"),
            unique_users=("user_id", "nunique"),
            avg_session_duration_min=("session_duration_min", "mean"),
            median_session_duration_min=("session_duration_min", "median"),
            avg_engagement_events=("engagement_events", "mean"),
            avg_pages_viewed=("pages_viewed", "mean"),
            avg_feature_usage_count=("feature_usage_count", "mean"),
            avg_session_score=("session_score", "mean"),
            completion_rate=("task_completed", "mean"),
        )
        .round(4)
    )
    group_summary.to_csv(TABLE_DIR / "group_summary.csv")
    print("Saved group_summary.csv")
    print(group_summary)

    # --- Chart 1: Session duration distribution ---
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(df["session_duration_min"], bins=40, color="#4C72B0", edgecolor="white")
    ax.set_xlabel("Session duration (minutes)")
    ax.set_ylabel("Sessions")
    ax.set_title("Distribution of Session Duration")
    fig.tight_layout()
    fig.savefig(CHART_DIR / "session_duration_distribution.png", dpi=150)
    plt.close(fig)

    # --- Chart 2: Engagement events distribution ---
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(df["engagement_events"], bins=40, color="#55A868", edgecolor="white")
    ax.set_xlabel("Engagement events per session")
    ax.set_ylabel("Sessions")
    ax.set_title("Distribution of Engagement Events")
    fig.tight_layout()
    fig.savefig(CHART_DIR / "engagement_events_distribution.png", dpi=150)
    plt.close(fig)

    # --- Chart 3: Session duration by experimental group (box plot) ---
    fig, ax = plt.subplots(figsize=(8, 5))
    data = [df.loc[df["experimental_group"] == g, "session_duration_min"] for g in ["Control", "Intervention"]]
    ax.boxplot(data, labels=["Control", "Intervention"])
    ax.set_ylabel("Session duration (minutes)")
    ax.set_title("Session Duration by Experimental Group")
    fig.tight_layout()
    fig.savefig(CHART_DIR / "session_duration_by_group.png", dpi=150)
    plt.close(fig)

    # --- Chart 4: Completion rate by group ---
    rates = df.groupby("experimental_group")["task_completed"].mean()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(rates.index, rates.values * 100, color=["#4C72B0", "#DD8452"])
    ax.set_ylabel("Completion rate (%)")
    ax.set_title("Task Completion Rate by Experimental Group")
    for i, v in enumerate(rates.values):
        ax.text(i, v * 100 + 1, f"{v*100:.1f}%", ha="center")
    fig.tight_layout()
    fig.savefig(CHART_DIR / "completion_rate_by_group.png", dpi=150)
    plt.close(fig)

    # --- Chart 5: Feature usage by primary feature ---
    feat = df["primary_feature"].value_counts()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(feat.index, feat.values, color="#8172B2")
    ax.set_xlabel("Primary feature")
    ax.set_ylabel("Sessions")
    ax.set_title("Sessions by Primary Feature Used")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    fig.tight_layout()
    fig.savefig(CHART_DIR / "feature_usage_by_feature.png", dpi=150)
    plt.close(fig)

    # --- Chart 6: Monthly session volume (quick EDA trend view) ---
    monthly_counts = df.set_index("timestamp").resample("M")["record_id"].count()
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(monthly_counts.index, monthly_counts.values, color="#4C72B0", linewidth=1.8)
    ax.set_xlabel("Month")
    ax.set_ylabel("Sessions")
    ax.set_title("Monthly Session Volume (EDA overview)")
    fig.tight_layout()
    fig.savefig(CHART_DIR / "monthly_session_volume.png", dpi=150)
    plt.close(fig)

    print(f"Charts saved to {CHART_DIR}:")
    for p in sorted(CHART_DIR.glob("*.png")):
        print(f"  - {p.name}")


if __name__ == "__main__":
    main()
