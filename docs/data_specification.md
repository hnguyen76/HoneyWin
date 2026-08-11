# Data specification — FORGE RDE/PMO synthetic portfolio

## 1. Purpose and source context

This specification converts the supplied `honeywell_forge_interview_context.md`
into a Power BI- and Streamlit-ready synthetic portfolio for a Senior Advanced
Data Analyst interview demonstration. The data is entirely simulated and is not
Honeywell internal data.

Supported analytical flow:

`Source-style records → governed semantic model → KPI/variance analysis → root-cause drill path → recommended action`

Required analysis areas:

- Financial management and project cost.
- Labor utilization and time-entry compliance.
- Workforce and capacity planning by month, team, skill, and location.
- Milestone, risk, issue, and project governance.
- Portfolio exception reporting with cross-table root-cause evidence.

## 2. Default configuration

| Attribute | Default | Rationale / convention |
|---|---|---|
| Random seed | `20250810` | The same configuration must produce byte-identical CSV files. |
| Data range | `2025-08-01`–`2026-08-11` | Requested simulation window through the current as-of date. |
| Data as-of date | `2026-08-11` | Latest synthetic portfolio reporting date. |
| Fiscal calendar | January–December | The source requires a defined fiscal calendar but does not prescribe a start month. |
| Projects | 1,000 | Requested portfolio scale. |
| Employees / contractors | 120 | Within the requested 80–150 range. |
| Labor fact size | 6,000–15,000 | Active employee–project–week entries plus controlled duplicates. |
| Approved portfolio budget | `$3.070B` | Calibrated to the closest fully reported Honeywell trailing-12-month total R&D cost benchmark. |
| CSV tables | 11 | Exact required table list. |
| Business anomalies | 7 | Each has a signal, root cause, drill path, recommendation, and impact. |
| Hours per FTE per month | 160 | Explicit workforce-capacity assumption. |
| Scheduled hours per workday | 8 | Used for scheduled, available, and PTO hours. |

Assumptions not prescribed by the source are documented here and are never
presented as real company facts.

The [public financial benchmark](honeywell_financial_benchmark.md) documents the
Honeywell/SEC sources and derivation used only to calibrate portfolio scale.

## 3. Model design

### 3.1 Table grains and expected volume

| Table | Grain | Default rows / range |
|---|---|---:|
| `DimDate` | Calendar date | 376 |
| `DimProject` | RDE project | 1,000 |
| `DimEmployee` | Employee or contractor | 120 |
| `DimTeam` | Engineering team | 8 |
| `DimSkill` | Workforce skill | 8 |
| `BridgeEmployeeSkill` | Effective employee–skill assignment | 120–360; final 218 |
| `FactLabor` | Employee–project–week time entry | 6,000–15,000; final 6,509 raw |
| `FactFinancial` | Project–month–cost category | Final 26,460 |
| `FactMilestone` | Project milestone | Final 8,010 |
| `FactWorkforcePlan` | Month–team–skill–location snapshot | Final 416 |
| `FactRiskIssue` | Project risk or issue | Final 5,002 |

### 3.2 Relationship rules

Power BI relationships are one-to-many and single-direction from a dimension to
a fact or bridge. No fact-to-fact relationship is allowed.

Canonical active paths:

- `DimDate[DateKey]` → labor week, financial month, milestone planned date,
  workforce month, and risk identified date.
- `DimProject[ProjectKey]` → labor, financial, milestone, and risk facts.
- `DimEmployee[EmployeeKey]` → labor and employee-skill bridge.
- `DimTeam[TeamKey]` → employee and workforce plan.
- `DimSkill[SkillKey]` → employee-skill bridge and workforce plan.

Inactive alternate paths:

- Milestone forecast date.
- Risk due date.
- Project primary team.
- Employee primary skill.

The alternate project-team and employee-primary-skill paths remain inactive to
avoid ambiguous routes into labor and bridge facts. Nullable milestone actual
and risk closed keys are still foreign-key validated in CSV, but the Python
connector emits blank nullable keys as text, so those two relationships are not
created in the live model.

Surrogate keys are stable integers. Business keys (`ProjectID`, `EmployeeID`,
`TeamID`, and `SkillID`) remain available for source-style traceability.

