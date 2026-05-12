import { cn } from '@/lib/cn';

interface SuggestedPromptsProps {
  onSelect: (prompt: string) => void;
}

const PROMPTS = [
  "What is my current cash runway?",
  "Show me last month's top 3 expenses",
  "Summarize the latest anomalies",
];

export function SuggestedPrompts({ onSelect }: SuggestedPromptsProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full w-full max-w-2xl mx-auto px-6 text-center animate-in fade-in zoom-in-95 duration-500">
      <div className="w-[60px] h-[60px] rounded-full bg-gradient-to-br from-primary-900 to-bg-raised flex items-center justify-center text-3xl mb-6 shadow-primary border border-border-default animate-pulse">
        💰
      </div>
      
      <h2 className="text-xl font-medium text-secondary mb-8">
        How can I help you analyze your finances today?
      </h2>

      <div className="flex flex-wrap justify-center gap-3">
        {PROMPTS.map((prompt) => (
          <button
            key={prompt}
            onClick={() => onSelect(prompt)}
            className={cn(
              'bg-bg-raised border border-border-default rounded-full px-4 py-2 text-sm text-secondary',
              'transition-all duration-150',
              'hover:border-primary-500 hover:text-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-500'
            )}
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}
