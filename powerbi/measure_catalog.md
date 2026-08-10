# Power BI measure catalog

Tạo một empty table tên `Measures`, đặt measures theo display folders dưới đây và dùng công thức trong `measures.dax`. `FactLabor` phải là query đã reject incomplete rows và deduplicate natural key.

## Financial & Project Cost

| Measure | Business definition | Format | Sign convention / usage |
|---|---|---|---|
| `Approved Budget` | Tổng current approved project budget từ dimension. | `$#,##0` | Positive budget; KPI card. |
| `Baseline Budget` | Original baseline budget. | `$#,##0` | Positive. |
| `Phased Budget` | Budget được phase ở project–month–category grain. | `$#,##0` | Dùng trend/category, không thay cho approved card. |
| `Actual Cost` | Sum actual labor + material + other. | `$#,##0` | Positive spend. |
| `Committed Cost` | Open committed cost. | `$#,##0` | Positive exposure. |
| `Forecast to Complete` | Forecast spend còn lại trong future periods. | `$#,##0` | Positive remaining cost. |
| `EAC` | Actual Cost + Forecast to Complete across the full project timeline. | `$#,##0` | Positive total expected cost; ignores canonical date filter so month axes do not turn EAC into monthly spend. |
| `Forecast Variance $` | Approved Budget − EAC. | `$#,##0;($#,##0)` | Negative = unfavorable/over budget. |
| `Forecast Variance %` | Forecast Variance $ / Approved Budget. | `0.0%;(0.0%)` | Negative = unfavorable. |
| `Budget Consumed %` | Actual Cost / Approved Budget. | `0.0%` | Higher = more consumed. |
| `Project Completion %` | Budget-weighted percent complete. | `0.0%` | 0–100%. |
| `Budget vs Completion Gap pp` | Budget Consumed % − Completion %. | `0.0%;(0.0%)` | Positive = spend ahead of progress. |
| `Earned Value (Mock)` | Approved budget × percent complete. | `$#,##0` | Portfolio proxy only; not a formal EVMS baseline. |
| `Cost Performance Index (Mock)` | Earned Value / Actual Cost. | `0.00x` | <1 unfavorable. |
| `Monthly Actual + Forecast Spend` | Additive actual-or-forecast amount by month. | `$#,##0` | Use on monthly trend, not as project-total EAC card. |
| `Labor Cost Reconciliation $` | Clean FactLabor cost − financial labor cost. | `$#,##0;($#,##0)` | Target 0. |
| `Labor Cost Variance $` | Actual-period labor budget − actual labor cost. | `$#,##0;($#,##0)` | Negative = unfavorable. |
| `Labor Cost Variance %` | Labor Cost Variance $ / actual-period labor budget. | `0.0%;(0.0%)` | Negative = unfavorable. |

## Labor Utilization

| Measure | Business definition | Format | Sign convention / usage |
|---|---|---|---|
| `Available Hours` | Scheduled hours after PTO/holiday. | `#,##0.0` | Denominator for utilization. |
| `Project Hours` | Productive/project hours, including overtime. | `#,##0.0` | Numerator. |
| `Non-Project Hours` | Admin, training, meetings and bench. | `#,##0.0` | Root-cause mix. |
| `Overtime Hours` | Overtime subset of Project Hours. | `#,##0.0` | Can push utilization >100%. |
| `PTO Hours` | PTO deducted from schedule. | `#,##0.0` | Denominator control. |
| `Labor Utilization %` | Project Hours / Available Hours. | `0.0%` | Higher is not automatically better; inspect overtime/mix. |
| `Weighted Utilization Target %` | Available-hour weighted employee/team target. | `0.0%` | Comparator. |
| `Utilization Gap pp` | Actual utilization − target. | `0.0%;(0.0%)` | Negative = below target. |
| `Non-Project / Bench %` | Non-project hours / available hours. | `0.0%` | Higher explains underallocation. |
| `Overtime % of Project Hours` | Overtime / project hours. | `0.0%` | Rate-mix driver. |
| `Contractor Project Hours %` | Contractor productive hours / total productive hours. | `0.0%` | Contractor reliance. |
| `Time-entry Compliance %` | 1 − late entries / all entries. | `0.0%` | Higher is better. |
| `Employee Utilization Band` | Distribution bucket for employee-level views. | Text | Use only with employee grain/distribution visual. |

