"""Relative-path data loading, validation, enrichment, and filtering."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIRECTORY = PROJECT_ROOT / "data" / "generated"

TABLE_DATE_COLUMNS: dict[str, list[str]] = {
    "DimDate": ["Date", "WeekStartDate", "WeekEndDate", "MonthStartDate"],
    "DimProject": ["StartDate", "PlannedEndDate", "ForecastEndDate", "ActualEndDate"],
    "DimEmployee": ["HireDate", "ExitDate"],
    "BridgeEmployeeSkill": ["EffectiveDate", "ExpirationDate"],
    "FactLabor": ["SubmissionDate"],
    "FactMilestone": ["PlannedDate", "ForecastDate", "ActualDate", "LastUpdatedDate"],
    "FactRiskIssue": ["IdentifiedDate", "DueDate", "ClosedDate"],
}

EXPECTED_TABLES = (
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
)


class DataLoadError(RuntimeError):
    """Raised when repository data cannot be loaded or validated."""


@dataclass(frozen=True)
class FilterSelection:
    """Global dashboard filters shared by every experience."""

    start_date: date
    end_date: date
    programs: tuple[str, ...] = ()
    projects: tuple[str, ...] = ()


@dataclass
class DashboardData:
    """Validated and enriched data frames used by the dashboard."""

    tables: dict[str, pd.DataFrame]
    projects: pd.DataFrame
    financial: pd.DataFrame
    labor: pd.DataFrame
    workforce: pd.DataFrame
    milestones: pd.DataFrame
    risks: pd.DataFrame
    manifest: dict[str, object]


@dataclass
class FilteredData:
    """Frames filtered by the global project and date context."""

    projects: pd.DataFrame
    financial: pd.DataFrame
    financial_all_dates: pd.DataFrame
    labor: pd.DataFrame
    workforce: pd.DataFrame
    milestones: pd.DataFrame
    risks: pd.DataFrame


def _date_from_key(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series.astype("Int64").astype("string"), format="%Y%m%d", errors="coerce")


def clean_labor_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Apply the audited reject-and-deduplicate rule used by Power BI."""

    clean = frame.dropna(subset=["ProjectHours", "ActualLaborCost"]).copy()
    clean = clean.sort_values("LaborRecordID")
    clean = clean.drop_duplicates(
        subset=["EmployeeKey", "ProjectKey", "WeekStartDateKey"],
        keep="first",
    )
    return clean.reset_index(drop=True)


