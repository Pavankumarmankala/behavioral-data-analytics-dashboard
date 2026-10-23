# Behavioral Data Analytics Dashboard

Analyzed behavioral datasets with Python and statistical techniques, applying exploratory data analysis to identify trends and actionable patterns that supported research decisions. Designed and delivered Power BI dashboards tracking key KPIs, translating stakeholder needs into clear, data-driven insights and recommendations.

This repository is a standalone, reproducible implementation of that work: a synthetic behavioral dataset at the same scale described in the project (50,000+ records spanning 3+ years), the full Python analysis pipeline, and the Power BI KPI layer defined as DAX measures and a documented data model.

> **Data note:** The dataset in this repo is synthetic and generated deterministically (`src/generate_data.py`, seed 42) so the project is shareable and reproducible. It mirrors the structure and scale of the original research data — session-level behavioral records with cohort/group, engagement, feature usage, and completion fields — without containing any real participant data.

## Scale

- **50,000+ behavioral records** — generator produces 52,000 session-level records
- **Longitudinal span: 3+ years** — 2022-01-01 to 2025-06-30 (3.5 years)
- **2,000 users** across cohorts, experimental groups, and user segments

## Dataset Schema

File: `data/raw/behavioral_data.csv` (generated, not committed — run the generator)

| Column | Description |
|---|---|
| `record_id` | Sequential session record ID |
| `user_id` | Anonymized user ID (e.g., `U00001`) |
| `timestamp` | Session date |
| `cohort` | Enrollment cohort (`Cohort_2022` … `Cohort_2025`) |
| `experimental_group` | `Control` or `Intervention` |
| `user_segment` | `New`, `Returning`, or `Power` |
| `session_duration_min` | Session duration in minutes |
| `engagement_events` | Engagement events in the session |
| `pages_viewed` | Pages viewed |
| `clicks` | Clicks |
| `feature_usage_count` | Distinct features used (0–6) |
| `primary_feature` | Primary feature used (`search`, `video`, `quiz`, `discussion`, `download`, `notes`, `none`) |
| `session_score` | Engagement score (0–100) |
| `task_completed` | Completion / conversion flag (0/1) |

## Methods

### 1. Exploratory Data Analysis — `src/eda.py`
- Descriptive statistics for all numeric behavioral variables
- Distributions: session duration and engagement events (histograms)
- Group comparisons: session duration by experimental group (box plot), completion rate by group, feature usage by primary feature
- Monthly session volume overview

Outputs: `outputs/tables/descriptive_stats.csv`, `outputs/tables/group_summary.csv`, charts in `outputs/charts/`

### 2. Hypothesis Testing & Correlation — `src/statistical_analysis.py`
Using Python's **SciPy** and **pandas**, exactly as described in the research work:
- **Welch's independent-samples t-test** — session duration, Control vs. Intervention
- **Chi-square test of independence** — task completion vs. experimental group
- **Pearson correlation analysis** — full correlation matrix across duration, engagement, pages, clicks, feature usage, session score, and completion, with p-values for key pairs
- **95% confidence intervals** — for group means, the group mean difference (Welch–Satterthwaite), and completion rates (overall and by group). Findings are validated with 95% confidence intervals.

Outputs: `outputs/tables/statistical_results.csv`, `outputs/tables/statistical_results.txt`, `outputs/tables/correlation_matrix.csv`

### 3. Time Series Analysis — `src/time_series_analysis.py`
- Monthly aggregation across the full 3+ year longitudinal span (42 months)
- 3-month rolling averages for sessions and completion rate
- Linear trend estimation (`scipy.stats.linregress`) for monthly sessions and average session duration, with slope, r, and p-value
- Yearly summary table

Outputs: `outputs/tables/monthly_timeseries.csv`, `outputs/tables/yearly_summary.csv`, `outputs/charts/monthly_trend.png`, `outputs/charts/monthly_completion_rate_trend.png`

### 4. KPI Aggregation — `src/kpi_aggregation.py`
Produces the dashboard-ready KPI tables that the Power BI layer consumes:
- `kpi_overall.csv` — single-row overall KPIs
- `kpi_by_group.csv` — KPIs by experimental group
- `kpi_by_cohort.csv` — KPIs by cohort
- `kpi_by_segment.csv` — KPIs by user segment
- `kpi_monthly.csv` — KPIs by month

KPI definitions: total sessions, unique users, sessions per user, average/median session duration, total/average engagement events, total pages viewed, total clicks, average feature usage count, average session score, completed sessions, and completion rate (%).

## Power BI Dashboard

