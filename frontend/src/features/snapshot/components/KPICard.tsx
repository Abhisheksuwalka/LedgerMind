import { ReactNode } from 'react';
import { cva } from 'class-variance-authority';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { cn } from '@/lib/cn';

const trendBadge = cva(
  'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold font-mono whitespace-nowrap',
  {
    variants: {
      direction: {
        positive: 'bg-success-subtle text-success-bright',
        negative: 'bg-danger-subtle text-danger-bright',
        neutral:  'bg-bg-hover text-secondary',
      }
    }
  }
);

interface KPICardProps {
  title: string;
  value: string | ReactNode;
  valueColor?: string;
  trendDirection?: 'positive' | 'negative' | 'neutral';
  trendText?: string;
  sparkline?: ReactNode;
  bottomSlot?: ReactNode;
  isLoading?: boolean;
  className?: string;
}

export function KPICard({
  title,
  value,
  valueColor,
  trendDirection,
  trendText,
  sparkline,
  bottomSlot,
  isLoading,
  className,
}: KPICardProps) {
  
  const renderTrendIcon = () => {
    if (trendDirection === 'positive') return <TrendingUp size={16} className="text-success-default" />;
    if (trendDirection === 'negative') return <TrendingDown size={16} className="text-danger-default" />;
    if (trendDirection === 'neutral') return <Minus size={16} className="text-secondary" />;
    return null;
  };

  return (
    <Card className={cn("p-6 flex flex-col justify-between h-full", className)}>
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-sm font-medium text-secondary uppercase tracking-wide">
          {title}
        </h4>
        {renderTrendIcon()}
      </div>

      <div className="mb-4 flex-1 flex flex-col justify-center">
        {isLoading ? (
          <div className="h-9 bg-bg-hover rounded animate-pulse w-24"></div>
        ) : (
          <div 
            className="text-3xl font-semibold font-mono tracking-tight"
            style={valueColor ? { color: valueColor } : undefined}
          >
            {value}
          </div>
        )}
      </div>

      <div className="flex items-center justify-between">
        <div className="flex-1">
          {sparkline && <div className="h-8">{sparkline}</div>}
        </div>
        
        {trendText && trendDirection && (
          <div className="ml-4">
            <span className={trendBadge({ direction: trendDirection })}>
              {trendText}
            </span>
          </div>
        )}
      </div>

      {bottomSlot && (
        <div className="w-full">
          {bottomSlot}
        </div>
      )}
    </Card>
  );
}
