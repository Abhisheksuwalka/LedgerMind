import { CheckCircle, Wrench } from 'lucide-react';
import { cn } from '@/lib/cn';
import { ToolCall } from '@/types/chat';

interface ToolCallPillProps {
  toolCall: ToolCall;
}

export function ToolCallPill({ toolCall }: ToolCallPillProps) {
  const isInProgress = toolCall.status === 'in-progress';

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 px-3 py-1 rounded-sm border text-xs font-mono mb-2',
        'bg-[rgba(139,92,246,0.1)] border-[rgba(139,92,246,0.3)] text-violet-400',
        isInProgress && 'animate-pulse'
      )}
    >
      <Wrench className="w-3 h-3" />
      <span>{toolCall.name}</span>
      {!isInProgress && <CheckCircle className="w-3 h-3 ml-1 text-violet-400" />}
    </div>
  );
}