## 4. Business definitions and reconciliation rules

### 4.1 Labor utilization

- `ScheduledHours`: working-day hours after holidays and before PTO.
- `AvailableHours = ScheduledHours - PTOHours`.
- `ProjectHours`: all productive/project hours, including overtime.
- `NonProjectHours`: administration, training, internal meetings, or bench time.
- `Utilization % = ProjectHours / AvailableHours`.
- `Weighted Utilization Target % = SUM(AvailableHours × employee target) / SUM(AvailableHours)`.
- `Utilization Gap = Utilization % - Weighted Utilization Target %`; negative is below target.
- `SubmissionStatus = Late` when submission occurs more than two days after the
  Sunday ending the work week.
- Overtime is included in the numerator but not added to the available-hours
  denominator, so utilization can exceed 100% and must be read with overtime.
- 176 employee-weeks are validly split across two projects. Scheduled,
  available, PTO, project, non-project, and overtime hours are allocated rather
  than duplicated.

### 4.2 Financial and project cost

- `ActualCostAmount = ActualLaborCost + ActualMaterialCost + ActualOtherCost`.
- Row-level `EAC = ActualCostAmount + ForecastToComplete`.
- Project/portfolio `EAC` uses actual plus forecast across the full timeline.
- `Forecast Variance $ = Approved Budget - EAC`; negative is unfavorable.
- `Budget Consumed % = Actual Cost / Approved Budget`.
- `Project Completion %` is approved-budget-weighted percent complete.
- `Budget vs Completion Gap = Budget Consumed % - Project Completion %`.
- Monthly/category `BudgetAmount` reconciles to `DimProject[ApprovedBudget]`.
- Financial actual labor cost reconciles to valid, deduplicated labor cost by
  project and month. Duplicate or incomplete time entries are removed first.
- `PeriodType = Actual` through the data as-of month and `Forecast` afterward.

### 4.3 Workforce and capacity

- `Capacity Gap FTE = ActualFTE - RequiredFTE`; negative is a shortage.
- `OpenDemandFTE = MAX(RequiredFTE - ActualFTE, 0)`.
- `AvailableCapacityHours = ActualFTE × 160`.
- `RequiredCapacityHours = RequiredFTE × 160`.
- Workforce KPI measures average monthly snapshots across the selected period;
  they do not sum headcount across months.
- `ContractorFTE` is a subset of `ActualFTE`.

### 4.4 Schedule, risk, and project health

- A completed milestone is on time when its actual date is no later than its
  planned date; an incomplete milestone uses its forecast date.
- `RiskScore = Probability × Impact`, with each component on a 1–5 scale.
- Health uses a transparent worst-status-wins rule:
  - **Red**: EAC over budget by more than 10%; critical milestone delay over 30
    days; utilization gap below -12 percentage points; or an open/monitoring
    critical risk whose mitigation has not started.
  - **Amber**: EAC over budget by 3–10%; milestone delay of 8–30 days;
    utilization gap below -5 percentage points; or overdue governance action.
  - **Green**: no red or amber condition.
- A separate budget-consumption red flag applies when spend leads completion by
  at least 15 percentage points.

## 5. Realism controls

- Project starts use irregular day-level dates. Program, manager, sponsor, and
  team assignments use weighted demand rather than round-robin allocation.
- Approved budgets are benchmark-scaled to exactly $3.070 billion with
  project-specific cost mixes and front-, bell-, or back-loaded monthly phase curves.
- Hire/exit timing, locations, contractor mix, rates, and utilization targets
  vary by team; resource names are synthetic pseudonyms.
- Labor includes persistent employee behavior, seasonality, team demand,
  quarter-hour entry increments, varied PTO/overtime, three entry sources, and
  occasional multi-project weeks.
- Milestones use program-specific templates, project schedule signals, 28
  distinct names, 41 schedule-variance values, and rolling update dates.
- Risk probability, status, and mitigation follow lifecycle logic; 85 contextual
  titles replace fixed repeated category titles.
- Workforce actual FTE reflects hires, exits, partial months, and leave. Required
  FTE is a smoothed demand series allocated only to staffed or designated hubs.

