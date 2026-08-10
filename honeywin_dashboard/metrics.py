"""Pure metric calculations aligned with the audited Power BI definitions."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .data import FilteredData


def safe_divide(numerator: float, denominator: float) -> float:
    """Return a stable ratio or NaN when the denominator is zero."""

    return float(numerator / denominator) if denominator else float("nan")


def financial_summary(data: FilteredData) -> dict[str, float]:
    """Calculate portfolio financial KPIs in the current filter context."""

    approved = float(data.projects["ApprovedBudget"].sum())
    baseline = float(data.projects["BaselineBudget"].sum())
    actual = float(data.financial["ActualCostAmount"].sum())
    committed = float(data.financial["CommittedCost"].sum())
    forecast_to_complete = float(data.financial_all_dates["ForecastToComplete"].sum())
    full_horizon_actual = float(data.financial_all_dates["ActualCostAmount"].sum())
    eac = full_horizon_actual + forecast_to_complete
    variance = approved - eac
    completion_value = float(
        (
            data.projects["ApprovedBudget"]
            * data.projects["PercentComplete"].fillna(0)
            / 100
        ).sum()
    )
    return {
        "approved_budget": approved,
        "baseline_budget": baseline,
        "budget_change": approved - baseline,
        "actual_cost": actual,
        "committed_cost": committed,
        "forecast_to_complete": forecast_to_complete,
        "eac": eac,
        "forecast_variance": variance,
        "forecast_variance_pct": safe_divide(variance, approved),
        "budget_consumed_pct": safe_divide(actual, approved),
        "project_completion_pct": safe_divide(completion_value, approved),
    }


def labor_summary(labor: pd.DataFrame) -> dict[str, float]:
    """Calculate labor utilization, target, compliance, and mix metrics."""

    available = float(labor["AvailableHours"].sum())
    project = float(labor["ProjectHours"].sum())
    target_numerator = float((labor["AvailableHours"] * labor["UtilizationTarget"]).sum())
    entries = int(len(labor))
    late = int((labor["SubmissionStatus"] == "Late").sum())
    overtime = float(labor["OvertimeHours"].sum())
    contractor_hours = float(
        labor.loc[labor["EmploymentType"] == "Contractor", "ProjectHours"].sum()
    )
    utilization = safe_divide(project, available)
    target = safe_divide(target_numerator, available)
    return {
        "available_hours": available,
        "project_hours": project,
        "non_project_hours": float(labor["NonProjectHours"].sum()),
        "overtime_hours": overtime,
        "pto_hours": float(labor["PTOHours"].sum()),
        "utilization": utilization,
        "target": target,
        "utilization_gap": utilization - target,
        "overtime_pct": safe_divide(overtime, project),
        "contractor_hours_pct": safe_divide(contractor_hours, project),
        "time_entries": entries,
        "late_entries": late,
        "compliance": 1 - safe_divide(late, entries),
    }


def workforce_summary(workforce: pd.DataFrame) -> dict[str, float]:
    """Calculate average monthly workforce snapshots, never period sums."""

    monthly = (
        workforce.groupby("MonthStartDate", as_index=False)[
            [
                "ActualFTE",
                "RequiredFTE",
                "OpenDemandFTE",
                "ContractorFTE",
                "AvailableCapacityHours",
                "RequiredCapacityHours",
            ]
        ]
        .sum()
        .sort_values("MonthStartDate")
    )
    if monthly.empty:
        return {key: float("nan") for key in (
            "actual_fte",
            "required_fte",
            "capacity_gap_fte",
            "open_demand_fte",
            "contractor_fte",
            "contractor_fte_pct",
            "demand_coverage_pct",
            "available_capacity_hours",
            "required_capacity_hours",
            "capacity_gap_hours",
            "hiring_need_fte",
        )}
    actual = float(monthly["ActualFTE"].mean())
    required = float(monthly["RequiredFTE"].mean())
    contractor = float(monthly["ContractorFTE"].mean())
    available_hours = float(monthly["AvailableCapacityHours"].mean())
    required_hours = float(monthly["RequiredCapacityHours"].mean())
    gap = actual - required
    return {
        "actual_fte": actual,
        "required_fte": required,
        "capacity_gap_fte": gap,
        "open_demand_fte": float(monthly["OpenDemandFTE"].mean()),
        "contractor_fte": contractor,
        "contractor_fte_pct": safe_divide(contractor, actual),
        "demand_coverage_pct": safe_divide(actual, required),
        "available_capacity_hours": available_hours,
        "required_capacity_hours": required_hours,
        "capacity_gap_hours": available_hours - required_hours,
        "hiring_need_fte": max(0.0, -gap),
    }


def governance_summary(
    projects: pd.DataFrame,
    milestones: pd.DataFrame,
    risks: pd.DataFrame,
) -> dict[str, float | int]:
    """Calculate governance, milestone, and risk KPIs."""

    at_risk = int(projects["ProjectStatus"].isin(["At Risk", "Delayed"]).sum())
    on_time = int((milestones["ScheduleVarianceDays"] <= 0).sum())
    open_critical = int(
        (
            (risks["IsCritical"] == 1)
            & risks["RiskStatus"].isin(["Open", "Monitoring"])
        ).sum()
    )
    without_mitigation = int(
        (
            (risks["IsCritical"] == 1)
            & risks["RiskStatus"].isin(["Open", "Monitoring"])
            & (risks["MitigationStatus"] == "Not Started")
        ).sum()
    )
    overdue = int((risks["IsOverdue"] == 1).sum())
    return {
        "total_projects": int(projects["ProjectKey"].nunique()),
        "active_projects": int(
            projects["ProjectStatus"].isin(["Active", "At Risk", "Delayed"]).sum()
        ),
        "projects_at_risk": at_risk,
        "milestones": int(len(milestones)),
        "on_time_milestones": on_time,
        "on_time_milestone_pct": safe_divide(on_time, len(milestones)),
        "average_schedule_variance": float(milestones["ScheduleVarianceDays"].mean()),
        "max_critical_delay": float(
            milestones.loc[milestones["IsCritical"] == 1, "ScheduleVarianceDays"].max()
        ),
        "open_critical_risks": open_critical,
        "critical_without_mitigation": without_mitigation,
        "overdue_actions": overdue,
        "average_risk_score": float(risks["RiskScore"].mean()),
    }


def project_health_table(data: FilteredData) -> pd.DataFrame:
    """Evaluate the documented worst-status-wins project health logic."""

    health = data.projects[
        [
            "ProjectKey",
            "ProjectID",
            "ProjectName",
            "Program",
            "ProjectStatus",
            "ApprovedBudget",
            "PercentComplete",
        ]
    ].copy()

    all_financial = data.financial_all_dates.groupby("ProjectKey", as_index=False).agg(
        FullActualCost=("ActualCostAmount", "sum"),
        ForecastToComplete=("ForecastToComplete", "sum"),
    )
    dated_actual = data.financial.groupby("ProjectKey", as_index=False).agg(
        ActualCost=("ActualCostAmount", "sum")
    )
    health = health.merge(all_financial, on="ProjectKey", how="left")
    health = health.merge(dated_actual, on="ProjectKey", how="left")

    if data.labor.empty:
        labor = pd.DataFrame(columns=["ProjectKey", "AvailableHours", "ProjectHours", "TargetHours"])
    else:
        labor_source = data.labor.assign(
            TargetHours=data.labor["AvailableHours"] * data.labor["UtilizationTarget"]
        )
        labor = labor_source.groupby("ProjectKey", as_index=False).agg(
            AvailableHours=("AvailableHours", "sum"),
            ProjectHours=("ProjectHours", "sum"),
            TargetHours=("TargetHours", "sum"),
        )
    health = health.merge(labor, on="ProjectKey", how="left")

    critical_milestones = data.milestones[data.milestones["IsCritical"] == 1]
    schedule = critical_milestones.groupby("ProjectKey", as_index=False).agg(
        MaxCriticalDelay=("ScheduleVarianceDays", "max")
    )
    health = health.merge(schedule, on="ProjectKey", how="left")

    risk_source = data.risks.assign(
        CriticalWithoutMitigation=(
            (data.risks["IsCritical"] == 1)
            & data.risks["RiskStatus"].isin(["Open", "Monitoring"])
            & (data.risks["MitigationStatus"] == "Not Started")
        ).astype(int),
        Overdue=(data.risks["IsOverdue"] == 1).astype(int),
    )
    risk = risk_source.groupby("ProjectKey", as_index=False).agg(
        CriticalWithoutMitigation=("CriticalWithoutMitigation", "sum"),
        OverdueActions=("Overdue", "sum"),
        MaxRiskScore=("RiskScore", "max"),
    )
    health = health.merge(risk, on="ProjectKey", how="left")

    numeric_columns = [
        "FullActualCost",
        "ForecastToComplete",
        "ActualCost",
        "AvailableHours",
        "ProjectHours",
        "TargetHours",
        "CriticalWithoutMitigation",
        "OverdueActions",
        "MaxRiskScore",
    ]
    health[numeric_columns] = health[numeric_columns].fillna(0)
    health["EAC"] = health["FullActualCost"] + health["ForecastToComplete"]
    health["ForecastVariance"] = health["ApprovedBudget"] - health["EAC"]
    health["BudgetConsumedPct"] = np.where(
        health["ApprovedBudget"] > 0,
        health["ActualCost"] / health["ApprovedBudget"],
        np.nan,
    )
    health["CompletionPct"] = health["PercentComplete"] / 100
    health["BudgetCompletionGap"] = health["BudgetConsumedPct"] - health["CompletionPct"]
    health["Utilization"] = np.where(
        health["AvailableHours"] > 0,
        health["ProjectHours"] / health["AvailableHours"],
        np.nan,
    )
    health["Target"] = np.where(
        health["AvailableHours"] > 0,
        health["TargetHours"] / health["AvailableHours"],
        np.nan,
    )
    health["UtilizationGap"] = health["Utilization"] - health["Target"]

    overrun = np.where(
        health["ApprovedBudget"] > 0,
        (health["EAC"] - health["ApprovedBudget"]) / health["ApprovedBudget"],
        np.nan,
    )
    health["CostHealth"] = np.select(
        [overrun > 0.10, overrun >= 0.03], ["Red", "Amber"], default="Green"
    )
    health["ScheduleHealth"] = np.select(
        [health["MaxCriticalDelay"] > 30, health["MaxCriticalDelay"] >= 8],
        ["Red", "Amber"],
        default="Green",
    )
    health["LaborHealth"] = np.select(
        [health["UtilizationGap"] < -0.12, health["UtilizationGap"] < -0.05],
        ["Red", "Amber"],
        default="Green",
    )
    health["RiskHealth"] = np.select(
        [health["CriticalWithoutMitigation"] > 0, health["OverdueActions"] > 0],
        ["Red", "Amber"],
        default="Green",
    )

    severity_rank = {"Green": 0, "Amber": 1, "Red": 2}
    health_columns = ["CostHealth", "ScheduleHealth", "LaborHealth", "RiskHealth"]
    health["OverallHealth"] = health[health_columns].apply(
        lambda row: max(row, key=severity_rank.get), axis=1
    )
    health["AnyRedFlag"] = (
        (health["OverallHealth"] == "Red") | (health["BudgetCompletionGap"] >= 0.15)
    )
    return health.sort_values(
        ["AnyRedFlag", "BudgetCompletionGap", "MaxRiskScore"], ascending=[False, False, False]
    ).reset_index(drop=True)


def project_health_counts(health: pd.DataFrame) -> dict[str, int]:
    """Count red, amber, green, and any-red-flag projects."""

    counts = health["OverallHealth"].value_counts()
    return {
        "red": int(counts.get("Red", 0)),
        "amber": int(counts.get("Amber", 0)),
        "green": int(counts.get("Green", 0)),
        "any_red_flag": int(health["AnyRedFlag"].sum()),
    }


def is_empty_metric(value: Any) -> bool:
    """Return whether a metric is unavailable for the current filter context."""

    return value is None or (isinstance(value, (float, np.floating)) and np.isnan(value))