> No `.pbix` file is included in this repository. The Power BI layer is represented by [`dax/measures.dax`](dax/measures.dax) plus the data-model description below — the measures and model fully define the dashboard and can be recreated in Power BI Desktop from the generated CSV.

### Data Model
- **Fact table:** `behavioral_data` — one row per session record (schema above), loaded from `data/raw/behavioral_data.csv` or from the KPI CSVs in `outputs/tables/`
- **Date table:** a calendar table on `timestamp` (marked as the date table) to enable the time-intelligence measures (MoM change, YTD, 3-month rolling average) in `dax/measures.dax`
- **Slicers / filters:** `experimental_group`, `cohort`, `user_segment`, `primary_feature`, and date range

### Dashboard Pages & KPIs

**Page 1 — Overview**
- KPI cards: Total Sessions, Unique Users, Avg Session Duration (min), Completion Rate %
- Monthly sessions trend (with 3-month rolling average)
- Completion rate trend over time

**Page 2 — Group Comparison**
- KPI cards: Completion Rate – Control vs. Intervention, Completion Rate Difference (pp), Avg Duration – Control vs. Intervention
- Session duration distribution by group
- Completion rate by experimental group

**Page 3 — Engagement & Features**
- Total Engagement Events, Avg Engagement Events, Avg Feature Usage Count, Avg Session Score
- Sessions by primary feature
- Engagement by user segment and cohort (from `kpi_by_segment.csv` / `kpi_by_cohort.csv`)

All KPIs on these pages are defined in `dax/measures.dax` and cross-checked against the CSVs produced by `src/kpi_aggregation.py`.

## Tech Stack

- **Python** — data generation and analysis
- **pandas** — data manipulation, EDA, aggregation, time series resampling
- **SciPy** — hypothesis testing, correlation, confidence intervals, trend regression
- **matplotlib** — charts (PNG outputs)
- **Power BI + DAX** — KPI dashboard layer (measures in `dax/measures.dax`)

## Setup & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate the synthetic dataset (52,000 records, 2022-01-01 to 2025-06-30)
python src/generate_data.py

# 3. Run the analyses (any order after step 2)
python src/eda.py
python src/statistical_analysis.py
python src/time_series_analysis.py
python src/kpi_aggregation.py
```

All outputs land in `outputs/charts/` (PNG) and `outputs/tables/` (CSV/TXT). Generated data and outputs are git-ignored and fully regenerable from the commands above.

## Project Structure

```
behavioral-data-analytics-dashboard/
├── README.md
├── requirements.txt
├── .gitignore
├── dax/
│   └── measures.dax            # Power BI KPI measures
├── src/
│   ├── generate_data.py        # Seeded synthetic dataset (50,000+ records, 3+ years)
│   ├── eda.py                  # Exploratory data analysis + charts
│   ├── statistical_analysis.py # Hypothesis tests, correlation, 95% CIs (SciPy)
│   ├── time_series_analysis.py # Monthly longitudinal trend analysis
│   └── kpi_aggregation.py      # Dashboard-ready KPI tables for Power BI
├── data/
│   ├── raw/                    # Generated behavioral_data.csv (git-ignored)
│   └── processed/
└── outputs/
    ├── charts/                 # PNG charts (git-ignored, regenerable)
    └── tables/                 # CSV/TXT results (git-ignored, regenerable)
```

## Key Results — What the Analysis Delivers

Consistent with the resume description, this pipeline is built to:

- Analyze **50,000+ behavioral records** spanning **3+ years** of longitudinal data with Python and statistical techniques
- Apply **exploratory data analysis** to identify trends and actionable patterns that support research decisions — distributions, group comparisons, and longitudinal trends are produced as charts and summary tables by `src/eda.py` and `src/time_series_analysis.py`
- Run **hypothesis testing and correlation analysis using SciPy and pandas**, with findings **validated with 95% confidence intervals** (`src/statistical_analysis.py`)
- Track **key KPIs in Power BI dashboards** — total sessions, unique users, session duration, engagement, feature usage, and completion rate, overall and by group/cohort/segment/month — defined in `dax/measures.dax` and materialized as CSVs by `src/kpi_aggregation.py`
- Translate stakeholder needs into clear, data-driven insights and recommendations through the three dashboard pages described above

Specific numeric findings are intentionally not stated here beyond the scale above: they are produced fresh on every run and can be read from `outputs/tables/statistical_results.txt`, `outputs/tables/monthly_timeseries.csv`, and the KPI CSVs after running the pipeline.

## Author

Pavan Kumar Mankala — Data Analyst / Data Engineer
