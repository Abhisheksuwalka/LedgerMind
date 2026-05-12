export function formatCurrency(
  value: number,
  currency: string = 'USD',
  compact: boolean = false
): string {
  if (compact && Math.abs(value) >= 1_000_000) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency', currency,
      notation: 'compact', maximumFractionDigits: 1
    }).format(value);
  }
  // also handle thousands for compact mode if requested, but PRD says only >= 1M for compact in the code snippet.
  // Actually, standard compact notation handles thousands automatically:
  if (compact) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency', currency,
      notation: 'compact', maximumFractionDigits: 1
    }).format(value);
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency', currency,
    minimumFractionDigits: 0, maximumFractionDigits: 0
  }).format(value);
}

export function formatPercent(value: number, decimals: number = 1): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`;
}

export function formatMonths(value: number): string {
  return `${value.toFixed(1)} mo`;
}

export function formatRelativeTime(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime();
  if (diff < 60_000) return 'just now';
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  return `${Math.floor(diff / 86_400_000)}d ago`;
}
