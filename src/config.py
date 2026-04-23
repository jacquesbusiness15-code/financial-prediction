"""Schema contract for the WISAG dataset.

Primary:  HEADER_MAP  - German header text  -> semantic name (robust).
Fallback: COLUMN_MAP  - Excel column letter -> semantic name (position-based;
          used only when the file has no recognizable WISAG headers).

`SCHEMA` is the single source of truth for dtype, nullability, and semantic
group. Column-group constants (`REVENUE_COLS`, `COST_COLS_DB`, `DIMENSIONS`,
etc.) are derived from it so they cannot drift out of sync. Bump
`SCHEMA_VERSION` whenever the contract changes - it's part of the parquet
cache key, so a bump invalidates every stored cache automatically.
"""

from openpyxl.utils import column_index_from_string

SCHEMA_VERSION = "wisag-v1"

HEADER_MAP: dict[str, str] = {
    "ID": "row_id",
    "Jahr": "year",
    "Monat": "month",
    "Region": "region",
    "Mandant": "entity",
    "Kurzbez": "short_description",
    "KST": "cost_center_id",
    "KSTName": "cost_center_name",
    "KBNR": "customer_id",
    "Kunde": "customer_name",
    "Abrechnungsart": "billing_type",
    "Vertriebsweg": "sales_channel",
    "OKZ": "internal_code",
    "Branche": "industry",
    "Dienstleistungsart": "service_type",
    "Produkt": "product",
    "Auftragstyp": "order_type",
    "Debitornr": "debtor_number",
    "Debitor": "debtor",
    "Debitor1": "debtor_alt",
    "Abgrenzung": "accrual_adjustment",
    "Ges_Ums": "revenue_total",
    "Sub_konzern": "subcontractor_group",
    "Sub_Sparte": "subcontractor_division",
    "EL1": "internal_service_el1",
    "Sub_extern": "subcontractor_external",
    "EL2": "internal_service_el2",
    "Fahrgeld": "travel_cost",
    "Direktlohn": "labor_direct",
    "Einweisung": "training_cost",
    "LFZ_Urlaub": "vacation_cost",
    "LFZ_Krank": "sick_cost",
    "Kalk_LNK": "labor_overhead",
    "Ges_Lohn": "labor_cost_total",
    "DB": "cm_db",
    "DB_%": "cm_db_pct",
    "MAT": "material_cost",
    "DB-1": "cm_db1",
    "DB-1_%": "cm_db1_pct",
    "KFZ": "vehicle_cost",
    "DB-2": "cm_db2",
    "DB-2_%": "cm_db2_pct",
    "Leistung_Std": "hours_actual",
    "Paus_Std": "hours_break",
    "Soll_Std": "hours_planned",
    "Prod_Std": "hours_productive",
    "Einweisung_Std": "hours_training",
    "Std_Festlohn": "hours_fixed_salary",
    "Ges_Intern": "internal_service_total",
    "Sub_Std": "subcontractor_hours",
    "Sub_Std_Einw": "subcontractor_hours_training",
    "Ges_Sub": "subcontractor_services_total",
    "Ges_oEinw": "services_total_excl_training",
    "Abw_Std": "hour_variance",
    "Delta_kl": "cost_variance",
    "Ist_Pauschal": "revenue_fixed",
    "Ist_Stunden": "revenue_hourly",
    "Ist_Sonstige": "revenue_other",
    "Pauschale": "contracted_fixed_price",
    "KBName": "customer_name_secondary",
    "DLQ_Soll_%": "quality_target",
    "DLQ_Ist_%": "quality_actual",
    "BL_Bemerkung": "manager_comment",
    "Auftragbeginn": "contract_start",
    "Auftragende": "contract_end",
    "Analyse_ABC": "abc_class",
    "Analyse": "analysis_category",
    "KST_FM": "fm_cost_center",
    "Soll_DB": "cm_planned",
    "Soll_SUBQ": "plan_subcontractor_ratio",
    "Soll_KLQ": "plan_labor_cost_ratio",
    "Soll_VL": "plan_overhead_factor",
    "UserName": "user_name",
}

