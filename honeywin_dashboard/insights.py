"""Data-driven business insights and corrective actions for dashboard pages."""

from __future__ import annotations

from dataclasses import dataclass
import math

import pandas as pd


@dataclass(frozen=True)
class BusinessInsight:
    """A supported observation paired with a recommended management response."""

    title: str
    evidence: str
    action: str
    tone: str = "primary"


def _currency(value: float) -> str:
    absolute = abs(float(value))
    sign = "-" if value < 0 else ""
    if absolute >= 1_000_000:
        return f"{sign}${absolute / 1_000_000:,.1f}M"
    if absolute >= 1_000:
        return f"{sign}${absolute / 1_000:,.0f}K"
    return f"{sign}${absolute:,.0f}"


def _percent(value: float) -> str:
    return "not available" if math.isnan(value) else f"{value:.1%}"


def _pp(value: float) -> str:
    return "not available" if math.isnan(value) else f"{value * 100:+.1f} pp"


def executive_insights(
    summary: dict[str, float],
    health: pd.DataFrame,
) -> list[BusinessInsight]:
    """Explain portfolio forecast, red-flag concentration, and cost/progress imbalance."""

    insights: list[BusinessInsight] = []
    variance = summary["forecast_variance"]
    variance_pct = summary["forecast_variance_pct"]
    overrun_projects = health[health["ForecastVariance"] < 0]
    if variance < 0 and not overrun_projects.empty:
        worst = overrun_projects.nsmallest(1, "ForecastVariance").iloc[0]
        insights.append(
            BusinessInsight(
                "Portfolio forecast is above approved funding",
                f"EAC is {_currency(summary['eac'])}, exceeding approved budget by "
                f"{_currency(-variance)} ({abs(variance_pct):.1%}); "
                f"{len(overrun_projects)} projects have an unfavorable forecast variance.",
                f"Require a cost recovery plan for {worst['ProjectID']} — "
                f"{worst['ProjectName']}, the largest forecast exposure at "
                f"{_currency(-worst['ForecastVariance'])} over budget.",
                "bad" if abs(variance_pct) >= 0.03 else "warning",
            )
        )
    else:
        insights.append(
            BusinessInsight(
                "Portfolio forecast remains within approved funding",
                f"EAC is {_currency(summary['eac'])} against "
                f"{_currency(summary['approved_budget'])} of approved budget.",
                "Maintain monthly estimate-at-completion reviews and preserve the current contingency position.",
                "good",
            )
        )

    driver_labels = {
        "CostHealth": "cost",
        "ScheduleHealth": "schedule",
        "LaborHealth": "labor",
        "RiskHealth": "risk",
    }
    driver_actions = {
        "CostHealth": "Validate scope, remaining forecast, and contingency assumptions for the affected projects.",
        "ScheduleHealth": "Rebaseline critical-path activities, assign recovery owners, and review milestone dates weekly.",
        "LaborHealth": "Reallocate available capacity to the affected projects and confirm resource demand with team leads.",
        "RiskHealth": "Start mitigation for unaddressed critical risks and close overdue actions with named owners and dates.",
    }
    red_count = int((health["OverallHealth"] == "Red").sum())
    amber_count = int((health["OverallHealth"] == "Amber").sum())
    if red_count or amber_count:
        driver_status = "Red" if red_count else "Amber"
        driver_counts = {
            column: int((health[column] == driver_status).sum()) for column in driver_labels
        }
        driver = max(driver_counts, key=driver_counts.get)
        insights.append(
            BusinessInsight(
                "Exception load is concentrated in a clear root-cause area",
                f"The current portfolio contains {red_count} red and {amber_count} amber projects; "
                f"{driver_labels[driver]} is the most frequent {driver_status.lower()} driver "
                f"({driver_counts[driver]} projects).",
                driver_actions[driver],
                "bad" if red_count else "warning",
            )
        )
    else:
        insights.append(
            BusinessInsight(
                "No red or amber project-health driver is present",
                f"All {len(health)} projects in the current filter context evaluate as green.",
                "Continue monitoring the cost, schedule, labor, and risk thresholds at each portfolio review.",
                "good",
            )
        )

    largest_gap = health.nlargest(1, "BudgetCompletionGap").iloc[0]
    gap = float(largest_gap["BudgetCompletionGap"])
    insights.append(
        BusinessInsight(
            "Cost consumption is ahead of reported progress",
            f"{largest_gap['ProjectID']} — {largest_gap['ProjectName']} has the largest "
            f"budget-to-completion gap at {_pp(gap)}.",
            "Reconcile percent-complete evidence with incurred cost and update the remaining-cost forecast before the next review.",
            "bad" if gap >= 0.15 else ("warning" if gap >= 0.05 else "good"),
        )
    )
    return insights


