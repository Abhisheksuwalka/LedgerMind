import { useEffect, useState } from 'react';
import { PieChart, Pie, Cell } from 'recharts';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';

interface HealthScoreGaugeProps {
  score: number;
}

export function HealthScoreGauge({ score }: HealthScoreGaugeProps) {
  const [displayScore, setDisplayScore] = useState(0);

  useEffect(() => {
    let start = 0;
    const duration = 800;
    const startTime = performance.now();

    function updateCounter(currentTime: number) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // easeOutExpo
      const easeProgress = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
      setDisplayScore(Math.floor(start + (score - start) * easeProgress));

      if (progress < 1) {
        requestAnimationFrame(updateCounter);
      }
    }

    requestAnimationFrame(updateCounter);
  }, [score]);

  function gaugeColor(s: number) {
    if (s >= 70) return 'var(--color-success-default)';
    if (s >= 40) return 'var(--color-warning-default)';
    return 'var(--color-danger-default)';
  }

  function getStatusText(s: number) {
    if (s >= 70) return 'Healthy';
    if (s >= 40) return 'Needs Attention';
    return 'At Risk';
  }

  const currentGaugeColor = gaugeColor(displayScore);
  const data = [
    { value: displayScore },
    { value: 100 - displayScore },
  ];

  // Calculate positions for tick labels
  // Angles are measured from horizontal right (0) in recharts, but startAngle=180, endAngle=0.
  // 180 degrees is 0 score, 0 degrees is 100 score.
  // Radius for labels slightly outside the outerRadius (110). Let's use 120.
  const cx = 120;
  const cy = 130;
  const labelRadius = 125;

  const getPos = (val: number) => {
    // 0 -> 180 deg (Math.PI), 100 -> 0 deg (0)
    const angle = Math.PI * (1 - val / 100);
    return {
      x: cx + Math.cos(angle) * labelRadius,
      y: cy - Math.sin(angle) * labelRadius,
    };
  };

  const pos40 = getPos(40);
  const pos70 = getPos(70);

  return (
    <Card className={`h-full ${score >= 80 ? 'shadow-[var(--shadow-success)]' : ''}`}>
      <CardHeader>
        <h3 className="text-lg font-semibold text-primary">Health Score</h3>
      </CardHeader>
      <CardBody className="flex flex-col items-center justify-center flex-1">
        <div className="relative w-[260px] h-[140px] flex justify-center mt-4">
          <PieChart width={240} height={130} className="absolute bottom-0">
            <Pie
              data={data}
              cx={120}
              cy={130}
              startAngle={180}
              endAngle={0}
              innerRadius={80}
              outerRadius={110}
              stroke="none"
              dataKey="value"
              isAnimationActive={false}
            >
              <Cell fill={currentGaugeColor} />
              <Cell fill="var(--color-bg-sunken)" />
            </Pie>
          </PieChart>
          
          <div className="absolute bottom-0 left-0 right-0 flex justify-center items-end pb-1">
            <span 
              className="text-4xl font-mono font-semibold tracking-tight"
              style={{ color: currentGaugeColor }}
            >
              {displayScore}
            </span>
          </div>

          <svg className="absolute bottom-0 left-[10px] w-[240px] h-[130px] pointer-events-none overflow-visible">
             <text x={0} y={130} className="text-[10px]" fill="var(--color-text-tertiary)" textAnchor="start">0</text>
             <text x={pos40.x - cx + 120} y={pos40.y - cy + 130} className="text-[10px]" fill="var(--color-text-tertiary)" textAnchor="middle">40</text>
             <text x={pos70.x - cx + 120} y={pos70.y - cy + 130} className="text-[10px]" fill="var(--color-text-tertiary)" textAnchor="middle">70</text>
             <text x={240} y={130} className="text-[10px]" fill="var(--color-text-tertiary)" textAnchor="end">100</text>
          </svg>
        </div>
        <div className="mt-6 text-center">
          <span className="font-medium px-4 py-1 rounded-full bg-opacity-10" style={{ color: currentGaugeColor, backgroundColor: `color-mix(in srgb, ${currentGaugeColor} 15%, transparent)` }}>
            {getStatusText(displayScore)}
          </span>
        </div>
      </CardBody>
    </Card>
  );
}
