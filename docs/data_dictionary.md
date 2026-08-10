# Data dictionary — FORGE RDE/PMO mock dataset

Type convention: `int`, `decimal(18,2)`, `text`, `date`, and `boolean`. `PK` is a physical primary key, `BK` is a business key, and `FK` is a foreign key. Columns are non-null unless explicitly marked otherwise.

## `DimDate.csv`

Grain: one calendar date from 2024-01-01 through 2025-12-31.

| Column | Type/key | Nullable | Definition/rule |
|---|---|---:|---|
| `DateKey` | int, PK | No | `YYYYMMDD`. |
| `Date` | date | No | Canonical calendar date. |
| `DayOfWeekName` | text | No | Monday–Sunday. |
| `DayOfWeekNumber` | int | No | Monday=1, Sunday=7. |
| `WeekStartDate` | date | No | Monday of ISO week. |
| `WeekEndDate` | date | No | Sunday of ISO week. |
| `WeekOfYear` | int | No | ISO week 1–53. |
| `MonthNumber` | int | No | 1–12. |
| `MonthName` | text | No | January–December. |
| `MonthStartDate` | date | No | First day of month. |
| `YearMonth` | text | No | `YYYY-MM`. |
| `CalendarQuarter` | text | No | `Q1`–`Q4`. |
| `CalendarYear` | int | No | Four-digit year. |
| `FiscalMonthNumber` | int | No | Same as calendar month under Jan fiscal start. |
| `FiscalQuarter` | text | No | Same as calendar quarter. |
| `FiscalYear` | int | No | Same as calendar year. |
| `IsWeekend` | boolean | No | 1 for Saturday/Sunday. |
| `IsHoliday` | boolean | No | 1 for fixed mock US holiday calendar. |
| `HolidayName` | text | Yes | Holiday label; blank otherwise. |
| `IsWorkingDay` | boolean | No | 1 when weekday and not holiday. |
| `WorkingHours` | decimal | No | 8 for working day, otherwise 0. |
| `PeriodType` | text | No | `Actual` through 2025-06-30, else `Forecast`. |

## `DimTeam.csv`

Grain: one engineering team.

| Column | Type/key | Nullable | Definition/rule |
|---|---|---:|---|
| `TeamKey` | int, PK | No | Stable surrogate key. |
| `TeamID` | text, BK | No | `TEAM-01`–`TEAM-08`. |
| `TeamName` | text | No | Engineering team label. |
| `TeamLeader` | text | No | Synthetic leader label. |
| `EngineeringFunction` | text | No | RDE/PMO function grouping. |
| `UtilizationTarget` | decimal | No | Team target stored as 0–1 decimal. |
| `ActiveFlag` | boolean | No | 1 for active team. |

## `DimSkill.csv`

Grain: one workforce skill.

| Column | Type/key | Nullable | Definition/rule |
|---|---|---:|---|
| `SkillKey` | int, PK | No | Stable surrogate key. |
| `SkillID` | text, BK | No | `SKILL-01`–`SKILL-08`. |
| `SkillName` | text | No | Software, Data, Systems, Mechanical, QA, Cloud/DevOps, Cybersecurity, or PMO. |
| `SkillFamily` | text | No | Broader skill family. |
| `SkillCategory` | text | No | Technical, Quality, or Program. |
| `AdjacencyGroup` | text | No | Cross-training/skill-adjacency group. |
| `IsCriticalSkill` | boolean | No | 1 for constrained/critical capability. |

## `DimProject.csv`

Grain: one FORGE-style RDE project; exactly 25 rows.

| Column | Type/key | Nullable | Definition/rule |
|---|---|---:|---|
| `ProjectKey` | int, PK | No | Stable surrogate key 1–25. |
| `ProjectID` | text, BK | No | `FORGE-001`–`FORGE-025`. |
| `ProjectName` | text | No | Synthetic project name. |
| `Program` | text | No | Portfolio program grouping. |
| `ProjectManager` | text | No | Synthetic PM label. |
| `Sponsor` | text | No | Synthetic sponsor role. |
| `PrimaryTeamKey` | int, FK | No | → `DimTeam[TeamKey]`. |
| `StartDate` | date | No | Planned/project start. |
| `PlannedEndDate` | date | No | Baseline end date. |
| `ForecastEndDate` | date | No | Current forecast end; includes controlled delay. |
| `ActualEndDate` | date | Yes | Populated only for completed project. |
| `ProjectStatus` | text | No | `Completed`, `Active`, `At Risk`, `Delayed`, `Planned`. |
| `Priority` | text | No | `High`, `Medium`, `Low`. |
| `PercentComplete` | decimal | No | 0–100 as of 2025-06-30. |
| `ApprovedBudget` | decimal | No | Current approved budget; reconciles to financial budget. |
| `BaselineBudget` | decimal | No | Original baseline before approved changes. |
| `BudgetClass` | text | No | `Small`, `Medium`, `Large`, `Strategic`. |