# Dtype tags used by the loader and parquet cache.
#   "Int64"            -> nullable integer (pandas extension dtype)
#   "float64"          -> numeric, NaN-friendly
#   "string"           -> pandas nullable string
#   "category"         -> low-cardinality string stored as category
#   "datetime64[ns]"   -> timestamp (parsed via pd.to_datetime)
#   "boolean"          -> nullable bool
#
# Group tag is used to derive the column-group constants further down.
SCHEMA: dict[str, tuple[str, str]] = {
    # identity
    "row_id":                        ("Int64",          "meta"),
    "year":                          ("Int64",          "meta"),
    "month":                         ("Int64",          "meta"),
    # dimensions
    "region":                        ("category",       "dimension"),
    "entity":                        ("category",       "dimension"),
    "short_description":             ("string",         "dimension"),
    "cost_center_id":                ("category",       "dimension"),
    "cost_center_name":              ("string",         "dimension"),
    "customer_id":                   ("string",         "dimension"),
    "customer_name":                 ("string",         "dimension"),
    "billing_type":                  ("category",       "dimension"),
    "sales_channel":                 ("category",       "dimension"),
    "internal_code":                 ("string",         "dimension"),
    "industry":                      ("category",       "dimension"),
    "service_type":                  ("category",       "dimension"),
    "product":                       ("string",         "dimension"),
    "order_type":                    ("category",       "dimension"),
    "debtor_number":                 ("string",         "dimension"),
    "debtor":                        ("string",         "dimension"),
    "debtor_alt":                    ("string",         "dimension"),
    "customer_name_secondary":       ("string",         "dimension"),
    "fm_cost_center":                ("string",         "dimension"),
    "abc_class":                     ("category",       "dimension"),
    "analysis_category":             ("string",         "dimension"),
    "manager_comment":               ("string",         "dimension"),
    "user_name":                     ("string",         "dimension"),
    # revenue
    "accrual_adjustment":            ("float64",        "revenue"),
    "revenue_total":                 ("float64",        "revenue"),
    "revenue_fixed":                 ("float64",        "revenue"),
    "revenue_hourly":                ("float64",        "revenue"),
    "revenue_other":                 ("float64",        "revenue"),
    "contracted_fixed_price":        ("float64",        "revenue"),
    # costs
    "subcontractor_group":           ("float64",        "cost"),
    "subcontractor_division":        ("float64",        "cost"),
    "internal_service_el1":          ("float64",        "cost"),
    "subcontractor_external":        ("float64",        "cost"),
    "internal_service_el2":          ("float64",        "cost"),
    "travel_cost":                   ("float64",        "cost"),
    "labor_direct":                  ("float64",        "cost"),
    "training_cost":                 ("float64",        "cost"),
    "vacation_cost":                 ("float64",        "cost"),
    "sick_cost":                     ("float64",        "cost"),
    "labor_overhead":                ("float64",        "cost"),
    "labor_cost_total":              ("float64",        "cost"),
    "material_cost":                 ("float64",        "cost"),
    "vehicle_cost":                  ("float64",        "cost"),
    "internal_service_total":        ("float64",        "cost"),
    "subcontractor_services_total":  ("float64",        "cost"),
    "services_total_excl_training":  ("float64",        "cost"),
    # contribution margins
    "cm_db":                         ("float64",        "cm"),
    "cm_db_pct":                     ("float64",        "cm"),
    "cm_db1":                        ("float64",        "cm"),
    "cm_db1_pct":                    ("float64",        "cm"),
    "cm_db2":                        ("float64",        "cm"),
    "cm_db2_pct":                    ("float64",        "cm"),
    # hours
    "hours_actual":                  ("float64",        "hours"),
    "hours_break":                   ("float64",        "hours"),
    "hours_planned":                 ("float64",        "hours"),
    "hours_productive":              ("float64",        "hours"),
    "hours_training":                ("float64",        "hours"),
    "hours_fixed_salary":            ("float64",        "hours"),
    "subcontractor_hours":           ("float64",        "hours"),
    "subcontractor_hours_training":  ("float64",        "hours"),
    "hour_variance":                 ("float64",        "hours"),
    "cost_variance":                 ("float64",        "hours"),
    # plan targets
    "cm_planned":                    ("float64",        "plan"),
    "plan_subcontractor_ratio":      ("float64",        "plan"),
    "plan_labor_cost_ratio":         ("float64",        "plan"),
    "plan_overhead_factor":          ("float64",        "plan"),
    # quality
    "quality_target":                ("float64",        "quality"),
    "quality_actual":                ("float64",        "quality"),
    # contract lifecycle
    "contract_start":                ("datetime64[ns]", "contract"),
    "contract_end":                  ("datetime64[ns]", "contract"),
}

