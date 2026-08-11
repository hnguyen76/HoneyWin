# HoneyWin realism audit — final

Generated from fixed-seed assets on `2026-08-11`.

## Executive summary

- Tables profiled: 11/11; DAX measures parsed: 70/70.
- Referential-integrity orphans: 0.
- Impossible-date conditions: 0.
- Artificiality signals: 0 (0 medium).
- Clean labor rows: 6,482; utilization: 85.43%; late submissions: 4.09%.
- Approved budget: $3,070,000,000; actual: $2,865,125,979; EAC: $3,074,824,815.

## Table profile

| Table | Rows | Columns | Null cells | Exact duplicates | Natural-key extras |
|---|---:|---:|---:|---:|---:|
| DimDate | 376 | 22 | 372 | 0 | 0 |
| DimProject | 1,000 | 17 | 588 | 0 | 0 |
| DimEmployee | 120 | 13 | 117 | 0 | 0 |
| DimTeam | 8 | 7 | 0 | 0 | 0 |
| DimSkill | 8 | 7 | 0 | 0 | 0 |
| BridgeEmployeeSkill | 218 | 10 | 330 | 0 | 0 |
| FactLabor | 6,509 | 16 | 24 | 0 | 15 |
| FactFinancial | 26,460 | 16 | 0 | 0 | 0 |
| FactMilestone | 8,010 | 16 | 2,040 | 0 | 0 |
| FactWorkforcePlan | 416 | 12 | 0 | 0 | 0 |
| FactRiskIssue | 5,002 | 21 | 7,674 | 0 | 0 |

## Artificiality signals

No material artificiality signals breached the audit thresholds.

## Business consistency

- Financial component failures: 0; EAC failures: 0; project budget failures: 0.
- Labor hour failures: 0; labor cost failures: 0; financial/labor reconciliation failures: 0.
- Workforce formula failures: open demand 0, capacity gap 0, capacity hours 0.
- Risk rule failures: score 0, severity 0, closure-date rules 0.

## Strongest project-level correlations

| Metric A | Metric B | Pearson r |
|---|---|---:|
| ApprovedBudget | EAC | 0.997 |
| ApprovedBudget | ActualCost | 0.982 |
| ActualCost | EAC | 0.981 |
| ProjectHours | OvertimeHours | 0.910 |
| AvgDelay | MaxDelay | 0.906 |
| PercentComplete | BudgetConsumedPct | 0.822 |
| Committed | BudgetConsumedPct | -0.795 |
| PercentComplete | Committed | -0.765 |
| AvgRiskScore | MaxRiskScore | 0.752 |
| AvgDelay | BudgetConsumedPct | 0.380 |
| PercentComplete | OvertimeHours | -0.376 |
| EAC | Committed | 0.351 |

## Semantic-model static audit

- Measure definitions: 70; duplicate names: 0; unresolved bracket references: 0.
- Display folders: {"01 Financial & Project Cost": 21, "02 Labor Utilization": 16, "03 Workforce & Capacity": 11, "04 Governance & Performance": 22}.
- Live relationship cardinality, DAX execution, refresh status, and report visual review are recorded separately after Power BI refresh.
