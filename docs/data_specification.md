# FORGE RDE/PMO mock data specification

## 1. Nguồn yêu cầu và mục tiêu

Specification này chuyển trực tiếp context trong file `honeywell_forge_interview_context.md` đang mở thành một bộ mock data Power BI-ready cho portfolio/phỏng vấn Senior Advanced Data Analyst. Dữ liệu hoàn toàn giả lập, không phải dữ liệu nội bộ Honeywell.

Business flow được hỗ trợ:

`SAP-style source data → data quality → star schema → DAX/KPI → root cause → recommendation → PMO decision`

Các nhóm phân tích bắt buộc:

- Financial management và project cost.
- Labor utilization và time-entry compliance.
- Workforce/capacity planning theo team, skill, location và month.
- Milestone, risk, issue và project governance.
- Portfolio exception reporting và drill-through đến root cause.

## 2. Cấu hình mặc định đã chốt

| Thuộc tính | Giá trị | Lý do/quy ước |
|---|---:|---|
| Random seed | `20250810` | Fixed seed; chạy lại cùng config phải tạo byte-identical CSV. |
| Data range | `2024-01-01`–`2025-12-31` | Đúng 24 calendar months. |
| Data as-of date | `2025-06-30` | Tách actual/forecast để EAC và workforce forecast có ý nghĩa. |
| Fiscal calendar | January–December | File nguồn yêu cầu chốt fiscal calendar nhưng không chỉ định tháng bắt đầu; dùng calendar year và ghi rõ assumption. |
| RDE projects | 25 | Business key `FORGE-001`–`FORGE-025`. |
| Employees/contractors | 120 | Business key `EMP-0001`–`EMP-0120`. |
| Labor fact size | 8,000–20,000 | Một record chuẩn cho mỗi employee–project–week đang active, cộng một số duplicate cố ý. |
| CSV tables | 11 | Đúng danh sách trong file nguồn. |
| Business anomalies | 7 | Có signal, root cause, drill path, recommendation và estimated impact. |
| Hours/FTE/month | 160 | Assumption minh bạch cho workforce capacity. |
| Scheduled hours/workday | 8 | Dùng để tính scheduled, available và PTO hours. |

Mọi assumption không được định nghĩa cụ thể trong file nguồn đều được ghi trong tài liệu này và không được trình bày như dữ liệu Honeywell thật.

## 3. Thiết kế mô hình

### 3.1 Grain và vai trò bảng

| Table | Grain | Expected rows |
|---|---|---:|
| `DimDate` | Một calendar date | 731 |
| `DimProject` | Một RDE project | 25 |
| `DimEmployee` | Một employee/contractor | 120 |
| `DimTeam` | Một engineering team | 8 |
| `DimSkill` | Một skill | 8 |
| `BridgeEmployeeSkill` | Một employee–skill effective assignment | 120–360 |
| `FactLabor` | Một employee–project–week time entry | 8,000–20,000 |
| `FactFinancial` | Một project–month–cost category | Tối đa 2,400 |
| `FactMilestone` | Một project–milestone | 125–300 |
| `FactWorkforcePlan` | Một month–team–skill–location | Khoảng 768 |
| `FactRiskIssue` | Một project–risk/issue | Khoảng 75–175 |

### 3.2 Relationship rules

Power BI relationship mặc định là one-to-many, single direction từ dimension sang fact/bridge. Không tạo relationship fact-to-fact.

| From (one) | To (many) | Key | Active relationship |
|---|---|---|---|
| `DimDate` | `FactLabor` | `DateKey` → `WeekStartDateKey` | Yes |
| `DimDate` | `FactFinancial` | `DateKey` → `MonthStartDateKey` | Yes |
| `DimDate` | `FactWorkforcePlan` | `DateKey` → `MonthStartDateKey` | Yes |
| `DimDate` | `FactMilestone` | `DateKey` → `PlannedDateKey` | Yes |
| `DimDate` | `FactMilestone` | `DateKey` → `ForecastDateKey` | No; role-playing |
| `DimDate` | `FactRiskIssue` | `DateKey` → `IdentifiedDateKey` | Yes |
| `DimDate` | `FactRiskIssue` | `DateKey` → `DueDateKey` | No; role-playing |
| `DimProject` | `FactLabor` | `ProjectKey` | Yes |
| `DimProject` | `FactFinancial` | `ProjectKey` | Yes |
| `DimProject` | `FactMilestone` | `ProjectKey` | Yes |
| `DimProject` | `FactRiskIssue` | `ProjectKey` | Yes |
| `DimEmployee` | `FactLabor` | `EmployeeKey` | Yes |
| `DimEmployee` | `BridgeEmployeeSkill` | `EmployeeKey` | Yes |
| `DimTeam` | `DimEmployee` | `TeamKey` | Yes |
| `DimTeam` | `DimProject` | `TeamKey` → `PrimaryTeamKey` | No; avoids an ambiguous labor path |
| `DimTeam` | `FactWorkforcePlan` | `TeamKey` | Yes |
| `DimSkill` | `DimEmployee` | `SkillKey` → `PrimarySkillKey` | No; avoids an ambiguous bridge path |
| `DimSkill` | `BridgeEmployeeSkill` | `SkillKey` | Yes |
| `DimSkill` | `FactWorkforcePlan` | `SkillKey` | Yes |

