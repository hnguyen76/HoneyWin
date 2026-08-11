"""Microsoft Fluent-inspired theme tokens and Streamlit presentation helpers."""

from __future__ import annotations

import html
import json
import math
from dataclasses import dataclass
from pathlib import Path

import streamlit as st

from .data import PROJECT_ROOT


@dataclass(frozen=True)
class ThemeTokens:
    primary: str
    secondary: str
    good: str
    warning: str
    bad: str
    purple: str
    background: str
    surface: str
    text: str
    muted: str
    border: str
    grid: str


@st.cache_resource
def load_theme_tokens() -> ThemeTokens:
    """Reuse the committed Power BI theme palette."""

    path = PROJECT_ROOT / "powerbi" / "HoneyWin_Microsoft_Fluent.json"
    theme = json.loads(path.read_text(encoding="utf-8"))
    colors = theme["dataColors"]
    return ThemeTokens(
        primary=colors[0],
        secondary=colors[1],
        good=theme["good"],
        warning=theme["neutral"],
        bad=theme["bad"],
        purple=colors[5],
        background="#F5F7FA",
        surface=theme["background"],
        text=theme["foreground"],
        muted="#605E5C",
        border="#E1DFDD",
        grid="#EDEBE9",
    )


def apply_app_style(tokens: ThemeTokens) -> None:
    """Apply responsive Fluent styling to Streamlit components."""

    st.markdown(
        f"""
        <style>
        :root {{
            --hw-primary: {tokens.primary};
            --hw-secondary: {tokens.secondary};
            --hw-good: {tokens.good};
            --hw-warning: {tokens.warning};
            --hw-bad: {tokens.bad};
            --hw-bg: {tokens.background};
            --hw-surface: {tokens.surface};
            --hw-text: {tokens.text};
            --hw-muted: {tokens.muted};
            --hw-border: {tokens.border};
        }}
        html, body, [class*="css"] {{
            font-family: "Segoe UI", Arial, sans-serif;
            color: var(--hw-text);
        }}
        .stApp {{ background: var(--hw-bg); }}
        .block-container {{
            max-width: 1480px;
            padding-top: 1.35rem;
            padding-bottom: 3rem;
        }}
        section[data-testid="stSidebar"] {{
            background: var(--hw-surface);
            border-right: 1px solid var(--hw-border);
        }}
        .brand-mark {{
            color: var(--hw-primary);
            font-size: 1.05rem;
            font-weight: 700;
            letter-spacing: .11em;
            margin-top: .25rem;
        }}
        .page-header {{
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: .85rem;
        }}
        .page-eyebrow {{
            color: var(--hw-primary);
            font-size: .74rem;
            font-weight: 700;
            letter-spacing: .09em;
            text-transform: uppercase;
            margin-bottom: .25rem;
        }}
        .page-title {{
            color: var(--hw-text);
            font-size: 2rem;
            font-weight: 650;
            line-height: 1.15;
            margin: 0;
        }}
        .page-subtitle {{
            color: var(--hw-muted);
            font-size: .92rem;
            margin-top: .35rem;
        }}
        .context-badge {{
            background: #EAF3FB;
            border: 1px solid #C7E0F4;
            border-radius: 999px;
            color: #005A9E;
            font-size: .76rem;
            font-weight: 600;
            padding: .4rem .75rem;
            white-space: nowrap;
        }}
        .benchmark-strip {{
            align-items: stretch;
            background: linear-gradient(100deg, #FFFFFF 0%, #F0F7FC 100%);
            border: 1px solid #C7E0F4;
            border-left: 4px solid var(--hw-primary);
            border-radius: 6px;
            display: grid;
            gap: 0;
            grid-template-columns: 1.45fr repeat(4, minmax(120px, 1fr));
            margin: .2rem 0 1rem;
            overflow: hidden;
        }}
        .benchmark-intro, .benchmark-item {{
            padding: .72rem .9rem;
        }}
        .benchmark-item {{
            border-left: 1px solid #DDEBF5;
        }}
        .benchmark-eyebrow, .benchmark-label {{
            color: var(--hw-primary);
            font-size: .66rem;
            font-weight: 700;
            letter-spacing: .06em;
            text-transform: uppercase;
        }}
        .benchmark-title {{
            color: var(--hw-text);
            font-size: .88rem;
            font-weight: 650;
            line-height: 1.25;
            margin-top: .16rem;
        }}
        .benchmark-value {{
            color: var(--hw-text);
            font-size: 1.03rem;
            font-weight: 650;
            margin-top: .12rem;
        }}
        .benchmark-note {{
            color: var(--hw-muted);
            font-size: .66rem;
            line-height: 1.3;
            margin-top: .12rem;
        }}
        .metric-card {{
            background: var(--hw-surface);
            border: 1px solid var(--hw-border);
            border-top: 3px solid var(--metric-color, var(--hw-primary));
            border-radius: 6px;
            box-shadow: 0 1px 2px rgba(0,0,0,.04);
            min-height: 118px;
            padding: .85rem .95rem .75rem;
        }}
        .metric-label {{
            color: var(--hw-muted);
            font-size: .78rem;
            font-weight: 600;
            line-height: 1.25;
            min-height: 1.9rem;
        }}
        .metric-value {{
            color: var(--hw-text);
            font-size: 1.72rem;
            font-weight: 650;
            letter-spacing: -.02em;
            line-height: 1.15;
            margin-top: .2rem;
        }}
        .metric-detail {{
            color: var(--metric-color, var(--hw-muted));
            font-size: .73rem;
            font-weight: 600;
            margin-top: .35rem;
        }}
        div[data-testid="stPlotlyChart"], div[data-testid="stDataFrame"] {{
            background: var(--hw-surface);
            border: 1px solid var(--hw-border);
            border-radius: 6px;
            box-shadow: 0 1px 2px rgba(0,0,0,.03);
            overflow: hidden;
        }}
        div[data-testid="stPlotlyChart"] {{ padding: .25rem .35rem; }}
        .section-heading {{
            color: var(--hw-text);
            font-size: 1.03rem;
            font-weight: 650;
            margin: 1.15rem 0 .55rem;
        }}
        .insight-card {{
            --insight-color: var(--hw-primary);
            background: var(--hw-surface);
            border: 1px solid var(--hw-border);
            border-left: 4px solid var(--insight-color);
            border-radius: 6px;
            box-shadow: 0 1px 2px rgba(0,0,0,.04);
            height: 100%;
            min-height: 224px;
            padding: .9rem 1rem;
        }}
        .insight-label, .action-label {{
            color: var(--insight-color);
            font-size: .68rem;
            font-weight: 700;
            letter-spacing: .08em;
            text-transform: uppercase;
        }}
        .insight-title {{
            color: var(--hw-text);
            font-size: .98rem;
            font-weight: 650;
            line-height: 1.3;
            margin: .25rem 0 .45rem;
        }}
        .insight-evidence, .insight-action {{
            color: var(--hw-muted);
            font-size: .79rem;
            line-height: 1.45;
        }}
        .insight-divider {{
            border-top: 1px solid var(--hw-border);
            margin: .7rem 0 .6rem;
        }}
        .insight-context {{
            color: var(--hw-muted);
            font-size: .73rem;
            margin: -.25rem 0 .55rem;
        }}
        .empty-state {{
            background: var(--hw-surface);
            border: 1px dashed #A19F9D;
            border-radius: 6px;
            color: var(--hw-muted);
            padding: 2.2rem;
            text-align: center;
        }}
        .dashboard-signature {{
            border-top: 1px solid var(--hw-border);
            color: var(--hw-muted);
            font-size: .76rem;
            font-weight: 600;
            letter-spacing: .02em;
            margin-top: 1.2rem;
            padding-top: .7rem;
            text-align: right;
        }}
        header[data-testid="stHeader"], footer {{ display: none; }}
        @media (max-width: 900px) {{
            .page-header {{ align-items: flex-start; flex-direction: column; }}
            .context-badge {{ white-space: normal; }}
            .benchmark-strip {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
            .benchmark-intro {{ grid-column: 1 / -1; }}
            .benchmark-item:nth-child(even) {{ border-left: none; }}
            .metric-card {{ min-height: 104px; }}
            div[data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; }}
            div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {{
                flex: 1 1 180px !important;
                min-width: 180px !important;
                width: auto !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str, context: str) -> None:
    """Render a consistent page heading and filter-context badge."""

    st.markdown(
        f"""
        <div class="page-header">
          <div>
            <div class="page-eyebrow">FORGE RDE / PMO</div>
            <h1 class="page-title">{html.escape(title)}</h1>
            <div class="page-subtitle">{html.escape(subtitle)}</div>
          </div>
          <div class="context-badge">{html.escape(context)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def benchmark_strip(benchmark: dict[str, object]) -> None:
    """Render the public Honeywell benchmark used to calibrate portfolio scale."""

    if not benchmark:
        return

    def billions(key: str) -> str:
        value = float(benchmark.get(key, 0) or 0)
        return f"${value / 1_000_000_000:.2f}B"

    period_end = str(benchmark.get("period_end", ""))
    period_label = f"TTM ending {period_end}" if period_end else "Trailing 12 months"
    values = (
        ("Net sales", billions("net_sales_usd"), "Public consolidated benchmark"),
        (
            "Product / service cost",
            billions("cost_of_products_and_services_usd"),
            "Public consolidated benchmark",
        ),
        ("Total R&D cost", billions("total_rd_cost_usd"), "Portfolio calibration basis"),
        (
            "Synthetic budget",
            billions("target_portfolio_approved_budget_usd"),
            "Reconciles to the R&D benchmark",
        ),
    )
    items = "".join(
        f"""
        <div class="benchmark-item">
          <div class="benchmark-label">{html.escape(label)}</div>
          <div class="benchmark-value">{html.escape(value)}</div>
          <div class="benchmark-note">{html.escape(note)}</div>
        </div>
        """
        for label, value, note in values
    )
    st.markdown(
        f"""
        <div class="benchmark-strip">
          <div class="benchmark-intro">
            <div class="benchmark-eyebrow">Public filing calibration</div>
            <div class="benchmark-title">Honeywell consolidated {html.escape(period_label)}</div>
            <div class="benchmark-note">Benchmark metadata only; project records remain synthetic.</div>
          </div>
          {items}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _tone_color(tokens: ThemeTokens, tone: str) -> str:
    return {
        "good": tokens.good,
        "warning": tokens.warning,
        "bad": tokens.bad,
        "neutral": tokens.muted,
        "primary": tokens.primary,
        "secondary": tokens.secondary,
    }.get(tone, tokens.primary)


def metric_card(
    label: str,
    value: str,
    detail: str,
    tokens: ThemeTokens,
    tone: str = "primary",
    tooltip: str | None = None,
) -> None:
    """Render an accessible KPI card with a conditional Fluent accent."""

    title = html.escape(tooltip or f"{label}: {value}. {detail}")
    st.markdown(
        f"""
        <div class="metric-card" style="--metric-color:{_tone_color(tokens, tone)}" title="{title}">
          <div class="metric-label">{html.escape(label)}</div>
          <div class="metric-value">{html.escape(value)}</div>
          <div class="metric-detail">{html.escape(detail)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(message: str) -> None:
    """Render a clear empty state for a filter combination with no records."""

    st.markdown(
        f'<div class="empty-state">{html.escape(message)}</div>',
        unsafe_allow_html=True,
    )


def section_heading(title: str) -> None:
    st.markdown(f'<div class="section-heading">{html.escape(title)}</div>', unsafe_allow_html=True)


def render_signature() -> None:
    """Render the dashboard creator signature consistently across all pages."""

    st.markdown(
        '<div class="dashboard-signature">Created by Hieu Nguyen</div>',
        unsafe_allow_html=True,
    )


def insight_card(
    title: str,
    evidence: str,
    action: str,
    tokens: ThemeTokens,
    tone: str = "primary",
) -> None:
    """Render a supported business insight with its recommended corrective action."""

    st.markdown(
        f"""
        <div class="insight-card" style="--insight-color:{_tone_color(tokens, tone)}">
          <div class="insight-label">Business insight</div>
          <div class="insight-title">{html.escape(title)}</div>
          <div class="insight-evidence">{html.escape(evidence)}</div>
          <div class="insight-divider"></div>
          <div class="action-label">Corrective action</div>
          <div class="insight-action">{html.escape(action)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_currency(value: float, decimals: int = 1) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    absolute = abs(value)
    sign = "-" if value < 0 else ""
    if absolute >= 1_000_000:
        return f"{sign}${absolute / 1_000_000:,.{decimals}f}M"
    if absolute >= 1_000:
        return f"{sign}${absolute / 1_000:,.{decimals}f}K"
    return f"{sign}${absolute:,.0f}"


def format_number(value: float, decimals: int = 1) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    if abs(value) >= 1_000:
        return f"{value / 1_000:,.{decimals}f}K"
    return f"{value:,.{decimals}f}"


def format_percent(value: float, decimals: int = 1) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    return f"{value:.{decimals}%}"


def format_pp(value: float, decimals: int = 1) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    return f"{value * 100:+.{decimals}f} pp"
