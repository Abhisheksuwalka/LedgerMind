import { Avatar } from '@/components/ui/Avatar';

export function TypingIndicator() {
  return (
    <div className="flex w-full gap-4 items-end justify-start animate-in fade-in slide-in-from-bottom-2 duration-300">
      <Avatar
        src="/favicon.ico"
        fallback="💰"
        className="w-7 h-7 bg-transparent border border-border-subtle shrink-0"
      />
      <div className="bg-bg-elevated border border-border-subtle rounded-tl-[4px] rounded-tr-[16px] rounded-br-[16px] rounded-bl-[16px] p-4 flex items-center gap-1.5 h-[44px]">
        <div
          className="w-[6px] h-[6px] bg-text-tertiary rounded-full"
          style={{ animation: 'bounce-scale 0.9s ease-in-out infinite', animationDelay: '0ms' }}
        />
        <div
          className="w-[6px] h-[6px] bg-text-tertiary rounded-full"
          style={{ animation: 'bounce-scale 0.9s ease-in-out infinite', animationDelay: '150ms' }}
        />
        <div
          className="w-[6px] h-[6px] bg-text-tertiary rounded-full"
          style={{ animation: 'bounce-scale 0.9s ease-in-out infinite', animationDelay: '300ms' }}
        />
      </div>
    </div>
  );
}