def financial_insights(
    summary: dict[str, float],
    health: pd.DataFrame,
    financial: pd.DataFrame,
) -> list[BusinessInsight]:
    """Explain forecast exposure, phased-plan variance, and commitments."""

    insights: list[BusinessInsight] = []
    unfavorable = health[health["ForecastVariance"] < 0]
    exposure = float(-unfavorable["ForecastVariance"].sum()) if not unfavorable.empty else 0.0
    if exposure > 0:
        worst = unfavorable.nsmallest(1, "ForecastVariance").iloc[0]
        insights.append(
            BusinessInsight(
                "Forecast overruns are concentrated in specific projects",
                f"{len(unfavorable)} projects account for {_currency(exposure)} of gross "
                f"forecast exposure; {worst['ProjectID']} is the largest at "
                f"{_currency(-worst['ForecastVariance'])}.",
                "Challenge remaining-cost assumptions on the exposed projects and document scope, rate, and schedule recovery levers.",
                "bad",
            )
        )
    else:
        insights.append(
            BusinessInsight(
                "No project is forecasting above approved budget",
                f"Portfolio EAC is {_currency(summary['eac'])} with a forecast variance of "
                f"{_currency(summary['forecast_variance'])}.",
                "Continue monthly EAC validation and monitor projects as contingency is consumed.",
                "good",
            )
        )

    if financial.empty:
        insights.append(
            BusinessInsight(
                "No posted cost is present in the selected period",
                "The active date and page filters return no financial transactions.",
                "Confirm the reporting period and cost-category filters before drawing a period variance conclusion.",
                "primary",
            )
        )
    else:
        category = financial.groupby("CostCategory", as_index=False).agg(
            PhasedBudget=("BudgetAmount", "sum"),
            ActualCost=("ActualCostAmount", "sum"),
        )
        category["PlanVariance"] = category["ActualCost"] - category["PhasedBudget"]
        largest_category = category.nlargest(1, "PlanVariance").iloc[0]
        category_variance = float(largest_category["PlanVariance"])
        insights.append(
            BusinessInsight(
                "A cost category is driving the largest phased-plan variance",
                f"{largest_category['CostCategory']} is "
                f"{_currency(abs(category_variance))} "
                f"{'above' if category_variance > 0 else 'below'} its phased budget in the selected period.",
                f"Review the timing and forecast assumptions behind {largest_category['CostCategory']} charges, then correct the next forecast cycle if the variance is structural.",
                "warning" if category_variance > 0 else "good",
            )
        )

    committed_ratio = (
        summary["committed_cost"] / summary["approved_budget"]
        if summary["approved_budget"]
        else float("nan")
    )
    insights.append(
        BusinessInsight(
            "Open commitments remain part of the funding exposure",
            f"Committed cost is {_currency(summary['committed_cost'])}, equal to "
            f"{_percent(committed_ratio)} of approved budget in the current context.",
            "Validate aged commitments, close fulfilled obligations, and incorporate remaining commitments into project-level EAC reviews.",
            "warning" if committed_ratio >= 0.05 else "primary",
        )
    )
    return insights


def labor_insights(
    summary: dict[str, float],
    labor: pd.DataFrame,
) -> list[BusinessInsight]:
    """Explain utilization, overtime, and time-entry compliance."""

    source = labor.assign(TargetHours=labor["AvailableHours"] * labor["UtilizationTarget"])
    team = source.groupby("TeamName", as_index=False).agg(
        AvailableHours=("AvailableHours", "sum"),
        ProjectHours=("ProjectHours", "sum"),
        TargetHours=("TargetHours", "sum"),
        OvertimeHours=("OvertimeHours", "sum"),
        LateEntries=("SubmissionStatus", lambda values: int((values == "Late").sum())),
    )
    team["Utilization"] = team["ProjectHours"] / team["AvailableHours"]
    team["Target"] = team["TargetHours"] / team["AvailableHours"]
    team["Gap"] = team["Utilization"] - team["Target"]
    team["OvertimeRate"] = team["OvertimeHours"] / team["ProjectHours"].replace(0, pd.NA)

    lowest = team.nsmallest(1, "Gap").iloc[0]
    highest_overtime = team.nlargest(1, "OvertimeRate").iloc[0]
    most_late = team.nlargest(1, "LateEntries").iloc[0]
    return [
        BusinessInsight(
            "Utilization is not meeting the weighted target",
            f"Portfolio utilization is {_percent(summary['utilization'])}, "
            f"{_pp(summary['utilization_gap'])} versus target; {lowest['TeamName']} "
            f"has the largest team gap at {_pp(float(lowest['Gap']))}.",
            f"Review the demand backlog and non-project allocation for {lowest['TeamName']}, then reassign available capacity to funded work where skills match.",
            "bad" if summary["utilization_gap"] < -0.12 else (
                "warning" if summary["utilization_gap"] < -0.05 else "good"
            ),
        ),
        BusinessInsight(
            "Overtime and time-entry discipline need targeted follow-up",
            f"Overtime is {_percent(summary['overtime_pct'])} of project hours and "
            f"{summary['late_entries']} entries were late. {highest_overtime['TeamName']} "
            f"has the highest overtime rate, while {most_late['TeamName']} has the most late entries.",
            "Confirm whether overtime reflects a persistent capacity constraint, rebalance assignments, and clear late submissions before the next reporting cut.",
            "warning" if summary["overtime_pct"] >= 0.05 or summary["compliance"] < 0.95 else "good",
        ),
    ]