## 6. Controlled anomaly scenarios

| ID | Required signal | Cross-table root cause | Drill path | Recommended action / impact |
|---|---|---|---|---|
| `A01` | `FORGE-001`: 55% complete, 70% consumed, EAC $400K above approved budget. | Critical milestone delay increases contractor/overtime and committed cost. | Project → financial month/category → labor employee/week → milestone. | Reforecast, control scope, and replace suitable contractor work with employees. |
| `A02` | QA utilization near 68% versus an 85% target in Feb–Jul 2026. | Normal availability but low project allocation and high non-project/bench time. | Team → employee → week → project/time mix. | Reallocate QA, improve assignments and demand planning; do not infer individual performance. |
| `A03` | Mar–Aug 2026: Software ~25/30 FTE, Data ~12/14; Systems ~18/17, Mechanical ~22/19. | Skill adjacency prevents excess capacity from filling the full shortage. | Month → skill → team/location → employee-skill bridge. | Cross-train adjacent skills, use short-term contractors, or hire if the gap persists. |
| `A04` | `FORGE-004` has a 45-day critical milestone delay and a later forecast finish. | Open dependency plus higher committed material/contractor cost. | Project → critical milestone → risk category → financial month/category. | Escalate the dependency and assign recovery-plan accountability. |
| `A05` | `FORGE-009` labor hours are near plan but labor cost is more than 15% unfavorable. | Contractor and overtime rate mix increases after February 2026. | Project → labor cost category → employment type → overtime week. | Change rate mix, cap overtime, and move suitable work to employees. |
| `A06` | Labor KPIs change before versus after cleansing. | 15 duplicate natural keys, 12 incomplete rows, and 266 late submissions. | QA result → LaborRecordID → employee/project/week. | Deduplicate, reject incomplete rows, validate entry, and follow up on compliance. |
| `A07` | `FORGE-007` is 48% complete but has consumed 68% of budget. | Front-loaded material/other spend and burn ahead of progress. | Project → financial month/category → milestone completion. | Apply a spend gate, review scope, and reforecast early. |

These are deterministic business scenarios, not independent random outliers.

## 7. File contract

- UTF-8 encoding, header row, comma delimiter, and `LF` line endings.
- ISO date format `YYYY-MM-DD`; month keys always use the first of the month.
- Boolean values stored as `0`/`1` for straightforward Power Query casting.
- Decimal point separator; hours/FTE and currency rounded to two decimals.
- Empty string represents a nullable value; no `NULL` or `N/A` token is used for
  numeric or date fields.
- Deterministic natural-grain ordering; CSV writer uses `lineterminator="\n"`.
- Controlled data-quality defects are limited to `FactLabor`. Dimension keys and
  all other relationships remain valid.

## 8. Deterministic generation sequence

1. Load and validate configuration and seed.
2. Build canonical date, team, skill, employee, and employee-skill dimensions.
3. Build project plan/budget and workforce-demand baselines.
4. Generate labor from employee availability and assignments; apply labor scenarios.
5. Generate financials that reconcile to labor and project budgets; apply cost scenarios.
6. Generate milestones and risks with linked schedule/risk scenarios.
7. Inject controlled data-quality defects last so clean baseline reconciliation remains valid.
8. Write 11 CSV files, manifest/checksums, and quality evidence.

## 9. Acceptance criteria

- Exactly 376 dates, 1,000 projects, 120 employees/contractors, and 11 CSV tables.
- `FactLabor` contains 6,000–15,000 rows.
- Approved project budgets reconcile to the documented $3.070 billion public R&D benchmark scale.
- Fixed seed and configuration produce byte-identical outputs and manifest hashes.
- No orphan foreign keys outside nullable role-playing date keys.
- Project monthly budgets reconcile to approved budget.
- Valid/deduplicated labor cost reconciles to financial labor actuals.
- All seven anomaly thresholds and cross-table evidence paths validate.
- QA clearly separates `PASS`, `FAIL`, and `EXPECTED_ANOMALY`.
- DAX and Streamlit catalogs document definitions, formats, sign conventions, and usage.
