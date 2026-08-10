"""Business-oriented Plotly charts for the five dashboard experiences."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .style import ThemeTokens


def _layout(
    figure: go.Figure,
    title: str,
    tokens: ThemeTokens,
    *,
    height: int = 390,
    hovermode: str | None = "x unified",
) -> go.Figure:
    figure.update_layout(
        title={"text": title, "x": 0.015, "xanchor": "left", "font": {"size": 16}},
        height=height,
        margin={"l": 24, "r": 20, "t": 58, "b": 30},
        paper_bgcolor=tokens.surface,
        plot_bgcolor=tokens.surface,
        font={"family": "Segoe UI, Arial, sans-serif", "color": tokens.text, "size": 12},
        hovermode=hovermode,
        hoverlabel={"bgcolor": tokens.surface, "font_color": tokens.text},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.01, "x": 0},
    )
    figure.update_xaxes(gridcolor=tokens.grid, linecolor=tokens.border, zerolinecolor=tokens.border)
    figure.update_yaxes(gridcolor=tokens.grid, linecolor=tokens.border, zerolinecolor=tokens.border)
    return figure


def program_financial_chart(
    projects: pd.DataFrame,
    financial: pd.DataFrame,
    financial_all_dates: pd.DataFrame,
    tokens: ThemeTokens,
) -> go.Figure:
    budget = projects.groupby("Program", as_index=False)["ApprovedBudget"].sum()
    actual = financial.groupby("Program", as_index=False)["ActualCostAmount"].sum()
    full = financial_all_dates.groupby("Program", as_index=False).agg(
        FullActual=("ActualCostAmount", "sum"),
        Forecast=("ForecastToComplete", "sum"),
    )
    full["EAC"] = full["FullActual"] + full["Forecast"]
    frame = budget.merge(actual, on="Program", how="left").merge(
        full[["Program", "EAC"]], on="Program", how="left"
    ).fillna(0)
    figure = go.Figure()
    for column, name, color in (
        ("ApprovedBudget", "Approved Budget", tokens.primary),
        ("ActualCostAmount", "Actual Cost", tokens.secondary),
        ("EAC", "EAC", tokens.good),
    ):
        figure.add_bar(
            x=frame["Program"],
            y=frame[column],
            name=name,
            marker_color=color,
            customdata=np.stack([frame[column] / 1_000_000], axis=-1),
            hovertemplate=f"<b>%{{x}}</b><br>{name}: $%{{customdata[0]:,.2f}}M<extra></extra>",
        )
    figure.update_layout(barmode="group")
    figure.update_yaxes(tickprefix="$", tickformat="~s", title="Portfolio value")
    return _layout(figure, "Budget, actual cost, and EAC by program", tokens, height=420)


def project_status_chart(projects: pd.DataFrame, tokens: ThemeTokens) -> go.Figure:
    frame = projects["ProjectStatus"].value_counts().rename_axis("Status").reset_index(name="Projects")
    color_map = {
        "Completed": tokens.good,
        "Active": tokens.primary,
        "At Risk": tokens.warning,
        "Delayed": tokens.bad,
        "On Hold": tokens.muted,
    }
    figure = go.Figure(
        go.Pie(
            labels=frame["Status"],
            values=frame["Projects"],
            hole=0.58,
            marker={"colors": [color_map.get(value, tokens.secondary) for value in frame["Status"]]},
            textinfo="label+value",
            hovertemplate="<b>%{label}</b><br>%{value} projects (%{percent})<extra></extra>",
        )
    )
    figure.update_layout(showlegend=False)
    return _layout(figure, "Project status mix", tokens, height=350, hovermode=None)


def monthly_spend_chart(financial: pd.DataFrame, tokens: ThemeTokens) -> go.Figure:
    frame = financial.groupby("MonthStartDate", as_index=False).agg(
        PhasedBudget=("BudgetAmount", "sum"),
        ActualForecast=("EAC", "sum"),
    )
    figure = go.Figure()
    figure.add_scatter(
        x=frame["MonthStartDate"],
        y=frame["ActualForecast"],
        name="Actual + Forecast Spend",
        mode="lines+markers",
        line={"color": tokens.primary, "width": 2.5},
        marker={"size": 5},
        hovertemplate="$%{y:,.0f}<extra></extra>",
    )
    figure.add_scatter(
        x=frame["MonthStartDate"],
        y=frame["PhasedBudget"],
        name="Phased Budget",
        mode="lines",
        line={"color": tokens.secondary, "width": 2.5},
        hovertemplate="$%{y:,.0f}<extra></extra>",
    )
    figure.update_yaxes(tickprefix="$", tickformat="~s", title="Monthly spend")
    return _layout(figure, "Monthly spend profile versus phased budget", tokens, height=410)


def project_variance_chart(health: pd.DataFrame, tokens: ThemeTokens) -> go.Figure:
    frame = health.sort_values("ForecastVariance").copy()
    frame["Color"] = np.where(frame["ForecastVariance"] < 0, tokens.bad, tokens.good)
    figure = go.Figure(
        go.Bar(
            x=frame["ForecastVariance"],
            y=frame["ProjectID"],
            orientation="h",
            marker_color=frame["Color"],
            customdata=np.stack(
                [frame["ProjectName"], frame["ApprovedBudget"], frame["EAC"]], axis=-1
            ),
            hovertemplate=(
                "<b>%{y} · %{customdata[0]}</b><br>"
                "Forecast variance: $%{x:,.0f}<br>"
                "Approved budget: $%{customdata[1]:,.0f}<br>"
                "EAC: $%{customdata[2]:,.0f}<extra></extra>"
            ),
        )
    )
    figure.add_vline(x=0, line_color=tokens.muted, line_width=1)
    figure.update_xaxes(tickprefix="$", tickformat="~s", title="Unfavorable ← variance → favorable")
    return _layout(figure, "Forecast variance by project", tokens, height=520, hovermode="y")


def cost_category_chart(financial: pd.DataFrame, tokens: ThemeTokens) -> go.Figure:
    frame = financial.groupby("CostCategory", as_index=False).agg(
        Budget=("BudgetAmount", "sum"),
        Actual=("ActualCostAmount", "sum"),
        Committed=("CommittedCost", "sum"),
    )
    figure = go.Figure()
    for column, color in (
        ("Budget", tokens.primary),
        ("Actual", tokens.secondary),
        ("Committed", tokens.warning),
    ):
        figure.add_bar(
            x=frame["CostCategory"],
            y=frame[column],
            name=column,
            marker_color=color,
            hovertemplate=f"<b>%{{x}}</b><br>{column}: $%{{y:,.0f}}<extra></extra>",
        )
    figure.update_layout(barmode="group")
    figure.update_yaxes(tickprefix="$", tickformat="~s", title="Cost")
    return _layout(figure, "Cost composition by category", tokens, height=410, hovermode="x")


def labor_trend_chart(labor: pd.DataFrame, tokens: ThemeTokens) -> go.Figure:
    source = labor.assign(
        Month=labor["WeekStartDate"].dt.to_period("M").dt.to_timestamp(),
        TargetHours=labor["AvailableHours"] * labor["UtilizationTarget"],
    )
    frame = source.groupby("Month", as_index=False).agg(
        ProjectHours=("ProjectHours", "sum"),
        AvailableHours=("AvailableHours", "sum"),
        TargetHours=("TargetHours", "sum"),
    )
    frame["Utilization"] = frame["ProjectHours"] / frame["AvailableHours"]
    frame["Target"] = frame["TargetHours"] / frame["AvailableHours"]
    frame["ToleranceFloor"] = frame["Target"] - 0.05

    figure = go.Figure()
    figure.add_scatter(
        x=frame["Month"],
        y=frame["ToleranceFloor"],
        name="Target - 5 pp",
        mode="lines",
        line={"color": "rgba(255,185,0,0)", "width": 0},
        showlegend=False,
        hoverinfo="skip",
    )
    figure.add_scatter(
        x=frame["Month"],
        y=frame["Target"],
        name="Weighted Target",
        mode="lines",
        line={"color": tokens.secondary, "width": 2},
        fill="tonexty",
        fillcolor="rgba(255,185,0,0.16)",
        hovertemplate="%{y:.1%}<extra></extra>",
    )
    figure.add_scatter(
        x=frame["Month"],
        y=frame["Utilization"],
        name="Labor Utilization",
        mode="lines+markers",
        line={"color": tokens.primary, "width": 2.6},
        marker={"size": 5},
        hovertemplate="%{y:.1%}<extra></extra>",
    )
    figure.update_yaxes(tickformat=".0%", title="Utilization")
    return _layout(
        figure,
        "Monthly utilization versus weighted target (amber band = within 5 pp below target)",
        tokens,
        height=420,
    )


def team_utilization_chart(labor: pd.DataFrame, tokens: ThemeTokens) -> go.Figure:
    source = labor.assign(TargetHours=labor["AvailableHours"] * labor["UtilizationTarget"])
    frame = source.groupby("TeamName", as_index=False).agg(
        ProjectHours=("ProjectHours", "sum"),
        AvailableHours=("AvailableHours", "sum"),
        TargetHours=("TargetHours", "sum"),
    )
    frame["Utilization"] = frame["ProjectHours"] / frame["AvailableHours"]
    frame["Target"] = frame["TargetHours"] / frame["AvailableHours"]
    frame["Gap"] = frame["Utilization"] - frame["Target"]
    frame = frame.sort_values("Gap")
    colors = np.where(frame["Gap"] < -0.12, tokens.bad, np.where(frame["Gap"] < -0.05, tokens.warning, tokens.good))
    figure = go.Figure(
        go.Bar(
            x=frame["Gap"],
            y=frame["TeamName"],
            orientation="h",
            marker_color=colors,
            customdata=np.stack([frame["Utilization"], frame["Target"]], axis=-1),
            hovertemplate=(
                "<b>%{y}</b><br>Gap: %{x:+.1%}<br>"
                "Utilization: %{customdata[0]:.1%}<br>Target: %{customdata[1]:.1%}<extra></extra>"
            ),
        )
    )
    figure.add_vline(x=0, line_color=tokens.muted, line_width=1)
    figure.update_xaxes(tickformat="+.0%", title="Utilization gap")
    return _layout(figure, "Utilization gap by team", tokens, height=410, hovermode="y")


def overtime_trend_chart(labor: pd.DataFrame, tokens: ThemeTokens) -> go.Figure:
    frame = (
        labor.assign(Month=labor["WeekStartDate"].dt.to_period("M").dt.to_timestamp())
        .groupby("Month", as_index=False)["OvertimeHours"]
        .sum()
    )
    figure = go.Figure(
        go.Bar(
            x=frame["Month"],
            y=frame["OvertimeHours"],
            marker_color=tokens.purple,
            hovertemplate="%{y:,.1f} hours<extra></extra>",
        )
    )
    figure.update_yaxes(title="Overtime hours")
    return _layout(figure, "Monthly overtime load", tokens, height=350)


def workforce_trend_chart(workforce: pd.DataFrame, tokens: ThemeTokens) -> go.Figure:
    frame = workforce.groupby("MonthStartDate", as_index=False).agg(
        ActualFTE=("ActualFTE", "sum"), RequiredFTE=("RequiredFTE", "sum")
    )
    frame["Gap"] = frame["ActualFTE"] - frame["RequiredFTE"]
    figure = go.Figure()
    figure.add_scatter(
        x=frame["MonthStartDate"],
        y=frame["RequiredFTE"],
        name="Required FTE",
        mode="lines",
        line={"color": tokens.secondary, "width": 2.5},
        hovertemplate="%{y:,.1f} FTE<extra></extra>",
    )
    figure.add_scatter(
        x=frame["MonthStartDate"],
        y=frame["ActualFTE"],
        name="Actual FTE",
        mode="lines+markers",
        line={"color": tokens.primary, "width": 2.5},
        marker={"size": 5},
        fill="tonexty",
        fillcolor="rgba(0,120,212,0.09)",
        customdata=frame[["Gap"]],
        hovertemplate="%{y:,.1f} FTE<br>Gap: %{customdata[0]:+.1f}<extra></extra>",
    )
    figure.update_yaxes(title="Monthly FTE")
    return _layout(figure, "Actual versus required workforce capacity", tokens, height=420)


def workforce_gap_chart(workforce: pd.DataFrame, tokens: ThemeTokens) -> go.Figure:
    monthly = workforce.groupby(["MonthStartDate", "SkillName"], as_index=False).agg(
        ActualFTE=("ActualFTE", "sum"), RequiredFTE=("RequiredFTE", "sum")
    )
    frame = monthly.groupby("SkillName", as_index=False)[["ActualFTE", "RequiredFTE"]].mean()
    frame["Gap"] = frame["ActualFTE"] - frame["RequiredFTE"]
    frame = frame.sort_values("Gap")
    colors = np.where(frame["Gap"] < 0, tokens.bad, tokens.good)
    figure = go.Figure(
        go.Bar(
            x=frame["Gap"],
            y=frame["SkillName"],
            orientation="h",
            marker_color=colors,
            customdata=np.stack([frame["ActualFTE"], frame["RequiredFTE"]], axis=-1),
            hovertemplate=(
                "<b>%{y}</b><br>Average gap: %{x:+.1f} FTE<br>"
                "Actual: %{customdata[0]:.1f}<br>Required: %{customdata[1]:.1f}<extra></extra>"
            ),
        )
    )
    figure.add_vline(x=0, line_color=tokens.muted, line_width=1)
    figure.update_xaxes(title="Average monthly capacity gap FTE")
    return _layout(figure, "Capacity gap by skill", tokens, height=410, hovermode="y")


def workforce_heatmap(workforce: pd.DataFrame, tokens: ThemeTokens) -> go.Figure:
    monthly = workforce.groupby(["MonthStartDate", "Location", "SkillName"], as_index=False).agg(
        Gap=("CapacityGapFTE", "sum")
    )
    frame = monthly.groupby(["Location", "SkillName"], as_index=False)["Gap"].mean()
    pivot = frame.pivot(index="Location", columns="SkillName", values="Gap").fillna(0)
    figure = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale=[[0, tokens.bad], [0.5, "#FFFFFF"], [1, tokens.good]],
            zmid=0,
            colorbar={"title": "Gap FTE"},
            hovertemplate="<b>%{y} · %{x}</b><br>Average gap: %{z:+.2f} FTE<extra></extra>",
        )
    )
    return _layout(figure, "Capacity gap by skill and location", tokens, height=390, hovermode=None)


def governance_category_chart(risks: pd.DataFrame, tokens: ThemeTokens) -> go.Figure:
    source = risks.assign(
        OpenCritical=(
            (risks["IsCritical"] == 1) & risks["RiskStatus"].isin(["Open", "Monitoring"])
        ).astype(int),
        Overdue=(risks["IsOverdue"] == 1).astype(int),
    )
    frame = source.groupby("RiskCategory", as_index=False).agg(
        OpenCritical=("OpenCritical", "sum"), Overdue=("Overdue", "sum")
    )
    figure = go.Figure()
    figure.add_bar(
        x=frame["OpenCritical"],
        y=frame["RiskCategory"],
        name="Open Critical Risks",
        orientation="h",
        marker_color=tokens.bad,
        hovertemplate="%{x} open critical<extra></extra>",
    )
    figure.add_bar(
        x=frame["Overdue"],
        y=frame["RiskCategory"],
        name="Overdue Actions",
        orientation="h",
        marker_color=tokens.warning,
        hovertemplate="%{x} overdue<extra></extra>",
    )
    figure.update_layout(barmode="group")
    figure.update_xaxes(dtick=1, title="Exception count")
    return _layout(figure, "Open critical risks and overdue actions by category", tokens, height=420, hovermode="y")


def risk_matrix_chart(risks: pd.DataFrame, tokens: ThemeTokens) -> go.Figure:
    size = np.maximum(risks["RiskScore"].astype(float), 2)
    color_map = {
        "Low": tokens.good,
        "Medium": tokens.primary,
        "High": tokens.warning,
        "Critical": tokens.bad,
    }
    figure = px.scatter(
        risks,
        x="Probability",
        y="Impact",
        size=size,
        color="RiskSeverity",
        color_discrete_map=color_map,
        hover_name="RiskTitle",
        hover_data={
            "ProjectID": True,
            "RiskCategory": True,
            "RiskStatus": True,
            "RiskScore": True,
            "Probability": True,
            "Impact": True,
        },
        size_max=28,
    )
    figure.update_xaxes(range=[0.5, 5.5], dtick=1, title="Probability")
    figure.update_yaxes(range=[0.5, 5.5], dtick=1, title="Impact")
    figure = _layout(
        figure, "Risk probability-impact matrix", tokens, height=430, hovermode="closest"
    )
    figure.update_layout(
        legend={"orientation": "v", "yanchor": "top", "y": 0.98, "x": 1.01},
        margin={"l": 24, "r": 92, "t": 58, "b": 30},
    )
    return figure


def milestone_delay_chart(milestones: pd.DataFrame, tokens: ThemeTokens) -> go.Figure:
    frame = milestones.groupby(["ProjectID", "ProjectName"], as_index=False).agg(
        MaxVariance=("ScheduleVarianceDays", "max"),
        AverageVariance=("ScheduleVarianceDays", "mean"),
    )
    frame = frame.sort_values("MaxVariance").tail(15)
    colors = np.where(frame["MaxVariance"] > 30, tokens.bad, np.where(frame["MaxVariance"] >= 8, tokens.warning, tokens.good))
    figure = go.Figure(
        go.Bar(
            x=frame["MaxVariance"],
            y=frame["ProjectID"],
            orientation="h",
            marker_color=colors,
            customdata=np.stack([frame["ProjectName"], frame["AverageVariance"]], axis=-1),
            hovertemplate=(
                "<b>%{y} · %{customdata[0]}</b><br>Max variance: %{x:.0f} days<br>"
                "Average variance: %{customdata[1]:.1f} days<extra></extra>"
            ),
        )
    )
    figure.add_vline(x=0, line_color=tokens.muted, line_width=1)
    figure.update_xaxes(title="Maximum milestone schedule variance (days)")
    return _layout(figure, "Projects with the largest milestone delay", tokens, height=430, hovermode="y")
