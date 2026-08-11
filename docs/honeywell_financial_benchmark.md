# Honeywell public financial benchmark

## Purpose

HoneyWin remains a fully synthetic interview/demo portfolio. Public Honeywell
financial disclosures are used only to calibrate the overall cost scale of the
1,000-project simulation; no project, employee, risk, schedule, or cost record
represents an actual Honeywell activity.

The requested simulation window is 2025-08-01 through 2026-08-11. Financial
statements are not published for arbitrary daily windows, and the third quarter
of 2026 was not complete at the simulation as-of date. The closest complete
12-month benchmark is therefore 2025-07-01 through 2026-06-30.

## Primary sources

- [Honeywell 2025 Form 10-K](https://www.sec.gov/Archives/edgar/data/773840/000077384026000013/hon-20251231.htm)
- [Honeywell Form 10-Q for the six months ended 2026-06-30](https://www.sec.gov/Archives/edgar/data/773840/000077384026000124/hon-20260630.htm)

All values below are USD millions. The 2025 second-half values are derived as
full-year 2025 less the six months ended 2025-06-30. The trailing-12-month (TTM)
values are derived as second-half 2025 plus first-half 2026.

| Metric | FY 2025 reported | H1 2025 reported | H2 2025 derived | H1 2026 reported | TTM derived |
|---|---:|---:|---:|---:|---:|
| Net sales | 37,442 | 18,247 | 19,195 | 18,862 | **38,057** |
| Cost of products and services sold | 23,613 | 11,121 | 12,492 | 11,670 | **24,162** |
| Company-funded R&D | 1,812 | 875 | 937 | 1,016 | **1,953** |
| Customer-sponsored R&D | 1,074 | 527 | 547 | 570 | **1,117** |
| Total R&D cost | 2,886 | 1,402 | 1,484 | 1,586 | **3,070** |

Derived TTM ratios:

- Cost of products and services sold / net sales: **63.49%**.
- Gross margin before separately reported R&D and SG&A: **36.51%**.
- Company-funded R&D / net sales: **5.13%**.
- Total R&D cost / net sales: **8.07%**.
- Customer-sponsored R&D / total R&D cost: **36.38%**.

Customer-sponsored R&D is included in cost of products and services sold under
Honeywell's disclosed accounting treatment. Company-funded R&D is reported as
a separate operating expense. These categories must not be added to cost of
products and services sold without accounting for that classification.

## Simulation use

The generator sets the 1,000-project portfolio's total approved budget to
**$3.070 billion**, matching the derived TTM total R&D cost benchmark. Project
budgets are then distributed deterministically across programs, sizes, and
schedule profiles. The broader $38.057 billion net-sales and $24.162 billion
cost-of-products-and-services benchmarks are retained as contextual metadata;
they are not fabricated into project-level revenue or cost records.

The June 2026 filing includes the historical results of Aerospace Technologies
through its June 29, 2026 spin-off. The benchmark is therefore appropriate only
as a consolidated historical scale reference, not as a post-spin Honeywell
Technologies forecast.
