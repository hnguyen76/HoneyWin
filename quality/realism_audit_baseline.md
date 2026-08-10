# HoneyWin realism audit — baseline

Generated from fixed-seed assets on `2026-08-10`.

## Executive summary

- Tables profiled: 11/11; DAX measures parsed: 70/70.
- Referential-integrity orphans: 0.
- Impossible-date conditions: 1.
- Artificiality signals: 14 (12 medium).
- Clean labor rows: 9,468; utilization: 83.93%; late submissions: 3.84%.
- Approved budget: $82,400,000; actual: $57,122,119; EAC: $84,967,519.

## Table profile

| Table | Rows | Columns | Null cells | Exact duplicates | Natural-key extras |
|---|---:|---:|---:|---:|---:|
| DimDate | 731 | 22 | 723 | 0 | 0 |
| DimProject | 25 | 17 | 18 | 0 | 0 |
| DimEmployee | 120 | 13 | 120 | 0 | 0 |
| DimTeam | 8 | 7 | 0 | 0 | 0 |
| DimSkill | 8 | 7 | 0 | 0 | 0 |
| BridgeEmployeeSkill | 205 | 10 | 360 | 0 | 0 |
| FactLabor | 9,495 | 16 | 24 | 0 | 15 |
| FactFinancial | 1,196 | 16 | 0 | 0 | 0 |
| FactMilestone | 198 | 16 | 140 | 0 | 0 |
| FactWorkforcePlan | 768 | 12 | 0 | 0 | 0 |
| FactRiskIssue | 120 | 21 | 188 | 0 | 0 |

## Artificiality signals

| Severity | Area | Signal | Observed | Why it matters |
|---|---|---|---|---|
| Medium | DimProject | Approved budgets on $50K grid | 1.0 | Too many round portfolio approvals look hand-authored. |
| Medium | DimProject | Distinct planned start dates | 9 | 25 projects share too few launch dates. |
| Medium | DimProject | Program counts | {'Connected Operations': 5, 'Industrial Analytics': 5, 'Digital Reliability': 5, 'Automation Platform': 5, 'Workforce Enablement': 5} | Every program has exactly the same project count. |
| Medium | DimEmployee | Distinct utilization targets | 4 | Targets are copied at team level with no role/contractor variation. |
| Low | DimEmployee | Exit records | 0 | A 24-month workforce snapshot has no transitions or inactive resources. |
| Medium | FactLabor | Hours on 0.5-hour grid | over 90% | Nearly all time entries use the same half-hour grid. |
| Medium | FactLabor | Distinct PTO values | 3 | PTO is limited to a few exact buckets. |
| Medium | FactMilestone | Distinct schedule variances | 9 | Schedule movement repeats from a short fixed list. |
| Medium | FactMilestone | In-progress completion rows | 4 | Milestones are almost entirely 0% or 100%. |
| Low | FactMilestone | Same last-updated ratio | 1.0 | Every record appears refreshed in one batch. |
| Medium | FactRiskIssue | Distinct risk titles | 6 | Risk register repeats a very small set of generic titles. |
| Medium | FactRiskIssue | Overdue ratio | 0.48333333333333334 | Portfolio-wide overdue share is implausibly high. |
| Medium | FactWorkforcePlan | Monthly actual FTE standard deviation | 0.0 | Workforce is perfectly flat across 24 months. |
| Medium | FactWorkforcePlan | Tiny demand in zero-staff locations | 384 | Demand allocation scatters implausible fractions across empty locations. |

## Business consistency

- Financial component failures: 0; EAC failures: 0; project budget failures: 0.
- Labor hour failures: 0; labor cost failures: 0; financial/labor reconciliation failures: 0.
- Workforce formula failures: open demand 0, capacity gap 0, capacity hours 0.
- Risk rule failures: score 0, severity 0, closure-date rules 0.

## Strongest project-level correlations

| Metric A | Metric B | Pearson r |
|---|---|---:|
| ApprovedBudget | EAC | 0.977 |
| PercentComplete | BudgetConsumedPct | 0.926 |
| PercentComplete | ActualCost | 0.843 |
| Committed | BudgetConsumedPct | -0.813 |
| ActualCost | BudgetConsumedPct | 0.812 |
| PercentComplete | Committed | -0.810 |
| AvgDelay | MaxDelay | 0.790 |
| AvgRiskScore | MaxRiskScore | 0.774 |
| ProjectHours | BudgetConsumedPct | 0.724 |
| ActualCost | Committed | -0.625 |
| PercentComplete | ProjectHours | 0.582 |
| ActualCost | ProjectHours | 0.534 |

## Semantic-model static audit

- Measure definitions: 70; duplicate names: 0; unresolved bracket references: 0.
- Display folders: {"01 Financial & Project Cost": 21, "02 Labor Utilization": 16, "03 Workforce & Capacity": 11, "04 Governance & Performance": 22}.
- Live relationship cardinality, DAX execution, refresh status, and report visual review are recorded separately after Power BI refresh.
