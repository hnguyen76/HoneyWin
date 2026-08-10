# Power BI model setup

## Import order

1. Import all CSV files from `data/generated` with UTF-8 encoding and comma delimiter.
2. Create a raw staging query for every CSV and disable load for staging queries.
3. For `FactLabor`, reject rows with blank `ProjectHours` or `ActualLaborCost`, then deduplicate on `EmployeeKey`, `ProjectKey`, `WeekStartDateKey`; load the clean result as `FactLabor`.
4. Load dimensions, bridge and remaining facts with the names used in `measures.dax`.
5. Mark `DimDate[Date]` as the model date table and sort `MonthName` by `MonthNumber`.

## Data types

- Keys: Whole Number, except business/record IDs which stay Text.
- Dates: Date.
- Hours, FTE, rates and currency: Decimal Number or Fixed Decimal Number.
- Boolean flags: Whole Number (`0`/`1`) or True/False after conversion.
- Percent targets: Decimal Number formatted as percentage.

## Relationships

Use one-to-many, single-direction relationships. Do not join facts directly.

| One side | Many side | Active |
|---|---|---:|
| `DimDate[DateKey]` | `FactLabor[WeekStartDateKey]` | Yes |
| `DimDate[DateKey]` | `FactFinancial[MonthStartDateKey]` | Yes |
| `DimDate[DateKey]` | `FactWorkforcePlan[MonthStartDateKey]` | Yes |
| `DimDate[DateKey]` | `FactMilestone[PlannedDateKey]` | Yes |
| `DimDate[DateKey]` | `FactMilestone[ForecastDateKey]` | No |
| `DimDate[DateKey]` | `FactRiskIssue[IdentifiedDateKey]` | Yes |
| `DimDate[DateKey]` | `FactRiskIssue[DueDateKey]` | No |
| `DimProject[ProjectKey]` | `FactLabor[ProjectKey]` | Yes |
| `DimProject[ProjectKey]` | `FactFinancial[ProjectKey]` | Yes |
| `DimProject[ProjectKey]` | `FactMilestone[ProjectKey]` | Yes |
| `DimProject[ProjectKey]` | `FactRiskIssue[ProjectKey]` | Yes |
| `DimEmployee[EmployeeKey]` | `FactLabor[EmployeeKey]` | Yes |
| `DimEmployee[EmployeeKey]` | `BridgeEmployeeSkill[EmployeeKey]` | Yes |
| `DimTeam[TeamKey]` | `DimEmployee[TeamKey]` | Yes |
| `DimTeam[TeamKey]` | `DimProject[PrimaryTeamKey]` | No |
| `DimTeam[TeamKey]` | `FactWorkforcePlan[TeamKey]` | Yes |
| `DimSkill[SkillKey]` | `DimEmployee[PrimarySkillKey]` | No |
| `DimSkill[SkillKey]` | `BridgeEmployeeSkill[SkillKey]` | Yes |
| `DimSkill[SkillKey]` | `FactWorkforcePlan[SkillKey]` | Yes |

The live model has 19 relationships: 15 active and 4 inactive. The inactive
project-team and employee-primary-skill paths prevent ambiguity with the active
labor/bridge paths. `ActualDateKey` and `ClosedDateKey` remain validated in the
CSV layer but are not modeled because the Python connector represents their
nullable blanks as text; adding them would require helper keys or sentinel dates.
Avoid enabling bidirectional filters through `BridgeEmployeeSkill`; use explicit
DAX/TREATAS or `USERELATIONSHIP` for alternate paths.

Disable Auto Date/Time and use only `DimDate`. Every Python M partition must end
with explicit `Table.TransformColumnTypes`; otherwise a Desktop refresh can
silently revert numeric fact columns to text.

## Required reconciliation before visuals

- `Labor Cost Reconciliation $` must be 0 at portfolio and project-month-category levels after cleansing.
- Project budget in `FactFinancial` must reconcile to `DimProject[ApprovedBudget]`.
- Row-level `EAC = ActualCostAmount + ForecastToComplete`.
- FTE cards use average monthly snapshots, not SUM across months.
- Forecast variance is `Approved Budget − EAC`; negative means unfavorable.
