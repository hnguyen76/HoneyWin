# HoneyWin realism audit — final

Generated from fixed-seed assets on `2026-08-10`.

## Executive summary

- Tables profiled: 11/11; DAX measures parsed: 70/70.
- Referential-integrity orphans: 0.
- Impossible-date conditions: 0.
- Artificiality signals: 0 (0 medium).
- Clean labor rows: 8,145; utilization: 84.31%; late submissions: 3.63%.
- Approved budget: $79,795,000; actual: $60,364,049; EAC: $81,999,921.

## Table profile

| Table | Rows | Columns | Null cells | Exact duplicates | Natural-key extras |
|---|---:|---:|---:|---:|---:|
| DimDate | 731 | 22 | 723 | 0 | 0 |
| DimProject | 25 | 17 | 16 | 0 | 0 |
| DimEmployee | 120 | 13 | 117 | 0 | 0 |
| DimTeam | 8 | 7 | 0 | 0 | 0 |
| DimSkill | 8 | 7 | 0 | 0 | 0 |
| BridgeEmployeeSkill | 216 | 10 | 304 | 0 | 0 |
| FactLabor | 8,172 | 16 | 24 | 0 | 15 |
| FactFinancial | 1,180 | 16 | 0 | 0 | 0 |
| FactMilestone | 201 | 16 | 166 | 0 | 0 |
| FactWorkforcePlan | 768 | 12 | 0 | 0 | 0 |
| FactRiskIssue | 118 | 21 | 178 | 0 | 0 |

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
| ApprovedBudget | EAC | 0.980 |
| AvgDelay | MaxDelay | 0.963 |
| PercentComplete | BudgetConsumedPct | 0.957 |
| AvgRiskScore | MaxRiskScore | 0.944 |
| ActualCost | EAC | 0.810 |
| PercentComplete | ActualCost | 0.803 |
| ApprovedBudget | ActualCost | 0.800 |
| PercentComplete | Committed | -0.767 |
| Committed | BudgetConsumedPct | -0.752 |
| ActualCost | BudgetConsumedPct | 0.749 |
| ProjectHours | BudgetConsumedPct | 0.683 |
| MaxDelay | MaxRiskScore | 0.643 |

## Semantic-model static audit

- Measure definitions: 70; duplicate names: 0; unresolved bracket references: 0.
- Display folders: {"01 Financial & Project Cost": 21, "02 Labor Utilization": 16, "03 Workforce & Capacity": 11, "04 Governance & Performance": 22}.
- Live relationship cardinality, DAX execution, refresh status, and report visual review are recorded separately after Power BI refresh.
