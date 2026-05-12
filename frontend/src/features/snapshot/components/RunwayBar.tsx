interface RunwayBarProps {
  months: number;
}

export function RunwayBar({ months }: RunwayBarProps) {
  // Cap between 0 and 12 for the position
  const clampedMonths = Math.min(Math.max(months, 0), 12);
  const positionPercent = (clampedMonths / 12) * 100;

  return (
    <div className="mt-3">
      <div 
        className="relative w-full h-[6px] rounded-full"
        style={{
          background: 'linear-gradient(to right, var(--color-danger-default), var(--color-warning-default), var(--color-success-default))'
        }}
      >
        <div 
          className="absolute top-1/2 w-3 h-3 bg-white rounded-full shadow-sm border border-border-strong"
          style={{ 
            left: `${positionPercent}%`, 
            transform: 'translate(-50%, -50%)',
            transition: 'left 0.3s ease-out'
          }}
        />
      </div>
    </div>
  );
}