def workforce_insights(
    summary: dict[str, float],
    workforce: pd.DataFrame,
) -> list[BusinessInsight]:
    """Explain supply-demand coverage and the most constrained workforce segment."""

    monthly_segment = workforce.groupby(
        ["MonthStartDate", "TeamName", "SkillName", "Location"], as_index=False
    ).agg(
        ActualFTE=("ActualFTE", "sum"),
        RequiredFTE=("RequiredFTE", "sum"),
        OpenDemandFTE=("OpenDemandFTE", "sum"),
    )
    segment = monthly_segment.groupby(
        ["TeamName", "SkillName", "Location"], as_index=False
    )[["ActualFTE", "RequiredFTE", "OpenDemandFTE"]].mean()
    segment["GapFTE"] = segment["ActualFTE"] - segment["RequiredFTE"]
    constrained = segment.nsmallest(1, "GapFTE").iloc[0]
    largest_open = segment.nlargest(1, "OpenDemandFTE").iloc[0]

    gap = summary["capacity_gap_fte"]
    return [
        BusinessInsight(
            "Workforce supply does not fully cover planned demand",
            f"Average demand coverage is {_percent(summary['demand_coverage_pct'])}, "
            f"with a {abs(gap):.1f} FTE {'shortfall' if gap < 0 else 'surplus'} across the selected period.",
            "Sequence hiring and internal reallocation against funded demand, then refresh required FTE assumptions with program owners.",
            "bad" if gap < 0 else "good",
        ),
        BusinessInsight(
            "The largest skill-location constraint is identifiable",
            f"{constrained['TeamName']} / {constrained['SkillName']} in "
            f"{constrained['Location']} has the largest average gap at "
            f"{float(constrained['GapFTE']):+.1f} FTE; the largest open-demand segment is "
            f"{largest_open['TeamName']} / {largest_open['SkillName']} at "
            f"{float(largest_open['OpenDemandFTE']):.1f} FTE.",
            f"Prioritize sourcing, cross-training, or reassignment for {constrained['SkillName']} in {constrained['Location']} and track closure against the monthly workforce plan.",
            "bad" if float(constrained["GapFTE"]) < 0 else "good",
        ),
    ]


def governance_insights(
    summary: dict[str, float | int],
    milestones: pd.DataFrame,
    risks: pd.DataFrame,
) -> list[BusinessInsight]:
    """Explain mitigation readiness, overdue actions, and critical-path delay."""

    open_critical = risks[
        (risks["IsCritical"] == 1) & risks["RiskStatus"].isin(["Open", "Monitoring"])
    ]
    if not open_critical.empty:
        top_category = open_critical["RiskCategory"].value_counts().idxmax()
        category_count = int((open_critical["RiskCategory"] == top_category).sum())
    else:
        top_category = "No category"
        category_count = 0

    critical_milestones = milestones[milestones["IsCritical"] == 1]
    delayed = critical_milestones.nlargest(1, "ScheduleVarianceDays")
    if delayed.empty:
        delay_evidence = "No critical milestone is present in the current filter context."
        delay_action = "Maintain milestone-owner updates and continue monitoring forecast dates."
        delay_tone = "good"
    else:
        milestone = delayed.iloc[0]
        delay_evidence = (
            f"{milestone['ProjectID']} — {milestone['MilestoneName']} has the largest "
            f"critical-path variance at {float(milestone['ScheduleVarianceDays']):.0f} days."
        )
        delay_action = (
            f"Assign a dated recovery plan to {milestone['MilestoneOwner']} and validate downstream dependencies for {milestone['ProjectID']}."
        )
        delay_tone = "bad" if float(milestone["ScheduleVarianceDays"]) > 30 else "warning"

    return [
        BusinessInsight(
            "Critical-risk mitigation is incomplete",
            f"There are {summary['open_critical_risks']} open critical risks, including "
            f"{summary['critical_without_mitigation']} without started mitigation; "
            f"{top_category} is the largest critical-risk category ({category_count}).",
            "Start mitigation for every unaddressed critical risk, confirm accountable owners, and escalate due dates that cannot be recovered.",
            "bad" if summary["critical_without_mitigation"] else (
                "warning" if summary["open_critical_risks"] else "good"
            ),
        ),
        BusinessInsight(
            "Governance follow-through and schedule recovery need focus",
            f"{summary['overdue_actions']} actions are overdue and milestone on-time performance is "
            f"{_percent(float(summary['on_time_milestone_pct']))}. {delay_evidence}",
            delay_action,
            "bad" if summary["overdue_actions"] or delay_tone == "bad" else delay_tone,
        ),
    ]
