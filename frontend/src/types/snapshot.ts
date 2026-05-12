export type TrendDirection = 'positive' | 'negative' | 'neutral';

export interface SparklinePoint {
  date: string;
  value: number;
}

export interface KPIData {
  value: number;
  trend: number;
  trendDirection: TrendDirection;
  sparkline: SparklinePoint[];
}

export interface QuickStatsData {
  totalRevenue: KPIData;
  totalExpenses: KPIData;
  netProfitMargin: KPIData; // value is a percentage (e.g., 24.7), trend is percentage points
  cashRunway: KPIData; // value is in months
}

export interface ChartDataPoint {
  date: string;
  revenue: number;
  expenses: number;
}

export interface Anomaly {
  id: string;
  title: string;
  severity: 'critical' | 'warning' | 'info';
  date: string;
}

export interface SnapshotData {
  quickStats: QuickStatsData;
  chartData: ChartDataPoint[];
  healthScore: number;
  anomalies: Anomaly[];
  lastSyncedAt: string;
}
