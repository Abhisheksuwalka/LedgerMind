import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/Select';

export interface AlertFiltersProps {
  severity: 'all' | 'info' | 'warning' | 'critical';
  sort: 'newest' | 'oldest' | 'severity';
  onSeverityChange: (value: AlertFiltersProps['severity']) => void;
  onSortChange: (value: AlertFiltersProps['sort']) => void;
}

export function AlertFilters({ severity, sort, onSeverityChange, onSortChange }: AlertFiltersProps) {
  return (
    <div className="flex gap-3 flex-wrap">
      <Select value={severity} onValueChange={(v) => onSeverityChange(v as AlertFiltersProps['severity'])}>
        <SelectTrigger className="w-[180px] h-9">
          <SelectValue placeholder="All Severities" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Severities</SelectItem>
          <SelectItem value="critical">Critical</SelectItem>
          <SelectItem value="warning">Warning</SelectItem>
          <SelectItem value="info">Info</SelectItem>
        </SelectContent>
      </Select>

      <Select value={sort} onValueChange={(v) => onSortChange(v as AlertFiltersProps['sort'])}>
        <SelectTrigger className="w-[160px] h-9">
          <SelectValue placeholder="Sort by" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="newest">Newest First</SelectItem>
          <SelectItem value="oldest">Oldest First</SelectItem>
          <SelectItem value="severity">By Severity</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
