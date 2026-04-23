// Shared API types — hand-mirrored from backend/schemas.py.

export type Severity = 'high' | 'medium' | 'low';
export type BaselineMode = 'mom' | 'yoy' | 'plan';

export interface SchemaReport {
  matched: string[];
  unmapped_input: string[];
  missing_expected: string[];
  missing_critical: string[];
  strategy: 'header' | 'position';
  expected_total: number;
  ok: boolean;
}

export interface DatasetSummary {
  rows: number;
  columns: number;
  period_min: string | null;
  period_max: string | null;
  regions: number | null;
  cost_centers: number | null;
  revenue_total: number | null;
  cm_db_total: number | null;
}

export interface DatasetFacets {
  regions: string[];
  services: string[];
  period_min: string | null;
  period_max: string | null;
}

export interface LoadDatasetResponse {
  dataset_id: string;
  summary: DatasetSummary;
  schema_report: SchemaReport;
  facets: DatasetFacets;
}

export interface KpiBlock {
  revenue: number;
  cm_db: number;
  cm_planned: number;
  plan_gap: number;
  cost_centers: number;
  anomalies_count: number;
}

export interface HeatmapPayload {
  row_dim: 'region' | 'cost_center';
  rows: string[];
  columns: string[];
  z: (number | null)[][];
}

export interface AnomalyRow {
  period: string;
  region: string | null;
  cost_center_id: string;
  cost_center_name: string | null;
  customer_name: string | null;
  service_type: string | null;
  cm_db: number | null;
  cm_db_pct: number | null;
  labor_ratio: number | null;
  cm_db_mom: number | null;
  cm_db_yoy: number | null;
  cm_vs_plan_delta: number | null;
  impact_eur: number;
  severity: Severity;
  anomaly_reasons: string;
}

export interface TopCostCenter {
  cost_center_id: string;
  cost_center_name: string | null;
  region: string | null;
  revenue_total: number;
  cm_db: number;
  cm_db_pct: number | null;
}

export interface PortfolioResponse {
  kpis: KpiBlock;
  heatmap: HeatmapPayload;
  top_cost_centers: TopCostCenter[];
  top_anomalies: AnomalyRow[];
}

export interface DriverOut {
  name: string;
  kind: 'revenue' | 'cost' | 'other' | 'residual';
  delta_eur: number;
  current: number | null;
  baseline: number | null;
}

export interface WaterfallRow {
  label: string;
  delta: number;
  kind: string;
}

export interface TimelinePoint {
  period: string;
  cm_db: number | null;
  cm_planned: number | null;
}

export interface PeerKpi {
  kpi: string;
  value: number;
  peer_median: number;
  peer_p25: number;
  peer_p75: number;
  percentile: number;
}

export interface HistoryStats {
  mean: number | null;
  std: number | null;
  min: number | null;
  max: number | null;
  last_12m_mean: number | null;
}

export interface DeepDiveResponse {
  cost_center_id: string;
  cost_center_name: string | null;
  region: string | null;
  service_type: string | null;
  period: string;
  baseline_label: string;
  observed_delta: number;
  modeled_delta: number;
  residual: number;
  residual_pct: number | null;
  drivers: DriverOut[];
  waterfall: WaterfallRow[];
  timeline: TimelinePoint[];
  kpis_vs_peers: PeerKpi[];
  history_stats: HistoryStats;
  labor_ratio: number | null;
  cm_current: number;
  cm_baseline: number;
  cm_current_pct: number | null;
  hour_variance: number | null;
  dq_accrual_flag: boolean;
  manager_comment: string | null;
}

export interface WarningRow {
  cost_center_id: string;
  cost_center_name: string | null;
  region: string | null;
  customer_name: string | null;
  service_type: string | null;
  period: string;
  signal: string;
  severity: Severity;
  detail: string;
  impact_eur: number;
}

export interface WarningsResponse {
  warnings: WarningRow[];
  counts: Record<string, number>;
  total_impact_eur: number;
}

export interface PlanVsActualMonth {
  period: string;
  revenue: number;
  planned: number;
  actual: number;
  gap_eur: number;
  gap_pct: number | null;
}

export interface PlanVsActualResponse {
  months: PlanVsActualMonth[];
  total_actual: number;
  total_planned: number;
  total_gap: number;
  worst_month: string | null;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

// ---------- Facility overview ----------

export type FacilityStatus = 'critical' | 'warn' | 'healthy';

export interface DriverItem {
  class_key: string;
  icon: string;
  title_key: string;
  sub_key: string;
  pct_change: number | null;
  delta_eur: number;
}

export interface ActionItem {
  key: string;
  icon: string;
  title_key: string;
  sub_key: string;
  impact_pct: number;
}

export interface SparklinePoint {
  period: string;
  margin: number;
}

export interface FacilityOverviewResponse {
  cost_center_id: string;
  cost_center_name: string | null;
  region: string | null;
  service_type: string | null;
  period: string;
  icon: string;
  status: FacilityStatus;
  margin_pct: number | null;
  margin_mom_delta: number | null;
  sparkline: SparklinePoint[];
  worst_drivers: DriverItem[];
  recommended_actions: ActionItem[];
  baseline_headcount: number;
  team_size_suggestion: number;
}

export interface SimulateTeamSizeRequest {
  cost_center_id: string;
  new_headcount: number;
  baseline_headcount?: number | null;
  period?: string | null;
}

export interface SimulateTeamSizeResponse {
  baseline_headcount: number;
  new_headcount: number;
  baseline_margin: number;
  new_margin: number;
  delta_margin: number;
  productivity_gain_pct: number;
  new_cm_eur: number;
}
