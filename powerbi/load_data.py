"""Power BI Python connector script for the generated FORGE dataset."""

from pathlib import Path

import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "generated"


def read_table(name: str, date_columns: list[str] | None = None) -> pd.DataFrame:
    """Read one generated CSV with explicit date parsing."""
    return pd.read_csv(DATA_DIR / f"{name}.csv", parse_dates=date_columns or [])


DimDate = read_table(
    "DimDate",
    ["Date", "WeekStartDate", "WeekEndDate", "MonthStartDate"],
)
DimProject = read_table(
    "DimProject",
    ["StartDate", "PlannedEndDate", "ForecastEndDate", "ActualEndDate"],
)
DimEmployee = read_table("DimEmployee", ["HireDate", "ExitDate"])
DimTeam = read_table("DimTeam")
DimSkill = read_table("DimSkill")
BridgeEmployeeSkill = read_table(
    "BridgeEmployeeSkill",
    ["EffectiveDate", "ExpirationDate"],
)

FactLabor = read_table("FactLabor", ["SubmissionDate"])
FactLabor.dropna(subset=["ProjectHours", "ActualLaborCost"], inplace=True)
FactLabor.sort_values("LaborRecordID", inplace=True)
FactLabor.drop_duplicates(
    subset=["EmployeeKey", "ProjectKey", "WeekStartDateKey"],
    keep="first",
    inplace=True,
)
FactLabor.reset_index(drop=True, inplace=True)

FactFinancial = read_table("FactFinancial")
FactMilestone = read_table(
    "FactMilestone",
    ["PlannedDate", "ForecastDate", "ActualDate", "LastUpdatedDate"],
)
FactWorkforcePlan = read_table("FactWorkforcePlan")
FactRiskIssue = read_table(
    "FactRiskIssue",
    ["IdentifiedDate", "DueDate", "ClosedDate"],
)