## `DimEmployee.csv`

Grain: one employee or contractor; exactly 120 rows.

| Column | Type/key | Nullable | Definition/rule |
|---|---|---:|---|
| `EmployeeKey` | int, PK | No | Stable surrogate key 1–120. |
| `EmployeeID` | text, BK | No | `EMP-0001`–`EMP-0120`. |
| `EmployeeName` | text | No | Synthetic label; not real personally identifiable information. |
| `TeamKey` | int, FK | No | → `DimTeam[TeamKey]`. |
| `PrimarySkillKey` | int, FK | No | → `DimSkill[SkillKey]`. |
| `Location` | text | No | Synthetic workforce location. |
| `EmploymentType` | text | No | `Employee` or `Contractor`. |
| `HireDate` | date | No | Employment effective date. |
| `ExitDate` | date | Yes | Blank until the resource exits. |
| `StandardLaborRate` | decimal | No | Hourly cost rate in USD. |
| `UtilizationTarget` | decimal | No | Inherited from team, 0–1 decimal. |
| `EmploymentStatus` | text | No | `Active` or `Exited` as of the data as-of date. |
| `IsActiveAsOfDate` | boolean | No | Active on 2025-06-30. |

## `BridgeEmployeeSkill.csv`

Grain: one effective employee–skill association.

| Column | Type/key | Nullable | Definition/rule |
|---|---|---:|---|
| `EmployeeSkillKey` | int, PK | No | Stable bridge record key. |
| `EmployeeKey` | int, FK | No | → `DimEmployee[EmployeeKey]`. |
| `SkillKey` | int, FK | No | → `DimSkill[SkillKey]`. |
| `ProficiencyLevel` | int | No | 1–5. |
| `ProficiencyCategory` | text | No | `Foundational`, `Intermediate`, `Advanced`, `Expert`. |
| `IsPrimarySkill` | boolean | No | Exactly one primary skill per employee. |
| `IsCertified` | boolean | No | Certification indicator. |
| `CertificationName` | text | Yes | Synthetic certification label. |
| `EffectiveDate` | date | No | Skill effective start. |
| `ExpirationDate` | date | Yes | Blank for current association. |

## `FactLabor.csv`

Grain: one employee–project–week time entry. The natural key is (`EmployeeKey`, `ProjectKey`, `WeekStartDateKey`). Fifteen duplicate natural keys are intentionally included for A06, while `LaborRecordID` remains unique.

| Column | Type/key | Nullable | Definition/rule |
|---|---|---:|---|
| `LaborRecordID` | text, PK | No | Deterministic record ID. |
| `WeekStartDateKey` | int, FK | No | Monday → `DimDate[DateKey]`. |
| `EmployeeKey` | int, FK | No | → `DimEmployee[EmployeeKey]`. |
| `ProjectKey` | int, FK | No | → `DimProject[ProjectKey]`. |
| `ScheduledHours` | decimal | No | Weekday hours excluding holidays, before PTO. |
| `AvailableHours` | decimal | No | Scheduled minus PTO. |
| `ProjectHours` | decimal | Yes | Productive/project hours including overtime; 12 blanks intentionally injected. |
| `NonProjectHours` | decimal | No | Admin/training/bench hours. |
| `OvertimeHours` | decimal | No | Subset of ProjectHours above available capacity. |
| `PTOHours` | decimal | No | Time off deducted from scheduled hours. |
| `StandardLaborRate` | decimal | No | Snapshot of employee rate. |
| `OvertimeRateMultiplier` | decimal | No | 1.5 for employees; 1.0 for contractors. |
| `ActualLaborCost` | decimal | Yes | Calculated cost; blank with missing ProjectHours. |
| `SubmissionDate` | date | No | Synthetic time-entry submission date. |
| `SubmissionStatus` | text | No | `On Time` or `Late`. |
| `TimeEntrySource` | text | No | `SAP-Style Time` mock source label. |

## `FactFinancial.csv`

Grain: project–month–cost category. Categories: `Labor`, `Contractor`, `Material`, `Other`.

| Column | Type/key | Nullable | Definition/rule |
|---|---|---:|---|
| `FinancialRecordID` | text, PK | No | Deterministic record ID. |
| `MonthStartDateKey` | int, FK | No | First day of month → `DimDate[DateKey]`. |
| `FiscalMonth` | text | No | `YYYY-MM`. |
| `ProjectKey` | int, FK | No | → `DimProject[ProjectKey]`. |
| `CostCategory` | text | No | Labor, Contractor, Material, Other. |
| `PeriodType` | text | No | `Actual` or `Forecast`. |
| `BudgetAmount` | decimal | No | Phased approved budget. |
| `ActualLaborCost` | decimal | No | Labor/contractor actual; 0 for other categories. |
| `ActualMaterialCost` | decimal | No | Material actual; 0 otherwise. |
| `ActualOtherCost` | decimal | No | Other actual; 0 otherwise. |
| `ActualCostAmount` | decimal | No | Sum of three actual components. |
| `CommittedCost` | decimal | No | Open committed cost allocated to month/category. |
| `ForecastToComplete` | decimal | No | Remaining forecast spend for future periods. |
| `EAC` | decimal | No | ActualCostAmount + ForecastToComplete. |
| `PlannedLaborHours` | decimal | No | Planned hours for Labor/Contractor; 0 otherwise. |
| `ActualLaborHours` | decimal | No | Valid/deduplicated labor hours; 0 otherwise. |

