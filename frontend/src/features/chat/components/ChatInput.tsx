import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { ArrowUp, Square } from 'lucide-react';
import { cn } from '@/lib/cn';

interface ChatInputProps {
  onSend: (message: string) => void;
  isStreaming: boolean;
  onStop?: () => void;
}

export function ChatInput({ onSend, isStreaming, onStop }: ChatInputProps) {
  const [value, setValue] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    // Read pre-populated message from sessionStorage if exists
    const prepopulated = sessionStorage.getItem('chat_prefill');
    if (prepopulated) {
      setValue(prepopulated);
      sessionStorage.removeItem('chat_prefill');
    }
    textareaRef.current?.focus();
  }, []);

  const adjustHeight = () => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
  };

  useEffect(() => {
    adjustHeight();
  }, [value]);

  const handleSend = () => {
    if (!value.trim() || isStreaming) return;
    onSend(value);
    setValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setValue('');
    }
  };

  const isEmpty = value.trim().length === 0;

  return (
    <div className="border-t border-border-subtle p-4 px-6 bg-bg-base">
      <div className="max-w-4xl mx-auto">
        <div
          className={cn(
            'flex items-end bg-bg-raised border rounded-[16px] p-3 transition-shadow duration-150',
            isFocused
              ? 'border-primary-500 shadow-[0_0_0_3px_rgba(59,130,246,0.15)]'
              : 'border-border-default'
          )}
        >
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder="Ask CashPilot anything..."
            className="flex-1 bg-transparent border-none outline-none resize-none min-h-[24px] max-h-[200px] text-primary placeholder:text-text-tertiary px-2 py-1 scroll-smooth"
            rows={1}
          />

          <button
            onClick={isStreaming ? onStop : handleSend}
            disabled={isEmpty && !isStreaming}
            className={cn(
              'flex-shrink-0 flex items-center justify-center w-9 h-9 rounded-full transition-all duration-150 ml-2 focus:outline-none focus:ring-2 focus:ring-primary-500',
              isStreaming
                ? 'bg-danger-subtle text-danger-default'
                : isEmpty
                ? 'bg-bg-hover text-text-tertiary cursor-not-allowed'
                : 'bg-primary-600 text-white hover:bg-primary-500'
            )}
            aria-label={isStreaming ? 'Stop generating' : 'Send message'}
          >
            {isStreaming ? (
              <Square className="w-4 h-4 fill-current" />
            ) : (
              <ArrowUp className="w-5 h-5" />
            )}
          </button>
        </div>
        <div className="text-center mt-2 text-xs text-text-tertiary">
          CashPilot can make mistakes. Consider verifying important information.
        </div>
      </div>
    </div>
  );
}
