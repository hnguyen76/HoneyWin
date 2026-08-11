# HoneyWin full realism and scale audit

Audit date: 2026-08-11

Scope: the fixed-seed generator, 11 generated CSV tables, configuration and
manifest, validator, Streamlit application, Power BI source assets, 70 DAX
measures, documentation, and automated tests.

## Outcome

- Simulation window: **2025-08-01 through 2026-08-11**.
- Portfolio: **1,000 synthetic projects** and **120 synthetic resources**.
- Financial scale: **$3.070 billion approved budget**, reconciled exactly to the
  documented public Honeywell trailing-12-month total R&D cost benchmark.
- Data QA: **53 PASS, 4 EXPECTED_ANOMALY, 0 FAIL**.
- Reproducibility and application tests: **27 passed**.
- Realism threshold flags: **0 final**.
- Integrity: **0 orphan keys, 0 project dates outside the simulation window,
  and 0 financial/labor/workforce/risk rule failures**.
- Power BI source generation: **70/70 measures generated successfully**.
- Streamlit startup smoke test and repository link check: **passed**.

## Public benchmark calibration

The closest fully reported 12-month benchmark to the requested daily window is
2025-07-01 through 2026-06-30. Derived consolidated values are:

| Metric | USD |
|---|---:|
| Net sales | $38.057B |
| Cost of products and services sold | $24.162B |
| Company-funded R&D | $1.953B |
| Customer-sponsored R&D | $1.117B |
| Total R&D cost | **$3.070B** |

The generator uses only the $3.070B total R&D figure to calibrate portfolio
approved-budget scale. Revenue and total cost of products/services remain
contextual metadata and are not fabricated into project-level records. See
[`docs/honeywell_financial_benchmark.md`](../docs/honeywell_financial_benchmark.md)
for sources, calculations, and accounting caveats.

## Final table profile

| Table | Rows | Intended nulls / controlled defects |
|---|---:|---|
| `DimDate` | 376 | `HolidayName` only on non-holidays |
| `DimProject` | 1,000 | `ActualEndDate` for incomplete work |
| `DimEmployee` | 120 | `ExitDate` for active resources |
| `DimTeam` | 8 | None |
| `DimSkill` | 8 | None |
| `BridgeEmployeeSkill` | 218 | Certification/expiration when not applicable |
| `FactLabor` | 6,509 raw / 6,482 clean | 12 controlled incomplete rows; 15 natural-key duplicate extras |
| `FactFinancial` | 26,460 | None |
| `FactMilestone` | 8,010 | Actual date/key for incomplete gates |
| `FactWorkforcePlan` | 416 | None |
| `FactRiskIssue` | 5,002 | Closed date/key for open items |

All non-null foreign keys resolve. Project lifecycle dates stay inside the
configured window, and project names are unique.

## Business consistency

- Approved budget: **$3,070,000,000.00**.
- Actual cost: **$2,865,125,979.30**.
- EAC: **$3,074,824,814.63**.
- Forecast variance: **-$4,824,814.63**.
- Financial component equality, row EAC equality, phased-budget equality,
  benchmark reconciliation, and clean labor-to-financial reconciliation all
  have zero failures.
- Clean labor utilization is **85.43%**; overtime is **2.42%** of project hours;
  late submissions are **4.09%**.
- Workforce actual FTE ranges from **114.1 to 116.9** by month, with no capacity
  formula failures or demand allocated to zero-staff locations.
- Milestones contain 28 distinct lifecycle names, 45 distinct schedule
  variances, and 1,015 in-progress rows.
- Risks/issues contain 2,324 distinct titles; the overdue ratio is **15.03%**,
  and score/severity/status/date rules all reconcile.

## Controlled anomaly validation

- A01: 55% complete, 70% consumed, EAC $400K above approved budget, with a
  42-day critical delay and overtime evidence.
- A02: QA utilization near 68% versus an 85% target during Feb-Jul 2026.
- A03: Software/Data shortages and Systems/Mechanical capacity during Mar-Aug
  2026, including realistic monthly roster variation.
- A04: 45-day critical delay with an open dependency and committed recovery cost.
- A05: FORGE-009 labor hours near plan but labor cost more than 15% unfavorable.
- A06: 15 duplicate extras and 12 incomplete labor rows retained for cleansing QA.
- A07: 48% completion versus 68% budget consumption with front-loaded spend.

## Remaining limitations

1. The 1,000 project records and all row-level values are synthetic. Public
   Honeywell disclosures calibrate scale only and do not validate any individual
   project, program, resource, risk, or forecast.
2. The benchmark ends 2026-06-30 because later completed-period filings were not
   available for the requested 2026-08-11 as-of date.
3. The June 2026 consolidated filing includes Aerospace Technologies through
   its June 29, 2026 spin-off, so the benchmark is historical consolidated scale,
   not a post-spin Honeywell Technologies forecast.
4. The local PBIX was refreshed, visually checked across all five pages, and
   saved on 2026-08-11. The binary remains excluded from Git, so users working
   from a source-only checkout must refresh their own local PBIX.
5. The synthetic portfolio retains 120 internal resources while many project
   costs represent material, vendor, and customer-sponsored work; it should not
   be interpreted as an employee-per-project staffing model.

## Evidence artifacts

- `data/generated/manifest.json` — row counts, configuration, benchmark metadata,
  and SHA-256 checksums.
- `quality/data_quality_summary.json` and `quality/data_quality_results.csv`.
- `quality/anomaly_evidence.csv` and `quality/labor_exceptions.csv`.
- `quality/realism_audit_final.json` and `quality/realism_audit_final.md`.
- `powerbi/measures.generated.json`, generated TMDL, and column type metadata.
