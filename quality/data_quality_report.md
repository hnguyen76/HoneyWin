# Data quality report — FORGE RDE/PMO mock dataset

Overall status: **PASS_WITH_EXPECTED_ANOMALIES**.

The intentional FactLabor defects are retained for interview-quality data cleansing and are marked `EXPECTED_ANOMALY`; all other quality gates must pass.

## Summary

| Status | Checks |
|---|---:|
| PASS | 50 |
| EXPECTED_ANOMALY | 4 |
| FAIL | 0 |

## Table volumes

| Table | Rows |
|---|---:|
| `DimDate` | 731 |
| `DimProject` | 25 |
| `DimEmployee` | 120 |
| `DimTeam` | 8 |
| `DimSkill` | 8 |
| `BridgeEmployeeSkill` | 216 |
| `FactLabor` | 8,172 |
| `FactFinancial` | 1,180 |
| `FactMilestone` | 201 |
| `FactWorkforcePlan` | 768 |
| `FactRiskIssue` | 118 |

## Controlled anomaly evidence

| ID | Signal | Observed | Root-cause evidence |
|---|---|---|---|
| A01 | FORGE-001 completion / consumed / EAC overrun | 55.00% / 70.00% / $400,000.00 | Critical milestone delay 42 days; 1,096.5 overtime hours after 2025-02-03. |
| A02 | QA utilization Jan–Jun 2025 | 68.09% vs 85.00% target | QA had 4,721.8 non-project/bench hours while available hours remained 14,664.0. |
| A03 | Jul–Dec 2025 actual/required FTE | Software 25/30; Data 12/14; Systems 18/17; Mechanical 22/19 | Employee primary skills and bridge proficiency show physical/systems excess cannot fully satisfy constrained digital skills. |
| A04 | FORGE-004 critical milestone delay | 45 days; forecast end 2025-11-29 | Open critical Dependency issue; contractor/material committed cost $600,230.13. |
| A05 | FORGE-009 labor hours vs labor cost plan | Hours 101.00%; cost 118.00% | Contractor hours 8,657.0; overtime hours 1,600.5. |
| A06 | Time-entry defects | 15 duplicate extras; 12 missing; 297 late | Natural-key duplication, incomplete labor fields and submission-date latency are independently traceable by LaborRecordID. |
| A07 | FORGE-007 completion vs budget consumed | 48.00% complete vs 68.00% consumed | Front-loaded material/other spend totals $1,092,374.07. |

## Failed checks

No unexpected failures.

## Cleansing order for Power BI

1. Type all key/date/numeric columns explicitly.
2. Reject labor rows with blank `ProjectHours` or `ActualLaborCost` to a QA exception query.
3. Deduplicate `FactLabor` on (`EmployeeKey`, `ProjectKey`, `WeekStartDateKey`) and retain one `LaborRecordID`.
4. Reconcile cleaned labor cost to financial labor by project/month/category.
5. Load clean facts to the model and keep QA counts as dashboard measures.
