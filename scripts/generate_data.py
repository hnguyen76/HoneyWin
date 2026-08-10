#!/usr/bin/env python3
"""Generate the fixed-seed FORGE RDE/PMO mock dataset.

The implementation uses only the Python standard library so the dataset can be
recreated on a clean machine. Business rules and intentional anomalies are
documented in docs/data_specification.md.
"""

from __future__ import annotations

import argparse
import calendar
import csv
import hashlib
import json
import math
import random
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Sequence


TEAM_DEFINITIONS = [
    (1, "TEAM-01", "Software Engineering", "Software RDE Leader", "Software RDE", 0.85, 25),
    (2, "TEAM-02", "Data Engineering & Analytics", "Data RDE Leader", "Data & Analytics", 0.85, 12),
    (3, "TEAM-03", "Systems Engineering", "Systems RDE Leader", "Systems RDE", 0.82, 18),
    (4, "TEAM-04", "Mechanical Engineering", "Mechanical RDE Leader", "Mechanical RDE", 0.80, 22),
    (5, "TEAM-05", "Quality Assurance", "Quality RDE Leader", "Quality Engineering", 0.85, 16),
    (6, "TEAM-06", "Cloud & DevOps", "Cloud RDE Leader", "Platform Engineering", 0.85, 12),
    (7, "TEAM-07", "Cybersecurity", "Cyber RDE Leader", "Product Security", 0.85, 8),
    (8, "TEAM-08", "RDE PMO", "RDE PMO Leader", "Project Management Office", 0.75, 7),
]

SKILL_DEFINITIONS = [
    (1, "SKILL-01", "Software", "Digital Engineering", "Technical", "Digital", 1),
    (2, "SKILL-02", "Data", "Data & Analytics", "Technical", "Digital", 1),
    (3, "SKILL-03", "Systems", "Systems Engineering", "Technical", "Systems", 1),
    (4, "SKILL-04", "Mechanical", "Mechanical Engineering", "Technical", "Physical", 0),
    (5, "SKILL-05", "Quality Assurance", "Quality Engineering", "Quality", "Quality", 0),
    (6, "SKILL-06", "Cloud & DevOps", "Platform Engineering", "Technical", "Digital", 1),
    (7, "SKILL-07", "Cybersecurity", "Product Security", "Technical", "Digital", 1),
    (8, "SKILL-08", "RDE PMO", "Project Management", "Program", "Program", 0),
]

PROJECT_NAMES = [
    "Connected Asset Insights",
    "Predictive Maintenance Engine",
    "Industrial Data Fabric",
    "Secure Edge Gateway",
    "Digital Twin Services",
    "Operations Reliability Hub",
    "Remote Monitoring Upgrade",
    "Energy Optimization Analytics",
    "Cloud Control Plane",
    "Equipment Health Scoring",
    "Workflow Automation Studio",
    "RDE Portfolio Telemetry",
    "Quality Signal Intelligence",
    "Condition Monitoring Refresh",
    "Field Service Decision Support",
    "Asset Performance API",
    "Cyber Hardening Release",
    "Engineering Knowledge Graph",
    "Release Governance Automation",
    "Sensor Diagnostics Platform",
    "Customer Operations Portal",
    "Model Lifecycle Controls",
    "Connected Plant Pilot",
    "Reliability Benchmarking",
    "RDE Capacity Planning Modernization",
]

PROGRAMS = [
    "Connected Operations",
    "Industrial Analytics",
    "Digital Reliability",
    "Automation Platform",
    "Workforce Enablement",
]

LOCATIONS = ["Atlanta, GA", "Phoenix, AZ", "Charlotte, NC", "Remote, US"]
COST_CATEGORIES = ["Labor", "Contractor", "Material", "Other"]
MILESTONE_NAMES = [
    "Concept Approval",
    "Requirements Baseline",
    "Architecture Review",
    "Prototype Complete",
    "Design Verification",
    "Integration Complete",
    "Security Review",
    "System Validation",
    "Pilot Readiness",
    "Customer Acceptance",
    "Production Release",
    "Benefits Review",
]

MILESTONE_TEMPLATES = {
    "Connected Operations": [
        "Concept Approval", "Field Discovery Complete", "Requirements Baseline",
        "Architecture Review", "Prototype Complete", "Site Integration Readiness",
        "System Validation", "Pilot Readiness", "Customer Acceptance", "Production Release",
    ],
    "Industrial Analytics": [
        "Concept Approval", "Data Readiness Review", "Requirements Baseline",
        "Model Design Review", "Prototype Complete", "Model Validation",
        "Security Review", "User Acceptance", "Production Release", "Benefits Review",
    ],
    "Digital Reliability": [
        "Concept Approval", "Failure Mode Review", "Requirements Baseline",
        "Architecture Review", "Diagnostic Model Complete", "Design Verification",
        "System Validation", "Pilot Readiness", "Customer Acceptance", "Benefits Review",
    ],
    "Automation Platform": [
        "Concept Approval", "Platform Requirements Baseline", "Architecture Review",
        "Interface Contract Review", "Prototype Complete", "Integration Complete",
        "Security Review", "Release Readiness", "Production Release", "Benefits Review",
    ],
    "Workforce Enablement": [
        "Concept Approval", "Process Discovery Complete", "Requirements Baseline",
        "Solution Design Review", "Configuration Complete", "Integration Complete",
        "User Acceptance", "Training Readiness", "Production Release", "Adoption Review",
    ],
}

SYNTHETIC_FIRST_NAMES = [
    "Alex", "Avery", "Cameron", "Casey", "Devon", "Drew", "Emerson", "Hayden",
    "Jamie", "Jordan", "Kai", "Logan", "Morgan", "Parker", "Quinn", "Reese",
    "Riley", "Robin", "Rowan", "Taylor",
]
SYNTHETIC_LAST_NAMES = [
    "Archer", "Bennett", "Brooks", "Carter", "Chen", "Diaz", "Ellis", "Foster",
    "Gupta", "Hayes", "Kim", "Lewis", "Morgan", "Nguyen", "Patel", "Reed",
    "Santos", "Shaw", "Turner", "Walker",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="config/default.json",
        help="Path to JSON config (default: config/default.json)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Override output directory from config",
    )
    return parser.parse_args()


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def iso(value: date | None) -> str:
    return value.isoformat() if value else ""


def date_key(value: date | None) -> int | str:
    return int(value.strftime("%Y%m%d")) if value else ""


def month_start(value: date) -> date:
    return value.replace(day=1)


def add_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    year, month_zero = divmod(month_index, 12)
    month = month_zero + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(value.day, last_day))


def month_end(value: date) -> date:
    return add_months(value.replace(day=1), 1) - timedelta(days=1)


