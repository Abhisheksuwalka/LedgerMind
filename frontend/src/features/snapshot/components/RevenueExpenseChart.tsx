import { useState } from 'react';
import {
  AreaChart,
  Area,
  ResponsiveContainer,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip
} from 'recharts';
import { Card, CardHeader, CardBody } from '@/components/ui/Card';
import { formatCurrency } from '@/lib/formatters';
import type { ChartDataPoint } from '@/types/snapshot';

interface RevenueExpenseChartProps {
  data: ChartDataPoint[];
}

function formatAxisDate(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { month: 'short' });
}

function CustomChartTooltip({ active, payload, label }: any) {
  if (active && payload && payload.length) {
    const rev = payload.find((p: any) => p.dataKey === 'revenue')?.value || 0;
    const exp = payload.find((p: any) => p.dataKey === 'expenses')?.value || 0;
    const profit = rev - exp;
    
    return (
      <div className="bg-bg-elevated border border-border-default rounded-md p-3 shadow-lg min-w-[150px]">
        <p className="text-xs text-secondary font-semibold mb-2">{formatAxisDate(label)}</p>
        <div className="flex justify-between items-center mb-1">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-primary-500"></div>
            <span className="text-xs text-primary">Revenue</span>
          </div>
          <span className="text-xs font-mono font-medium text-primary">
            {formatCurrency(rev, 'USD', true)}
          </span>
        </div>
        <div className="flex justify-between items-center mb-2 pb-2 border-b border-border-subtle">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-danger-default"></div>
            <span className="text-xs text-primary">Expenses</span>
          </div>
          <span className="text-xs font-mono font-medium text-primary">
            {formatCurrency(exp, 'USD', true)}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-xs text-secondary">Net Profit</span>
          <span className={`text-xs font-mono font-medium ${profit >= 0 ? 'text-success-default' : 'text-danger-default'}`}>
            {formatCurrency(profit, 'USD', true)}
          </span>
        </div>
      </div>
    );
  }
  return null;
}

export function RevenueExpenseChart({ data }: RevenueExpenseChartProps) {
  const [timePeriod, setTimePeriod] = useState('12M');
  const periods = ['1M', '3M', '6M', 'YTD', '12M', 'All'];

  const latestData = data.length > 0 ? data[data.length - 1] : { revenue: 0, expenses: 0 };

  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between pb-2 border-b border-border-subtle mb-4">
        <div>
          <h3 className="text-lg font-semibold text-primary">Revenue vs. Expenses</h3>
          
          <div className="flex items-center gap-6 mt-3">
            <div className="flex items-center gap-2">
              <div className="w-[10px] h-[3px] rounded-full bg-primary-500"></div>
              <span className="text-xs text-secondary">Revenue</span>
              <span className="text-xs font-mono font-semibold text-primary-500 ml-1">
                {formatCurrency(latestData.revenue, 'USD', true)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-[10px] h-[3px] rounded-full bg-danger-default"></div>
              <span className="text-xs text-secondary">Expenses</span>
              <span className="text-xs font-mono font-semibold text-danger-default ml-1">
                {formatCurrency(latestData.expenses, 'USD', true)}
              </span>
            </div>
          </div>
        </div>

        <div className="flex bg-bg-sunken rounded-md p-0.5">
          {periods.map((p) => (
            <button
              key={p}
              onClick={() => setTimePeriod(p)}
              className={`px-3 py-1 text-xs font-medium rounded-sm transition-colors ${
                timePeriod === p
                  ? 'bg-primary-600 text-white shadow-sm'
                  : 'text-secondary hover:bg-bg-hover'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </CardHeader>
      <CardBody>
        <ResponsiveContainer width="100%" height={320}>
          <AreaChart data={data} margin={{ top: 16, right: 16, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id="gradRevenue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gradExpense" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#F43F5E" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#F43F5E" stopOpacity={0} />
              </linearGradient>
            </defs>

            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--color-chart-grid)"
              vertical={false}
            />

            <XAxis
              dataKey="date"
              tickFormatter={formatAxisDate}
              tick={{ fill: 'var(--color-chart-axis)', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />

            <YAxis
              tickFormatter={(v) => formatCurrency(v, 'USD', true)}
              tick={{ fill: 'var(--color-chart-axis)', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={64}
            />

            <Tooltip content={<CustomChartTooltip />} cursor={{ stroke: 'var(--color-border-strong)', strokeWidth: 1 }} />

            <Area
              type="monotone"
              dataKey="revenue"
              stroke="#3B82F6"
              strokeWidth={2}
              fill="url(#gradRevenue)"
              dot={false}
              activeDot={{ r: 4, fill: '#3B82F6', stroke: '#fff', strokeWidth: 2 }}
            />

            <Area
              type="monotone"
              dataKey="expenses"
              stroke="#F43F5E"
              strokeWidth={2}
              fill="url(#gradExpense)"
              dot={false}
              activeDot={{ r: 4, fill: '#F43F5E', stroke: '#fff', strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardBody>
    </Card>
  );
}
