# Power BI dashboard specification

## Deliverable

- Local PBIX: `HoneyWin_FORGE_RDE_PMO.pbix` (intentionally excluded from Git)
- Theme: `HoneyWin_Microsoft_Fluent.json`
- Model input: 11 CSV tables from `data/generated`
- Semantic model: 70 DAX measures, 19 relationships (15 active, 4 inactive)
- Report canvas: 5 pages, 20 KPI cards, 5 native Power BI charts, 5 contextual slicers

## Theme

Theme sử dụng ngôn ngữ Microsoft Fluent/Power BI: Segoe UI, nền trang `#F5F7FA`,
card trắng, accent chính `#0078D4`, cùng màu trạng thái green/amber/red. Theme đã
được import trực tiếp vào PBIX; file JSON được giữ riêng để tái sử dụng.

## Page and visual mapping

| Page | KPI cards | Main chart | Slicer |
|---|---|---|---|
| Executive Overview | Approved Budget; Actual Cost; EAC; Projects with Any Red Flag | Approved Budget vs Actual Cost vs EAC by Program — clustered column with labels | Program |
| Financial & Cost | Approved Budget; Actual Cost; EAC; Forecast Variance % | Monthly Actual + Forecast Spend vs Phased Budget by YearMonth — chronological line | PeriodType |
| Labor Utilization | Labor Utilization %; Weighted Utilization Target %; Overtime Hours; Time-entry Compliance % | Labor Utilization % vs Weighted Target % by YearMonth — target/trend line | EmploymentType |
| Workforce Capacity | Actual FTE; Required FTE; Capacity Gap FTE; Hiring / Reallocation Need FTE | Actual FTE vs Required FTE by YearMonth — capacity/demand line | Location |
| Governance & Risk | Projects At Risk; On-Time Milestone %; Open Critical Risks; Overdue Actions | Open Critical Risks vs Overdue Actions by RiskCategory — labeled clustered bar | RiskSeverity |

## Semantic-model implementation

- Measures are stored under `DimProject` and organized into four display folders:
  Financial & Project Cost, Labor Utilization, Workforce & Capacity, and Governance
  & Performance.
- `FactLabor` loaded into the model is the clean 8,145-row frame after 12 incomplete
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

- Data QA: 50 PASS, 4 EXPECTED_ANOMALY, 0 unexpected failures.
- Controlled anomalies validated: A01–A07.
- Automated tests: 7 passed.
- DAX smoke test: 70/70 measures evaluated successfully.
- Model metadata: 11 tables; 19 relationships, 15 active and 4 inactive.
- Report UI: all five named pages, five contextual slicers, labels, multi-series
  tooltips, target/comparison lines, and Fluent red/amber governance colors are saved.

Portfolio totals used for the final smoke test:

| KPI | Value |
|---|---:|
| Approved Budget | $79,795,000 |
| Actual Cost | $60,364,049.07 |
| EAC | $81,999,920.57 |
| Forecast Variance | -2.76% |
| Labor Utilization | 84.31% |
| Weighted Utilization Target | 83.19% |
| Average Actual FTE | 103.97 |
| Average Required FTE | 122.96 |
| Projects At Risk | 5 |
