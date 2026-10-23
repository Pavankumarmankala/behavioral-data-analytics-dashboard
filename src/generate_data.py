"""
Synthetic behavioral dataset generator.

Produces a deterministic, seeded dataset of 50,000+ session-level
behavioral records spanning 3+ years, consistent with the project
description: behavioral research data suitable for exploratory data
analysis, hypothesis testing, correlation analysis, and longitudinal
time series analysis.

Usage:
    python src/generate_data.py
Output:
    data/raw/behavioral_data.csv
"""

import math
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

SEED = 42
N_RECORDS = 52_000
N_USERS = 2_000
START_DATE = date(2022, 1, 1)
END_DATE = date(2025, 6, 30)  # 3.5 years

FEATURES = ["search", "video", "quiz", "discussion", "download", "notes"]


def main() -> None:
    rng = random.Random(SEED)

    # Build user pool with stable attributes
    users = []
    for user_id in range(1, N_USERS + 1):
        # Cohort by enrollment year, weighted toward earlier years
        cohort_year = rng.choices([2022, 2023, 2024, 2025], weights=[40, 30, 20, 10])[0]
        group = rng.choice(["Control", "Intervention"])
        segment = rng.choices(["New", "Returning", "Power"], weights=[35, 45, 20])[0]
        # Baseline engagement tendency per user (0.7 - 1.3)
        baseline = 0.7 + rng.random() * 0.6
        users.append(
            {
                "user_id": f"U{user_id:05d}",
                "cohort": f"Cohort_{cohort_year}",
                "enrollment_year": cohort_year,
                "experimental_group": group,
                "user_segment": segment,
                "baseline": baseline,
            }
        )

    total_days = (END_DATE - START_DATE).days

    records = []
    for i in range(1, N_RECORDS + 1):
        user = rng.choice(users)

        # Date: uniform over span, but not before user's cohort year starts
        cohort_start_offset = (date(user["enrollment_year"], 1, 1) - START_DATE).days
        day_offset = rng.randint(max(0, cohort_start_offset), total_days)
        session_date = START_DATE + timedelta(days=day_offset)

        # Longitudinal trend: slight growth over time (normalized 0..1)
        time_progress = day_offset / total_days if total_days else 0

        # Group effect: Intervention modestly higher engagement
        group_factor = 1.18 if user["experimental_group"] == "Intervention" else 1.0
        segment_factor = {"New": 0.85, "Returning": 1.0, "Power": 1.35}[user["user_segment"]]
        trend_factor = 1.0 + 0.15 * time_progress

        # Session duration (minutes): log-normal-like via exp of normal-ish
        # Box-Muller style using random.gauss
        base_duration = rng.gauss(24, 9)
        session_duration = max(1.0, base_duration * user["baseline"] * group_factor * segment_factor * trend_factor)
        session_duration = round(min(session_duration, 120.0), 2)

        # Engagement events correlated with duration
        expected_events = session_duration * 0.55 * user["baseline"] * group_factor
        engagement_events = max(0, int(rng.gauss(expected_events, max(2.0, expected_events * 0.3))))

        # Pages viewed correlated with engagement
        pages_viewed = max(1, int(engagement_events * rng.uniform(0.4, 0.7) + rng.randint(0, 3)))

        # Clicks correlated with pages
        clicks = max(0, int(pages_viewed * rng.uniform(1.2, 2.4)))

        # Feature usage: count of distinct features used in session (0-6)
        # Probability per feature rises with duration
        p_feature = min(0.85, 0.15 + session_duration / 90.0)
        features_used_list = [f for f in FEATURES if rng.random() < p_feature]
        feature_usage_count = len(features_used_list)
        primary_feature = rng.choice(features_used_list) if features_used_list else "none"

        # Completion / conversion: logistic function of duration, group, features
        logit = (
            -1.6
            + 0.045 * session_duration
            + 0.18 * feature_usage_count
            + (0.45 if user["experimental_group"] == "Intervention" else 0.0)
            + 0.25 * time_progress
        )
        p_complete = 1 / (1 + math.exp(-logit))
        task_completed = 1 if rng.random() < p_complete else 0

        # Session score (0-100 engagement score)
        session_score = round(
            max(0.0, min(100.0, rng.gauss(48 + session_duration * 0.45 + feature_usage_count * 3.0, 14))),
            2,
        )

        records.append(
            {
                "record_id": i,
                "user_id": user["user_id"],
                "timestamp": session_date.isoformat(),
                "cohort": user["cohort"],
                "experimental_group": user["experimental_group"],
                "user_segment": user["user_segment"],
                "session_duration_min": session_duration,
                "engagement_events": engagement_events,
                "pages_viewed": pages_viewed,
                "clicks": clicks,
                "feature_usage_count": feature_usage_count,
                "primary_feature": primary_feature,
                "session_score": session_score,
                "task_completed": task_completed,
            }
        )

    df = pd.DataFrame(records).sort_values(["timestamp", "record_id"]).reset_index(drop=True)
    # Re-assign record_id after sort to keep it sequential by date
    df["record_id"] = range(1, len(df) + 1)

    out_path = Path(__file__).resolve().parent.parent / "data" / "raw" / "behavioral_data.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    print(f"Generated {len(df):,} records")
    print(f"Date span: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Unique users: {df['user_id'].nunique():,}")
    print(f"Groups: {df['experimental_group'].value_counts().to_dict()}")
    print(f"Cohorts: {sorted(df['cohort'].unique())}")
    print(f"Saved to: {out_path}")


if __name__ == "__main__":
    main()
