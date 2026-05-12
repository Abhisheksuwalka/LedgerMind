import { KPICard } from './KPICard';
import { TinySparkLine } from './TinySparkLine';
import { RunwayBar } from './RunwayBar';
import { formatCurrency, formatPercent, formatMonths } from '@/lib/formatters';
import type { QuickStatsData } from '@/types/snapshot';

interface QuickStatsProps {
  data: QuickStatsData;
  isLoading?: boolean;
}

export function QuickStats({ data, isLoading }: QuickStatsProps) {
  // Helpers
  const formatPercentagePoint = (val: number) => `${val > 0 ? '+' : ''}${val.toFixed(1)}pp`;
  
  const getRunwayColor = (months: number) => {
    if (months > 6) return 'var(--color-success-default)';
    if (months >= 3) return 'var(--color-warning-default)';
    return 'var(--color-danger-default)';
  };

  const runwayColor = getRunwayColor(data.cashRunway.value);
  const isRunwayDanger = data.cashRunway.value < 3;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Total Revenue */}
      <KPICard
        title="Total Revenue"
        value={formatCurrency(data.totalRevenue.value, 'USD', true)}
        trendDirection={data.totalRevenue.trendDirection}
        trendText={formatPercent(data.totalRevenue.trend)}
        sparkline={<TinySparkLine data={data.totalRevenue.sparkline} color="var(--color-primary-500)" />}
        isLoading={isLoading}
      />

      {/* Total Expenses */}
      <KPICard
        title="Total Expenses"
        value={formatCurrency(data.totalExpenses.value, 'USD', true)}
        // Expenses logic: increasing is bad (negative direction), decreasing is good (positive direction)
        // Wait, the hook sets trendDirection as 'negative' for expenses dropping. Let's just use what the hook provides or correct the hook.
        // If trend > 0, it's bad.
        trendDirection={data.totalExpenses.trend > 0 ? 'negative' : 'positive'}
        trendText={formatPercent(data.totalExpenses.trend)}
        sparkline={<TinySparkLine data={data.totalExpenses.sparkline} color="var(--color-danger-default)" />}
        isLoading={isLoading}
      />

      {/* Net Profit Margin */}
      <KPICard
        title="Net Profit Margin"
        value={`${data.netProfitMargin.value.toFixed(1)}%`}
        trendDirection={data.netProfitMargin.trendDirection}
        trendText={formatPercentagePoint(data.netProfitMargin.trend)}
        sparkline={<TinySparkLine data={data.netProfitMargin.sparkline} color="var(--color-success-default)" />}
        isLoading={isLoading}
      />

      {/* Cash Runway */}
      <KPICard
        title="Cash Runway"
        value={formatMonths(data.cashRunway.value)}
        valueColor={runwayColor}
        className={isRunwayDanger ? 'shadow-[var(--shadow-danger)]' : ''}
        bottomSlot={<RunwayBar months={data.cashRunway.value} />}
        isLoading={isLoading}
      />
    </div>
  );
}
