# HoneyWin RDE / PMO Portfolio Analytics

HoneyWin is a reproducible synthetic RDE/PMO analytics portfolio with two
presentation layers: an interactive Streamlit application and an audited
Microsoft Power BI implementation. It demonstrates financial control, labor
utilization, workforce capacity planning, milestone governance, and risk
management without using confidential or real Honeywell operating data.

Dashboard link: https://honeywin-powerbi-dashboard.streamlit.app/

[![Streamlit Executive Overview](docs/assets/streamlit/executive-overview.png)](docs/streamlit_gallery.md)

[![Power BI Executive Overview](docs/assets/dashboard/executive-overview.png)](docs/dashboard_gallery.md)

Review the [interactive dashboard gallery](docs/streamlit_gallery.md), the
[Power BI gallery](docs/dashboard_gallery.md), or the
[full realism and optimization audit](quality/full_realism_optimization_report.md).

## Highlights

- Six interactive pages: five focused analytics experiences plus a centralized
  Business Insights & Actions hub.
- Interactive global date/program/project filters plus page-specific team,
  cost, employment, location, skill, status, and risk filters where supported.
- Microsoft Fluent-inspired responsive UI with KPI cards, variance views,
  target bands, accessible conditional colors, Plotly tooltips, and detail tables.
- A dedicated, filter-aware sixth page consolidates supported financial, labor,
  capacity, schedule, and risk insights with recommended corrective actions.
- Eleven linked CSV tables covering 2025-08-01 through 2026-08-11, 1,000 projects, and 120 synthetic
  employees/contractors.
- Fixed random seed `20250810`, deterministic CSV output, and SHA-256 manifest.
- Seven controlled business anomalies with cross-table root-cause evidence.
- Power BI model assets defining 70 DAX measures, 12 semantic tables, and 20 relationships.
- Automated data, calculation, rendering, startup, link, and reproducibility tests.

## Interactive application

The Streamlit entry point is [`app.py`](app.py). It loads the committed audited
data through repository-relative paths, validates manifest row counts, caches
data loading, applies the same labor cleansing rule as Power BI, and calculates
all displayed metrics from source frames.

### Local setup

Python 3.11 or later is required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Start the application:

```powershell
python -m streamlit run app.py
```

Streamlit will print the local URL, normally `http://localhost:8501`. The app
uses a wide layout and remains usable at narrower browser widths through
responsive card and chart wrapping.

### Application architecture

```text
app.py                              Minimal Streamlit entry point
honeywin_dashboard/data.py          Cached loading, validation, joins, filters
honeywin_dashboard/metrics.py       Pure audited KPI calculations
honeywin_dashboard/charts.py        Reusable Plotly business charts
honeywin_dashboard/filters.py       Navigation and supported filter controls
honeywin_dashboard/style.py         Fluent tokens, CSS, KPI formatting
honeywin_dashboard/pages.py         Five analytics views and one insight hub
.streamlit/config.toml              Deterministic local theme/server settings
tests/test_streamlit_dashboard.py   Loader, calculation, filter, and render tests
```

The Power BI theme file is the palette source for the Streamlit application, so
both presentation layers use the same primary, secondary, good, warning, and bad
status colors.

## Dataset

Default scope:

- Date range: 2025-08-01 through 2026-08-11; data as of 2026-08-11.
- 1,000 FORGE-style synthetic RDE projects.
- 120 synthetic employees and contractors.
- 6,509 raw labor records; 6,482 after reject-and-deduplicate cleansing.
- 11 UTF-8 Power BI-ready CSV tables.
- 7 deterministic anomaly/root-cause scenarios.
- $3.070 billion total approved portfolio budget, calibrated to Honeywell's
  closest fully reported trailing-12-month total R&D cost benchmark.

| Table | Rows | Grain |
|---|---:|---|
| `DimDate` | 376 | Calendar date |
| `DimProject` | 1,000 | Project |
| `DimEmployee` | 120 | Employee or contractor |
| `DimTeam` | 8 | Engineering team |
| `DimSkill` | 8 | Workforce skill |
| `BridgeEmployeeSkill` | 218 | Employee–skill association |
| `FactLabor` | 6,509 | Employee–project–week time entry |
| `FactFinancial` | 26,460 | Project–month–cost category |
| `FactMilestone` | 8,010 | Project milestone |
| `FactWorkforcePlan` | 416 | Month–team–skill–location snapshot |
| `FactRiskIssue` | 5,002 | Project risk or issue |

See the [data specification](docs/data_specification.md) and
[data dictionary](docs/data_dictionary.md) for grains, keys, definitions, and
business rules. The [public financial benchmark](docs/honeywell_financial_benchmark.md)
documents the SEC/Honeywell sources, derivation, accounting caveats, and how the
benchmark is used without presenting synthetic records as company actuals.

## Data refresh and Power BI assets

Regenerate and validate the fixed-seed data:

```powershell
python scripts\generate_data.py
python scripts\validate_data.py
python scripts\audit_realism.py --label final
python scripts\build_powerbi_model_assets.py
```

Running the generator again with the same configuration must produce
byte-identical CSV files and manifest checksums. Restart Streamlit after a data
refresh; its cached loader will validate the new manifest before rendering.

Power BI source assets are stored under `powerbi/`, including the Fluent theme,
Power Query cleansing logic, relationship/setup guidance, DAX source, generated
measure metadata, and TMDL. The local PBIX binary is intentionally excluded from
Git. See the [Power BI dashboard specification](powerbi/dashboard_spec.md) and
[measure catalog](powerbi/measure_catalog.md).

## Validation

Run the complete automated suite:

```powershell
python -m compileall -q app.py honeywin_dashboard scripts tests
python scripts\validate_data.py
python scripts\audit_realism.py --label final
python -m pytest -q
python scripts\smoke_streamlit.py
python scripts\check_repo_links.py
```

Current audited acceptance results:

- Data QA: 53 PASS, 4 expected anomaly warnings, 0 unexpected failures.
- Reproducibility and application tests: 27 passed.
- Realism audit: 0 final artificiality flags, down from 14 at baseline.
- Referential integrity: 0 orphan keys and 0 impossible-date conditions.
- Refreshed local PBIX: all five pages rendered successfully against the
  1,000-project dataset on 2026-08-11. The last structure audit found 12
  semantic tables (11 source tables plus `DimLocation`), 70/70 DAX measures,
  and 16 active plus 4 inactive relationships.
- Streamlit browser review: six pages rendered without application errors;
  1440×1000 wide captures and a 900-pixel responsive overflow check passed.

## Streamlit Community Cloud deployment

The dashboard is deployed at
[honeywin-powerbi-dashboard.streamlit.app](https://honeywin-powerbi-dashboard.streamlit.app/).
Streamlit Community Cloud currently tracks the
`agent/honeywin-powerbi-audit-delivery` branch with `app.py` as the entry point,
so pushes to that branch trigger a redeployment. The application requires no
secrets. Access may require Streamlit sign-in depending on the workspace sharing
configuration.

After a deployment, confirm the health page, all six navigation states, and the
committed QA suite.

## Data classification

All project, resource, owner, sponsor, risk, financial, and workforce records are
synthetic interview/demo constructs. They are not external benchmarks, production
forecasts, or statements about Honeywell performance.