def _read_tables(data_directory: Path) -> tuple[dict[str, pd.DataFrame], dict[str, object]]:
    manifest_path = data_directory / "manifest.json"
    if not manifest_path.exists():
        raise DataLoadError(f"Dataset manifest is missing: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    tables: dict[str, pd.DataFrame] = {}
    for table_name in EXPECTED_TABLES:
        path = data_directory / f"{table_name}.csv"
        if not path.exists():
            raise DataLoadError(f"Required table is missing: {path}")
        tables[table_name] = pd.read_csv(
            path,
            parse_dates=TABLE_DATE_COLUMNS.get(table_name, []),
            low_memory=False,
        )

    expected_rows = {entry["table"]: entry["row_count"] for entry in manifest["files"]}
    mismatches = {
        name: (len(frame), expected_rows.get(name))
        for name, frame in tables.items()
        if len(frame) != expected_rows.get(name)
    }
    if mismatches:
        detail = ", ".join(
            f"{name}: loaded {actual}, manifest {expected}"
            for name, (actual, expected) in mismatches.items()
        )
        raise DataLoadError(f"Manifest row-count validation failed: {detail}")
    return tables, manifest


def _enrich_tables(tables: dict[str, pd.DataFrame], manifest: dict[str, object]) -> DashboardData:
    projects = tables["DimProject"].copy()
    teams = tables["DimTeam"][["TeamKey", "TeamName", "EngineeringFunction"]].copy()
    project_team = teams.rename(columns={"TeamKey": "PrimaryTeamKey", "TeamName": "ProjectTeam"})
    projects = projects.merge(project_team, on="PrimaryTeamKey", how="left", validate="many_to_one")

    project_lookup = projects[
        ["ProjectKey", "ProjectID", "ProjectName", "Program", "ProjectStatus", "ProjectTeam"]
    ]

    financial = tables["FactFinancial"].copy()
    financial["MonthStartDate"] = _date_from_key(financial["MonthStartDateKey"])
    financial = financial.merge(project_lookup, on="ProjectKey", how="left", validate="many_to_one")

    employees = tables["DimEmployee"][
        [
            "EmployeeKey",
            "EmployeeID",
            "EmployeeName",
            "TeamKey",
            "Location",
            "EmploymentType",
            "UtilizationTarget",
        ]
    ].copy()
    employees = employees.merge(teams, on="TeamKey", how="left", validate="many_to_one")
    labor = clean_labor_frame(tables["FactLabor"])
    labor["WeekStartDate"] = _date_from_key(labor["WeekStartDateKey"])
    labor = labor.merge(employees, on="EmployeeKey", how="left", validate="many_to_one")
    labor = labor.merge(project_lookup, on="ProjectKey", how="left", validate="many_to_one")

    workforce = tables["FactWorkforcePlan"].copy()
    workforce["MonthStartDate"] = _date_from_key(workforce["MonthStartDateKey"])
    workforce = workforce.merge(teams, on="TeamKey", how="left", validate="many_to_one")
    workforce = workforce.merge(
        tables["DimSkill"][["SkillKey", "SkillName", "SkillFamily", "SkillCategory"]],
        on="SkillKey",
        how="left",
        validate="many_to_one",
    )

    milestones = tables["FactMilestone"].merge(
        project_lookup, on="ProjectKey", how="left", validate="many_to_one"
    )
    risks = tables["FactRiskIssue"].merge(
        project_lookup, on="ProjectKey", how="left", validate="many_to_one"
    )

    return DashboardData(
        tables=tables,
        projects=projects,
        financial=financial,
        labor=labor,
        workforce=workforce,
        milestones=milestones,
        risks=risks,
        manifest=manifest,
    )


@st.cache_data(show_spinner=False)
def load_dashboard_data(data_directory: str | Path = DATA_DIRECTORY) -> DashboardData:
    """Load all audited tables from a repository-relative directory."""

    resolved = Path(data_directory).resolve()
    tables, manifest = _read_tables(resolved)
    return _enrich_tables(tables, manifest)


def apply_global_filters(data: DashboardData, selection: FilterSelection) -> FilteredData:
    """Apply conformed project filters and the primary date role for each fact."""

    projects = data.projects.copy()
    if selection.programs:
        projects = projects[projects["Program"].isin(selection.programs)]
    if selection.projects:
        projects = projects[projects["ProjectID"].isin(selection.projects)]
    project_keys = set(projects["ProjectKey"])

    start = pd.Timestamp(selection.start_date)
    end = pd.Timestamp(selection.end_date)
    financial_all_dates = data.financial[data.financial["ProjectKey"].isin(project_keys)].copy()
    financial = financial_all_dates[
        financial_all_dates["MonthStartDate"].between(start, end)
    ].copy()
    labor = data.labor[
        data.labor["ProjectKey"].isin(project_keys) & data.labor["WeekStartDate"].between(start, end)
    ].copy()
    milestones = data.milestones[
        data.milestones["ProjectKey"].isin(project_keys)
        & data.milestones["PlannedDate"].between(start, end)
    ].copy()
    risks = data.risks[
        data.risks["ProjectKey"].isin(project_keys)
        & data.risks["IdentifiedDate"].between(start, end)
    ].copy()
    workforce = data.workforce[data.workforce["MonthStartDate"].between(start, end)].copy()

    return FilteredData(
        projects=projects,
        financial=financial,
        financial_all_dates=financial_all_dates,
        labor=labor,
        workforce=workforce,
        milestones=milestones,
        risks=risks,
    )
