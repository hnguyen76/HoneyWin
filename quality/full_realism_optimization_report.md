# HoneyWin Power BI — full realism and optimization audit

Audit date: 2026-08-10

Scope: 11 generated CSV tables, JSON configuration/manifest/model/theme assets, generator, validator, 70 DAX measures, live semantic model, and all 5 report pages.

## Outcome

The fixed-seed dataset was regenerated and the open PBIX was refreshed, optimized, visually reviewed, and saved. Final acceptance status:

- Data QA: **50 PASS, 4 EXPECTED_ANOMALY, 0 FAIL**.
- Reproducibility tests: **7/7 passed**.
- Realism threshold flags: **0 final, down from 14 baseline**.
- Integrity: **0 orphan keys, 0 impossible-date conditions, 0 financial/labor/workforce/risk rule failures**.
- Live model: **12 semantic tables (11 source tables plus `DimLocation`), 20 relationships (16 active/4 inactive), 70/70 DAX measures evaluated successfully**.
- Report: **5 pages, 20 KPI cards, 5 optimized charts, 5 contextual slicers**, Microsoft Fluent theme, no visual error in the final screenshots.

## Assets inspected

- CSV: all 11 files in `data/generated`, including physical and natural keys, every nullable/numeric/date/categorical column, and cross-table aggregates.
- JSON: `config/default.json`, generated `manifest.json`, `measures.generated.json`, `column_types.generated.json`, and `HoneyWin_Microsoft_Fluent.json`.
- Code/model: generator, validator, Power BI loader/M partitions, 70-measure DAX source/generated assets, and all live TOM relationships.
- Report pages: Executive Overview, Financial & Cost, Labor Utilization, Workforce Capacity, and Governance & Risk.

## Baseline-to-final realism profile

| Signal | Baseline | Final | Implemented reason/change |
|---|---:|---:|---|
| Artificiality flags | 14 | 0 | Removed threshold-level round-robin, grid, flat-snapshot, repeated-title and fixed-list patterns. |
| Project start dates | 9 distinct | 25 distinct | Irregular day-level project launches. |
| Budgets on exact $50K grid | 100% | 32% | $5K approval granularity plus preserved anomaly budgets. |
| Program distribution | 5/5/5/5/5 | 8/8/4/3/2 | Weighted portfolio demand rather than exact round-robin. |
| Employee utilization targets | 4 values | 16 values | Team baseline plus role/contractor variation. |
| Workforce transitions | 0 exits | 3 exits; staggered 2024/2025 hires | Added roster movement while retaining 120 dimension rows. |
| Labor rows | 9,495 raw / 9,468 clean | 8,172 raw / 8,145 clean | Kept required volume, added hire/exit timing and 169 capacity-preserving multi-project splits. |
| Project hours on 0.5-hour grid | >90% | 49.8% | Quarter-hour entries, variable PTO/overtime and persistent weekly utilization. |
| Time-entry sources | 1 | 3 | SAP-style, mobile and manager-adjustment mix. |
| Milestone names | 12 generic prefix names | 28 program-specific names | Program lifecycle templates and optional gates. |
| Schedule variance values | 9 | 41 | Project schedule signal plus controlled variation. |
| In-progress milestones | 4 | 19 | Continuous gate progression instead of almost all 0/100. |
| Same milestone update date | 100% | 7.5% top share | Rolling operational update cadence. |
| Risk titles | 6 | 85 | Category templates plus project context. |
| Overdue risk/action ratio | 48.3% | 24.6% | Status/mitigation/closure now depends on due-date lifecycle. |
| Monthly actual FTE standard deviation | 0.0 | 10.71 | Hire, exit, partial-month and leave effects; forecast profile preserved. |
| Tiny demand in empty locations | 384 rows | 0 rows | Demand allocated to staffed locations or a designated hub. |

These changes preserve CSV schemas, stable primary/business keys, all documented foreign keys, fixed seed `20250810`, and anomaly thresholds A01–A07.

## Final table and null/cardinality profile

| Table | Rows | Intended nulls | Duplicate result |
|---|---:|---|---|
| DimDate | 731 | HolidayName only on non-holidays | 0 PK/exact duplicates |
| DimProject | 25 | ActualEndDate for incomplete work | 0 |
| DimEmployee | 120 | ExitDate for active resources | 0 |
| DimTeam | 8 | None | 0 |
| DimSkill | 8 | None | 0 |
| BridgeEmployeeSkill | 216 | Certification/expiration when not applicable | 0 |
| FactLabor | 8,172 raw / 8,145 model-clean | 12 controlled incomplete entries | 15 controlled natural-key extras; physical keys unique |
| FactFinancial | 1,180 | None | 0 |
| FactMilestone | 201 | Actual date/key for incomplete gates | 0 |
| FactWorkforcePlan | 768 | None | 0 |
| FactRiskIssue | 118 | Closed date/key for open items | 0 |

All non-null foreign keys resolve. Nullable date keys also resolve when populated. Date coverage remains exactly 2024-01-01 through 2025-12-31 with data as-of 2025-06-30.

## Business consistency and outliers