Surrogate keys là integer ổn định. Business keys (`ProjectID`, `EmployeeID`, `TeamID`, `SkillID`) được giữ để trace về source-style records. Nullable `ActualDateKey`/`ClosedDateKey` vẫn được QA như foreign key trong CSV nhưng không tạo live Power BI relationship vì Python connector biểu diễn blank dưới dạng text.

## 4. Business definitions và reconciliation rules

### 4.1 Labor

- `ScheduledHours`: working days trong tuần × 8, sau khi loại holiday nhưng trước PTO.
- `AvailableHours = ScheduledHours - PTOHours`.
- `ProjectHours`: toàn bộ productive/project hours, đã bao gồm `OvertimeHours`.
- `NonProjectHours`: admin, training, internal meeting hoặc bench.
- Reconciliation: `ProjectHours + NonProjectHours = AvailableHours + OvertimeHours`.
- `Utilization % = SUM(ProjectHours) / SUM(AvailableHours)`.
- `Utilization Gap = Utilization % - weighted target utilization %`; âm nghĩa là dưới target.
- `ActualLaborCost = (ProjectHours - OvertimeHours) × StandardLaborRate + OvertimeHours × StandardLaborRate × OvertimeRateMultiplier`.
- `SubmissionStatus = Late` khi `SubmissionDate` sau Chủ nhật kết thúc tuần hơn 2 ngày.
- Overtime nằm trong numerator nhưng không cộng vào available-hours denominator; vì vậy utilization có thể lớn hơn 100% và phải được đọc cùng overtime.
- 169 employee-weeks được tách hợp lệ qua hai projects; scheduled/available/PTO/project/non-project/overtime được phân bổ, không nhân đôi capacity.

### 4.2 Financial

- `ActualCostAmount = ActualLaborCost + ActualMaterialCost + ActualOtherCost`.
- `EAC = ActualCostAmount + ForecastToComplete` ở additive monthly/category grain.
- `Forecast Variance $ = Approved Budget - EAC`; số âm là unfavorable/over budget.
- `Forecast Variance % = Forecast Variance $ / Approved Budget`.
- `Budget Consumed % = Actual Cost / Approved Budget`.
- `BudgetAmount` được phase theo month/category và reconcile về `DimProject[ApprovedBudget]`.
- `ActualLaborCost` trong financial phải reconcile với valid, deduplicated `FactLabor[ActualLaborCost]` theo project/month. Duplicate/missing time-entry rows được phát hiện trước khi reconciliation.
- `PeriodType = Actual` đến data as-of month; các tháng sau là `Forecast`.

### 4.3 Workforce

- `Capacity Gap FTE = ActualFTE - RequiredFTE`; âm là thiếu capacity.
- `OpenDemandFTE = MAX(RequiredFTE - ActualFTE, 0)`.
- `Demand Coverage % = ActualFTE / RequiredFTE`.
- `AvailableCapacityHours = ActualFTE × 160`.
- `RequiredCapacityHours = RequiredFTE × 160`.
- `ContractorFTE` là subset của `ActualFTE`.

### 4.4 Schedule, risk và health

- `ScheduleVarianceDays = ForecastDate - PlannedDate`.
- On-time milestone: actual date không sau planned date; milestone chưa hoàn thành dùng forecast date.
- `RiskScore = Probability × Impact`, mỗi thành phần theo scale 1–5.
- Health rule minh bạch, worst-status-wins:
  - **Red**: EAC over budget >10%, critical milestone delay >30 ngày, utilization gap < -12 percentage points, hoặc critical risk chưa có mitigation.
  - **Amber**: EAC over budget 3–10%, milestone delay 8–30 ngày, hoặc utilization gap < -5 percentage points.
  - **Green**: trong tolerance.

### 4.5 Realism controls

- Project start dates là irregular day-level dates; program/manager/sponsor/team assignments dùng weighted demand logic thay vì round-robin.
- Approved budgets dùng $5K approval granularity với project-specific category mix và front/bell/back-loaded phase curves.
- Employee hire/exit timing, location, contractor mix, rates và utilization targets thay đổi theo team; tên là synthetic pseudonyms.
- Labor utilization có employee persistence, seasonality, team demand, quarter-hour entry grain, varied PTO/overtime, three entry sources và occasional multi-project weeks.
- Milestone templates thay đổi theo program; forecast variance có project-level schedule signal, 28 distinct names, 41 variance values và rolling update dates.
- Risk probability/status/mitigation phụ thuộc lifecycle; 85 distinct contextual titles thay cho một title cố định mỗi category.
- Workforce actual FTE phản ánh hire/exit/partial-month/leave; required FTE là smoothed trend và demand chỉ phân bổ vào staffed or designated hub locations.

