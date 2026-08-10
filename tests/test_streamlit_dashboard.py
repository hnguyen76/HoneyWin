"""Automated validation for Streamlit data, calculations, and page rendering."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from honeywin_dashboard.data import FilterSelection, apply_global_filters, load_dashboard_data
from honeywin_dashboard.metrics import (
    financial_summary,
    labor_summary,
    project_health_counts,
    project_health_table,
    workforce_summary,
)
from honeywin_dashboard.pages import _health_indicator
from scripts.check_repo_links import broken_links


@pytest.fixture(scope="module")
def dashboard_data():
    return load_dashboard_data()


@pytest.fixture(scope="module")
def full_context(dashboard_data):
    return apply_global_filters(
        dashboard_data,
        FilterSelection(date(2024, 1, 1), date(2025, 12, 31)),
    )


def test_cached_loader_validates_all_tables_and_clean_labor(dashboard_data) -> None:
    assert len(dashboard_data.tables) == 11
    assert len(dashboard_data.tables["FactLabor"]) == 8_172
    assert len(dashboard_data.labor) == 8_145
    assert dashboard_data.manifest["random_seed"] == 20_250_810


def test_financial_metrics_reconcile_to_source_frames(full_context) -> None:
    summary = financial_summary(full_context)
    expected_eac = (
        full_context.financial_all_dates["ActualCostAmount"].sum()
        + full_context.financial_all_dates["ForecastToComplete"].sum()
    )
    assert summary["approved_budget"] == pytest.approx(
        full_context.projects["ApprovedBudget"].sum()
    )
    assert summary["eac"] == pytest.approx(expected_eac)
    assert summary["forecast_variance"] == pytest.approx(
        summary["approved_budget"] - summary["eac"]
    )


def test_labor_metrics_use_weighted_target_and_clean_entries(full_context) -> None:
    summary = labor_summary(full_context.labor)
    expected_target = (
        full_context.labor["AvailableHours"] * full_context.labor["UtilizationTarget"]
    ).sum() / full_context.labor["AvailableHours"].sum()
    assert summary["time_entries"] == 8_145
    assert summary["target"] == pytest.approx(expected_target)
    assert summary["utilization"] == pytest.approx(
        full_context.labor["ProjectHours"].sum()
        / full_context.labor["AvailableHours"].sum()
    )


def test_workforce_metrics_average_monthly_snapshots(full_context) -> None:
    summary = workforce_summary(full_context.workforce)
    monthly = full_context.workforce.groupby("MonthStartDate")[
        ["ActualFTE", "RequiredFTE"]
    ].sum()
    assert summary["actual_fte"] == pytest.approx(monthly["ActualFTE"].mean())
    assert summary["required_fte"] == pytest.approx(monthly["RequiredFTE"].mean())
    assert summary["capacity_gap_fte"] == pytest.approx(
        summary["actual_fte"] - summary["required_fte"]
    )


def test_filters_respect_program_project_and_fact_date_roles(dashboard_data) -> None:
    selection = FilterSelection(
        date(2025, 1, 1),
        date(2025, 6, 30),
        programs=("Automation Platform",),
    )
    filtered = apply_global_filters(dashboard_data, selection)
    assert set(filtered.projects["Program"]) == {"Automation Platform"}
    assert filtered.financial["MonthStartDate"].between("2025-01-01", "2025-06-30").all()
    assert filtered.labor["WeekStartDate"].between("2025-01-01", "2025-06-30").all()
    assert set(filtered.financial["ProjectKey"]).issubset(set(filtered.projects["ProjectKey"]))
    assert len(filtered.financial_all_dates) > len(filtered.financial)


def test_project_health_matches_audited_red_flag_population(full_context) -> None:
    health = project_health_table(full_context)
    counts = project_health_counts(health)
    assert counts["any_red_flag"] == 6
    assert set(health["OverallHealth"]).issubset({"Green", "Amber", "Red"})
    assert pd.api.types.is_bool_dtype(health["AnyRedFlag"])


def test_health_indicator_uses_colored_dots_instead_of_status_text() -> None:
    assert _health_indicator("Green") == "🟢"
    assert _health_indicator("Amber") == "🟠"
    assert _health_indicator("Red") == "🔴"
    assert _health_indicator(None) == "⚪"


def test_dashboard_creator_signature_is_rendered() -> None:
    app = AppTest.from_file("app.py", default_timeout=20)
    app.run()
    assert not app.exception
    assert any("Created by Hieu Nguyen" in element.value for element in app.markdown)


def test_repository_markdown_links_resolve() -> None:
    assert broken_links() == []


@pytest.mark.parametrize(
    "page_name",
    [
        "Executive Overview",
        "Financial & Cost",
        "Labor Utilization",
        "Workforce Capacity",
        "Governance & Risk",
    ],
)
def test_each_streamlit_experience_renders(page_name: str) -> None:
    app = AppTest.from_file("app.py", default_timeout=20)
    app.run()
    assert not app.exception
    app.sidebar.radio[0].set_value(page_name).run()
    assert not app.exception
    assert app.sidebar.radio[0].value == page_name
