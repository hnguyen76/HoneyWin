"""Streamlit page composition for the five Power BI-aligned experiences."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import streamlit as st

from .charts import (
    cost_category_chart,
    governance_category_chart,
    labor_trend_chart,
    milestone_delay_chart,
    monthly_spend_chart,
    overtime_trend_chart,
    program_financial_chart,
    project_status_chart,
    project_variance_chart,
    risk_matrix_chart,
    team_utilization_chart,
    workforce_gap_chart,
    workforce_heatmap,
    workforce_trend_chart,
)
from .data import (
    DataLoadError,
    FilterSelection,
    FilteredData,
    apply_global_filters,
    load_dashboard_data,
)
from .filters import (
    apply_frame_filters,
    render_global_filters,
    render_navigation,
    render_page_filters,
)
from .insights import (
    BusinessInsight,
    executive_insights,
    financial_insights,
    governance_insights,
    labor_insights,
    workforce_insights,
)
from .metrics import (
    financial_summary,
    governance_summary,
    labor_summary,
    project_health_counts,
    project_health_table,
    workforce_summary,
)
from .style import (
    ThemeTokens,
    apply_app_style,
    empty_state,
    format_currency,
    format_number,
    format_percent,
    format_pp,
    insight_card,
    load_theme_tokens,
    metric_card,
    page_header,
    render_signature,
    section_heading,
)


CHART_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
    "scrollZoom": False,
}

HEALTH_INDICATORS = {
    "Green": "🟢",
    "Amber": "🟠",
    "Red": "🔴",
}


def _health_indicator(value: object) -> str:
    """Return a compact colored-dot indicator for a project health status."""

    return HEALTH_INDICATORS.get(str(value), "⚪")


def _filter_context(selection: FilterSelection, project_count: int) -> str:
    programs = f"{len(selection.programs)} selected" if selection.programs else "All programs"
    return (
        f"{selection.start_date:%b %Y} – {selection.end_date:%b %Y} · "
        f"{programs} · {project_count} projects"
    )


def _scope_to_projects(data: FilteredData, projects: pd.DataFrame) -> FilteredData:
    keys = set(projects["ProjectKey"])
    return replace(
        data,
        projects=projects,
        financial=data.financial[data.financial["ProjectKey"].isin(keys)].copy(),
        financial_all_dates=data.financial_all_dates[
            data.financial_all_dates["ProjectKey"].isin(keys)
        ].copy(),
        labor=data.labor[data.labor["ProjectKey"].isin(keys)].copy(),
        milestones=data.milestones[data.milestones["ProjectKey"].isin(keys)].copy(),
        risks=data.risks[data.risks["ProjectKey"].isin(keys)].copy(),
    )


def _financial_tone(summary: dict[str, float]) -> str:
    if not summary["approved_budget"]:
        return "neutral"
    overrun = -summary["forecast_variance_pct"]
    if overrun > 0.10:
        return "bad"
    if overrun >= 0.03:
        return "warning"
    return "good"


def _render_insights(insights: list[BusinessInsight], tokens: ThemeTokens) -> None:
    section_heading("Business insights & corrective actions")
    st.markdown(
        '<div class="insight-context">Generated from the current filter context. Actions are recommendations, not recorded management decisions.</div>',
        unsafe_allow_html=True,
    )
    columns = st.columns(len(insights))
    for column, insight in zip(columns, insights):
        with column:
            insight_card(
                insight.title,
                insight.evidence,
                insight.action,
                tokens,
                insight.tone,
            )


def _render_executive(
    data: FilteredData,
    selection: FilterSelection,
    page_filters: dict[str, list[object]],
    tokens: ThemeTokens,
) -> None:
    projects = apply_frame_filters(data.projects, page_filters)
    scoped = _scope_to_projects(data, projects)
    page_header(
        "Executive Overview",
        "Portfolio performance, forecast exposure, and the projects that require attention.",
        _filter_context(selection, len(projects)),
    )
    if projects.empty:
        empty_state("No projects match the current portfolio filters.")
        return

    financial = financial_summary(scoped)
    health = project_health_table(scoped)
    health_counts = project_health_counts(health)
    cards = st.columns(5)
    with cards[0]:
        metric_card(
            "Approved Budget",
            format_currency(financial["approved_budget"], 0),
            f"{format_currency(financial['budget_change'], 1)} vs baseline",
            tokens,
            "primary",
        )
    with cards[1]:
        metric_card(
            "Actual Cost",
            format_currency(financial["actual_cost"], 0),
            f"{format_percent(financial['budget_consumed_pct'])} of approved budget",
            tokens,
            "secondary",
        )
    with cards[2]:
        metric_card(
            "Estimate at Completion",
            format_currency(financial["eac"], 0),
            "Full-horizon actual + forecast",
            tokens,
            _financial_tone(financial),
        )
    with cards[3]:
        metric_card(
            "Forecast Variance",
            format_percent(financial["forecast_variance_pct"]),
            f"{format_currency(financial['forecast_variance'], 1)} · negative is unfavorable",
            tokens,
            "bad" if financial["forecast_variance"] < 0 else "good",
        )
    with cards[4]:
        metric_card(
            "Projects with Any Red Flag",
            f"{health_counts['any_red_flag']}",
            f"{health_counts['red']} red · {health_counts['amber']} amber",
            tokens,
            "bad" if health_counts["any_red_flag"] else "good",
        )

    _render_insights(executive_insights(financial, health), tokens)

    section_heading("Portfolio trajectory")
    left, right = st.columns([2.25, 1])
    with left:
        st.plotly_chart(
            program_financial_chart(
                projects, scoped.financial, scoped.financial_all_dates, tokens
            ),
            use_container_width=True,
            config=CHART_CONFIG,
        )
    with right:
        st.plotly_chart(
            project_status_chart(projects, tokens),
            use_container_width=True,
            config=CHART_CONFIG,
        )

    st.plotly_chart(
        monthly_spend_chart(scoped.financial, tokens),
        use_container_width=True,
        config=CHART_CONFIG,
    )

    section_heading("Priority project exceptions")
    table = health[
        [
            "ProjectID",
            "ProjectName",
            "Program",
            "ProjectStatus",
            "OverallHealth",
            "BudgetConsumedPct",
            "CompletionPct",
            "BudgetCompletionGap",
            "ForecastVariance",
            "MaxCriticalDelay",
            "MaxRiskScore",
        ]
    ].head(12).copy()
    table["OverallHealth"] = table["OverallHealth"].map(_health_indicator)
    table["BudgetCompletionGapPP"] = table["BudgetCompletionGap"] * 100
    table = table.drop(columns="BudgetCompletionGap")
    st.dataframe(
        table,
        hide_index=True,
        use_container_width=True,
        column_config={
            "ProjectID": "Project",
            "ProjectName": "Project name",
            "ProjectStatus": "Status",
            "OverallHealth": st.column_config.TextColumn(
                "Health",
                help="🟢 On track · 🟠 Watch · 🔴 Critical",
                width="small",
            ),
            "BudgetConsumedPct": st.column_config.ProgressColumn(
                "Budget consumed", min_value=0, max_value=1.25, format="percent"
            ),
            "CompletionPct": st.column_config.ProgressColumn(
                "Completion", min_value=0, max_value=1, format="percent"
            ),
            "BudgetCompletionGapPP": st.column_config.NumberColumn("Gap", format="%+.1f pp"),
            "ForecastVariance": st.column_config.NumberColumn("Forecast variance", format="$%0.0f"),
            "MaxCriticalDelay": st.column_config.NumberColumn("Critical delay", format="%.0f days"),
            "MaxRiskScore": "Max risk score",
        },
    )
    st.caption("Health: 🟢 On track · 🟠 Watch · 🔴 Critical")


def _render_financial(
    data: FilteredData,
    selection: FilterSelection,
    page_filters: dict[str, list[object]],
    tokens: ThemeTokens,
) -> None:
    financial = apply_frame_filters(data.financial, page_filters)
    all_dates = apply_frame_filters(data.financial_all_dates, page_filters)
    scoped = replace(data, financial=financial, financial_all_dates=all_dates)
    page_header(
        "Financial & Cost",
        "Budget consumption, forecast exposure, cost mix, and project-level variance.",
        _filter_context(selection, len(data.projects)),
    )
    if financial.empty and all_dates.empty:
        empty_state("No financial records match the selected filters.")
        return
    summary = financial_summary(scoped)
    health = project_health_table(scoped)
    cards = st.columns(5)
    card_values = (
        (
            "Approved Budget",
            format_currency(summary["approved_budget"], 0),
            f"{format_currency(summary['budget_change'], 1)} vs baseline",
            "primary",
        ),
        (
            "Actual Cost",
            format_currency(summary["actual_cost"], 0),
            f"{format_percent(summary['budget_consumed_pct'])} consumed",
            "secondary",
        ),
        (
            "EAC",
            format_currency(summary["eac"], 0),
            "Full-horizon estimate",
            _financial_tone(summary),
        ),
        (
            "Forecast Variance",
            format_percent(summary["forecast_variance_pct"]),
            format_currency(summary["forecast_variance"], 1),
            "bad" if summary["forecast_variance"] < 0 else "good",
        ),
        (
            "Committed Cost",
            format_currency(summary["committed_cost"], 1),
            "Open commitments in date context",
            "warning" if summary["committed_cost"] else "neutral",
        ),
    )
    for column, (label, value, detail, tone) in zip(cards, card_values):
        with column:
            metric_card(label, value, detail, tokens, tone)

    _render_insights(financial_insights(summary, health, financial), tokens)

    section_heading("Spend and plan variance")
    st.plotly_chart(
        monthly_spend_chart(financial, tokens), use_container_width=True, config=CHART_CONFIG
    )
    left, right = st.columns([1, 1.15])
    with left:
        st.plotly_chart(
            cost_category_chart(financial, tokens),
            use_container_width=True,
            config=CHART_CONFIG,
        )
    with right:
        st.plotly_chart(
            project_variance_chart(health, tokens),
            use_container_width=True,
            config=CHART_CONFIG,
        )

    section_heading("Project financial detail")
    detail = project_health_table(scoped)[
        [
            "ProjectID",
            "ProjectName",
            "Program",
            "ApprovedBudget",
            "ActualCost",
            "EAC",
            "ForecastVariance",
            "BudgetConsumedPct",
            "CompletionPct",
        ]
    ]
    st.dataframe(
        detail,
        hide_index=True,
        use_container_width=True,
        column_config={
            "ProjectID": "Project",
            "ProjectName": "Project name",
            "ApprovedBudget": st.column_config.NumberColumn("Approved budget", format="$%0.0f"),
            "ActualCost": st.column_config.NumberColumn("Actual cost", format="$%0.0f"),
            "EAC": st.column_config.NumberColumn("EAC", format="$%0.0f"),
            "ForecastVariance": st.column_config.NumberColumn("Forecast variance", format="$%0.0f"),
            "BudgetConsumedPct": st.column_config.NumberColumn("Budget consumed", format="percent"),
            "CompletionPct": st.column_config.NumberColumn("Completion", format="percent"),
        },
    )


def _render_labor(
    data: FilteredData,
    selection: FilterSelection,
    page_filters: dict[str, list[object]],
    tokens: ThemeTokens,
) -> None:
    labor = apply_frame_filters(data.labor, page_filters)
    page_header(
        "Labor Utilization",
        "Productive capacity, target attainment, overtime, and time-entry discipline.",
        _filter_context(selection, len(data.projects)),
    )
    if labor.empty:
        empty_state("No clean labor records match the selected filters.")
        return
    summary = labor_summary(labor)
    gap_tone = "bad" if summary["utilization_gap"] < -0.12 else (
        "warning" if summary["utilization_gap"] < -0.05 else "good"
    )
    cards = st.columns(5)
    values = (
        ("Labor Utilization", format_percent(summary["utilization"]), "Project hours / available hours", gap_tone),
        ("Weighted Target", format_percent(summary["target"]), "Availability-weighted employee target", "secondary"),
        ("Utilization Gap", format_pp(summary["utilization_gap"]), "Actual minus weighted target", gap_tone),
        ("Overtime Hours", format_number(summary["overtime_hours"]), f"{format_percent(summary['overtime_pct'])} of project hours", "warning"),
        ("Time-entry Compliance", format_percent(summary["compliance"]), f"{summary['late_entries']} late entries", "good" if summary["compliance"] >= 0.95 else "warning"),
    )
    for column, (label, value, detail, tone) in zip(cards, values):
        with column:
            metric_card(label, value, detail, tokens, tone)

    _render_insights(labor_insights(summary, labor), tokens)

    section_heading("Utilization trajectory and target performance")
    st.plotly_chart(
        labor_trend_chart(labor, tokens), use_container_width=True, config=CHART_CONFIG
    )
    left, right = st.columns([1.15, 1])
    with left:
        st.plotly_chart(
            team_utilization_chart(labor, tokens), use_container_width=True, config=CHART_CONFIG
        )
    with right:
        st.plotly_chart(
            overtime_trend_chart(labor, tokens), use_container_width=True, config=CHART_CONFIG
        )

    section_heading("Resource-level utilization exceptions")
    source = labor.assign(TargetHours=labor["AvailableHours"] * labor["UtilizationTarget"])
    employee = source.groupby(
        ["EmployeeID", "EmployeeName", "TeamName", "EmploymentType"], as_index=False
    ).agg(
        AvailableHours=("AvailableHours", "sum"),
        ProjectHours=("ProjectHours", "sum"),
        TargetHours=("TargetHours", "sum"),
        OvertimeHours=("OvertimeHours", "sum"),
        LateEntries=("SubmissionStatus", lambda values: int((values == "Late").sum())),
    )
    employee["Utilization"] = employee["ProjectHours"] / employee["AvailableHours"]
    employee["Target"] = employee["TargetHours"] / employee["AvailableHours"]
    employee["Gap"] = employee["Utilization"] - employee["Target"]
    employee = employee.sort_values(["Gap", "OvertimeHours"]).head(20)
    st.dataframe(
        employee,
        hide_index=True,
        use_container_width=True,
        column_config={
            "EmployeeID": "Resource",
            "EmployeeName": "Resource name",
            "TeamName": "Team",
            "EmploymentType": "Employment type",
            "AvailableHours": st.column_config.NumberColumn("Available hours", format="%.1f"),
            "ProjectHours": st.column_config.NumberColumn("Project hours", format="%.1f"),
            "TargetHours": None,
            "Utilization": st.column_config.NumberColumn("Utilization", format="percent"),
            "Target": st.column_config.NumberColumn("Target", format="percent"),
            "Gap": st.column_config.NumberColumn("Gap", format="percent"),
            "OvertimeHours": st.column_config.NumberColumn("Overtime", format="%.1f"),
            "LateEntries": "Late entries",
        },
    )


def _render_workforce(
    data: FilteredData,
    selection: FilterSelection,
    page_filters: dict[str, list[object]],
    tokens: ThemeTokens,
) -> None:
    workforce = apply_frame_filters(data.workforce, page_filters)
    page_header(
        "Workforce Capacity",
        "Monthly supply, required demand, skill shortages, and location-level capacity.",
        f"{selection.start_date:%b %Y} – {selection.end_date:%b %Y} · Workforce plan grain",
    )
    st.caption("Program and project filters do not apply because the workforce plan has no project key.")
    if workforce.empty:
        empty_state("No workforce-plan records match the selected filters.")
        return
    summary = workforce_summary(workforce)
    gap_tone = "bad" if summary["capacity_gap_fte"] < 0 else "good"
    cards = st.columns(5)
    values = (
        ("Actual FTE", format_number(summary["actual_fte"]), "Average monthly snapshot", "primary"),
        ("Required FTE", format_number(summary["required_fte"]), "Average monthly demand", "secondary"),
        ("Capacity Gap FTE", f"{summary['capacity_gap_fte']:+.1f}", "Actual minus required", gap_tone),
        ("Open Demand FTE", format_number(summary["open_demand_fte"]), "Average monthly open demand", "warning" if summary["open_demand_fte"] else "neutral"),
        ("Demand Coverage", format_percent(summary["demand_coverage_pct"]), f"{summary['hiring_need_fte']:.1f} FTE hiring/reallocation need", gap_tone),
    )
    for column, (label, value, detail, tone) in zip(cards, values):
        with column:
            metric_card(label, value, detail, tokens, tone)

    _render_insights(workforce_insights(summary, workforce), tokens)

    section_heading("Capacity trajectory and shortage concentration")
    st.plotly_chart(
        workforce_trend_chart(workforce, tokens), use_container_width=True, config=CHART_CONFIG
    )
    left, right = st.columns([1, 1.1])
    with left:
        st.plotly_chart(
            workforce_gap_chart(workforce, tokens), use_container_width=True, config=CHART_CONFIG
        )
    with right:
        st.plotly_chart(
            workforce_heatmap(workforce, tokens), use_container_width=True, config=CHART_CONFIG
        )

    section_heading("Average monthly capacity by team, skill, and location")
    monthly = workforce.groupby(
        ["MonthStartDate", "TeamName", "SkillName", "Location"], as_index=False
    ).agg(ActualFTE=("ActualFTE", "sum"), RequiredFTE=("RequiredFTE", "sum"))
    detail = monthly.groupby(["TeamName", "SkillName", "Location"], as_index=False)[
        ["ActualFTE", "RequiredFTE"]
    ].mean()
    detail["GapFTE"] = detail["ActualFTE"] - detail["RequiredFTE"]
    detail = detail.sort_values("GapFTE").head(30)
    st.dataframe(
        detail,
        hide_index=True,
        use_container_width=True,
        column_config={
            "TeamName": "Team",
            "SkillName": "Skill",
            "ActualFTE": st.column_config.NumberColumn("Actual FTE", format="%.2f"),
            "RequiredFTE": st.column_config.NumberColumn("Required FTE", format="%.2f"),
            "GapFTE": st.column_config.NumberColumn("Gap FTE", format="%+.2f"),
        },
    )


def _render_governance(
    data: FilteredData,
    selection: FilterSelection,
    page_filters: dict[str, list[object]],
    tokens: ThemeTokens,
) -> None:
    risks = apply_frame_filters(data.risks, page_filters)
    page_header(
        "Governance & Risk",
        "Milestone reliability, risk exposure, overdue actions, and mitigation readiness.",
        _filter_context(selection, len(data.projects)),
    )
    summary = governance_summary(data.projects, data.milestones, risks)
    cards = st.columns(5)
    values = (
        ("Projects at Risk", f"{summary['projects_at_risk']}", "At Risk or Delayed status", "bad" if summary["projects_at_risk"] else "good"),
        ("On-time Milestones", format_percent(float(summary["on_time_milestone_pct"])), f"{summary['on_time_milestones']} of {summary['milestones']}", "good" if float(summary["on_time_milestone_pct"]) >= 0.8 else "warning"),
        ("Open Critical Risks", f"{summary['open_critical_risks']}", f"{summary['critical_without_mitigation']} without mitigation", "bad" if summary["open_critical_risks"] else "good"),
        ("Overdue Actions", f"{summary['overdue_actions']}", "Risk and issue actions past due", "warning" if summary["overdue_actions"] else "good"),
        ("Average Risk Score", format_number(float(summary["average_risk_score"])), "Probability × impact", "warning" if float(summary["average_risk_score"]) >= 10 else "primary"),
    )
    for column, (label, value, detail, tone) in zip(cards, values):
        with column:
            metric_card(label, value, detail, tokens, tone)

    _render_insights(governance_insights(summary, data.milestones, risks), tokens)

    if risks.empty:
        empty_state("No risk or issue records match the selected risk filters.")
    else:
        section_heading("Risk exposure and action load")
        left, right = st.columns([1.1, 1])
        with left:
            st.plotly_chart(
                governance_category_chart(risks, tokens),
                use_container_width=True,
                config=CHART_CONFIG,
            )
        with right:
            st.plotly_chart(
                risk_matrix_chart(risks, tokens),
                use_container_width=True,
                config=CHART_CONFIG,
            )

    if not data.milestones.empty:
        st.plotly_chart(
            milestone_delay_chart(data.milestones, tokens),
            use_container_width=True,
            config=CHART_CONFIG,
        )

    if not risks.empty:
        section_heading("Open governance detail")
        detail = risks[
            [
                "RiskIssueID",
                "ProjectID",
                "RecordType",
                "RiskTitle",
                "RiskCategory",
                "RiskSeverity",
                "RiskScore",
                "RiskStatus",
                "MitigationStatus",
                "DueDate",
                "IsOverdue",
            ]
        ].sort_values(["IsOverdue", "RiskScore"], ascending=[False, False])
        st.dataframe(
            detail,
            hide_index=True,
            use_container_width=True,
            column_config={
                "RiskIssueID": "Risk / issue",
                "ProjectID": "Project",
                "RecordType": "Type",
                "RiskTitle": "Title",
                "RiskCategory": "Category",
                "RiskSeverity": "Severity",
                "RiskScore": "Score",
                "RiskStatus": "Status",
                "MitigationStatus": "Mitigation",
                "DueDate": st.column_config.DateColumn("Due date", format="YYYY-MM-DD"),
                "IsOverdue": st.column_config.CheckboxColumn("Overdue"),
            },
        )


def run_dashboard() -> None:
    """Configure and render the Streamlit application."""

    st.set_page_config(
        page_title="HoneyWin Portfolio Analytics",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    tokens = load_theme_tokens()
    apply_app_style(tokens)

    try:
        with st.spinner("Loading audited portfolio data…"):
            data = load_dashboard_data()
    except (DataLoadError, OSError, ValueError) as exc:
        st.error("The audited dataset could not be loaded.")
        st.code(str(exc))
        st.info("Regenerate the data with `python scripts/generate_data.py`, then restart the app.")
        st.stop()

    page = render_navigation()
    selection = render_global_filters(data)
    filtered = apply_global_filters(data, selection)
    page_filters = render_page_filters(page, filtered)

    renderers = {
        "Executive Overview": _render_executive,
        "Financial & Cost": _render_financial,
        "Labor Utilization": _render_labor,
        "Workforce Capacity": _render_workforce,
        "Governance & Risk": _render_governance,
    }
    renderers[page](filtered, selection, page_filters, tokens)
    st.caption(
        f"Synthetic interview/demo dataset · Fixed seed {data.manifest['random_seed']} · "
        f"Data as of {data.manifest['data_as_of_date']} · No external data connection"
    )
    render_signature()