## `FactMilestone.csv`

Grain: one milestone for one project; 5–12 milestones per project.

| Column | Type/key | Nullable | Definition/rule |
|---|---|---:|---|
| `MilestoneKey` | int, PK | No | Stable milestone key. |
| `ProjectKey` | int, FK | No | → `DimProject[ProjectKey]`. |
| `MilestoneSequence` | int | No | Order within project. |
| `MilestoneName` | text | No | Standard RDE stage/milestone label. |
| `PlannedDateKey` | int, FK | No | → `DimDate[DateKey]`. |
| `ForecastDateKey` | int, FK | No | → `DimDate[DateKey]`. |
| `ActualDateKey` | int, FK | Yes | → `DimDate[DateKey]`; blank when incomplete. |
| `PlannedDate` | date | No | Baseline milestone date. |
| `ForecastDate` | date | No | Current forecast. |
| `ActualDate` | date | Yes | Actual completion date. |
| `CompletionPercent` | decimal | No | 0–100. |
| `ScheduleVarianceDays` | int | No | Forecast minus planned days. |
| `ScheduleStatus` | text | No | `On Time`, `At Risk`, `Delayed`, `Complete`. |
| `IsCritical` | boolean | No | Critical-path indicator. |
| `MilestoneOwner` | text | No | Synthetic owner role. |
| `LastUpdatedDate` | date | No | Data as-of date. |

## `FactWorkforcePlan.csv`

Grain: month–team–skill–location.

| Column | Type/key | Nullable | Definition/rule |
|---|---|---:|---|
| `WorkforcePlanRecordID` | text, PK | No | Deterministic record ID. |
| `MonthStartDateKey` | int, FK | No | → `DimDate[DateKey]`. |
| `TeamKey` | int, FK | No | → `DimTeam[TeamKey]`. |
| `SkillKey` | int, FK | No | → `DimSkill[SkillKey]`. |
| `Location` | text | No | Workforce planning location. |
| `RequiredFTE` | decimal | No | Demand/required capacity. |
| `ActualFTE` | decimal | No | Available headcount/FTE. |
| `OpenDemandFTE` | decimal | No | MAX(Required−Actual, 0). |
| `ContractorFTE` | decimal | No | Contractor subset of actual. |
| `CapacityGapFTE` | decimal | No | Actual−Required; negative is shortage. |
| `AvailableCapacityHours` | decimal | No | ActualFTE × 160. |
| `RequiredCapacityHours` | decimal | No | RequiredFTE × 160. |

## `FactRiskIssue.csv`

Grain: one risk or issue for one project.

| Column | Type/key | Nullable | Definition/rule |
|---|---|---:|---|
| `RiskIssueKey` | int, PK | No | Stable surrogate key. |
| `RiskIssueID` | text, BK | No | Deterministic risk/issue ID. |
| `ProjectKey` | int, FK | No | → `DimProject[ProjectKey]`. |
| `RecordType` | text | No | `Risk` or `Issue`. |
| `RiskTitle` | text | No | Synthetic risk/issue description. |
| `RiskCategory` | text | No | Schedule, Cost, Resource, Technical, Quality, Dependency. |
| `Probability` | int | No | 1–5. |
| `Impact` | int | No | 1–5. |
| `RiskScore` | int | No | Probability × Impact. |
| `RiskSeverity` | text | No | Low, Medium, High, Critical. |
| `Owner` | text | No | Synthetic accountable role. |
| `IdentifiedDateKey` | int, FK | No | → `DimDate[DateKey]`. |
| `DueDateKey` | int, FK | No | → `DimDate[DateKey]`. |
| `ClosedDateKey` | int, FK | Yes | → `DimDate[DateKey]`; blank while open. |
| `IdentifiedDate` | date | No | Risk/issue creation date. |
| `DueDate` | date | No | Mitigation/action due date. |
| `ClosedDate` | date | Yes | Closure date when closed. |
| `RiskStatus` | text | No | `Open`, `Monitoring`, `Mitigated`, `Closed`. |
| `MitigationStatus` | text | No | `Not Started`, `In Progress`, `Completed`, `Not Required`. |
| `IsCritical` | boolean | No | 1 for critical open governance item. |
| `IsOverdue` | boolean | No | Open item with due date before data as-of date. |