## 5. Controlled anomaly specification

| ID | Signal phải thấy | Root cause được chứng minh ở bảng khác | Drill path | Recommendation/impact |
|---|---|---|---|---|
| `A01` | `FORGE-001` complete 55%, consumed 70%; EAC đúng $400K trên approved budget. | Critical milestone delay làm contractor/overtime và committed cost tăng. | Project → financial category/month → labor employee/week → milestone. | Reforecast, khóa scope, thay contractor bằng employee phù hợp; tránh/giảm phần overrun dự kiến. |
| `A02` | Quality Assurance utilization khoảng 68% so với target 85% trong Jan–Jun 2025. | Available hours vẫn bình thường nhưng project assignment thấp và non-project/bench cao; không dùng dữ liệu performance để quy lỗi cá nhân. | Team → employee → week → assigned project/time mix. | Reallocate QA, điều chỉnh assignment/schedule và cải thiện demand planning. |
| `A03` | Jul–Dec 2025: Software 25/30 FTE, Data 12/14; Systems 18/17, Mechanical 22/19. | Primary/bridge skills cho thấy excess capacity không có skill adjacency đủ để lấp toàn bộ shortage. | Month → skill → team/location → employee skill bridge. | Cross-train Mechanical/Systems, contractor ngắn hạn, hiring nếu gap kéo dài. |
| `A04` | `FORGE-004` có critical milestone forecast trễ 45 ngày và forecast end date bị đẩy. | Risk/issue dependency mở và committed material/contractor cost tăng sau delay. | Project → critical milestone → linked risk category → financial month/category. | Escalate dependency, recovery plan và milestone owner accountability. |
| `A05` | `FORGE-009` total labor hours gần plan nhưng labor cost unfavorable >15%. | Contractor share và overtime mix cao hơn plan sau Mar 2025. | Project → labor cost category → employment type → overtime week. | Điều chỉnh rate mix, cap overtime và chuyển việc phù hợp về employee. |
| `A06` | KPI labor thay đổi trước/sau cleansing. | 15 duplicate natural time-entry keys, 12 missing project-hours/cost rows và late submissions. | QA result → LaborRecordID → employee/project/week. | Deduplicate, reject incomplete rows, time-entry validation và compliance follow-up. |
| `A07` | `FORGE-007` complete 48% nhưng consumed 68% budget. | Front-loaded material/other spend và burn rate cao hơn progress; tách khỏi A01 để minh họa budget-consumption red flag. | Project → financial month/category → milestone completion. | Spend gate, scope review và reforecast sớm. |

Anomaly là deterministic business scenarios, không phải các outlier random độc lập.

## 6. CSV contract

- Encoding UTF-8, có header, delimiter comma, line ending `LF`.
- Date format ISO `YYYY-MM-DD`; month key luôn là ngày đầu tháng.
- Boolean lưu `0`/`1` để Power Query dễ cast.
- Decimal dùng dấu chấm; hours/FTE làm tròn 2 chữ số; currency làm tròn 2 chữ số.
- Empty string biểu diễn nullable value; không dùng chuỗi `NULL`, `N/A` cho numeric/date.
- Record order deterministic theo natural grain; CSV writer dùng `lineterminator="\n"`.
- Các lỗi DQ cố ý chỉ nằm trong `FactLabor`; dimension key và relationship còn lại phải hợp lệ.

## 7. Generation order

1. `DimDate`, `DimTeam`, `DimSkill`.
2. `DimProject`, `DimEmployee`, `BridgeEmployeeSkill`.
3. Project plan/budget và workforce demand baseline.
4. `FactLabor` từ employee availability/assignment; cài labor anomalies.
5. `FactFinancial` reconcile về labor và project budget; cài cost anomalies.
6. `FactMilestone`, `FactRiskIssue`; cài schedule/risk relationships.
7. Cài controlled DQ defects cuối cùng để không làm sai baseline reconciliation.
8. Xuất 11 CSV, manifest/checksum và chạy quality suite.

## 8. Acceptance gates

- Đúng 24 months, 25 projects, 120 employees, 11 CSV.
- `FactLabor` trong khoảng 8,000–20,000 rows.
- Fixed seed + config tạo byte-identical output và identical SHA-256 manifest.
- Không có orphan foreign key ngoài nullable role-playing date keys.
- Project budget phase reconcile với approved budget.
- Valid/deduplicated labor reconcile với financial labor actual.
- 7 anomalies đạt threshold đã chốt và có cross-table evidence.
- QA report phân biệt `PASS`, `FAIL` và `EXPECTED_ANOMALY`; expected defects không bị che giấu.
- DAX catalog ghi business definition, format, sign convention và page usage.
