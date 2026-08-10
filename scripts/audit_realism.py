#!/usr/bin/env python3
"""Profile HoneyWin data/model assets and write a reproducible realism audit."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


TABLES = [
    "DimDate",
    "DimProject",
    "DimEmployee",
    "DimTeam",
    "DimSkill",
    "BridgeEmployeeSkill",
    "FactLabor",
    "FactFinancial",
    "FactMilestone",
    "FactWorkforcePlan",
    "FactRiskIssue",
]

PRIMARY_KEYS = {
    "DimDate": ["DateKey"],
    "DimProject": ["ProjectKey"],
    "DimEmployee": ["EmployeeKey"],
    "DimTeam": ["TeamKey"],
    "DimSkill": ["SkillKey"],
    "BridgeEmployeeSkill": ["EmployeeSkillKey"],
    "FactLabor": ["LaborRecordID"],
    "FactFinancial": ["FinancialRecordID"],
    "FactMilestone": ["MilestoneKey"],
    "FactWorkforcePlan": ["WorkforcePlanRecordID"],
    "FactRiskIssue": ["RiskIssueKey"],
}

NATURAL_KEYS = {
    "DimDate": ["Date"],
    "DimProject": ["ProjectID"],
    "DimEmployee": ["EmployeeID"],
    "DimTeam": ["TeamName"],
    "DimSkill": ["SkillName"],
    "BridgeEmployeeSkill": ["EmployeeKey", "SkillKey"],
    "FactLabor": ["EmployeeKey", "ProjectKey", "WeekStartDateKey"],
    "FactFinancial": ["ProjectKey", "MonthStartDateKey", "CostCategory"],
    "FactMilestone": ["ProjectKey", "MilestoneSequence"],
    "FactWorkforcePlan": ["MonthStartDateKey", "TeamKey", "SkillKey", "Location"],
    "FactRiskIssue": ["RiskIssueID"],
}

FOREIGN_KEYS = [
    ("DimProject", "PrimaryTeamKey", "DimTeam", "TeamKey"),
    ("DimEmployee", "TeamKey", "DimTeam", "TeamKey"),
    ("DimEmployee", "PrimarySkillKey", "DimSkill", "SkillKey"),
    ("BridgeEmployeeSkill", "EmployeeKey", "DimEmployee", "EmployeeKey"),
    ("BridgeEmployeeSkill", "SkillKey", "DimSkill", "SkillKey"),
    ("FactLabor", "WeekStartDateKey", "DimDate", "DateKey"),
    ("FactLabor", "EmployeeKey", "DimEmployee", "EmployeeKey"),
    ("FactLabor", "ProjectKey", "DimProject", "ProjectKey"),
    ("FactFinancial", "MonthStartDateKey", "DimDate", "DateKey"),
    ("FactFinancial", "ProjectKey", "DimProject", "ProjectKey"),
    ("FactMilestone", "ProjectKey", "DimProject", "ProjectKey"),
    ("FactMilestone", "PlannedDateKey", "DimDate", "DateKey"),
    ("FactMilestone", "ForecastDateKey", "DimDate", "DateKey"),
    ("FactMilestone", "ActualDateKey", "DimDate", "DateKey"),
    ("FactWorkforcePlan", "MonthStartDateKey", "DimDate", "DateKey"),
    ("FactWorkforcePlan", "TeamKey", "DimTeam", "TeamKey"),
    ("FactWorkforcePlan", "SkillKey", "DimSkill", "SkillKey"),
    ("FactRiskIssue", "ProjectKey", "DimProject", "ProjectKey"),
    ("FactRiskIssue", "IdentifiedDateKey", "DimDate", "DateKey"),
    ("FactRiskIssue", "DueDateKey", "DimDate", "DateKey"),
    ("FactRiskIssue", "ClosedDateKey", "DimDate", "DateKey"),
]

DATE_COLUMNS = {
    "DimDate": ["Date", "MonthStartDate"],
    "DimProject": ["StartDate", "PlannedEndDate", "ForecastEndDate", "ActualEndDate"],
    "DimEmployee": ["HireDate", "ExitDate"],
    "FactLabor": ["SubmissionDate"],
    "FactMilestone": ["PlannedDate", "ForecastDate", "ActualDate", "LastUpdatedDate"],
    "FactRiskIssue": ["IdentifiedDate", "DueDate", "ClosedDate"],
}

ROUNDNESS_COLUMNS = {
    "DimProject": ["BaselineBudget", "ApprovedBudget", "PercentComplete"],
    "FactLabor": ["ScheduledHours", "AvailableHours", "ProjectHours", "NonProjectHours", "OvertimeHours", "PTOHours"],
    "FactFinancial": ["BudgetAmount", "ActualCostAmount", "ForecastToComplete", "EAC", "CommittedCost"],
    "FactMilestone": ["CompletionPercent", "ScheduleVarianceDays"],
    "FactWorkforcePlan": ["RequiredFTE", "ActualFTE", "OpenDemandFTE", "ContractorFTE"],
    "FactRiskIssue": ["RiskScore"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data/generated")
    parser.add_argument("--quality-dir", default="quality")
    parser.add_argument("--label", default="current", help="Suffix used for audit artifacts.")
    return parser.parse_args()


def scalar(value: Any) -> Any:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (pd.Timestamp, date)):
        return value.isoformat()
    return value


def read_tables(data_dir: Path) -> dict[str, pd.DataFrame]:
    tables: dict[str, pd.DataFrame] = {}
    for table in TABLES:
        path = data_dir / f"{table}.csv"
        tables[table] = pd.read_csv(path, low_memory=False)
    return tables


def numeric_stats(series: pd.Series) -> dict[str, Any]:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return {}
    q1, q3 = values.quantile([0.25, 0.75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return {
        "min": scalar(values.min()),
        "q1": scalar(q1),
        "median": scalar(values.median()),
        "mean": scalar(values.mean()),
        "q3": scalar(q3),
        "max": scalar(values.max()),
        "std": scalar(values.std(ddof=0)),
        "iqr_outliers": int(((values < lower) | (values > upper)).sum()) if iqr > 0 else 0,
    }


def roundness(series: pd.Series) -> dict[str, Any]:
    values = pd.to_numeric(series, errors="coerce").dropna()
    nonzero = values[values.abs() > 1e-9]
    if nonzero.empty:
        return {"nonzero": 0, "integer_ratio": None, "multiple_5_ratio": None, "multiple_1000_ratio": None}
    return {
        "nonzero": int(len(nonzero)),
        "integer_ratio": scalar(np.isclose(nonzero % 1, 0, atol=1e-8).mean()),
        "multiple_5_ratio": scalar(np.isclose(nonzero % 5, 0, atol=1e-8).mean()),
        "multiple_1000_ratio": scalar(np.isclose(nonzero % 1000, 0, atol=1e-8).mean()),
    }


def profile_table(name: str, frame: pd.DataFrame) -> dict[str, Any]:
    column_profiles: dict[str, Any] = {}
    for column in frame.columns:
        series = frame[column]
        nonnull = series.dropna()
        counts = nonnull.astype(str).value_counts()
        profile: dict[str, Any] = {
            "dtype": str(series.dtype),
            "nulls": int(series.isna().sum()),
            "null_ratio": scalar(series.isna().mean()),
            "distinct": int(nonnull.nunique(dropna=True)),
            "distinct_ratio": scalar(nonnull.nunique(dropna=True) / len(nonnull)) if len(nonnull) else None,
            "top_value": scalar(counts.index[0]) if len(counts) else None,
            "top_count": int(counts.iloc[0]) if len(counts) else 0,
            "top_ratio": scalar(counts.iloc[0] / len(nonnull)) if len(nonnull) else None,
        }
        if pd.api.types.is_numeric_dtype(series):
            profile["numeric"] = numeric_stats(series)
        column_profiles[column] = profile
    pk = PRIMARY_KEYS[name]
    nk = NATURAL_KEYS[name]
    return {
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
        "exact_duplicate_rows": int(frame.duplicated().sum()),
        "primary_key_duplicates": int(frame.duplicated(pk).sum()),
        "natural_key_duplicate_extras": int(frame.duplicated(nk).sum()),
        "columns_profile": column_profiles,
        "roundness": {
            column: roundness(frame[column])
            for column in ROUNDNESS_COLUMNS.get(name, [])
            if column in frame
        },
    }


def integrity_profile(tables: dict[str, pd.DataFrame]) -> dict[str, Any]:
    results: dict[str, Any] = {}

    def normalized(value: Any) -> str:
        if isinstance(value, (int, np.integer)):
            return str(int(value))
        if isinstance(value, (float, np.floating)) and float(value).is_integer():
            return str(int(value))
        return str(value)

    for child, child_col, parent, parent_col in FOREIGN_KEYS:
        child_values = tables[child][child_col].dropna()
        parent_values = {normalized(value) for value in tables[parent][parent_col].dropna()}
        orphans = child_values[~child_values.map(normalized).isin(parent_values)]
        results[f"{child}.{child_col}->{parent}.{parent_col}"] = {
            "orphans": int(len(orphans)),
            "sample": [scalar(value) for value in orphans.head(5).tolist()],
        }
    return results


def date_profile(tables: dict[str, pd.DataFrame]) -> dict[str, Any]:
    coverage: dict[str, Any] = {}
    invalid: list[dict[str, Any]] = []
    for table, columns in DATE_COLUMNS.items():
        for column in columns:
            parsed = pd.to_datetime(tables[table][column], errors="coerce")
            raw_nonnull = tables[table][column].notna()
            invalid_count = int((raw_nonnull & parsed.isna()).sum())
            coverage[f"{table}.{column}"] = {
                "min": scalar(parsed.min()) if parsed.notna().any() else None,
                "max": scalar(parsed.max()) if parsed.notna().any() else None,
                "invalid": invalid_count,
            }
            if invalid_count:
                invalid.append({"table": table, "column": column, "count": invalid_count})

    projects = tables["DimProject"].copy()
    start = pd.to_datetime(projects["StartDate"])
    end = pd.to_datetime(projects["PlannedEndDate"])
    forecast = pd.to_datetime(projects["ForecastEndDate"])
    actual = pd.to_datetime(projects["ActualEndDate"], errors="coerce")
    impossible = {
        "project_end_before_start": int((end < start).sum()),
        "project_forecast_before_start": int((forecast < start).sum()),
        "project_actual_before_start": int((actual.notna() & (actual < start)).sum()),
    }

    milestone = tables["FactMilestone"].copy()
    planned = pd.to_datetime(milestone["PlannedDate"])
    forecast_m = pd.to_datetime(milestone["ForecastDate"])
    actual_m = pd.to_datetime(milestone["ActualDate"], errors="coerce")
    impossible.update(
        {
            "milestone_variance_mismatch": int(((forecast_m - planned).dt.days != milestone["ScheduleVarianceDays"]).sum()),
            "milestone_actual_before_project_start": int(
                (actual_m < milestone["ProjectKey"].map(projects.set_index("ProjectKey")["StartDate"]).pipe(pd.to_datetime)).sum()
            ),
        }
    )

    risks = tables["FactRiskIssue"].copy()
    identified = pd.to_datetime(risks["IdentifiedDate"])
    due = pd.to_datetime(risks["DueDate"])
    closed = pd.to_datetime(risks["ClosedDate"], errors="coerce")
    impossible.update(
        {
            "risk_due_before_identified": int((due < identified).sum()),
            "risk_closed_before_identified": int((closed.notna() & (closed < identified)).sum()),
        }
    )
    return {"coverage": coverage, "invalid_dates": invalid, "impossible_dates": impossible}


def clean_labor(labor: pd.DataFrame) -> pd.DataFrame:
    return (
        labor.dropna(subset=["ProjectHours", "ActualLaborCost"])
        .drop_duplicates(["EmployeeKey", "ProjectKey", "WeekStartDateKey"], keep="first")
        .copy()
    )


def business_profile(tables: dict[str, pd.DataFrame]) -> dict[str, Any]:
    projects = tables["DimProject"].set_index("ProjectKey")
    labor = clean_labor(tables["FactLabor"])
    financial = tables["FactFinancial"].copy()
    milestones = tables["FactMilestone"].copy()
    workforce = tables["FactWorkforcePlan"].copy()
    risks = tables["FactRiskIssue"].copy()

    financial_component_delta = (
        financial["ActualLaborCost"] + financial["ActualMaterialCost"] + financial["ActualOtherCost"] - financial["ActualCostAmount"]
    )
    financial_eac_delta = financial["ActualCostAmount"] + financial["ForecastToComplete"] - financial["EAC"]
    budget_by_project = financial.groupby("ProjectKey")["BudgetAmount"].sum()
    budget_delta = budget_by_project - projects["ApprovedBudget"]

    employees = tables["DimEmployee"].set_index("EmployeeKey")
    labor = labor.join(employees[["EmploymentType"]], on="EmployeeKey")
    labor["Month"] = pd.to_datetime(labor["WeekStartDateKey"].astype(str), format="%Y%m%d").dt.to_period("M").astype(str)
    labor["CostCategory"] = np.where(labor["EmploymentType"].eq("Contractor"), "Contractor", "Labor")
    labor_cost = labor.groupby(["ProjectKey", "Month", "CostCategory"])["ActualLaborCost"].sum()
    financial["Month"] = pd.to_datetime(financial["MonthStartDateKey"].astype(str), format="%Y%m%d").dt.to_period("M").astype(str)
    financial_labor = (
        financial[financial["CostCategory"].isin(["Labor", "Contractor"])]
        .groupby(["ProjectKey", "Month", "CostCategory"])["ActualLaborCost"]
        .sum()
    )
    reconciliation = labor_cost.subtract(financial_labor, fill_value=0)

    labor_hours_delta = labor["ProjectHours"] + labor["NonProjectHours"] - labor["AvailableHours"] - labor["OvertimeHours"]
    expected_cost = (
        (labor["ProjectHours"] - labor["OvertimeHours"]) * labor["StandardLaborRate"]
        + labor["OvertimeHours"] * labor["StandardLaborRate"] * labor["OvertimeRateMultiplier"]
    )

    wf_open_delta = workforce["OpenDemandFTE"] - (workforce["RequiredFTE"] - workforce["ActualFTE"]).clip(lower=0)
    wf_gap_delta = workforce["CapacityGapFTE"] - (workforce["ActualFTE"] - workforce["RequiredFTE"])
    wf_hours_delta = workforce["AvailableCapacityHours"] - workforce["ActualFTE"] * 160

    severity_expected = np.select(
        [risks["RiskScore"] >= 20, risks["RiskScore"] >= 12, risks["RiskScore"] >= 6],
        ["Critical", "High", "Medium"],
        default="Low",
    )
    risk_rule_errors = {
        "score_mismatch": int((risks["RiskScore"] != risks["Probability"] * risks["Impact"]).sum()),
        "severity_mismatch": int((risks["RiskSeverity"] != severity_expected).sum()),
        "closed_status_missing_date": int((risks["RiskStatus"].eq("Closed") & risks["ClosedDate"].isna()).sum()),
        "open_status_has_closed_date": int((~risks["RiskStatus"].eq("Closed") & risks["ClosedDate"].notna()).sum()),
    }

    monthly_actual = workforce.groupby("MonthStartDateKey")["ActualFTE"].sum()
    monthly_required = workforce.groupby("MonthStartDateKey")["RequiredFTE"].sum()
    util = labor["ProjectHours"].sum() / labor["AvailableHours"].sum()
    overtime_ratio = labor["OvertimeHours"].sum() / labor["ProjectHours"].sum()
    late_ratio = tables["FactLabor"]["SubmissionStatus"].eq("Late").mean()

    return {
        "financial": {
            "component_failures_gt_0_02": int((financial_component_delta.abs() > 0.02).sum()),
            "eac_failures_gt_0_02": int((financial_eac_delta.abs() > 0.02).sum()),
            "project_budget_failures_gt_0_02": int((budget_delta.abs() > 0.02).sum()),
            "labor_reconciliation_failures_gt_0_05": int((reconciliation.abs() > 0.05).sum()),
            "approved_budget": scalar(projects["ApprovedBudget"].sum()),
            "actual_cost": scalar(financial["ActualCostAmount"].sum()),
            "eac": scalar(financial["EAC"].sum()),
            "eac_variance": scalar(projects["ApprovedBudget"].sum() - financial["EAC"].sum()),
        },
        "labor": {
            "clean_rows": int(len(labor)),
            "missing_rows": int(tables["FactLabor"][["ProjectHours", "ActualLaborCost"]].isna().any(axis=1).sum()),
            "natural_duplicate_extras": int(tables["FactLabor"].duplicated(["EmployeeKey", "ProjectKey", "WeekStartDateKey"]).sum()),
            "hours_reconciliation_failures_gt_0_02": int((labor_hours_delta.abs() > 0.02).sum()),
            "cost_reconciliation_failures_gt_0_02": int(((expected_cost - labor["ActualLaborCost"]).abs() > 0.02).sum()),
            "utilization": scalar(util),
            "overtime_ratio": scalar(overtime_ratio),
            "late_submission_ratio": scalar(late_ratio),
        },
        "workforce": {
            "open_demand_formula_failures_gt_0_02": int((wf_open_delta.abs() > 0.02).sum()),
            "capacity_gap_formula_failures_gt_0_02": int((wf_gap_delta.abs() > 0.02).sum()),
            "available_hours_formula_failures_gt_0_02": int((wf_hours_delta.abs() > 0.02).sum()),
            "monthly_actual_min": scalar(monthly_actual.min()),
            "monthly_actual_max": scalar(monthly_actual.max()),
            "monthly_actual_std": scalar(monthly_actual.std(ddof=0)),
            "monthly_required_std": scalar(monthly_required.std(ddof=0)),
            "zero_actual_positive_demand_rows": int(((workforce["ActualFTE"] == 0) & (workforce["RequiredFTE"] > 0)).sum()),
        },
        "milestones": {
            "rows": int(len(milestones)),
            "distinct_names": int(milestones["MilestoneName"].nunique()),
            "distinct_variances": int(milestones["ScheduleVarianceDays"].nunique()),
            "fractional_completion_rows": int((~milestones["CompletionPercent"].isin([0, 100])).sum()),
            "same_last_updated_ratio": scalar(milestones["LastUpdatedDate"].value_counts(normalize=True).iloc[0]),
        },
        "risk": {
            "rows": int(len(risks)),
            "distinct_titles": int(risks["RiskTitle"].nunique()),
            "overdue_ratio": scalar(risks["IsOverdue"].mean()),
            "status_counts": {str(k): int(v) for k, v in risks["RiskStatus"].value_counts().items()},
            **risk_rule_errors,
        },
    }


def correlation_profile(tables: dict[str, pd.DataFrame]) -> dict[str, Any]:
    projects = tables["DimProject"].set_index("ProjectKey")[["ApprovedBudget", "PercentComplete"]].copy()
    financial = tables["FactFinancial"].groupby("ProjectKey").agg(
        ActualCost=("ActualCostAmount", "sum"), EAC=("EAC", "sum"), Committed=("CommittedCost", "sum")
    )
    labor = clean_labor(tables["FactLabor"]).groupby("ProjectKey").agg(
        ProjectHours=("ProjectHours", "sum"), OvertimeHours=("OvertimeHours", "sum")
    )
    milestone = tables["FactMilestone"].groupby("ProjectKey").agg(
        AvgDelay=("ScheduleVarianceDays", "mean"), MaxDelay=("ScheduleVarianceDays", "max")
    )
    risk = tables["FactRiskIssue"].groupby("ProjectKey").agg(
        AvgRiskScore=("RiskScore", "mean"), MaxRiskScore=("RiskScore", "max"), RiskCount=("RiskIssueKey", "count")
    )
    joined = projects.join(financial).join(labor).join(milestone).join(risk)
    joined["BudgetConsumedPct"] = joined["ActualCost"] / joined["ApprovedBudget"]
    joined["EACVariancePct"] = (joined["EAC"] - joined["ApprovedBudget"]) / joined["ApprovedBudget"]
    corr = joined.corr(numeric_only=True).round(4)
    pairs: list[dict[str, Any]] = []
    for i, left in enumerate(corr.columns):
        for right in corr.columns[i + 1 :]:
            value = corr.loc[left, right]
            if pd.notna(value):
                pairs.append({"left": left, "right": right, "pearson": scalar(value)})
    pairs.sort(key=lambda item: abs(item["pearson"]), reverse=True)
    return {"project_rows": int(len(joined)), "strongest_pairs": pairs[:20], "matrix": corr.to_dict()}


def model_profile(root: Path) -> dict[str, Any]:
    measures_path = root / "powerbi" / "measures.generated.json"
    definitions = json.loads(measures_path.read_text(encoding="utf-8"))
    names = [item["name"] for item in definitions]
    folders = Counter(item["displayFolder"] for item in definitions)
    expressions = "\n".join(item["expression"] for item in definitions)
    referenced_measure_names = set(re.findall(r"(?<![A-Za-z0-9_'])\[([^\]]+)\]", expressions))
    unresolved = sorted(name for name in referenced_measure_names if name not in names)
    relationship_specs = re.findall(r"@\('R_[^\n]+", (root / "scripts" / "apply_powerbi_model.ps1").read_text(encoding="utf-8"))
    return {
        "measure_count": len(definitions),
        "duplicate_measure_names": sorted(name for name, count in Counter(names).items() if count > 1),
        "folders": dict(sorted(folders.items())),
        "unresolved_measure_references": unresolved,
        "measures_with_division_operator": [item["name"] for item in definitions if re.search(r"(?<!/) / (?!/)", item["expression"])],
        "measure_names": names,
        "relationship_specs_in_apply_script": len(relationship_specs),
    }


def artificiality_flags(tables: dict[str, pd.DataFrame], business: dict[str, Any]) -> list[dict[str, Any]]:
    flags: list[dict[str, Any]] = []

    def add(area: str, signal: str, observed: Any, reason: str, severity: str = "Medium") -> None:
        flags.append({"area": area, "severity": severity, "signal": signal, "observed": scalar(observed), "reason": reason})

    project = tables["DimProject"]
    budget_round = np.isclose(project["ApprovedBudget"] % 50_000, 0).mean()
    if budget_round > 0.5:
        add("DimProject", "Approved budgets on $50K grid", budget_round, "Too many round portfolio approvals look hand-authored.")
    if project["StartDate"].nunique() < 15:
        add("DimProject", "Distinct planned start dates", project["StartDate"].nunique(), "25 projects share too few launch dates.")
    if project["Program"].value_counts().nunique() == 1:
        add("DimProject", "Program counts", project["Program"].value_counts().to_dict(), "Every program has exactly the same project count.")

    employee = tables["DimEmployee"]
    if employee["UtilizationTarget"].nunique() <= 5:
        add("DimEmployee", "Distinct utilization targets", employee["UtilizationTarget"].nunique(), "Targets are copied at team level with no role/contractor variation.")
    if employee["ExitDate"].notna().sum() == 0:
        add("DimEmployee", "Exit records", 0, "A 24-month workforce snapshot has no transitions or inactive resources.", "Low")

    labor = tables["FactLabor"]
    if labor["ProjectHours"].dropna().mul(2).round().sub(labor["ProjectHours"].dropna().mul(2)).abs().lt(1e-8).mean() > 0.9:
        add("FactLabor", "Hours on 0.5-hour grid", "over 90%", "Nearly all time entries use the same half-hour grid.")
    if labor["PTOHours"].nunique(dropna=True) <= 3:
        add("FactLabor", "Distinct PTO values", labor["PTOHours"].nunique(dropna=True), "PTO is limited to a few exact buckets.")

    milestone = tables["FactMilestone"]
    if business["milestones"]["distinct_variances"] < 15:
        add("FactMilestone", "Distinct schedule variances", business["milestones"]["distinct_variances"], "Schedule movement repeats from a short fixed list.")
    if business["milestones"]["fractional_completion_rows"] < len(milestone) * 0.08:
        add("FactMilestone", "In-progress completion rows", business["milestones"]["fractional_completion_rows"], "Milestones are almost entirely 0% or 100%.")
    if business["milestones"]["same_last_updated_ratio"] > 0.9:
        add("FactMilestone", "Same last-updated ratio", business["milestones"]["same_last_updated_ratio"], "Every record appears refreshed in one batch.", "Low")

    risk = tables["FactRiskIssue"]
    if business["risk"]["distinct_titles"] < len(risk) * 0.4:
        add("FactRiskIssue", "Distinct risk titles", business["risk"]["distinct_titles"], "Risk register repeats a very small set of generic titles.")
    if business["risk"]["overdue_ratio"] > 0.4:
        add("FactRiskIssue", "Overdue ratio", business["risk"]["overdue_ratio"], "Portfolio-wide overdue share is implausibly high.")

    workforce = tables["FactWorkforcePlan"]
    if business["workforce"]["monthly_actual_std"] < 0.05:
        add("FactWorkforcePlan", "Monthly actual FTE standard deviation", business["workforce"]["monthly_actual_std"], "Workforce is perfectly flat across 24 months.")
    small_demand = ((workforce["ActualFTE"] == 0) & workforce["RequiredFTE"].between(0.01, 0.49)).sum()
    if small_demand > 50:
        add("FactWorkforcePlan", "Tiny demand in zero-staff locations", int(small_demand), "Demand allocation scatters implausible fractions across empty locations.")

    return flags


def markdown_report(audit: dict[str, Any]) -> str:
    business = audit["business"]
    flags = audit["artificiality_flags"]
    lines = [
        f"# HoneyWin realism audit — {audit['label']}",
        "",
        f"Generated from fixed-seed assets on `{audit['generated_at']}`.",
        "",
        "## Executive summary",
        "",
        f"- Tables profiled: {len(audit['tables'])}/11; DAX measures parsed: {audit['model']['measure_count']}/70.",
        f"- Referential-integrity orphans: {sum(item['orphans'] for item in audit['integrity'].values())}.",
        f"- Impossible-date conditions: {sum(audit['dates']['impossible_dates'].values())}.",
        f"- Artificiality signals: {len(flags)} ({sum(item['severity'] == 'Medium' for item in flags)} medium).",
        f"- Clean labor rows: {business['labor']['clean_rows']:,}; utilization: {business['labor']['utilization']:.2%}; late submissions: {business['labor']['late_submission_ratio']:.2%}.",
        f"- Approved budget: ${business['financial']['approved_budget']:,.0f}; actual: ${business['financial']['actual_cost']:,.0f}; EAC: ${business['financial']['eac']:,.0f}.",
        "",
        "## Table profile",
        "",
        "| Table | Rows | Columns | Null cells | Exact duplicates | Natural-key extras |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, profile in audit["tables"].items():
        nulls = sum(column["nulls"] for column in profile["columns_profile"].values())
        lines.append(
            f"| {name} | {profile['rows']:,} | {profile['columns']} | {nulls:,} | {profile['exact_duplicate_rows']} | {profile['natural_key_duplicate_extras']} |"
        )
    lines.extend(["", "## Artificiality signals", ""])
    if flags:
        lines.extend(["| Severity | Area | Signal | Observed | Why it matters |", "|---|---|---|---|---|"])
        for item in flags:
            observed = str(item["observed"]).replace("|", "/")
            lines.append(f"| {item['severity']} | {item['area']} | {item['signal']} | {observed} | {item['reason']} |")
    else:
        lines.append("No material artificiality signals breached the audit thresholds.")

    lines.extend(
        [
            "",
            "## Business consistency",
            "",
            f"- Financial component failures: {business['financial']['component_failures_gt_0_02']}; EAC failures: {business['financial']['eac_failures_gt_0_02']}; project budget failures: {business['financial']['project_budget_failures_gt_0_02']}.",
            f"- Labor hour failures: {business['labor']['hours_reconciliation_failures_gt_0_02']}; labor cost failures: {business['labor']['cost_reconciliation_failures_gt_0_02']}; financial/labor reconciliation failures: {business['financial']['labor_reconciliation_failures_gt_0_05']}.",
            f"- Workforce formula failures: open demand {business['workforce']['open_demand_formula_failures_gt_0_02']}, capacity gap {business['workforce']['capacity_gap_formula_failures_gt_0_02']}, capacity hours {business['workforce']['available_hours_formula_failures_gt_0_02']}.",
            f"- Risk rule failures: score {business['risk']['score_mismatch']}, severity {business['risk']['severity_mismatch']}, closure-date rules {business['risk']['closed_status_missing_date'] + business['risk']['open_status_has_closed_date']}.",
            "",
            "## Strongest project-level correlations",
            "",
            "| Metric A | Metric B | Pearson r |",
            "|---|---|---:|",
        ]
    )
    for item in audit["correlations"]["strongest_pairs"][:12]:
        lines.append(f"| {item['left']} | {item['right']} | {item['pearson']:.3f} |")
    lines.extend(
        [
            "",
            "## Semantic-model static audit",
            "",
            f"- Measure definitions: {audit['model']['measure_count']}; duplicate names: {len(audit['model']['duplicate_measure_names'])}; unresolved bracket references: {len(audit['model']['unresolved_measure_references'])}.",
            f"- Display folders: {json.dumps(audit['model']['folders'], ensure_ascii=False)}.",
            "- Live relationship cardinality, DAX execution, refresh status, and report visual review are recorded separately after Power BI refresh.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    data_dir = (root / args.data_dir).resolve()
    quality_dir = (root / args.quality_dir).resolve()
    quality_dir.mkdir(parents=True, exist_ok=True)
    tables = read_tables(data_dir)
    table_profiles = {name: profile_table(name, frame) for name, frame in tables.items()}
    business = business_profile(tables)
    try:
        data_dir_reference = data_dir.relative_to(root).as_posix()
    except ValueError:
        data_dir_reference = str(data_dir)
    audit = {
        "label": args.label,
        "generated_at": date.today().isoformat(),
        "data_dir": data_dir_reference,
        "tables": table_profiles,
        "integrity": integrity_profile(tables),
        "dates": date_profile(tables),
        "business": business,
        "correlations": correlation_profile(tables),
        "model": model_profile(root),
        "artificiality_flags": artificiality_flags(tables, business),
    }
    json_path = quality_dir / f"realism_audit_{args.label}.json"
    md_path = quality_dir / f"realism_audit_{args.label}.md"
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(markdown_report(audit), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"Artificiality signals: {len(audit['artificiality_flags'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