CRITICAL_SEMANTIC_COLS: list[str] = [
    "year", "month", "region", "cost_center_id",
    "revenue_total", "cm_db", "labor_cost_total",
]

OPTIONAL_SEMANTIC_COLS: list[str] = [
    v for v in HEADER_MAP.values() if v not in CRITICAL_SEMANTIC_COLS
]

COLUMN_MAP: dict[str, str] = {
    "A": "row_id",
    "B": "year",
    "C": "month",
    "D": "region",
    "E": "entity",
    "F": "short_description",
    "G": "cost_center_id",
    "H": "cost_center_name",
    "I": "customer_id",
    "J": "customer_name",
    "K": "billing_type",
    "L": "sales_channel",
    "M": "internal_code",
    "N": "industry",
    "O": "service_type",
    "P": "product",
    "Q": "order_type",
    "R": "debtor_number",
    "S": "debtor",
    "T": "debtor_alt",
    "U": "accrual_adjustment",
    "V": "revenue_total",
    "W": "subcontractor_group",
    "X": "subcontractor_division",
    "Y": "internal_service_el1",
    "Z": "subcontractor_external",
    "AA": "internal_service_el2",
    "AB": "travel_cost",
    "AC": "labor_direct",
    "AD": "training_cost",
    "AE": "vacation_cost",
    "AF": "sick_cost",
    "AG": "labor_overhead",
    "AH": "labor_cost_total",
    "AI": "cm_db",
    "AJ": "cm_db_pct",
    "AK": "material_cost",
    "AL": "cm_db1",
    "AM": "cm_db1_pct",
    "AN": "vehicle_cost",
    "AO": "cm_db2",
    "AP": "cm_db2_pct",
    "AQ": "hours_actual",
    "AR": "hours_break",
    "AS": "hours_planned",
    "AT": "hours_productive",
    "AU": "hours_training",
    "AV": "hours_fixed_salary",
    "AW": "internal_service_total",
    "AX": "subcontractor_hours",
    "AY": "subcontractor_hours_training",
    "AZ": "subcontractor_services_total",
    "BA": "services_total_excl_training",
    "BB": "hour_variance",
    "BC": "cost_variance",
    "BD": "revenue_fixed",
    "BE": "revenue_hourly",
    "BF": "revenue_other",
    "BG": "contracted_fixed_price",
    "BH": "cost_center_name_ext",
    "BI": "quality_target",
    "BJ": "quality_actual",
    "BK": "manager_comment",
    "BL": "contract_start",
    "BM": "contract_end",
    "BN": "abc_class",
    "BO": "analysis_category",
    "BP": "fm_cost_center",
    "BQ": "cm_planned",
    "BR": "plan_subcontractor_ratio",
    "BS": "plan_labor_cost_ratio",
    "BT": "plan_overhead_factor",
    "BU": "user_name",
}


def _cols_in_group(tag: str) -> list[str]:
    return [name for name, (_, g) in SCHEMA.items() if g == tag]


# Groups used across features/drivers/benchmarks. Derived from SCHEMA so they
# cannot drift out of sync.
REVENUE_COLS = ["revenue_total"]
REVENUE_BREAKDOWN_COLS = ["revenue_fixed", "revenue_hourly", "revenue_other"]

COST_COLS_DB = [  # costs above DB (labor, subcontracting, travel, internal services)
    "subcontractor_group",
    "subcontractor_division",
    "subcontractor_external",
    "internal_service_el1",
    "internal_service_el2",
    "travel_cost",
    "labor_cost_total",
]
COST_COLS_DB1_EXTRA = ["material_cost"]        # DB -> DB1 adds material
COST_COLS_DB2_EXTRA = ["vehicle_cost"]         # DB1 -> DB2 adds vehicle

LABOR_SUBCOMPONENTS = [
    "labor_direct",
    "training_cost",
    "vacation_cost",
    "sick_cost",
    "labor_overhead",
]

KEY_OPS_KPIS = [
    "productivity_ratio",
    "absence_rate",
    "training_intensity",
    "subcontractor_share",
    "labor_cost_per_productive_hour",
    "quality_gap",
]

DIMENSIONS = ["region", "entity", "cost_center_id", "cost_center_name",
              "customer_id", "customer_name", "service_type", "industry",
              "billing_type", "abc_class"]


def col_letter_to_index(letter: str) -> int:
    """Convert 'A'..'BU' to a zero-based column index."""
    return column_index_from_string(letter) - 1
