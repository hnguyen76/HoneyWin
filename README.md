# FORGE RDE/PMO synthetic Power BI dataset

Bộ deliverable này được xây trực tiếp từ source context
`honeywell_forge_interview_context.md` (SHA-256 được ghi trong source traceability).
Đây là mock data cho portfolio/phỏng vấn, không phải dữ liệu nội bộ Honeywell.

## Kết quả mặc định

- 24 tháng: 2024-01-01 đến 2025-12-31; data as-of 2025-06-30.
- 25 FORGE-style RDE projects.
- 120 employees/contractors.
- 8,172 raw labor records; 8,145 records sau reject + deduplicate.
- 11 linked CSV tables, UTF-8 và Power BI-ready.
- Fixed random seed `20250810` và SHA-256 manifest.
- 7 controlled business anomalies có cross-table root-cause evidence.
- QA result: `PASS_WITH_EXPECTED_ANOMALIES`, 50 passed checks, 4 expected warnings, 0 unexpected failures.
- DAX catalog cho Financial, Labor, Workforce và Governance/Health.

## Cấu trúc chính

```text
config/default.json                 Default scope và fixed seed
docs/data_specification.md          Grain, keys, rules, sign conventions, anomalies
docs/data_dictionary.md             Dictionary cho toàn bộ columns của 11 tables
docs/source_traceability.md         Mapping từ source Markdown đến deliverables
scripts/generate_data.py            Reproducible standard-library generator
scripts/validate_data.py            QA, reconciliation và anomaly validation
scripts/audit_realism.py            Cardinality, outlier, realism, rule và correlation audit
data/generated/*.csv                11 generated tables
data/generated/manifest.json        Row counts và SHA-256 checksums
quality/data_quality_report.md       Human-readable QA report
quality/data_quality_results.csv     54 machine-readable checks
quality/anomaly_evidence.csv         Signal/root cause/recommendation/impact
quality/labor_exceptions.csv         Duplicate, missing và late-entry drill list
quality/full_realism_optimization_report.md  Full before/after implementation audit
powerbi/FactLabor_Clean.pq           Power Query reject + deduplicate logic
powerbi/model_setup.md               Import, types và relationship instructions
powerbi/measures.dax                 DAX measure definitions
powerbi/measure_catalog.md           Definition, format, sign convention, page mapping
scripts/audit_powerbi_live.ps1       Live model/relationship + 70-measure smoke test
scripts/optimize_powerbi_report.ps1  Reproducible report visual construction pass
tests/test_pipeline.py               Reproducibility và acceptance tests
requirements.txt                     Pinned audit/test/Power BI Python dependencies
```

## Rebuild và kiểm tra

Yêu cầu Python 3.11+. Generator và validator chỉ dùng standard library; realism
audit, tests và Power BI Python loader dùng các package được pin trong
`requirements.txt`.

```powershell
python -m pip install -r requirements.txt
python scripts\generate_data.py
python scripts\validate_data.py
python scripts\audit_realism.py --label final
python -m pytest -q
```

Chạy lại với cùng `config/default.json` phải tạo byte-identical CSV. Test so sánh toàn bộ file bytes và SHA-256 giữa hai fresh output directories, đồng thời so với manifest đang commit.

## 11 CSV tables

| Table | Rows | Grain |
|---|---:|---|
| `DimDate` | 731 | Date |
| `DimProject` | 25 | Project |
| `DimEmployee` | 120 | Employee/contractor |
| `DimTeam` | 8 | Engineering team |
| `DimSkill` | 8 | Skill |
| `BridgeEmployeeSkill` | 216 | Employee–skill |
| `FactLabor` | 8,172 | Employee–project–week |
| `FactFinancial` | 1,180 | Project–month–cost category |
| `FactMilestone` | 201 | Project–milestone |
| `FactWorkforcePlan` | 768 | Month–team–skill–location |
| `FactRiskIssue` | 118 | Project–risk/issue |

## Controlled anomalies

| ID | Verified signal | Root cause |
|---|---|---|
| A01 | `FORGE-001`: 55% complete, 70% consumed, EAC over exactly $400K. | Critical milestone delayed 42 days; 1,096.5 overtime hours after delay. |
| A02 | QA utilization 68.09% vs 85% target in Jan–Jun 2025. | 4,721.8 non-project/bench hours with normal available capacity. |
| A03 | Software −5 FTE, Data −2; Systems +1, Mechanical +3 in Jul–Dec 2025. | Primary/bridge skill profile prevents direct full reallocation. |
| A04 | `FORGE-004` critical milestone delayed 45 days. | Open critical dependency and $600,230.13 contractor/material commitment. |
| A05 | `FORGE-009`: labor hours 101% of plan but cost 118%. | 8,657 contractor hours and 1,600.5 overtime hours. |
| A06 | 15 duplicate extras, 12 incomplete rows, 297 late submissions. | Time-entry process/data validation defects. |
| A07 | `FORGE-007`: 48% complete vs 68% consumed. | $1,092,374.07 front-loaded material/other spend. |

Observed values are generated, then independently re-read from CSV by `validate_data.py`; they are not copied from generator variables.

## Power BI workflow

1. Import the folder `data/generated` and apply explicit data types.
2. Use `powerbi/FactLabor_Clean.pq` or implement the same steps: reject 12 incomplete rows, sort/retain deterministically, then remove 15 duplicate natural-key extras.
3. Configure one-to-many, single-direction relationships in `powerbi/model_setup.md`; keep role-playing date relationships inactive.
4. Create an empty table named `Measures`, add formulas from `powerbi/measures.dax`, then apply formats/display folders from the catalog.
5. Confirm `Labor Cost Reconciliation $ = 0` before building visuals.

The workbook `.xlsx` review mentioned as an optional convenience in the source context is not included because the required spreadsheet artifact runtime was unavailable. The requested CSV dataset and all QA/Power BI assets are complete and independently reproducible.

## Completed Power BI dashboard

The completed local report contains the optimized 11-table model, 70/70
live-tested DAX measures, 19 unambiguous relationships, the Microsoft Fluent
theme, and five report pages with KPI cards, comparison/trend charts, target
lines, contextual slicers, labels, tooltips, and Fluent status colors. The PBIX
binary is intentionally excluded from Git; every generated dataset, model asset,
measure definition, QA result, and reproducible build script is versioned.

[![Executive Overview dashboard](docs/assets/dashboard/executive-overview.png)](docs/dashboard_gallery.md)

Review the [five-page dashboard gallery](docs/dashboard_gallery.md), the
[dashboard specification](powerbi/dashboard_spec.md), or the
[full realism and optimization audit](quality/full_realism_optimization_report.md).

Gallery baseline: all slicers are set to **All**, no cross-highlight is active,
and every screenshot uses the native 1200×675 report canvas.
