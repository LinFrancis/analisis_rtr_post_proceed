# 🌍 Resilience Enabling Conditions — Diagnostic Tool

Interactive Streamlit dashboard for analyzing resilience assessment survey data (Race to Resilience).

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
streamlit run app.py
```

Then upload your Excel file (must contain a sheet named **DATASET**).

## Features

| Tab | Description |
|-----|-------------|
| Overview | KPI cards, radar chart, category comparison |
| Gap Analysis | Gap, Resolution Gap, System Stress rankings |
| Categories | Heatmap + expandable sub-category breakdowns |
| Typology | Enabler / Bottleneck / Emerging / Latent classification |
| Variability | CV scatter plots, high-disagreement flags |
| Priority & Capacity | Priority Score ranking + Efficiency index |
| Data Explorer | Searchable table, CSV export, Q comparison scatter |
| Glossary | Full definitions of all metrics |

## Sidebar Controls

- **Upload** your `.xlsx` file
- **Thresholds**: adjust High/Low for typology classification
- **Filters**: Category, Sub Category dynamic selectors
