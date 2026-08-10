"""Streamlit navigation and filter controls."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from typing import Any

import pandas as pd
import streamlit as st

from .data import DashboardData, FilterSelection, FilteredData


PAGE_NAMES = (
    "Executive Overview",
    "Financial & Cost",
    "Labor Utilization",
    "Workforce Capacity",
    "Governance & Risk",
    "Business Insights & Actions",
)


def render_navigation() -> str:
    """Render the six-page navigation control."""

    st.sidebar.markdown("<div class='brand-mark'>HONEYWIN</div>", unsafe_allow_html=True)
    st.sidebar.caption("RDE / PMO portfolio analytics")
    return st.sidebar.radio(
        "Dashboard",
        PAGE_NAMES,
        key="dashboard_page",
        help="Choose a portfolio analytics experience.",
    )


def render_global_filters(data: DashboardData) -> FilterSelection:
    """Render the date, program, and project filters shared by all pages."""

    st.sidebar.divider()
    st.sidebar.markdown("### Portfolio filters")
    date_dimension = data.tables["DimDate"]
    minimum_date = date_dimension["Date"].min().date()
    maximum_date = date_dimension["Date"].max().date()
    selected_dates = st.sidebar.date_input(
        "Date range",
        value=(minimum_date, maximum_date),
        min_value=minimum_date,
        max_value=maximum_date,
        key="global_date_range",
        help="Uses the primary date role for each fact table. EAC remains a full-horizon measure.",
    )
    if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
    else:
        start_date = end_date = selected_dates if isinstance(selected_dates, date) else minimum_date

    programs = sorted(data.projects["Program"].dropna().unique().tolist())
    selected_programs = st.sidebar.multiselect(
        "Program",
        programs,
        key="global_programs",
        placeholder="All programs",
    )

    project_options = data.projects
    if selected_programs:
        project_options = project_options[project_options["Program"].isin(selected_programs)]
    project_labels = dict(zip(project_options["ProjectID"], project_options["ProjectName"]))
    selected_projects = st.sidebar.multiselect(
        "Project",
        sorted(project_labels),
        key="global_projects",
        format_func=lambda project_id: f"{project_id} · {project_labels[project_id]}",
        placeholder="All projects",
    )

    st.sidebar.caption(
        "Blank multi-selects mean All. Filters are applied only where the corresponding data grain supports them."
    )
    return FilterSelection(
        start_date=start_date,
        end_date=end_date,
        programs=tuple(selected_programs),
        projects=tuple(selected_projects),
    )


def _options(frame: pd.DataFrame, column: str) -> list[Any]:
    if column not in frame or frame.empty:
        return []
    return sorted(frame[column].dropna().unique().tolist())


def _multi_filter(label: str, options: Iterable[Any], key: str) -> list[Any]:
    values = list(options)
    return st.sidebar.multiselect(label, values, key=key, placeholder=f"All {label.lower()}")


def render_page_filters(page: str, data: FilteredData) -> dict[str, list[Any]]:
    """Render filters supported by the selected experience and its data grain."""

    if page == "Business Insights & Actions":
        return {}

    st.sidebar.divider()
    st.sidebar.markdown("### Page filters")
    filters: dict[str, list[Any]] = {}
    if page == "Executive Overview":
        filters["ProjectStatus"] = _multi_filter(
            "Project status", _options(data.projects, "ProjectStatus"), "executive_status"
        )
    elif page == "Financial & Cost":
        filters["PeriodType"] = _multi_filter(
            "Period type", _options(data.financial, "PeriodType"), "financial_period"
        )
        filters["CostCategory"] = _multi_filter(
            "Cost category", _options(data.financial, "CostCategory"), "financial_category"
        )
    elif page == "Labor Utilization":
        filters["TeamName"] = _multi_filter(
            "Team", _options(data.labor, "TeamName"), "labor_team"
        )
        filters["EmploymentType"] = _multi_filter(
            "Employment type", _options(data.labor, "EmploymentType"), "labor_employment"
        )
        filters["SubmissionStatus"] = _multi_filter(
            "Submission status", _options(data.labor, "SubmissionStatus"), "labor_submission"
        )
    elif page == "Workforce Capacity":
        filters["TeamName"] = _multi_filter(
            "Team", _options(data.workforce, "TeamName"), "workforce_team"
        )
        filters["SkillName"] = _multi_filter(
            "Skill", _options(data.workforce, "SkillName"), "workforce_skill"
        )
        filters["Location"] = _multi_filter(
            "Location", _options(data.workforce, "Location"), "workforce_location"
        )
    elif page == "Governance & Risk":
        filters["RiskSeverity"] = _multi_filter(
            "Risk severity", _options(data.risks, "RiskSeverity"), "governance_severity"
        )
        filters["RiskStatus"] = _multi_filter(
            "Risk status", _options(data.risks, "RiskStatus"), "governance_status"
        )
        filters["RecordType"] = _multi_filter(
            "Record type", _options(data.risks, "RecordType"), "governance_record_type"
        )
        filters["RiskCategory"] = _multi_filter(
            "Risk category", _options(data.risks, "RiskCategory"), "governance_category"
        )
    return filters


def apply_frame_filters(frame: pd.DataFrame, selections: dict[str, list[Any]]) -> pd.DataFrame:
    """Apply selected categorical values to a frame without mutating the source."""

    filtered = frame.copy()
    for column, values in selections.items():
        if values and column in filtered:
            filtered = filtered[filtered[column].isin(values)]
    return filtered