def iter_dates(start: date, end: date) -> Iterable[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def iter_months(start: date, end: date) -> Iterable[date]:
    current = month_start(start)
    last = month_start(end)
    while current <= last:
        yield current
        current = add_months(current, 1)


def iter_mondays(start: date, end: date) -> Iterable[date]:
    current = start + timedelta(days=(7 - start.weekday()) % 7)
    if start.weekday() == 0:
        current = start
    while current <= end:
        yield current
        current += timedelta(days=7)


def round2(value: float | Decimal) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def allocate(total: float, weights: Sequence[float], decimals: int = 2) -> list[float]:
    """Allocate a total exactly using largest remainders."""
    if not weights:
        return []
    scale = 10**decimals
    total_units = int((Decimal(str(total)) * scale).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    clean = [max(0.0, float(weight)) for weight in weights]
    weight_sum = sum(clean)
    if weight_sum <= 0:
        clean = [1.0] * len(weights)
        weight_sum = float(len(weights))
    exact = [Decimal(total_units) * Decimal(str(weight)) / Decimal(str(weight_sum)) for weight in clean]
    floors = [int(value.to_integral_value(rounding=ROUND_FLOOR)) for value in exact]
    remainder = total_units - sum(floors)
    order = sorted(range(len(exact)), key=lambda i: (exact[i] - floors[i], -i), reverse=True)
    for index in order[:remainder]:
        floors[index] += 1
    return [units / scale for units in floors]


def stable_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Cannot write empty table: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def fixed_holidays(year: int) -> dict[date, str]:
    holidays = {
        date(year, 1, 1): "New Year's Day",
        date(year, 7, 4): "Independence Day",
        date(year, 12, 25): "Christmas Day",
    }
    november_first = date(year, 11, 1)
    first_thursday = november_first + timedelta(days=(3 - november_first.weekday()) % 7)
    holidays[first_thursday + timedelta(weeks=3)] = "Thanksgiving Day"
    return holidays


def build_dim_date(config: dict[str, Any]) -> list[dict[str, Any]]:
    start = parse_date(config["start_date"])
    end = parse_date(config["end_date"])
    as_of = parse_date(config["data_as_of_date"])
    holidays: dict[date, str] = {}
    for year in range(start.year, end.year + 1):
        holidays.update(fixed_holidays(year))
    rows: list[dict[str, Any]] = []
    for current in iter_dates(start, end):
        iso_calendar = current.isocalendar()
        is_weekend = current.weekday() >= 5
        holiday_name = holidays.get(current, "")
        is_holiday = bool(holiday_name)
        is_working = not is_weekend and not is_holiday
        rows.append(
            {
                "DateKey": date_key(current),
                "Date": iso(current),
                "DayOfWeekName": current.strftime("%A"),
                "DayOfWeekNumber": current.isoweekday(),
                "WeekStartDate": iso(current - timedelta(days=current.weekday())),
                "WeekEndDate": iso(current - timedelta(days=current.weekday()) + timedelta(days=6)),
                "WeekOfYear": iso_calendar.week,
                "MonthNumber": current.month,
                "MonthName": current.strftime("%B"),
                "MonthStartDate": iso(current.replace(day=1)),
                "YearMonth": current.strftime("%Y-%m"),
                "CalendarQuarter": f"Q{((current.month - 1) // 3) + 1}",
                "CalendarYear": current.year,
                "FiscalMonthNumber": current.month,
                "FiscalQuarter": f"Q{((current.month - 1) // 3) + 1}",
                "FiscalYear": current.year,
                "IsWeekend": int(is_weekend),
                "IsHoliday": int(is_holiday),
                "HolidayName": holiday_name,
                "IsWorkingDay": int(is_working),
                "WorkingHours": 8.0 if is_working else 0.0,
                "PeriodType": "Actual" if current <= as_of else "Forecast",
            }
        )
    return rows


def build_dim_team() -> list[dict[str, Any]]:
    return [
        {
            "TeamKey": key,
            "TeamID": team_id,
            "TeamName": name,
            "TeamLeader": leader,
            "EngineeringFunction": function,
            "UtilizationTarget": target,
            "ActiveFlag": 1,
        }
        for key, team_id, name, leader, function, target, _ in TEAM_DEFINITIONS
    ]


def build_dim_skill() -> list[dict[str, Any]]:
    return [
        {
            "SkillKey": key,
            "SkillID": skill_id,
            "SkillName": name,
            "SkillFamily": family,
            "SkillCategory": category,
            "AdjacencyGroup": adjacency,
            "IsCriticalSkill": critical,
        }
        for key, skill_id, name, family, category, adjacency, critical in SKILL_DEFINITIONS
    ]


def project_status(start: date, planned_end: date, as_of: date) -> tuple[str, float, date | None]:
    if start > as_of:
        return "Planned", 0.0, None
    if planned_end <= as_of - timedelta(days=30):
        return "Completed", 100.0, planned_end - timedelta(days=3),
    elapsed = max(0, (as_of - start).days)
    duration = max(1, (planned_end - start).days)
    percent = min(95.0, max(8.0, round2(100 * elapsed / duration * 0.92)))
    return "Active", percent, None


def build_dim_project(config: dict[str, Any], rng: random.Random) -> list[dict[str, Any]]:
    as_of = parse_date(config["data_as_of_date"])
    end = parse_date(config["end_date"])
    rows: list[dict[str, Any]] = []
    used_start_dates: set[date] = set()
    program_team_weights = {
        "Connected Operations": [3, 4, 1, 6],
        "Industrial Analytics": [2, 1, 6, 3],
        "Digital Reliability": [3, 5, 2, 4],
        "Automation Platform": [1, 6, 7, 3],
        "Workforce Enablement": [8, 2, 5, 1],
    }
    for project_key in range(1, config["project_count"] + 1):
        if project_key == 2:
            start = date(2024, 1, 1)
        elif project_key == 3:
            start = date(2024, 2, 5)
        elif project_key in {22, 25}:
            start = date(2025, rng.randint(7, 10), rng.randint(1, 20))
        else:
            start = date(2024, 1, 1) + timedelta(days=rng.randint(0, 500))
        while start in used_start_dates:
            start += timedelta(days=1)
        used_start_dates.add(start)
        duration_months = rng.randint(8, 17)
        planned_end = month_end(add_months(start, duration_months - 1))
        if planned_end > end:
            planned_end = end - timedelta(days=rng.randint(0, 20))
        schedule_variance = max(-7, min(35, round(rng.gauss(8, 10))))
        forecast_end = min(end, planned_end + timedelta(days=schedule_variance))
        forecast_end = max(start, forecast_end)
        status, percent_complete, actual_end = project_status(start, planned_end, as_of)
        if status == "Completed" and actual_end is not None:
            actual_end = min(as_of, max(start, planned_end + timedelta(days=rng.randint(-14, 9))))
        elif status == "Active" and schedule_variance >= 18:
            status = "At Risk"
        approved_budget = float(rng.randrange(245, 1121) * 5_000)
        baseline_budget = float(round(approved_budget * rng.uniform(0.91, 0.995) / 1_000) * 1_000)
        if approved_budget >= 4_500_000 or schedule_variance >= 20:
            priority = rng.choices(["High", "Medium"], weights=[0.72, 0.28], k=1)[0]
        elif approved_budget < 2_000_000:
            priority = rng.choices(["Medium", "Low", "High"], weights=[0.55, 0.35, 0.10], k=1)[0]
        else:
            priority = rng.choices(["High", "Medium", "Low"], weights=[0.32, 0.58, 0.10], k=1)[0]
        program = rng.choices(PROGRAMS, weights=[0.28, 0.24, 0.20, 0.17, 0.11], k=1)[0]
        primary_team = rng.choices(program_team_weights[program], weights=[0.44, 0.28, 0.18, 0.10], k=1)[0]
        if project_key == 1:
            start, planned_end = date(2024, 10, 1), date(2025, 10, 31)
            forecast_end = date(2025, 12, 12)
            status, percent_complete, actual_end = "At Risk", 55.0, None
            approved_budget, baseline_budget, priority = 3_000_000.0, 2_800_000.0, "High"
        elif project_key == 4:
            start, planned_end = date(2024, 6, 1), date(2025, 10, 15)
            forecast_end = date(2025, 11, 29)
            status, percent_complete, actual_end = "Delayed", 62.0, None
            approved_budget, baseline_budget, priority = 3_600_000.0, 3_450_000.0, "High"
        elif project_key == 7:
            start, planned_end = date(2024, 11, 1), date(2025, 11, 30)
            forecast_end = date(2025, 12, 14)
            status, percent_complete, actual_end = "At Risk", 48.0, None
            approved_budget, baseline_budget, priority = 2_500_000.0, 2_500_000.0, "High"
        elif project_key == 9:
            start, planned_end = date(2024, 7, 1), date(2025, 9, 30)
            forecast_end = date(2025, 10, 15)
            status, percent_complete, actual_end = "At Risk", 60.0, None
            approved_budget, baseline_budget, priority = 2_800_000.0, 2_650_000.0, "High"
        if approved_budget < 1_750_000:
            budget_class = "Small"
        elif approved_budget < 3_500_000:
            budget_class = "Medium"
        elif approved_budget < 5_000_000:
            budget_class = "Large"
        else:
            budget_class = "Strategic"
        rows.append(
            {
                "ProjectKey": project_key,
                "ProjectID": f"FORGE-{project_key:03d}",
                "ProjectName": PROJECT_NAMES[project_key - 1],
                "Program": program,
                "ProjectManager": f"Project Manager {rng.choices(range(1, 11), weights=[14, 13, 12, 11, 10, 9, 8, 7, 5, 3], k=1)[0]:02d}",
                "Sponsor": f"RDE Sponsor {rng.choices(range(1, 7), weights=[25, 21, 18, 15, 12, 9], k=1)[0]:02d}",
                "PrimaryTeamKey": primary_team,
                "StartDate": iso(start),
                "PlannedEndDate": iso(planned_end),
                "ForecastEndDate": iso(forecast_end),
                "ActualEndDate": iso(actual_end),
                "ProjectStatus": status,
                "Priority": priority,
                "PercentComplete": percent_complete,
                "ApprovedBudget": approved_budget,
                "BaselineBudget": baseline_budget,
                "BudgetClass": budget_class,
            }
        )
    return rows


def build_dim_employee(
    config: dict[str, Any], rng: random.Random
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    as_of = parse_date(config["data_as_of_date"])
    employees: list[dict[str, Any]] = []
    bridge: list[dict[str, Any]] = []
    employee_key = 1
    bridge_key = 1
    base_rates = {1: 88, 2: 92, 3: 95, 4: 84, 5: 76, 6: 100, 7: 105, 8: 90}
    contractor_rates = {1: 0.24, 2: 0.25, 3: 0.11, 4: 0.09, 5: 0.10, 6: 0.33, 7: 0.25, 8: 0.14}
    adjacency = {
        1: [2, 6, 7],
        2: [1, 6],
        3: [4, 5, 1],
        4: [3, 5],
        5: [3, 4],
        6: [1, 2, 7],
        7: [1, 6],
        8: [3, 5],
    }
    location_weights = {
        1: [0.32, 0.14, 0.34, 0.20],
        2: [0.24, 0.10, 0.30, 0.36],
        3: [0.18, 0.30, 0.42, 0.10],
        4: [0.12, 0.48, 0.34, 0.06],
        5: [0.22, 0.18, 0.48, 0.12],
        6: [0.20, 0.08, 0.22, 0.50],
        7: [0.22, 0.12, 0.26, 0.40],
        8: [0.36, 0.08, 0.32, 0.24],
    }
    for team_key, _, _, _, _, target, headcount in TEAM_DEFINITIONS:
        for local_index in range(headcount):
            is_contractor = rng.random() < contractor_rates[team_key]
            employment_type = "Contractor" if is_contractor else "Employee"
            location = rng.choices(LOCATIONS, weights=location_weights[team_key], k=1)[0]
            rate = base_rates[team_key] * rng.uniform(0.86, 1.17)
            if is_contractor:
                rate *= rng.uniform(1.28, 1.48)
            rate = round2(rate)
            tenure_roll = rng.random()
            if tenure_roll < 0.72:
                hire_date = date(rng.randint(2021, 2023), rng.randint(1, 12), rng.randint(1, 25))
            elif tenure_roll < 0.91:
                hire_date = date(2024, rng.randint(1, 12), rng.randint(1, 25))
            else:
                hire_date = date(2025, rng.randint(1, 6), rng.randint(1, 25))
            exit_date: date | None = None
            planned_exit = {
                (5, 2): date(2024, 8, 16),
                (6, 1): date(2025, 2, 7),
                (8, 3): date(2024, 11, 22),
            }.get((team_key, local_index))
            if planned_exit is not None:
                exit_date = planned_exit
                if hire_date >= exit_date:
                    hire_date = date(2022, rng.randint(1, 10), rng.randint(1, 25))
            name_index = employee_key - 1
            first_name = SYNTHETIC_FIRST_NAMES[(name_index * 7 + team_key) % len(SYNTHETIC_FIRST_NAMES)]
            last_name = SYNTHETIC_LAST_NAMES[(name_index * 11 + local_index) % len(SYNTHETIC_LAST_NAMES)]
            utilization_target = min(0.91, max(0.70, target + rng.gauss(0.0, 0.012) + (0.012 if is_contractor else 0.0)))
            employees.append(
                {
                    "EmployeeKey": employee_key,
                    "EmployeeID": f"EMP-{employee_key:04d}",
                    "EmployeeName": f"{first_name} {last_name}",
                    "TeamKey": team_key,
                    "PrimarySkillKey": team_key,
                    "Location": location,
                    "EmploymentType": employment_type,
                    "HireDate": iso(hire_date),
                    "ExitDate": iso(exit_date),
                    "StandardLaborRate": rate,
                    "UtilizationTarget": round2(utilization_target),
                    "EmploymentStatus": "Inactive" if exit_date and exit_date <= as_of else "Active",
                    "IsActiveAsOfDate": int(hire_date <= as_of and (exit_date is None or exit_date > as_of)),
                }
            )
            primary_level = rng.choice([3, 4, 4, 5])
            is_certified = int(primary_level >= 4 and rng.random() < 0.65)
            bridge.append(
                {
                    "EmployeeSkillKey": bridge_key,
                    "EmployeeKey": employee_key,
                    "SkillKey": team_key,
                    "ProficiencyLevel": primary_level,
                    "ProficiencyCategory": proficiency_category(primary_level),
                    "IsPrimarySkill": 1,
                    "IsCertified": is_certified,
                    "CertificationName": f"Mock {SKILL_DEFINITIONS[team_key - 1][2]} Certification" if is_certified else "",
                    "EffectiveDate": iso(hire_date),
                    "ExpirationDate": iso(add_months(hire_date, rng.randint(24, 36))) if is_certified else "",
                }
            )
            bridge_key += 1
            secondary_count = rng.choices([0, 1, 2], weights=[0.35, 0.5, 0.15], k=1)[0]
            for secondary_skill in rng.sample(adjacency[team_key], k=min(secondary_count, len(adjacency[team_key]))):
                level = rng.choice([1, 2, 2, 3])
                bridge.append(
                    {
                        "EmployeeSkillKey": bridge_key,
                        "EmployeeKey": employee_key,
                        "SkillKey": secondary_skill,
                        "ProficiencyLevel": level,
                        "ProficiencyCategory": proficiency_category(level),
                        "IsPrimarySkill": 0,
                        "IsCertified": 0,
                        "CertificationName": "",
                        "EffectiveDate": iso(min(as_of, hire_date + timedelta(days=rng.randint(90, 240)))),
                        "ExpirationDate": "",
                    }
                )
                bridge_key += 1
            employee_key += 1
    if len(employees) != config["employee_count"]:
        raise ValueError(f"Employee design creates {len(employees)} rows, expected {config['employee_count']}")
    return employees, bridge


def proficiency_category(level: int) -> str:
    return {1: "Foundational", 2: "Intermediate", 3: "Advanced", 4: "Advanced", 5: "Expert"}[level]


def select_special_employees(employees: list[dict[str, Any]]) -> tuple[set[int], set[int]]:
    rate_mix = {
        row["EmployeeKey"]
        for row in employees
        if row["EmploymentType"] == "Contractor" and row["TeamKey"] in {1, 2, 6}
    }
    rate_mix.update(
        row["EmployeeKey"]
        for row in employees
        if row["EmploymentType"] == "Employee" and row["TeamKey"] in {1, 2, 6} and row["EmployeeKey"] % 7 == 0
    )
    overrun = {
        row["EmployeeKey"]
        for row in employees
        if row["TeamKey"] in {3, 4} and (row["EmploymentType"] == "Contractor" or row["EmployeeKey"] % 9 == 0)
    }
    return rate_mix, overrun


def build_fact_labor(
    config: dict[str, Any],
    rng: random.Random,
    dim_date: list[dict[str, Any]],
    projects: list[dict[str, Any]],
    employees: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    start = parse_date(config["start_date"])
    as_of = parse_date(config["data_as_of_date"])
    working_hours_by_date = {parse_date(row["Date"]): row["WorkingHours"] for row in dim_date}
    project_dates = [
        (
            row["ProjectKey"],
            row["PrimaryTeamKey"],
            parse_date(row["StartDate"]),
            parse_date(row["ForecastEndDate"]),
        )
        for row in projects
    ]
    rate_mix_employees, overrun_employees = select_special_employees(employees)
    base_rows: list[dict[str, Any]] = []
    record_number = 1
    employee_utilization = {
        employee["EmployeeKey"]: employee["UtilizationTarget"] + rng.gauss(0.0, 0.018)
        for employee in employees
    }
    prior_project: dict[int, int] = {}
    team_demand_effect = {1: 0.018, 2: 0.012, 3: 0.004, 4: -0.008, 5: -0.004, 6: 0.016, 7: 0.006, 8: -0.025}
    for week_start in iter_mondays(start, as_of):
        scheduled = sum(working_hours_by_date.get(week_start + timedelta(days=offset), 0.0) for offset in range(7))
        week_end = week_start + timedelta(days=6)
        active_projects = [item for item in project_dates if item[2] <= week_start <= item[3] and item[2] <= as_of]
        for employee in employees:
            if parse_date(employee["HireDate"]) > week_end:
                continue
            if employee["ExitDate"] and parse_date(employee["ExitDate"]) < week_start:
                continue
            if not active_projects:
                continue
            candidate_weights = []
            for candidate in active_projects:
                weight = 1.0
                if candidate[1] == employee["TeamKey"]:
                    weight *= 4.6
                if prior_project.get(employee["EmployeeKey"]) == candidate[0]:
                    weight *= 2.8
                candidate_weights.append(weight)
            project_key = rng.choices(active_projects, weights=candidate_weights, k=1)[0][0]
            pto_hours = 0.0
            pto_roll = rng.random()
            if scheduled >= 32 and pto_roll < 0.025:
                pto_hours = rng.choice([16.0, 24.0])
            elif scheduled >= 24 and pto_roll < 0.052:
                pto_hours = 12.0
            elif scheduled >= 16 and pto_roll < 0.105:
                pto_hours = 8.0
            elif scheduled >= 8 and pto_roll < 0.145:
                pto_hours = 4.0
            pto_hours = min(pto_hours, scheduled)
            available = scheduled - pto_hours
            overtime = 0.0
            seasonal_effect = -0.018 if week_start.month in {7, 8, 12} else (0.008 if week_start.month in {3, 4, 10} else 0.0)
            utilization_driver = (
                employee["UtilizationTarget"]
                + team_demand_effect[employee["TeamKey"]]
                + seasonal_effect
                + rng.gauss(0.0, 0.028)
            )
            base_util = 0.64 * employee_utilization[employee["EmployeeKey"]] + 0.36 * utilization_driver
            if employee["TeamKey"] == 5 and date(2025, 1, 6) <= week_start <= as_of:
                base_util = 0.678 + rng.gauss(0.0, 0.004)
                overtime = 0.0
            if employee["EmployeeKey"] in rate_mix_employees and date(2025, 3, 3) <= week_start <= as_of:
                project_key = 9
                base_util = rng.uniform(0.91, 0.965)
                overtime = round(rng.uniform(3.5, 8.25) * 4) / 4
            elif employee["EmployeeKey"] in overrun_employees and date(2025, 2, 3) <= week_start <= as_of:
                project_key = 1
                base_util = rng.uniform(0.885, 0.945)
                overtime = round(rng.uniform(4.0, 10.0) * 4) / 4
            elif rng.random() < max(0.025, min(0.09, 0.04 + max(0.0, base_util - 0.84))) and available >= 24:
                overtime = round(rng.uniform(1.0, 6.5) * 4) / 4
            base_util = max(0.48, min(0.98, base_util))
            employee_utilization[employee["EmployeeKey"]] = base_util
            prior_project[employee["EmployeeKey"]] = project_key
            regular_productive = min(available, max(0.0, round(base_util * available * 4) / 4))
            project_hours = round2(regular_productive + overtime)
            non_project = round2(available + overtime - project_hours)
            multiplier = 1.0 if employee["EmploymentType"] == "Contractor" else 1.5
            labor_cost = round2(
                (project_hours - overtime) * employee["StandardLaborRate"]
                + overtime * employee["StandardLaborRate"] * multiplier
            )
            late_probability = 0.028 + (0.025 if week_start >= date(2025, 4, 1) else 0.0) + (0.018 if employee["EmploymentType"] == "Contractor" else 0.0)
            late = rng.random() < late_probability
            submission_date = week_end + timedelta(days=round(rng.triangular(4, 14, 6)) if late else rng.choices([0, 1, 2, 3], weights=[18, 46, 29, 7], k=1)[0])
            source = rng.choices(
                ["SAP-Style Time", "Mobile Time Entry", "Manager Adjustment"],
                weights=[88, 10, 2 if late else 1],
                k=1,
            )[0]
            base_rows.append(
                {
                    "LaborRecordID": f"LAB-{record_number:06d}",
                    "WeekStartDateKey": date_key(week_start),
                    "EmployeeKey": employee["EmployeeKey"],
                    "ProjectKey": project_key,
                    "ScheduledHours": round2(scheduled),
                    "AvailableHours": round2(available),
                    "ProjectHours": project_hours,
                    "NonProjectHours": non_project,
                    "OvertimeHours": round2(overtime),
                    "PTOHours": round2(pto_hours),
                    "StandardLaborRate": employee["StandardLaborRate"],
                    "OvertimeRateMultiplier": multiplier,
                    "ActualLaborCost": labor_cost,
                    "SubmissionDate": iso(submission_date),
                    "SubmissionStatus": "Late" if late else "On Time",
                    "TimeEntrySource": source,
                }
            )
            record_number += 1
    # A modest share of employee-weeks is split across two concurrent projects.
    # Hours/capacity are allocated, not duplicated, so utilization and cost still reconcile.
    employee_by_key = {employee["EmployeeKey"]: employee for employee in employees}
    split_candidates = [
        index
        for index, row in enumerate(base_rows)
        if row["ProjectKey"] not in {1, 4, 7, 9}
        and float(row["ProjectHours"]) >= 18.0
        and float(row["ScheduledHours"]) >= 24.0
    ]
    split_rows: list[dict[str, Any]] = []
    for index in rng.sample(split_candidates, min(180, len(split_candidates))):
        source = base_rows[index]
        week_key = int(source["WeekStartDateKey"])
        week = date(week_key // 10000, (week_key // 100) % 100, week_key % 100)
        employee = employee_by_key[int(source["EmployeeKey"])]
        alternatives = [
            item
            for item in project_dates
            if item[0] != source["ProjectKey"] and item[2] <= week <= item[3]
        ]
        if not alternatives:
            continue
        weights = [3.2 if item[1] == employee["TeamKey"] else 1.0 for item in alternatives]
        secondary_project = rng.choices(alternatives, weights=weights, k=1)[0][0]
        fraction = rng.choice([0.25, 0.30, 0.35, 0.40])
        split = dict(source)
        split["LaborRecordID"] = f"LAB-{record_number:06d}"
        split["ProjectKey"] = secondary_project
        record_number += 1
        for field in [
            "ScheduledHours", "ProjectHours", "OvertimeHours", "PTOHours",
        ]:
            total = float(source[field])
            secondary_value = round2(round(total * fraction * 4) / 4)
            source[field] = round2(total - secondary_value)
            split[field] = secondary_value
        for row in (source, split):
            row["AvailableHours"] = round2(float(row["ScheduledHours"]) - float(row["PTOHours"]))
            row["NonProjectHours"] = round2(
                float(row["AvailableHours"]) + float(row["OvertimeHours"]) - float(row["ProjectHours"])
            )
            row["ActualLaborCost"] = round2(
                (float(row["ProjectHours"]) - float(row["OvertimeHours"])) * float(row["StandardLaborRate"])
                + float(row["OvertimeHours"]) * float(row["StandardLaborRate"]) * float(row["OvertimeRateMultiplier"])
            )
        split_rows.append(split)
    base_rows.extend(split_rows)
    eligible_missing = [
        i
        for i, row in enumerate(base_rows)
        if row["ProjectKey"] not in {1, 7, 9}
        and row["EmployeeKey"] % 5 != 0
    ]
    missing_indices = set(rng.sample(eligible_missing, 12))
    valid_rows = [dict(row) for index, row in enumerate(base_rows) if index not in missing_indices]
    output_rows = [dict(row) for row in base_rows]
    for index in missing_indices:
        output_rows[index]["ProjectHours"] = ""
        output_rows[index]["ActualLaborCost"] = ""
    duplicate_candidates = [row for row in valid_rows if row["ProjectKey"] not in {1, 7, 9}]
    duplicate_source_rows = rng.sample(duplicate_candidates, 15)
    for source in duplicate_source_rows:
        duplicate = dict(source)
        duplicate["LaborRecordID"] = f"LAB-{record_number:06d}"
        record_number += 1
        output_rows.append(duplicate)
    output_rows.sort(
        key=lambda row: (
            int(row["WeekStartDateKey"]),
            int(row["EmployeeKey"]),
            int(row["ProjectKey"]),
            row["LaborRecordID"],
        )
    )
    metadata = {
        "base_rows": len(base_rows),
        "multi_project_split_rows": len(split_rows),
        "missing_rows": len(missing_indices),
        "duplicate_rows": len(duplicate_source_rows),
    }
    return output_rows, valid_rows, metadata


def labor_aggregates(
    valid_labor: list[dict[str, Any]], employee_by_key: dict[int, dict[str, Any]]
) -> tuple[dict[tuple[int, date, str], float], dict[tuple[int, date, str], float]]:
    costs: dict[tuple[int, date, str], float] = defaultdict(float)
    hours: dict[tuple[int, date, str], float] = defaultdict(float)
    for row in valid_labor:
        week = date(int(str(row["WeekStartDateKey"])) // 10000, (int(str(row["WeekStartDateKey"])) // 100) % 100, int(str(row["WeekStartDateKey"])) % 100)
        month = month_start(week)
        employment_type = employee_by_key[int(row["EmployeeKey"])]["EmploymentType"]
        category = "Contractor" if employment_type == "Contractor" else "Labor"
        key = (int(row["ProjectKey"]), month, category)
        costs[key] += float(row["ActualLaborCost"])
        hours[key] += float(row["ProjectHours"])
    return ({key: round2(value) for key, value in costs.items()}, {key: round2(value) for key, value in hours.items()})


def build_fact_financial(
    config: dict[str, Any],
    rng: random.Random,
    projects: list[dict[str, Any]],
    employees: list[dict[str, Any]],
    valid_labor: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    as_of = parse_date(config["data_as_of_date"])
    employee_by_key = {row["EmployeeKey"]: row for row in employees}
    labor_costs, labor_hours = labor_aggregates(valid_labor, employee_by_key)
    rows: list[dict[str, Any]] = []
    record_number = 1
    for project in projects:
        project_key = project["ProjectKey"]
        start = month_start(parse_date(project["StartDate"]))
        end = month_start(parse_date(project["ForecastEndDate"]))
        months = list(iter_months(start, end))
        cells = [(month, category) for month in months for category in COST_CATEGORIES]
        base_share = {"Labor": 0.42, "Contractor": 0.12, "Material": 0.32, "Other": 0.14}
        share_raw = {category: base_share[category] * rng.uniform(0.78, 1.24) for category in COST_CATEGORIES}
        share_total = sum(share_raw.values())
        category_share = {category: share_raw[category] / share_total for category in COST_CATEGORIES}
        if project_key == 9:
            category_share = {"Labor": 0.35, "Contractor": 0.20, "Material": 0.30, "Other": 0.15}
        curve_type = rng.choices(["bell", "front", "back"], weights=[58, 22, 20], k=1)[0]
        budget_weights: list[float] = []
        for month, category in cells:
            position = months.index(month) / max(1, len(months) - 1)
            if curve_type == "front":
                phase = 1.45 - 0.72 * position
            elif curve_type == "back":
                phase = 0.72 + 0.85 * position
            else:
                phase = 0.68 + 0.72 * math.sin(math.pi * position)
            category_timing = 1.0
            if category == "Material":
                category_timing = 1.18 - 0.34 * position
            elif category == "Contractor":
                category_timing = 0.86 + 0.30 * position
            elif category == "Other":
                category_timing = 0.94 + 0.10 * math.cos(math.pi * position)
            budget_weights.append(category_share[category] * phase * category_timing * rng.uniform(0.94, 1.06))
        budget_allocations = allocate(project["ApprovedBudget"], budget_weights)
        actual_labor_total = sum(
            labor_costs.get((project_key, month, category), 0.0)
            for month in months
            for category in ("Labor", "Contractor")
            if month <= month_start(as_of)
        )
        percent = project["PercentComplete"] / 100.0
        if project_key == 1:
            actual_target = project["ApprovedBudget"] * 0.70
        elif project_key == 7:
            actual_target = project["ApprovedBudget"] * 0.68
        elif project["ProjectStatus"] == "Completed":
            actual_target = project["ApprovedBudget"] * rng.uniform(0.94, 1.045)
        else:
            schedule_days = (parse_date(project["ForecastEndDate"]) - parse_date(project["PlannedEndDate"])).days
            ratio = 0.96 + max(0, schedule_days) * 0.0018 + rng.gauss(0.0, 0.035)
            actual_target = project["ApprovedBudget"] * percent * ratio
        actual_target = max(actual_labor_total, actual_target)
        actual_target = round2(actual_target)
        actual_cells = [(month, category) for month, category in cells if month <= month_start(as_of)]
        residual_actual = max(0.0, actual_target - actual_labor_total)
        material_other_cells = [(month, category) for month, category in actual_cells if category in {"Material", "Other"}]
        material_weights = []
        budget_by_cell = dict(zip(cells, budget_allocations, strict=True))
        for month, category in material_other_cells:
            frontload = 1.8 if project_key == 7 and month <= date(2025, 3, 1) else 1.0
            material_weights.append(max(0.01, budget_by_cell[(month, category)]) * frontload * rng.uniform(0.82, 1.18))
        material_allocations = dict(
            zip(material_other_cells, allocate(residual_actual, material_weights), strict=True)
        )
        if project_key == 1:
            desired_eac = project["ApprovedBudget"] + 400_000.0
        elif project_key == 4:
            desired_eac = project["ApprovedBudget"] * 1.12
        elif project_key == 7:
            desired_eac = project["ApprovedBudget"] * 1.08
        elif project_key == 9:
            desired_eac = project["ApprovedBudget"] * 1.06
        elif project["ProjectStatus"] == "Completed":
            desired_eac = actual_target
        else:
            schedule_days = max(0, (parse_date(project["ForecastEndDate"]) - parse_date(project["PlannedEndDate"])).days)
            consumption_gap = max(0.0, actual_target / project["ApprovedBudget"] - percent)
            eac_ratio = 1.0 + 0.62 * consumption_gap + 0.0012 * schedule_days + rng.gauss(0.0, 0.022)
            if project["ProjectStatus"] in {"At Risk", "Delayed"}:
                eac_ratio += 0.012
            desired_eac = project["ApprovedBudget"] * min(1.17, max(0.93, eac_ratio))
        desired_eac = round2(max(actual_target, desired_eac))
        future_cells = [(month, category) for month, category in cells if month > month_start(as_of)]
        future_total = max(0.0, desired_eac - actual_target)
        forecast_weights = []
        for month, category in future_cells:
            weight = max(0.01, budget_by_cell[(month, category)]) * rng.uniform(0.92, 1.08)
            if project_key == 1 and category in {"Contractor", "Other"}:
                weight *= 1.55
            if project_key == 4 and category in {"Contractor", "Material"}:
                weight *= 1.45
            forecast_weights.append(weight)
        forecast_allocations = dict(zip(future_cells, allocate(future_total, forecast_weights), strict=True))
        if project_key == 9:
            p9_actual_labor_cells = [
                i
                for i, (month, category) in enumerate(cells)
                if month <= month_start(as_of) and category in {"Labor", "Contractor"}
            ]
            target_labor_budget = round2(actual_labor_total / 1.18) if actual_labor_total else 0.0
            fixed = allocate(
                target_labor_budget,
                [labor_costs.get((project_key, cells[i][0], cells[i][1]), 0.1) for i in p9_actual_labor_cells],
            )
            fixed_by_index = dict(zip(p9_actual_labor_cells, fixed, strict=True))
            remaining_indices = [i for i in range(len(cells)) if i not in fixed_by_index]
            remaining_budget = project["ApprovedBudget"] - target_labor_budget
            remaining = allocate(remaining_budget, [budget_weights[i] for i in remaining_indices])
            for i, value in fixed_by_index.items():
                budget_allocations[i] = value
            for i, value in zip(remaining_indices, remaining, strict=True):
                budget_allocations[i] = value
        project_actual_hours = sum(
            labor_hours.get((project_key, month, category), 0.0)
            for month in months
            for category in ("Labor", "Contractor")
            if month <= month_start(as_of)
        )
        project9_planned_total = project_actual_hours / 1.01 if project_key == 9 else None
        p9_hour_cells = [
            (month, category)
            for month, category in cells
            if month <= month_start(as_of) and category in {"Labor", "Contractor"}
        ]
        p9_planned_alloc = (
            dict(
                zip(
                    p9_hour_cells,
                    allocate(project9_planned_total or 0.0, [labor_hours.get((project_key, *cell), 0.1) for cell in p9_hour_cells]),
                    strict=True,
                )
            )
            if project_key == 9
            else {}
        )
        planned_employee_rate = rng.uniform(82.0, 103.0)
        planned_contractor_rate = rng.uniform(116.0, 148.0)
        for index, (month, category) in enumerate(cells):
            actual_labor = labor_costs.get((project_key, month, category), 0.0) if category in {"Labor", "Contractor"} else 0.0
            actual_material = material_allocations.get((month, category), 0.0) if category == "Material" else 0.0
            actual_other = material_allocations.get((month, category), 0.0) if category == "Other" else 0.0
            actual_cost = round2(actual_labor + actual_material + actual_other)
            forecast = forecast_allocations.get((month, category), 0.0)
            commitment_rate = 0.0
            if month > month_start(as_of):
                months_ahead = max(1, (month.year - as_of.year) * 12 + month.month - as_of.month)
                category_commitment = 0.03 if category == "Other" else (0.06 if category == "Labor" else 0.14)
                commitment_rate = min(0.62, max(0.12, 0.34 - 0.025 * months_ahead + category_commitment + rng.gauss(0.0, 0.045)))
                if project_key == 4 and category in {"Contractor", "Material"}:
                    commitment_rate = rng.uniform(0.58, 0.74)
            committed = round2(forecast * commitment_rate)
            actual_hours = labor_hours.get((project_key, month, category), 0.0) if category in {"Labor", "Contractor"} else 0.0
            if category == "Labor":
                planned_hours = round2(budget_allocations[index] / planned_employee_rate)
            elif category == "Contractor":
                planned_hours = round2(budget_allocations[index] / planned_contractor_rate)
            else:
                planned_hours = 0.0
            if project_key == 9 and (month, category) in p9_planned_alloc:
                planned_hours = p9_planned_alloc[(month, category)]
            rows.append(
                {
                    "FinancialRecordID": f"FIN-{record_number:06d}",
                    "MonthStartDateKey": date_key(month),
                    "FiscalMonth": month.strftime("%Y-%m"),
                    "ProjectKey": project_key,
                    "CostCategory": category,
                    "PeriodType": "Actual" if month <= month_start(as_of) else "Forecast",
                    "BudgetAmount": budget_allocations[index],
                    "ActualLaborCost": round2(actual_labor),
                    "ActualMaterialCost": round2(actual_material),
                    "ActualOtherCost": round2(actual_other),
                    "ActualCostAmount": actual_cost,
                    "CommittedCost": committed,
                    "ForecastToComplete": round2(forecast),
                    "EAC": round2(actual_cost + forecast),
                    "PlannedLaborHours": planned_hours,
                    "ActualLaborHours": round2(actual_hours),
                }
            )
            record_number += 1
    return rows


def interpolate_date(start: date, end: date, position: float) -> date:
    return start + timedelta(days=round((end - start).days * position))


def build_fact_milestone(
    config: dict[str, Any], rng: random.Random, projects: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    as_of = parse_date(config["data_as_of_date"])
    rows: list[dict[str, Any]] = []
    milestone_key = 1
    for project in projects:
        project_key = project["ProjectKey"]
        start = parse_date(project["StartDate"])
        planned_end = parse_date(project["PlannedEndDate"])
        template = MILESTONE_TEMPLATES[project["Program"]]
        milestone_count = rng.randint(6, min(10, len(template)))
        interior_indices = sorted(rng.sample(range(1, len(template) - 1), milestone_count - 2))
        names = [template[0], *(template[index] for index in interior_indices), template[-1]]
        project_schedule_variance = (
            parse_date(project["ForecastEndDate"]) - parse_date(project["PlannedEndDate"])
        ).days
        for sequence, name in enumerate(names, start=1):
            position = sequence / milestone_count
            planned = interpolate_date(start, planned_end, position)
            delay = round(project_schedule_variance * position + rng.gauss(0.0, 5.5))
            delay = max(-10, min(32, delay))
            critical = int(
                sequence in {max(2, milestone_count // 2), milestone_count}
                or name in {"Security Review", "Release Readiness", "System Validation"} and rng.random() < 0.35
            )
            if project_key == 1 and sequence == max(2, milestone_count // 2):
                planned = date(2025, 2, 28)
                delay = 42
                critical = 1
            if project_key == 4 and sequence == max(2, milestone_count // 2):
                planned = date(2025, 4, 15)
                delay = 45
                critical = 1
            forecast = planned + timedelta(days=delay)
            if forecast < start:
                forecast = start
            if forecast > parse_date(config["end_date"]):
                forecast = parse_date(config["end_date"])
            actual: date | None = None
            completion = 0.0
            if project_key == 4 and delay == 45:
                completion = 75.0
            elif planned <= as_of and (
                project["ProjectStatus"] == "Completed"
                or project["PercentComplete"] / 100.0 >= position + 0.07
            ):
                actual = max(start, min(as_of, forecast + timedelta(days=rng.randint(-3, 2))))
                completion = 100.0
            elif planned <= as_of and project["PercentComplete"] / 100.0 >= position - 0.30:
                relative_progress = (project["PercentComplete"] / 100.0 - position + 0.30) / 0.37
                completion = round2(min(90.0, max(10.0, 10.0 + 80.0 * relative_progress + rng.gauss(0.0, 4.0))))
            if actual is not None:
                schedule_status = "Complete"
            elif delay > 30:
                schedule_status = "Delayed"
            elif delay >= 8:
                schedule_status = "At Risk"
            else:
                schedule_status = "On Time"
            rows.append(
                {
                    "MilestoneKey": milestone_key,
                    "ProjectKey": project_key,
                    "MilestoneSequence": sequence,
                    "MilestoneName": name,
                    "PlannedDateKey": date_key(planned),
                    "ForecastDateKey": date_key(forecast),
                    "ActualDateKey": date_key(actual),
                    "PlannedDate": iso(planned),
                    "ForecastDate": iso(forecast),
                    "ActualDate": iso(actual),
                    "CompletionPercent": completion,
                    "ScheduleVarianceDays": (forecast - planned).days,
                    "ScheduleStatus": schedule_status,
                    "IsCritical": critical,
                    "MilestoneOwner": f"Milestone Owner {((project_key + sequence) % 12) + 1:02d}",
                    "LastUpdatedDate": iso(
                        as_of
                        - timedelta(
                            days=rng.randint(2, 21)
                            if actual is not None
                            else rng.randint(0, 8) if completion > 0 else rng.randint(5, 28)
                        )
                    ),
                }
            )
            milestone_key += 1
    return rows


def severity_from_score(score: int) -> str:
    if score >= 20:
        return "Critical"
    if score >= 12:
        return "High"
    if score >= 6:
        return "Medium"
    return "Low"


def build_fact_risk_issue(
    config: dict[str, Any], rng: random.Random, projects: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    as_of = parse_date(config["data_as_of_date"])
    start_range = parse_date(config["start_date"])
    categories = ["Schedule", "Cost", "Resource", "Technical", "Quality", "Dependency"]
    titles = {
        "Schedule": [
            "Integration sequence may compress validation", "Supplier lead time threatens the next gate",
            "Test environment availability may move the baseline", "Release window has limited recovery float",
            "Late design decision may affect downstream work", "Pilot readiness depends on unresolved actions",
        ],
        "Cost": [
            "Specialist rate mix is above plan", "Material quotation may exceed the estimate",
            "Rework could consume management reserve", "Cloud run cost is trending above the baseline",
            "Committed spend limits recovery options", "Scope clarification may require a budget change",
        ],
        "Resource": [
            "Critical skill coverage is below demand", "Shared engineer availability may delay delivery",
            "Backfill timing creates a capacity gap", "Contractor transition may reduce throughput",
            "Competing portfolio priority constrains staffing", "Review capacity is concentrated in one role",
        ],
        "Technical": [
            "Interface behavior remains unproven", "Performance margin may not meet the target",
            "Legacy data quality could require redesign", "Prototype result may require architecture rework",
            "Environment parity is not yet demonstrated", "Technical debt may complicate integration",
        ],
        "Quality": [
            "Verification evidence is incomplete", "Defect closure rate may miss the exit criterion",
            "Traceability coverage requires remediation", "Regression scope may exceed the test window",
            "Acceptance criteria remain partially ambiguous", "Field issue recurrence needs containment",
        ],
        "Dependency": [
            "External interface decision is blocking delivery", "Vendor component readiness is uncertain",
            "Security approval is on the critical path", "Platform release timing may create a mismatch",
            "Customer test access is not yet confirmed", "Upstream data contract remains unresolved",
        ],
    }
    owner_roles = [
        "Project Manager", "Technical Lead", "Product Owner", "Systems Lead", "Quality Lead",
        "Security Lead", "Finance Partner", "Supplier Manager", "Data Lead", "Release Manager",
    ]
    rows: list[dict[str, Any]] = []
    risk_key = 1
    for project in projects:
        count = rng.randint(3, 7)
        project_start = max(start_range, parse_date(project["StartDate"]))
        for sequence in range(1, count + 1):
            category = rng.choices(categories, weights=[19, 15, 18, 21, 14, 13], k=1)[0]
            record_type = "Issue" if rng.random() < 0.27 else "Risk"
            probability = rng.choices([1, 2, 3, 4, 5], weights=[8, 24, 36, 23, 9], k=1)[0]
            impact_weights = [5, 18, 34, 29, 14] if record_type == "Issue" else [10, 25, 34, 23, 8]
            impact = rng.choices([1, 2, 3, 4, 5], weights=impact_weights, k=1)[0]
            if project_start <= as_of:
                identified = project_start + timedelta(days=rng.randint(0, max(1, min(300, (as_of - project_start).days))))
            else:
                earliest = max(start_range, project_start - timedelta(days=120))
                identified = earliest + timedelta(days=rng.randint(0, max(1, (as_of - earliest).days)))
            due = min(parse_date(config["end_date"]), identified + timedelta(days=round(rng.triangular(28, 155, 68))))
            if due < as_of:
                status = rng.choices(["Open", "Monitoring", "Mitigated", "Closed"], weights=[12, 18, 32, 38], k=1)[0]
            else:
                status = rng.choices(["Open", "Monitoring", "Mitigated", "Closed"], weights=[42, 38, 14, 6], k=1)[0]
            mitigation = {
                "Open": rng.choices(["Not Started", "In Progress"], weights=[56, 44], k=1)[0],
                "Monitoring": rng.choices(["In Progress", "Completed"], weights=[78, 22], k=1)[0],
                "Mitigated": "Completed",
                "Closed": rng.choices(["Completed", "Not Required"], weights=[88, 12], k=1)[0],
            }[status]
            if project["ProjectKey"] == 4 and sequence == 1:
                category, probability, impact = "Dependency", 5, 5
                record_type = "Issue"
                identified, due = date(2025, 2, 15), date(2025, 4, 10)
                status, mitigation = "Open", "Not Started"
            elif project["ProjectKey"] == 1 and sequence == 1:
                category, probability, impact = "Cost", 5, 5
                identified, due = date(2025, 3, 1), date(2025, 5, 15)
                status, mitigation = "Monitoring", "In Progress"
            score = probability * impact
            severity = severity_from_score(score)
            closed: date | None = None
            if status == "Closed":
                latest_close = max(identified, min(as_of, due + timedelta(days=30)))
                closed = identified + timedelta(days=rng.randint(0, max(0, (latest_close - identified).days)))
            is_critical = int(severity == "Critical" and status not in {"Mitigated", "Closed"})
            is_overdue = int(closed is None and due < as_of and status not in {"Mitigated", "Closed"})
            rows.append(
                {
                    "RiskIssueKey": risk_key,
                    "RiskIssueID": f"RI-{project['ProjectKey']:03d}-{sequence:02d}",
                    "ProjectKey": project["ProjectKey"],
                    "RecordType": record_type,
                    "RiskTitle": (
                        f"{rng.choice(titles[category])} — {project['ProjectName']}"
                        if rng.random() < 0.48
                        else rng.choice(titles[category])
                    ),
                    "RiskCategory": category,
                    "Probability": probability,
                    "Impact": impact,
                    "RiskScore": score,
                    "RiskSeverity": severity,
                    "Owner": owner_roles[(project["ProjectKey"] * 3 + sequence * 2) % len(owner_roles)],
                    "IdentifiedDateKey": date_key(identified),
                    "DueDateKey": date_key(due),
                    "ClosedDateKey": date_key(closed),
                    "IdentifiedDate": iso(identified),
                    "DueDate": iso(due),
                    "ClosedDate": iso(closed),
                    "RiskStatus": status,
                    "MitigationStatus": mitigation,
                    "IsCritical": is_critical,
                    "IsOverdue": is_overdue,
                }
            )
            risk_key += 1
    return rows


def build_fact_workforce_plan(
    config: dict[str, Any], rng: random.Random, employees: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    start = parse_date(config["start_date"])
    end = parse_date(config["end_date"])
    as_of = parse_date(config["data_as_of_date"])
    monthly_hours = float(config["standard_monthly_hours_per_fte"])
    resources: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for employee in employees:
        key = (employee["TeamKey"], employee["Location"])
        resources[key].append(employee)
    rows: list[dict[str, Any]] = []
    record_number = 1
    target_required = {1: 30.0, 2: 14.0, 3: 17.0, 4: 19.0}
    demand_hub = {
        1: "Charlotte, NC", 2: "Remote, US", 3: "Charlotte, NC", 4: "Phoenix, AZ",
        5: "Charlotte, NC", 6: "Remote, US", 7: "Remote, US", 8: "Atlanta, GA",
    }
    demand_state = {team_key: headcount * rng.uniform(0.94, 1.01) for team_key, _, _, _, _, _, headcount in TEAM_DEFINITIONS}
    for month in iter_months(start, end):
        month_last = month_end(month)
        month_index = (month.year - start.year) * 12 + month.month - start.month
        for team_key, _, _, _, _, _, headcount in TEAM_DEFINITIONS:
            location_actual: list[float] = []
            location_contractor: list[float] = []
            for location in LOCATIONS:
                actual_fte = 0.0
                contractor_fte = 0.0
                for employee in resources[(team_key, location)]:
                    hire = parse_date(employee["HireDate"])
                    employee_exit = parse_date(employee["ExitDate"]) if employee["ExitDate"] else None
                    if hire > month_last or (employee_exit is not None and employee_exit < month):
                        contribution = 0.0
                    elif month > month_start(as_of):
                        contribution = 1.0
                    elif hire >= month or (employee_exit is not None and employee_exit <= month_last):
                        active_start = max(month, hire)
                        active_end = min(month_last, employee_exit) if employee_exit is not None else month_last
                        contribution = max(0, (active_end - active_start).days + 1)
                        contribution /= (month_last - month).days + 1
                    else:
                        contribution = 1.0
                    actual_fte += contribution
                    if employee["EmploymentType"] == "Contractor":
                        contractor_fte += contribution
                if month <= month_start(as_of) and actual_fte >= 2.0 and rng.random() < 0.16:
                    leave_adjustment = rng.choice([0.1, 0.2, 0.3, 0.5])
                    actual_fte = max(0.0, actual_fte - leave_adjustment)
                    contractor_fte = min(contractor_fte, actual_fte)
                location_actual.append(round2(actual_fte))
                location_contractor.append(round2(contractor_fte))
            if month >= date(2025, 7, 1) and team_key in target_required:
                required_total = target_required[team_key]
            else:
                growth = 1.0 + 0.0022 * month_index
                seasonality = 0.015 if month.month in {9, 10, 11} else (-0.012 if month.month in {6, 7, 12} else 0.0)
                team_bias = {1: 0.7, 2: 0.4, 3: 0.1, 4: -0.5, 5: -0.2, 6: 0.5, 7: 0.2, 8: -0.15}[team_key]
                desired = headcount * (growth + seasonality) + team_bias + rng.gauss(0.0, 0.35)
                demand_state[team_key] = 0.74 * demand_state[team_key] + 0.26 * desired
                required_total = round2(max(0.0, demand_state[team_key]))
            demand_delta = max(0.0, required_total - sum(location_actual))
            allocation_weights = []
            for location, actual_fte in zip(LOCATIONS, location_actual, strict=True):
                hub_boost = max(1.0, demand_delta * 0.65) if location == demand_hub[team_key] else 0.0
                allocation_weights.append(actual_fte + hub_boost)
            required_allocations = allocate(
                required_total,
                allocation_weights,
            )
            for location, actual_fte, contractor_fte, required_fte in zip(
                LOCATIONS, location_actual, location_contractor, required_allocations, strict=True
            ):
                gap = round2(actual_fte - required_fte)
                rows.append(
                    {
                        "WorkforcePlanRecordID": f"WFP-{record_number:06d}",
                        "MonthStartDateKey": date_key(month),
                        "TeamKey": team_key,
                        "SkillKey": team_key,
                        "Location": location,
                        "RequiredFTE": required_fte,
                        "ActualFTE": actual_fte,
                        "OpenDemandFTE": round2(max(required_fte - actual_fte, 0.0)),
                        "ContractorFTE": contractor_fte,
                        "CapacityGapFTE": gap,
                        "AvailableCapacityHours": round2(actual_fte * monthly_hours),
                        "RequiredCapacityHours": round2(required_fte * monthly_hours),
                    }
                )
                record_number += 1
    return rows


def build_manifest(
    output_dir: Path, config: dict[str, Any], tables: dict[str, list[dict[str, Any]]]
) -> dict[str, Any]:
    files = []
    for table_name, rows in tables.items():
        path = output_dir / f"{table_name}.csv"
        files.append(
            {
                "table": table_name,
                "file": path.name,
                "row_count": len(rows),
                "sha256": stable_sha256(path),
            }
        )
    return {
        "dataset": "FORGE RDE PMO synthetic portfolio",
        "data_classification": "Synthetic / interview portfolio only",
        "random_seed": config["random_seed"],
        "start_date": config["start_date"],
        "end_date": config["end_date"],
        "data_as_of_date": config["data_as_of_date"],
        "table_count": len(tables),
        "files": files,
    }


def load_config(config_path: Path) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def generate(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    rng = random.Random(int(config["random_seed"]))
    dim_date = build_dim_date(config)
    dim_team = build_dim_team()
    dim_skill = build_dim_skill()
    dim_project = build_dim_project(config, rng)
    dim_employee, bridge_employee_skill = build_dim_employee(config, rng)
    fact_labor, valid_labor, labor_metadata = build_fact_labor(
        config, rng, dim_date, dim_project, dim_employee
    )
    fact_financial = build_fact_financial(
        config, rng, dim_project, dim_employee, valid_labor
    )
    fact_milestone = build_fact_milestone(config, rng, dim_project)
    fact_workforce_plan = build_fact_workforce_plan(config, rng, dim_employee)
    fact_risk_issue = build_fact_risk_issue(config, rng, dim_project)
    tables = {
        "DimDate": dim_date,
        "DimProject": dim_project,
        "DimEmployee": dim_employee,
        "DimTeam": dim_team,
        "DimSkill": dim_skill,
        "BridgeEmployeeSkill": bridge_employee_skill,
        "FactLabor": fact_labor,
        "FactFinancial": fact_financial,
        "FactMilestone": fact_milestone,
        "FactWorkforcePlan": fact_workforce_plan,
        "FactRiskIssue": fact_risk_issue,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    for table_name, rows in tables.items():
        write_csv(output_dir / f"{table_name}.csv", rows)
    manifest = build_manifest(output_dir, config, tables)
    manifest["intentional_labor_data_quality"] = labor_metadata
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    requested_config = Path(args.config)
    config_path = requested_config if requested_config.is_absolute() else repo_root / requested_config
    config = load_config(config_path)
    requested_output = Path(args.output_dir) if args.output_dir else Path(config["output_directory"])
    output_dir = requested_output if requested_output.is_absolute() else repo_root / requested_output
    manifest = generate(config, output_dir)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
