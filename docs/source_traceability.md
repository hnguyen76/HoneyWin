# Source traceability

## Authoritative context

- File: `honeywell_forge_interview_context.md` (source context supplied outside this repository)
- SHA-256: `C28B2DA8A25C2C2ACBD926049A6EDD71656F302FA1E02BACDE10773B3E883908`
- Usage: source of truth for domain, scope, table list, business definitions, anomaly scenarios, Power BI model, KPI catalog and acceptance criteria.

## Requirement-to-deliverable mapping

| Source section | Requirement used | Implemented in |
|---|---|---|
| 1–2 | FORGE RDE/PMO business purpose; synthetic/interview-only classification; SAP-style analytics flow. | `README.md`, data specification, manifest metadata. |
| 3 | Utilization numerator/denominator, target gap, segmentation and root-cause framework. | Labor dictionary/rules, generator, QA and DAX labor folder. |
| 5 | Original brief: 24–36 months, 20–30 projects, 80–150 people, 8K–20K labor rows and exact 11-table list/grains. | A later user-approved scale override sets 2025-08-01–2026-08-11, 1,000 projects, 120 resources, 6,509 raw labor rows, and the same 11 named CSVs/grains. |
| 6 | Seven causal anomalies and cross-table drill-through requirements. | Controlled A01–A07 specification, deterministic generation and `quality/anomaly_evidence.csv`. |
| 7 | Conformed dimensions, star schema, single-direction relationships, canonical date and measure-table rule. | `powerbi/model_setup.md` and DAX measure table instructions. |
| 8 | Five dashboard page KPI sets, financial/utilization/workforce formulas, sign conventions and health thresholds. | `powerbi/measures.dax`, measure catalog and QA threshold checks. |
| 9 | Interview story patterns for overrun, low utilization, capacity and reporting process. | Root-cause/recommendation/business-impact columns in anomaly evidence. |
| 10 | CSV/data dictionary, fixed seed, QA, model, measure catalog and ≥5 anomalies. | Entire repository and automated acceptance suite. |
| 11 | Sequence specification → generation → validation → DAX/dashboard preparation. | Execution order and repository workflow. |

## Explicit assumptions where the source is silent

The source requires these items to be fixed but does not prescribe their exact value. They are therefore stated explicitly instead of being presented as Honeywell facts:

- Calendar-year fiscal calendar (January start).
- Data range 2025-08-01–2026-08-11 and data as-of 2026-08-11.
- Portfolio approved-budget scale is calibrated to the documented $3.070B
  Honeywell public trailing-12-month total R&D benchmark; all row-level data
  remains synthetic.
- Eight-hour workday and 160 hours/FTE/month.
- Synthetic team, project, resource, location and owner labels.
- USD as the mock reporting currency.
- Worst-status-wins for overall health, using the exact Red/Amber triggers in the source.
