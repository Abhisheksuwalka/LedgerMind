import { useId } from 'react';
import { AreaChart, Area, ResponsiveContainer } from 'recharts';
import type { SparklinePoint } from '@/types/snapshot';

interface TinySparkLineProps {
  data: SparklinePoint[];
  color: string; // Tailwind hex or CSS variable
}

export function TinySparkLine({ data, color }: TinySparkLineProps) {
  const id = useId();
  const gradientId = `spark-${id.replace(/:/g, '')}`; // useId might contain colons which are invalid in URLs

  return (
    <ResponsiveContainer width={80} height={32}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.3} />
            <stop offset="95%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={1.5}
          fill={`url(#${gradientId})`}
          dot={false}
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
