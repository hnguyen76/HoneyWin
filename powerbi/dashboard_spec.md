# Power BI dashboard specification

## Deliverable

- Local PBIX: `HoneyWin_FORGE_RDE_PMO.pbix` (intentionally excluded from Git)
- Theme: `HoneyWin_Microsoft_Fluent.json`
- Model input: 11 CSV tables from `data/generated`
- Semantic model: 12 tables, 70 DAX measures, 20 relationships (16 active, 4 inactive)
- Report canvas: 5 pages, 20 KPI cards, 5 native Power BI charts, 5 contextual slicers

## Theme

The theme uses Microsoft Fluent/Power BI visual language: Segoe UI, page
background `#F5F7FA`, white cards, primary accent `#0078D4`, and explicit
green/amber/red status colors. The theme is imported into the local PBIX and the
JSON file is retained for reuse by Power BI and Streamlit.

## Page and visual mapping

| Page | KPI cards | Main chart | Slicer |
|---|---|---|---|
| Executive Overview | Approved Budget; Actual Cost; EAC; Projects with Any Red Flag | Approved Budget vs Actual Cost vs EAC by Program — clustered column with labels | Program |
| Financial & Cost | Approved Budget; Actual Cost; EAC; Forecast Variance % | Monthly Actual + Forecast Spend vs Phased Budget by YearMonth — chronological line | PeriodType |
| Labor Utilization | Labor Utilization %; Weighted Utilization Target %; Overtime Hours; Time-entry Compliance % | Labor Utilization % vs Weighted Target % by YearMonth — target/trend line | EmploymentType |
| Workforce Capacity | Actual FTE; Required FTE; Capacity Gap FTE; Hiring / Reallocation Need FTE | Actual FTE vs Required FTE by YearMonth — capacity/demand line | Location (`DimLocation[Location]`) |
| Governance & Risk | Projects At Risk; On-Time Milestone %; Open Critical Risks; Overdue Actions | Open Critical Risks vs Overdue Actions by RiskCategory — labeled clustered bar | RiskSeverity |

> The workforce `Location` slicer uses `DimLocation[Location]`, which has an
> active one-to-many relationship to `FactWorkforcePlan[Location]`.

## Semantic-model implementation

- Measures are stored under `DimProject` and organized into four display folders:
  Financial & Project Cost, Labor Utilization, Workforce & Capacity, and Governance
  & Performance.
- `FactLabor` loaded into the model is the clean 6,482-row frame after 12 incomplete
  rows and 15 duplicate extras are excluded.
- `DimDate[YearMonth]` is sorted by `DimDate[MonthStartDate]`.
- Auto Date/Time is disabled; hidden local date tables are removed so `DimDate`
  is the only calendar path.
- Forecast/Due date and alternate project-team/employee-primary-skill paths are
  inactive to prevent ambiguous filtering; Planned/Identified paths remain active.
- Every M partition applies explicit `Table.TransformColumnTypes`, preventing a
  Python connector refresh from silently reverting fact columns to text.
- Python connector row-number helper columns are hidden.

## Verification evidence

- Data QA: 53 PASS, 4 EXPECTED_ANOMALY, 0 unexpected failures.
- Controlled anomalies validated: A01–A07.
- Core reproducibility tests: 8 passed; Streamlit data/calculation/render tests: 19 passed.
- DAX smoke test: 70/70 measures evaluated successfully.
- Model metadata: 12 tables (11 source tables plus `DimLocation`); 20
  relationships, 16 active and 4 inactive.
- Report UI: all five named pages, five contextual slicers, labels, multi-series
  tooltips, target/comparison lines, and Fluent red/amber governance colors are saved.
- Live PBIX refresh: completed and saved on 2026-08-11; each report page was
  visually inspected against the 1,000-project data scope.
- Location slicer interaction: rebound from `DimEmployee[Location]` to
  `DimLocation[Location]` and verified against the active one-to-many path to
  `FactWorkforcePlan[Location]`. Atlanta returned 24.7 actual / 25.6 required
  FTE, Charlotte returned 42.7 / 45.8, and Select all restored 115.8 / 121.8.

Portfolio totals used for the final smoke test:

| KPI | Value |
|---|---:|
| Approved Budget | $3,070,000,000 |
| Actual Cost | $2,865,125,979.30 |
| EAC | $3,074,824,814.63 |
| Forecast Variance | -0.16% |
| Labor Utilization | 85.43% |
| Weighted Utilization Target | 83.47% |
| Average Actual FTE | 115.78 |
| Average Required FTE | 121.80 |
| Projects At Risk | 115 |