- Approved budget: **$79,795,000**; actual cost: **$60,364,049.07**; EAC: **$81,999,920.57**; forecast variance: **-$2,204,920.57 / -2.76%**.
- Financial component equality, row EAC equality, project phased-budget equality, and clean labor-to-financial reconciliation all have **0 failures**.
- Clean labor utilization is **84.31%** versus weighted target **83.19%**; overtime is **1.57%** of project hours and late submissions are **3.63%**.
- Workforce formula checks for open demand, gap, and capacity hours have **0 failures**. Monthly actual FTE ranges **83.96–117.00**; required-demand series is smoothed rather than independent monthly noise.
- Milestone schedule variance, risk score/severity, closure dates, and workforce arithmetic all reconcile. The baseline closed-before-identified risk defect was removed.
- Extreme overtime, cost burn, milestone delays, skill gaps, and critical risks are retained only where supported by the seven documented anomaly/root-cause scenarios.

Project-level correlation review found expected structural relationships without making causal claims: ApprovedBudget–EAC `r=0.980`, PercentComplete–BudgetConsumedPct `r=0.957`, ActualCost–EAC `r=0.810`, and MaxDelay–MaxRiskScore `r=0.643`. These are descriptive synthetic-data correlations, not evidence about a real company.

## DAX and semantic-model audit

- Parsed all **70** definitions: 70 unique names, 0 unresolved measure references, 0 unsafe raw division operators, and four documented display folders.
- Evaluated every measure against the refreshed live model: **70 PASS / 0 FAIL**.
- Kept the two explicitly named mock earned-value measures labeled as mock; no unsupported business claim was added.
- Refined `Labor Health` so `< -12pp` is Red, `-12pp to -5pp` is Amber, and other nonblank results are Green.
- Disabled Auto Date/Time and removed 13 regenerated local date objects, leaving 11 source/business tables, the intentional `DimLocation`, and one canonical `DimDate`.
- Persisted `Table.TransformColumnTypes` in every M partition. This fixes the observed refresh defect where Python output silently reverted fact numerics to Text and broke 48 measures.
- Relationships are single-direction and unambiguous: 16 active plus 4 inactive alternate/role-playing paths. The active `DimLocation` path filters workforce snapshots; project-team and employee-primary-skill stay inactive because enabling either creates a second path to labor/bridge facts.

## Report-page changes

| Page | What changed | Why |
|---|---|---|
| Executive Overview | Program slicer; Budget/Actual/EAC clustered comparison; value labels; native multi-series tooltip | Shows variance and scale together instead of budget alone. |
| Financial & Cost | PeriodType slicer; monthly actual+forecast versus phased-budget line | Makes spend profile and plan divergence visible over time. |
| Labor Utilization | EmploymentType slicer; utilization versus weighted-target line | Adds the requested target band/comparator and exposes time variation. |
| Workforce Capacity | Location slicer; Actual FTE versus Required FTE line | Replaces a static ranking with the capacity/demand trajectory. |
| Governance & Risk | RiskSeverity slicer; labeled exceptions by RiskCategory; Open Critical red and Overdue amber | Focuses the page on actionable governance load with Fluent status colors. |

Titles, axes, legends, labels, and default multi-series tooltips use the existing Microsoft Fluent theme. Slicer selections were left at All so saved portfolio totals are not silently filtered.

## Controlled anomaly validation

- A01: 55% complete / 70% consumed / EAC +$400K; 42-day critical delay and 1,096.5 overtime hours.
- A02: QA utilization 68.09% versus 85%; 4,721.8 non-project hours.
- A03: Software -5 FTE, Data -2, Systems +1, Mechanical +3 in Jul–Dec 2025.
- A04: 45-day critical delay with open dependency and $600,230.13 contractor/material commitment.
- A05: 101% planned hours but 118% planned labor cost; contractor/overtime rate-mix root cause.
- A06: 15 duplicate extras, 12 incomplete entries, 297 late submissions.
- A07: 48% complete versus 68% consumed; $1,092,374.07 front-loaded material/other spend.

## Remaining limitations

1. The PBIX Python source embeds the current absolute repository path. Moving the project requires updating the Power BI Python data-source path.
2. Nullable `FactMilestone[ActualDateKey]` and `FactRiskIssue[ClosedDateKey]` remain CSV-validated but are not live relationships because the connector emits blank nullable keys as text. Planned/Forecast and Identified/Due paths cover current visuals.
3. Workforce KPI cards are averages across the selected months, not “latest month” snapshots. This prevents summing periodic snapshots; use the page/date context when a point-in-time view is needed.
4. The dataset is deliberately synthetic. Pseudonyms, risk wording, distributions, thresholds, and seven anomalies are interview/demo constructs, not external benchmarks or Honeywell facts.
5. Visual review was performed in the current Power BI Desktop version/window/zoom. The included UI-automation scripts may need coordinate adjustment on another display scale or Desktop release.

## Evidence artifacts

- `realism_audit_baseline.json/.md` and `realism_audit_final.json/.md`
- `data_quality_summary.json`, `data_quality_results.csv`, `anomaly_evidence.csv`
- `powerbi_live_audit.json` — live tables, rows, 20 relationships, and all 70 DAX results
- `report_visual_audit.json` — page/visual names and bounds
- `docs/assets/dashboard/*.png` and `docs/dashboard_gallery.md` — five clean 1200×675 report-canvas screenshots
- `data/generated/manifest.json` — final row counts and SHA-256 checksums
