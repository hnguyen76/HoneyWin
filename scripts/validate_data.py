#!/usr/bin/env python3
"""Validate the generated FORGE dataset and write auditable QA artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable


EXPECTED_TABLES = [
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


@dataclass
class CheckResult:
    CheckID: str
    Category: str
    CheckName: str
    Status: str
    Severity: str
    ObservedValue: str
    ExpectedRule: str
    AffectedRows: int
    Details: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data/generated")
    parser.add_argument("--quality-dir", default="quality")
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def to_float(value: str | float | int | None) -> float:
    if value is None or value == "":
        raise ValueError("blank numeric value")
    return float(value)


def to_int(value: str | int) -> int:
    return int(value)


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def date_from_key(value: str | int) -> date:
    return datetime.strptime(str(value), "%Y%m%d").date()


def month_key(value: str | int) -> tuple[int, int]:
    text = str(value)
    return int(text[:4]), int(text[4:6])


def money(value: float) -> str:
    return f"${value:,.2f}"


def pct(value: float) -> str:
    return f"{value:.2%}"


class QualitySuite:
    def __init__(self) -> None:
        self.results: list[CheckResult] = []

    def add(
        self,
        check_id: str,
        category: str,
        name: str,
        passed: bool,
        observed: Any,
        expected: str,
        affected: int = 0,
        details: str = "",
        expected_anomaly: bool = False,
        severity: str = "Error",
    ) -> None:
        if expected_anomaly:
            status = "EXPECTED_ANOMALY" if passed else "FAIL"
        else:
            status = "PASS" if passed else "FAIL"
        self.results.append(
            CheckResult(
                CheckID=check_id,
                Category=category,
                CheckName=name,
                Status=status,
                Severity=severity,
                ObservedValue=str(observed),
                ExpectedRule=expected,
                AffectedRows=affected,
                Details=details,
            )
        )


def primary_key_checks(
    suite: QualitySuite, tables: dict[str, list[dict[str, str]]]
) -> None:
    primary_keys = {
        "DimDate": "DateKey",
        "DimProject": "ProjectKey",
        "DimEmployee": "EmployeeKey",
        "DimTeam": "TeamKey",
        "DimSkill": "SkillKey",
        "BridgeEmployeeSkill": "EmployeeSkillKey",
        "FactLabor": "LaborRecordID",
        "FactFinancial": "FinancialRecordID",
        "FactMilestone": "MilestoneKey",
        "FactWorkforcePlan": "WorkforcePlanRecordID",
        "FactRiskIssue": "RiskIssueKey",
    }
    for sequence, (table, key) in enumerate(primary_keys.items(), start=1):
        values = [row[key] for row in tables[table]]
        blanks = sum(value == "" for value in values)
        duplicates = len(values) - len(set(values))
        suite.add(
            f"PK-{sequence:02d}",
            "Primary Key",
            f"{table}.{key} is unique and nonblank",
            blanks == 0 and duplicates == 0,
            f"blank={blanks}; duplicate={duplicates}",
            "0 blank and 0 duplicate physical primary keys",
            blanks + duplicates,
        )


def foreign_key_checks(
    suite: QualitySuite, tables: dict[str, list[dict[str, str]]]
) -> None:
    relationships = [
        ("DimProject", "PrimaryTeamKey", "DimTeam", "TeamKey", False),
        ("DimEmployee", "TeamKey", "DimTeam", "TeamKey", False),
        ("DimEmployee", "PrimarySkillKey", "DimSkill", "SkillKey", False),
        ("BridgeEmployeeSkill", "EmployeeKey", "DimEmployee", "EmployeeKey", False),
        ("BridgeEmployeeSkill", "SkillKey", "DimSkill", "SkillKey", False),
        ("FactLabor", "WeekStartDateKey", "DimDate", "DateKey", False),
        ("FactLabor", "EmployeeKey", "DimEmployee", "EmployeeKey", False),
        ("FactLabor", "ProjectKey", "DimProject", "ProjectKey", False),
        ("FactFinancial", "MonthStartDateKey", "DimDate", "DateKey", False),
        ("FactFinancial", "ProjectKey", "DimProject", "ProjectKey", False),
        ("FactMilestone", "ProjectKey", "DimProject", "ProjectKey", False),
        ("FactMilestone", "PlannedDateKey", "DimDate", "DateKey", False),
        ("FactMilestone", "ForecastDateKey", "DimDate", "DateKey", False),
        ("FactMilestone", "ActualDateKey", "DimDate", "DateKey", True),
        ("FactWorkforcePlan", "MonthStartDateKey", "DimDate", "DateKey", False),
        ("FactWorkforcePlan", "TeamKey", "DimTeam", "TeamKey", False),
        ("FactWorkforcePlan", "SkillKey", "DimSkill", "SkillKey", False),
        ("FactRiskIssue", "ProjectKey", "DimProject", "ProjectKey", False),
        ("FactRiskIssue", "IdentifiedDateKey", "DimDate", "DateKey", False),
        ("FactRiskIssue", "DueDateKey", "DimDate", "DateKey", False),
        ("FactRiskIssue", "ClosedDateKey", "DimDate", "DateKey", True),
    ]
    for sequence, (child, child_key, parent, parent_key, nullable) in enumerate(relationships, start=1):
        parent_values = {row[parent_key] for row in tables[parent]}
        orphans = [
            row[child_key]
            for row in tables[child]
            if not (nullable and row[child_key] == "") and row[child_key] not in parent_values
        ]
        suite.add(
            f"FK-{sequence:02d}",
            "Referential Integrity",
            f"{child}.{child_key} resolves to {parent}.{parent_key}",
            len(orphans) == 0,
            len(orphans),
            "0 orphan foreign keys",
            len(orphans),
            f"Sample: {orphans[:5]}" if orphans else "",
        )


def clean_labor(
    labor: list[dict[str, str]],
) -> tuple[list[dict[str, str]], int, list[dict[str, str]], list[dict[str, str]]]:
    natural_counts = Counter(
        (row["EmployeeKey"], row["ProjectKey"], row["WeekStartDateKey"]) for row in labor
    )
    duplicate_extra = sum(count - 1 for count in natural_counts.values() if count > 1)
    duplicate_rows = [
        row
        for row in labor
        if natural_counts[(row["EmployeeKey"], row["ProjectKey"], row["WeekStartDateKey"])] > 1
    ]
    missing_rows = [row for row in labor if row["ProjectHours"] == "" or row["ActualLaborCost"] == ""]
    seen: set[tuple[str, str, str]] = set()
    cleaned: list[dict[str, str]] = []
    for row in labor:
        if row["ProjectHours"] == "" or row["ActualLaborCost"] == "":
            continue
        key = (row["EmployeeKey"], row["ProjectKey"], row["WeekStartDateKey"])
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(row)
    return cleaned, duplicate_extra, duplicate_rows, missing_rows


def labor_checks(
    suite: QualitySuite, tables: dict[str, list[dict[str, str]]]
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    labor = tables["FactLabor"]
    cleaned, duplicate_extra, duplicate_rows, missing_rows = clean_labor(labor)
    suite.add(
        "DQ-01",
        "Intentional Data Quality",
        "Duplicate employee-project-week records",
        duplicate_extra == 15,
        duplicate_extra,
        "Exactly 15 duplicate natural-key extras are intentionally injected",
        duplicate_extra,
        "A06 controlled defect; physical LaborRecordID remains unique.",
        expected_anomaly=True,
        severity="Warning",
    )
    suite.add(
        "DQ-02",
        "Intentional Data Quality",
        "Missing ProjectHours/ActualLaborCost records",
        len(missing_rows) == 12,
        len(missing_rows),
        "Exactly 12 incomplete time entries are intentionally injected",
        len(missing_rows),
        "A06 controlled defect; reject before KPI aggregation.",
        expected_anomaly=True,
        severity="Warning",
    )
    late_rows = [row for row in labor if row["SubmissionStatus"] == "Late"]
    suite.add(
        "DQ-03",
        "Time Entry Compliance",
        "Late submission records are present and traceable",
        len(late_rows) > 0,
        f"{len(late_rows)} ({len(late_rows) / len(labor):.2%})",
        "At least one late submission with SubmissionStatus=Late",
        len(late_rows),
        "Late entries support time-entry compliance analysis.",
        expected_anomaly=True,
        severity="Warning",
    )
    arithmetic_failures = []
    cost_failures = []
    for row in cleaned:
        available = to_float(row["AvailableHours"])
        project = to_float(row["ProjectHours"])
        non_project = to_float(row["NonProjectHours"])
        overtime = to_float(row["OvertimeHours"])
        if abs((project + non_project) - (available + overtime)) > 0.011:
            arithmetic_failures.append(row["LaborRecordID"])
        expected_cost = (project - overtime) * to_float(row["StandardLaborRate"]) + overtime * to_float(
            row["StandardLaborRate"]
        ) * to_float(row["OvertimeRateMultiplier"])
        if abs(expected_cost - to_float(row["ActualLaborCost"])) > 0.02:
            cost_failures.append(row["LaborRecordID"])
    suite.add(
        "LAB-01",
        "Labor Reconciliation",
        "Project + non-project hours reconcile to available + overtime",
        len(arithmetic_failures) == 0,
        len(arithmetic_failures),
        "0 failures after excluding incomplete/duplicate records",
        len(arithmetic_failures),
    )
    suite.add(
        "LAB-02",
        "Labor Reconciliation",
        "Actual labor cost recomputes from rate and overtime mix",
        len(cost_failures) == 0,
        len(cost_failures),
        "0 failures within $0.02 row tolerance",
        len(cost_failures),
    )
    exceptions: list[dict[str, str]] = []
    duplicate_ids = {row["LaborRecordID"] for row in duplicate_rows}
    missing_ids = {row["LaborRecordID"] for row in missing_rows}
    for row in labor:
        exception_types = []
        if row["LaborRecordID"] in duplicate_ids:
            exception_types.append("DuplicateNaturalKey")
        if row["LaborRecordID"] in missing_ids:
            exception_types.append("MissingLaborValue")
        if row["SubmissionStatus"] == "Late":
            exception_types.append("LateSubmission")
        if exception_types:
            exceptions.append(
                {
                    "ExceptionType": "|".join(exception_types),
                    "LaborRecordID": row["LaborRecordID"],
                    "EmployeeKey": row["EmployeeKey"],
                    "ProjectKey": row["ProjectKey"],
                    "WeekStartDateKey": row["WeekStartDateKey"],
                    "Details": "Controlled A06 data-quality evidence",
                }
            )
    return cleaned, exceptions


def financial_checks(
    suite: QualitySuite,
    tables: dict[str, list[dict[str, str]]],
    cleaned_labor: list[dict[str, str]],
) -> None:
    financial = tables["FactFinancial"]
    component_failures = []
    eac_failures = []
    for row in financial:
        actual = to_float(row["ActualLaborCost"]) + to_float(row["ActualMaterialCost"]) + to_float(
            row["ActualOtherCost"]
        )
        if abs(actual - to_float(row["ActualCostAmount"])) > 0.011:
            component_failures.append(row["FinancialRecordID"])
        if abs(to_float(row["ActualCostAmount"]) + to_float(row["ForecastToComplete"]) - to_float(row["EAC"])) > 0.011:
            eac_failures.append(row["FinancialRecordID"])
    suite.add(
        "FIN-01",
        "Financial Reconciliation",
        "Actual cost equals labor + material + other components",
        len(component_failures) == 0,
        len(component_failures),
        "0 row-level component failures",
        len(component_failures),
    )
    suite.add(
        "FIN-02",
        "Financial Reconciliation",
        "EAC equals actual cost + forecast to complete",
        len(eac_failures) == 0,
        len(eac_failures),
        "0 row-level EAC failures",
        len(eac_failures),
    )
    budget_by_project: dict[int, float] = defaultdict(float)
    for row in financial:
        budget_by_project[to_int(row["ProjectKey"])] += to_float(row["BudgetAmount"])
    projects = {to_int(row["ProjectKey"]): row for row in tables["DimProject"]}
    budget_failures = [
        project_key
        for project_key, project in projects.items()
        if abs(budget_by_project[project_key] - to_float(project["ApprovedBudget"])) > 0.02
    ]
    suite.add(
        "FIN-03",
        "Financial Reconciliation",
        "Phased financial budget reconciles to approved project budget",
        len(budget_failures) == 0,
        len(budget_failures),
        "All 25 projects within $0.02",
        len(budget_failures),
    )
    employees = {row["EmployeeKey"]: row for row in tables["DimEmployee"]}
    labor_cost_by_key: dict[tuple[int, tuple[int, int], str], float] = defaultdict(float)
    for row in cleaned_labor:
        employee = employees[row["EmployeeKey"]]
        category = "Contractor" if employee["EmploymentType"] == "Contractor" else "Labor"
        key = (to_int(row["ProjectKey"]), month_key(row["WeekStartDateKey"]), category)
        labor_cost_by_key[key] += to_float(row["ActualLaborCost"])
    financial_labor_by_key: dict[tuple[int, tuple[int, int], str], float] = defaultdict(float)
    for row in financial:
        if row["CostCategory"] in {"Labor", "Contractor"}:
            key = (to_int(row["ProjectKey"]), month_key(row["MonthStartDateKey"]), row["CostCategory"])
            financial_labor_by_key[key] += to_float(row["ActualLaborCost"])
    all_keys = set(labor_cost_by_key) | set(financial_labor_by_key)
    reconciliation_failures = [
        key
        for key in all_keys
        if abs(labor_cost_by_key[key] - financial_labor_by_key[key]) > 0.05
    ]
    suite.add(
        "FIN-04",
        "Cross-Table Reconciliation",
        "Clean labor cost reconciles to financial labor by project-month-category",
        len(reconciliation_failures) == 0,
        len(reconciliation_failures),
        "0 differences above $0.05 after dedupe/reject rules",
        len(reconciliation_failures),
        f"Sample: {reconciliation_failures[:3]}" if reconciliation_failures else "",
    )


def general_checks(suite: QualitySuite, tables: dict[str, list[dict[str, str]]]) -> None:
    suite.add(
        "VOL-01",
        "Volume",
        "Dataset contains exactly 11 linked CSV tables",
        len(tables) == 11,
        len(tables),
        "11 tables",
    )
    suite.add(
        "VOL-02",
        "Volume",
        "DimDate covers exactly 24 months",
        len({row["YearMonth"] for row in tables["DimDate"]}) == 24,
        len({row["YearMonth"] for row in tables["DimDate"]}),
        "24 distinct YearMonth values",
    )
    suite.add(
        "VOL-03",
        "Volume",
        "Project count",
        len(tables["DimProject"]) == 25,
        len(tables["DimProject"]),
        "25 projects",
    )
    suite.add(
        "VOL-04",
        "Volume",
        "Employee/contractor count",
        len(tables["DimEmployee"]) == 120,
        len(tables["DimEmployee"]),
        "120 resources",
    )
    suite.add(
        "VOL-05",
        "Volume",
        "Labor fact volume",
        8_000 <= len(tables["FactLabor"]) <= 20_000,
        len(tables["FactLabor"]),
        "8,000–20,000 rows",
    )
    bridge_primary = Counter(
        row["EmployeeKey"] for row in tables["BridgeEmployeeSkill"] if row["IsPrimarySkill"] == "1"
    )
    primary_failures = [employee for employee, count in bridge_primary.items() if count != 1]
    missing_employees = {
        row["EmployeeKey"] for row in tables["DimEmployee"]
    } - set(bridge_primary)
    suite.add(
        "MOD-01",
        "Modeling",
        "Each employee has exactly one primary bridge skill",
        not primary_failures and not missing_employees,
        len(primary_failures) + len(missing_employees),
        "0 employee exceptions",
        len(primary_failures) + len(missing_employees),
    )


def anomaly_evidence(
    suite: QualitySuite,
    tables: dict[str, list[dict[str, str]]],
    cleaned_labor: list[dict[str, str]],
) -> list[dict[str, str]]:
    projects = {to_int(row["ProjectKey"]): row for row in tables["DimProject"]}
    employees = {row["EmployeeKey"]: row for row in tables["DimEmployee"]}
    financial_by_project: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in tables["FactFinancial"]:
        financial_by_project[to_int(row["ProjectKey"])].append(row)
    milestones_by_project: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in tables["FactMilestone"]:
        milestones_by_project[to_int(row["ProjectKey"])].append(row)
    risks_by_project: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in tables["FactRiskIssue"]:
        risks_by_project[to_int(row["ProjectKey"])].append(row)
    evidence: list[dict[str, str]] = []

    def totals(project_key: int) -> tuple[float, float, float]:
        rows = financial_by_project[project_key]
        return (
            sum(to_float(row["ActualCostAmount"]) for row in rows),
            sum(to_float(row["EAC"]) for row in rows),
            to_float(projects[project_key]["ApprovedBudget"]),
        )

    actual1, eac1, budget1 = totals(1)
    max_critical_delay1 = max(
        to_int(row["ScheduleVarianceDays"])
        for row in milestones_by_project[1]
        if row["IsCritical"] == "1"
    )
    p1_overtime = sum(
        to_float(row["OvertimeHours"])
        for row in cleaned_labor
        if row["ProjectKey"] == "1" and to_int(row["WeekStartDateKey"]) >= 20250203
    )
    a01_pass = (
        abs(to_float(projects[1]["PercentComplete"]) - 55.0) < 0.001
        and abs(actual1 / budget1 - 0.70) < 0.0001
        and abs((eac1 - budget1) - 400_000.0) < 0.05
        and max_critical_delay1 > 30
        and p1_overtime > 0
    )
    suite.add(
        "ANOM-01",
        "Business Anomaly",
        "A01 cost overrun is present with cross-table root cause",
        a01_pass,
        f"complete=55%; consumed={actual1 / budget1:.2%}; EAC over={money(eac1 - budget1)}",
        "55% complete, 70% consumed, EAC over by $400K, critical delay >30d, overtime >0",
    )
    evidence.append(
        {
            "AnomalyID": "A01",
            "SignalMetric": "FORGE-001 completion / consumed / EAC overrun",
            "ObservedValue": f"55.00% / {actual1 / budget1:.2%} / {money(eac1 - budget1)}",
            "Threshold": "55% / 70% / $400K",
            "RootCauseEvidence": f"Critical milestone delay {max_critical_delay1} days; {p1_overtime:,.1f} overtime hours after 2025-02-03.",
            "DrillPath": "Project → Financial category/month → Labor employee/week → Milestone",
            "Recommendation": "Reforecast, lock scope, replace avoidable contractor/overtime mix and escalate recovery plan.",
            "EstimatedBusinessImpact": f"Management action against {money(eac1 - budget1)} forecast exposure.",
        }
    )

    qa_employee_keys = {key for key, row in employees.items() if row["TeamKey"] == "5"}
    qa_rows = [
        row
        for row in cleaned_labor
        if row["EmployeeKey"] in qa_employee_keys and 20250106 <= to_int(row["WeekStartDateKey"]) <= 20250630
    ]
    qa_project_hours = sum(to_float(row["ProjectHours"]) for row in qa_rows)
    qa_available = sum(to_float(row["AvailableHours"]) for row in qa_rows)
    qa_non_project = sum(to_float(row["NonProjectHours"]) for row in qa_rows)
    qa_util = qa_project_hours / qa_available
    a02_pass = abs(qa_util - 0.68) <= 0.005 and qa_non_project > 0
    suite.add(
        "ANOM-02",
        "Business Anomaly",
        "A02 QA low utilization is allocation-driven",
        a02_pass,
        pct(qa_util),
        "67.5%–68.5% vs 85% target with non-project capacity",
    )
    evidence.append(
        {
            "AnomalyID": "A02",
            "SignalMetric": "QA utilization Jan–Jun 2025",
            "ObservedValue": f"{pct(qa_util)} vs 85.00% target",
            "Threshold": "Approximately 68%",
            "RootCauseEvidence": f"QA had {qa_non_project:,.1f} non-project/bench hours while available hours remained {qa_available:,.1f}.",
            "DrillPath": "Team → Employee → Week → Project/time mix",
            "Recommendation": "Reallocate QA capacity, adjust assignments and improve demand planning.",
            "EstimatedBusinessImpact": f"Recoverable utilization gap of {(0.85 - qa_util):.1%} or about {(0.85 - qa_util) * qa_available:,.0f} project hours.",
        }
    )

    target = {1: (25.0, 30.0), 2: (12.0, 14.0), 3: (18.0, 17.0), 4: (22.0, 19.0)}
    workforce_actual: dict[tuple[str, int], float] = defaultdict(float)
    workforce_required: dict[tuple[str, int], float] = defaultdict(float)
    for row in tables["FactWorkforcePlan"]:
        if to_int(row["MonthStartDateKey"]) >= 20250701 and to_int(row["SkillKey"]) in target:
            month = row["MonthStartDateKey"]
            skill = to_int(row["SkillKey"])
            workforce_actual[(month, skill)] += to_float(row["ActualFTE"])
            workforce_required[(month, skill)] += to_float(row["RequiredFTE"])
    a03_pass = all(
        abs(workforce_actual[(month, skill)] - actual) < 0.01
        and abs(workforce_required[(month, skill)] - required) < 0.01
        for month, skill in workforce_actual
        for actual, required in [target[skill]]
    ) and len(workforce_actual) == 24
    suite.add(
        "ANOM-03",
        "Business Anomaly",
        "A03 skill mismatch profile is present Jul–Dec 2025",
        a03_pass,
        "Software 25/30; Data 12/14; Systems 18/17; Mechanical 22/19",
        "Exact monthly actual/required FTE profile for 4 skills across 6 months",
    )
    evidence.append(
        {
            "AnomalyID": "A03",
            "SignalMetric": "Jul–Dec 2025 actual/required FTE",
            "ObservedValue": "Software 25/30; Data 12/14; Systems 18/17; Mechanical 22/19",
            "Threshold": "-5, -2, +1, +3 FTE gaps",
            "RootCauseEvidence": "Employee primary skills and bridge proficiency show physical/systems excess cannot fully satisfy constrained digital skills.",
            "DrillPath": "Month → Skill → Team/location → Employee skill bridge",
            "Recommendation": "Cross-train adjacent skills, use short-term contractors, then hire for sustained gaps.",
            "EstimatedBusinessImpact": "Targets 7 FTE shortage while using 4 FTE excess as a reallocation pool.",
        }
    )

    p4_critical_delay = max(
        to_int(row["ScheduleVarianceDays"])
        for row in milestones_by_project[4]
        if row["IsCritical"] == "1"
    )
    p4_dependency = [
        row
        for row in risks_by_project[4]
        if row["RiskCategory"] == "Dependency" and row["RiskStatus"] == "Open" and row["IsCritical"] == "1"
    ]
    p4_committed = sum(
        to_float(row["CommittedCost"])
        for row in financial_by_project[4]
        if row["CostCategory"] in {"Contractor", "Material"}
    )
    a04_pass = p4_critical_delay == 45 and len(p4_dependency) >= 1 and p4_committed > 0
    suite.add(
        "ANOM-04",
        "Business Anomaly",
        "A04 critical schedule delay is linked to dependency and commitment",
        a04_pass,
        f"delay={p4_critical_delay}d; critical dependency={len(p4_dependency)}; committed={money(p4_committed)}",
        "45-day delay, open critical dependency, committed contractor/material cost >0",
    )
    evidence.append(
        {
            "AnomalyID": "A04",
            "SignalMetric": "FORGE-004 critical milestone delay",
            "ObservedValue": f"{p4_critical_delay} days; forecast end {projects[4]['ForecastEndDate']}",
            "Threshold": ">30 days (Red)",
            "RootCauseEvidence": f"Open critical Dependency issue; contractor/material committed cost {money(p4_committed)}.",
            "DrillPath": "Project → Critical milestone → Dependency risk → Financial commitment",
            "Recommendation": "Escalate dependency owner and run a dated recovery plan.",
            "EstimatedBusinessImpact": "Makes schedule-driven cost exposure visible before final spend.",
        }
    )

    p9_actual_fin = [
        row
        for row in financial_by_project[9]
        if row["PeriodType"] == "Actual" and row["CostCategory"] in {"Labor", "Contractor"}
    ]
    p9_actual_hours = sum(to_float(row["ActualLaborHours"]) for row in p9_actual_fin)
    p9_plan_hours = sum(to_float(row["PlannedLaborHours"]) for row in p9_actual_fin)
    p9_actual_cost = sum(to_float(row["ActualLaborCost"]) for row in p9_actual_fin)
    p9_budget_cost = sum(to_float(row["BudgetAmount"]) for row in p9_actual_fin)
    p9_contractor_hours = sum(
        to_float(row["ProjectHours"])
        for row in cleaned_labor
        if row["ProjectKey"] == "9" and employees[row["EmployeeKey"]]["EmploymentType"] == "Contractor"
    )
    p9_overtime = sum(
        to_float(row["OvertimeHours"]) for row in cleaned_labor if row["ProjectKey"] == "9"
    )
    hour_ratio = p9_actual_hours / p9_plan_hours
    cost_ratio = p9_actual_cost / p9_budget_cost
    a05_pass = 0.98 <= hour_ratio <= 1.02 and cost_ratio > 1.15 and p9_contractor_hours > 0 and p9_overtime > 0
    suite.add(
        "ANOM-05",
        "Business Anomaly",
        "A05 labor-rate mix variance is present",
        a05_pass,
        f"hours={hour_ratio:.2%} of plan; cost={cost_ratio:.2%} of plan",
        "Hours within ±2%; labor cost >115%; contractor and overtime hours >0",
    )
    evidence.append(
        {
            "AnomalyID": "A05",
            "SignalMetric": "FORGE-009 labor hours vs labor cost plan",
            "ObservedValue": f"Hours {hour_ratio:.2%}; cost {cost_ratio:.2%}",
            "Threshold": "Hours 98–102%; cost >115%",
            "RootCauseEvidence": f"Contractor hours {p9_contractor_hours:,.1f}; overtime hours {p9_overtime:,.1f}.",
            "DrillPath": "Project → Cost category → Employment type → Overtime week",
            "Recommendation": "Rebalance rate mix, cap overtime and move suitable work to employees.",
            "EstimatedBusinessImpact": f"Current-period labor variance exposure {money(p9_actual_cost - p9_budget_cost)}.",
        }
    )

    _, duplicate_extra, _, missing_rows = clean_labor(tables["FactLabor"])
    late_count = sum(row["SubmissionStatus"] == "Late" for row in tables["FactLabor"])
    a06_pass = duplicate_extra == 15 and len(missing_rows) == 12 and late_count > 0
    suite.add(
        "ANOM-06",
        "Business Anomaly",
        "A06 time-entry data-quality defects are present",
        a06_pass,
        f"duplicates={duplicate_extra}; missing={len(missing_rows)}; late={late_count}",
        "15 duplicate extras, 12 incomplete records, late submissions >0",
        expected_anomaly=True,
        severity="Warning",
    )
    evidence.append(
        {
            "AnomalyID": "A06",
            "SignalMetric": "Time-entry defects",
            "ObservedValue": f"{duplicate_extra} duplicate extras; {len(missing_rows)} missing; {late_count} late",
            "Threshold": "15 / 12 / >0",
            "RootCauseEvidence": "Natural-key duplication, incomplete labor fields and submission-date latency are independently traceable by LaborRecordID.",
            "DrillPath": "QA result → LaborRecordID → Employee/project/week",
            "Recommendation": "Deduplicate, reject incomplete rows and enforce submission validation.",
            "EstimatedBusinessImpact": "Prevents duplicate/missing entries from distorting utilization and cost KPIs.",
        }
    )

    actual7, eac7, budget7 = totals(7)
    material_other7 = sum(
        to_float(row["ActualMaterialCost"]) + to_float(row["ActualOtherCost"])
        for row in financial_by_project[7]
    )
    a07_pass = (
        abs(to_float(projects[7]["PercentComplete"]) - 48.0) < 0.001
        and abs(actual7 / budget7 - 0.68) < 0.0001
        and material_other7 > 0
    )
    suite.add(
        "ANOM-07",
        "Business Anomaly",
        "A07 budget-consumption red flag is present",
        a07_pass,
        f"complete=48%; consumed={actual7 / budget7:.2%}",
        "48% complete and 68% budget consumed",
    )
    evidence.append(
        {
            "AnomalyID": "A07",
            "SignalMetric": "FORGE-007 completion vs budget consumed",
            "ObservedValue": f"48.00% complete vs {actual7 / budget7:.2%} consumed",
            "Threshold": "48% vs 68%",
            "RootCauseEvidence": f"Front-loaded material/other spend totals {money(material_other7)}.",
            "DrillPath": "Project → Financial month/category → Milestone completion",
            "Recommendation": "Apply spend gate, scope review and early reforecast.",
            "EstimatedBusinessImpact": f"Highlights {20:.0f} percentage-point spend/progress gap.",
        }
    )
    return evidence


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fieldnames or list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown_report(
    path: Path,
    tables: dict[str, list[dict[str, str]]],
    results: list[CheckResult],
    evidence: list[dict[str, str]],
    overall_status: str,
) -> None:
    counts = Counter(result.Status for result in results)
    lines = [
        "# Data quality report — FORGE RDE/PMO mock dataset",
        "",
        f"Overall status: **{overall_status}**.",
        "",
        "The intentional FactLabor defects are retained for interview-quality data cleansing and are marked `EXPECTED_ANOMALY`; all other quality gates must pass.",
        "",
        "## Summary",
        "",
        "| Status | Checks |",
        "|---|---:|",
        f"| PASS | {counts.get('PASS', 0)} |",
        f"| EXPECTED_ANOMALY | {counts.get('EXPECTED_ANOMALY', 0)} |",
        f"| FAIL | {counts.get('FAIL', 0)} |",
        "",
        "## Table volumes",
        "",
        "| Table | Rows |",
        "|---|---:|",
    ]
    lines.extend(f"| `{table}` | {len(rows):,} |" for table, rows in tables.items())
    lines.extend(
        [
            "",
            "## Controlled anomaly evidence",
            "",
            "| ID | Signal | Observed | Root-cause evidence |",
            "|---|---|---|---|",
        ]
    )
    for item in evidence:
        lines.append(
            f"| {item['AnomalyID']} | {item['SignalMetric']} | {item['ObservedValue']} | {item['RootCauseEvidence']} |"
        )
    lines.extend(
        [
            "",
            "## Failed checks",
            "",
        ]
    )
    failures = [result for result in results if result.Status == "FAIL"]
    if failures:
        lines.extend(
            [
                "| Check | Observed | Expected | Details |",
                "|---|---|---|---|",
            ]
        )
        for result in failures:
            lines.append(
                f"| {result.CheckID} — {result.CheckName} | {result.ObservedValue} | {result.ExpectedRule} | {result.Details} |"
            )
    else:
        lines.append("No unexpected failures.")
    lines.extend(
        [
            "",
            "## Cleansing order for Power BI",
            "",
            "1. Type all key/date/numeric columns explicitly.",
            "2. Reject labor rows with blank `ProjectHours` or `ActualLaborCost` to a QA exception query.",
            "3. Deduplicate `FactLabor` on (`EmployeeKey`, `ProjectKey`, `WeekStartDateKey`) and retain one `LaborRecordID`.",
            "4. Reconcile cleaned labor cost to financial labor by project/month/category.",
            "5. Load clean facts to the model and keep QA counts as dashboard measures.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def validate(data_dir: Path, quality_dir: Path) -> dict[str, Any]:
    missing_files = [table for table in EXPECTED_TABLES if not (data_dir / f"{table}.csv").exists()]
    if missing_files:
        raise FileNotFoundError(f"Missing required CSV files: {missing_files}")
    tables = {table: read_csv(data_dir / f"{table}.csv") for table in EXPECTED_TABLES}
    suite = QualitySuite()
    general_checks(suite, tables)
    primary_key_checks(suite, tables)
    foreign_key_checks(suite, tables)
    cleaned_labor, exceptions = labor_checks(suite, tables)
    financial_checks(suite, tables, cleaned_labor)
    evidence = anomaly_evidence(suite, tables, cleaned_labor)
    failures = [result for result in suite.results if result.Status == "FAIL"]
    overall_status = "FAIL" if failures else "PASS_WITH_EXPECTED_ANOMALIES"
    quality_dir.mkdir(parents=True, exist_ok=True)
    write_csv(quality_dir / "data_quality_results.csv", [asdict(result) for result in suite.results])
    write_csv(quality_dir / "labor_exceptions.csv", exceptions)
    write_csv(quality_dir / "anomaly_evidence.csv", evidence)
    summary = {
        "overall_status": overall_status,
        "generated_at": "deterministic-validation-no-runtime-timestamp",
        "check_counts": dict(Counter(result.Status for result in suite.results)),
        "unexpected_failures": [asdict(result) for result in failures],
        "table_rows": {table: len(rows) for table, rows in tables.items()},
        "clean_labor_rows": len(cleaned_labor),
        "labor_exception_rows": len(exceptions),
        "validated_anomalies": [item["AnomalyID"] for item in evidence],
    }
    (quality_dir / "data_quality_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_markdown_report(
        quality_dir / "data_quality_report.md",
        tables,
        suite.results,
        evidence,
        overall_status,
    )
    return summary


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = Path(args.data_dir)
    quality_dir = Path(args.quality_dir)
    if not data_dir.is_absolute():
        data_dir = repo_root / data_dir
    if not quality_dir.is_absolute():
        quality_dir = repo_root / quality_dir
    summary = validate(data_dir, quality_dir)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if summary["overall_status"] == "FAIL":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