## Workforce / Capacity

FTE metrics use average monthly snapshots across the selected period, avoiding invalid summation of headcount across months.

| Measure | Business definition | Format | Sign convention / usage |
|---|---|---|---|
| `Actual FTE` | Average monthly actual capacity. | `#,##0.0` | Positive capacity. |
| `Required FTE` | Average monthly demand. | `#,##0.0` | Positive requirement. |
| `Capacity Gap FTE` | Actual − Required. | `#,##0.0;(#,##0.0)` | Negative = shortage. |
| `Open Demand FTE` | Average positive shortage only. | `#,##0.0` | Positive need. |
| `Contractor FTE` | Contractor subset of actual. | `#,##0.0` | Positive. |
| `Contractor FTE %` | Contractor / actual. | `0.0%` | Reliance indicator. |
| `Demand Coverage %` | Actual / required. | `0.0%` | <100% shortage. |
| `Available Capacity Hours` | Actual FTE × 160. | `#,##0` | Average monthly hours. |
| `Required Capacity Hours` | Required FTE × 160. | `#,##0` | Average monthly hours. |
| `Capacity Gap Hours` | Available − required hours. | `#,##0;(#,##0)` | Negative = shortage. |
| `Hiring / Reallocation Need FTE` | MAX(0, −capacity gap). | `#,##0.0` | Positive action need. |

## Governance / Project Health

| Measure | Business definition | Format | Sign convention / usage |
|---|---|---|---|
| `Active Projects` | Active + At Risk + Delayed. | `#,##0` | Portfolio count. |
| `Projects At Risk` | At Risk + Delayed statuses. | `#,##0` | Management attention. |
| `On-Time Milestone %` | Milestones with variance ≤0 / all milestones. | `0.0%` | Higher is better. |
| `Average Schedule Variance Days` | Average forecast minus planned days. | `0.0` | Positive = late. |
| `Max Critical Milestone Delay Days` | Maximum critical-path variance. | `0` | >30 = Red. |
| `Open Critical Risks` | Critical Open/Monitoring items. | `#,##0` | Governance KPI count; health becomes Red only when mitigation has not started. |
| `Critical Risks without Mitigation` | Critical Open/Monitoring items whose mitigation is Not Started. | `#,##0` | >0 = Red under the source health logic. |
| `Overdue Actions` | Open items with overdue due date. | `#,##0` | >0 requires action. |
| `Cost Health` | Red >10% EAC over; Amber 3–10%; else Green. | Text | Transparent rule. |
| `Schedule Health` | Red >30d; Amber 8–30d; else Green. | Text | Transparent rule. |
| `Labor Health` | Amber when utilization gap <-5pp; else Green. | Text | The source defines utilization as an Amber trigger, not a standalone Red rule. |
| `Risk Health` | Red if a critical risk has no mitigation started; Amber if overdue; else Green. | Text | Transparent rule. |
| `Overall Project Health` | Worst of Cost/Schedule/Labor/Risk. | Text | Worst-status-wins; no black box weighting. |
| `Projects with Budget-Consumption Red Flag` | Count projects whose consumed-progress gap ≥15pp. | `#,##0` | Exception count. |
| `Projects with Any Red Flag` | Overall Red or budget-consumption gap ≥15pp. | `#,##0` | Executive exception count. |

## Dashboard mapping

- Executive / PMO Overview: approved budget, actual, committed, EAC, variance, utilization, active/at-risk projects, on-time milestones, red flags.
- Financial & Project Cost: phased budget, actual components, EAC, variance, burn/forecast trend, CPI mock proxy.
- Labor Utilization: hours mix, utilization/target/gap, overtime, contractor reliance, compliance and employee bands.
- Workforce / Capacity: actual/required/gap/open demand/contractor/coverage by month–team–skill–location.
- Governance & Performance: health measures, milestone variance, risk score, critical risks, overdue actions and exception counts.
