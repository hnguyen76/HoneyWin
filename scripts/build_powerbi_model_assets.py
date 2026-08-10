"""Build repeatable Power BI semantic-model assets from the canonical DAX file.

The generated JSON is consumed by ``apply_powerbi_model.ps1`` to update the
semantic model currently open in Power BI Desktop.  A TMDL version is emitted
as a portable, human-reviewable equivalent.
"""

from __future__ import annotations

import json
import re
import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DAX_PATH = ROOT / "powerbi" / "measures.dax"
JSON_PATH = ROOT / "powerbi" / "measures.generated.json"
TMDL_PATH = ROOT / "powerbi" / "measures.generated.tmdl"
COLUMN_TYPES_PATH = ROOT / "powerbi" / "column_types.generated.json"
NULLABLE_RAW_COLUMNS = {
    ("DimEmployee", "ExitDate"),
    ("BridgeEmployeeSkill", "ExpirationDate"),
    ("FactMilestone", "ActualDateKey"),
    ("FactMilestone", "ActualDate"),
    ("FactRiskIssue", "ClosedDateKey"),
    ("FactRiskIssue", "ClosedDate"),
}

SECTION_FOLDERS = {
    "Financial & Project Cost": "01 Financial & Project Cost",
    "Labor Utilization": "02 Labor Utilization",
    "Workforce / Capacity Planning": "03 Workforce & Capacity",
    "Governance, Schedule & Risk": "04 Governance & Performance",
}

CURRENCY = {
    "Approved Budget", "Baseline Budget", "Phased Budget", "Actual Cost",
    "Actual Labor Cost", "Actual Material Cost", "Actual Other Cost",
    "Committed Cost", "Forecast to Complete", "EAC", "Forecast Variance $",
    "Earned Value (Mock)", "Monthly Actual + Forecast Spend",
    "Labor Cost Reconciliation $", "Labor Cost Variance $",
}
PERCENT = {
    "Forecast Variance %", "Budget Consumed %", "Project Completion %",
    "Budget vs Completion Gap pp", "Labor Cost Variance %",
    "Labor Utilization %", "Weighted Utilization Target %", "Utilization Gap pp",
    "Non-Project / Bench %", "Overtime % of Project Hours",
    "Contractor Project Hours %", "Time-entry Compliance %", "Contractor FTE %",
    "Demand Coverage %", "On-Time Milestone %",
}
INTEGER = {
    "Time Entries", "Late Time Entries", "Total Projects", "Active Projects",
    "Projects At Risk", "Milestones", "On-Time Milestones",
    "Max Critical Milestone Delay Days", "Open Critical Risks",
    "Critical Risks without Mitigation", "Overdue Actions", "Red Projects",
    "Amber Projects", "Green Projects", "Projects with Budget-Consumption Red Flag",
    "Projects with Any Red Flag",
}
HOURS = {
    "Available Hours", "Project Hours", "Non-Project Hours", "Overtime Hours",
    "PTO Hours", "Contractor Project Hours", "Available Capacity Hours",
    "Required Capacity Hours", "Capacity Gap Hours",
}
TEXT = {
    "Employee Utilization Band", "Cost Health", "Schedule Health", "Labor Health",
    "Risk Health", "Overall Project Health",
}


def format_string(name: str) -> str:
    if name in CURRENCY:
        return "$#,##0;($#,##0)"
    if name in PERCENT:
        return "0.0%;(0.0%)"
    if name in INTEGER:
        return "#,##0"
    if name in HOURS:
        return "#,##0.0;(#,##0.0)"
    if name in TEXT:
        return ""
    if name == "Cost Performance Index (Mock)":
        return "0.00x"
    return "#,##0.0;(#,##0.0)"


def parse_measures(text: str) -> list[dict[str, str]]:
    current_folder = "00 General"
    measures: list[dict[str, str]] = []
    current: dict[str, object] | None = None
    header_re = re.compile(r"^([^/].*?)\s*=\s*$")

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("//"):
            section = stripped.removeprefix("//").strip()
            if section in SECTION_FOLDERS:
                current_folder = SECTION_FOLDERS[section]
            continue

        match = header_re.match(line)
        token = match.group(1).strip().upper() if match else ""
        is_keyword = token == "RETURN" or token.startswith("VAR ")
        if match and not is_keyword and not line.startswith((" ", "\t")):
            if current:
                current["expression"] = "\n".join(current.pop("lines")).strip()
                measures.append(current)  # type: ignore[arg-type]
            name = match.group(1).strip()
            current = {
                "name": name,
                "displayFolder": current_folder,
                "formatString": format_string(name),
                "lines": [],
            }
        elif current is not None:
            current["lines"].append(line)  # type: ignore[union-attr]

    if current:
        current["expression"] = "\n".join(current.pop("lines")).strip()
        measures.append(current)  # type: ignore[arg-type]

    return measures


def tmdl_quote(name: str) -> str:
    return "'" + name.replace("'", "''") + "'"


def build_tmdl(measures: list[dict[str, str]]) -> str:
    lines = ["createOrReplace", "", "\tref table DimProject"]
    for measure in measures:
        lines.extend(["", f"\t\tmeasure {tmdl_quote(measure['name'])} ="])
        expression_lines = measure["expression"].splitlines()
        lines.extend(f"\t\t\t{line}" if line else "" for line in expression_lines)
        if measure["formatString"]:
            lines.append(f"\t\t\tformatString: {measure['formatString']}")
        lines.append(f"\t\t\tdisplayFolder: {measure['displayFolder']}")
    return "\n".join(lines) + "\n"


def build_column_types() -> dict[str, dict[str, str]]:
    namespace = runpy.run_path(str(ROOT / "powerbi" / "load_data.py"))
    table_names = [
        "DimDate", "DimProject", "DimEmployee", "DimTeam", "DimSkill",
        "BridgeEmployeeSkill", "FactFinancial", "FactLabor", "FactMilestone",
        "FactRiskIssue", "FactWorkforcePlan",
    ]
    result: dict[str, dict[str, str]] = {}
    for table_name in table_names:
        frame = namespace[table_name]
        result[table_name] = {}
        for column_name, dtype in frame.dtypes.items():
            dtype_text = str(dtype)
            if "datetime" in dtype_text:
                target_type = "DateTime"
            elif column_name.endswith("Key") or dtype_text.startswith("int"):
                target_type = "Int64"
            elif dtype_text.startswith("float"):
                target_type = "Double"
            elif dtype_text.startswith("bool"):
                target_type = "Boolean"
            else:
                target_type = "String"
            # Project-specific overrides can remain here if a connector ever
            # emits a nullable field with an unusable inferred storage type.
            if (table_name, column_name) in NULLABLE_RAW_COLUMNS:
                target_type = "String"
            result[table_name][column_name] = target_type
    return result


def main() -> None:
    measures = parse_measures(DAX_PATH.read_text(encoding="utf-8"))
    if len(measures) != 70:
        raise RuntimeError(f"Expected 70 measures, parsed {len(measures)}")
    JSON_PATH.write_text(json.dumps(measures, ensure_ascii=False, indent=2), encoding="utf-8")
    TMDL_PATH.write_text(build_tmdl(measures), encoding="utf-8")
    COLUMN_TYPES_PATH.write_text(
        json.dumps(build_column_types(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Generated {len(measures)} measures")
    print(JSON_PATH)
    print(TMDL_PATH)
    print(COLUMN_TYPES_PATH)


if __name__ == "__main__":
    main()
