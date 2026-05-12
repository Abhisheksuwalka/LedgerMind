import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { AlertCircle, ChevronDown, ChevronUp, Terminal } from 'lucide-react';
import { Avatar } from '@/components/ui/Avatar';
import { Message } from '@/types/chat';
import { cn } from '@/lib/cn';
import { ToolCallPill } from './ToolCallPill';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const [showDetails, setShowDetails] = useState(false);
  const isUser = message.role === 'user';
  const isError = message.isError;
  const isDev = import.meta.env.DEV;

  return (
    <div
      className={cn(
        'flex w-full gap-4 items-end animate-in fade-in slide-in-from-bottom-2 duration-300',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      {!isUser && (
        <Avatar
          src="/favicon.ico"
          fallback="💰"
          className="w-7 h-7 bg-transparent border border-border-subtle shrink-0"
        />
      )}

      <div
        className={cn(
          'flex flex-col',
          isUser ? 'items-end max-w-[70%]' : 'items-start max-w-[80%]'
        )}
      >
        {/* Single legacy toolCall */}
        {message.toolCall && <ToolCallPill toolCall={message.toolCall} />}
        {/* Multiple tools from the ReAct agent */}
        {message.toolsUsed && message.toolsUsed.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-2">
            {message.toolsUsed.map((tool) => (
              <ToolCallPill
                key={tool}
                toolCall={{ id: tool, name: tool, status: 'complete' }}
              />
            ))}
          </div>
        )}

        <div
          className={cn(
            'text-base leading-relaxed relative group',
            isUser
              ? 'bg-primary-700 text-white rounded-[16px] rounded-br-[4px] px-4 py-3'
              : cn(
                  'bg-bg-elevated border rounded-[16px] rounded-tl-[4px] p-4 prose prose-invert prose-p:leading-relaxed prose-pre:bg-bg-sunken prose-pre:font-mono prose-pre:rounded-md prose-pre:p-4 prose-th:bg-bg-hover prose-th:font-semibold prose-td:border prose-td:border-border-default prose-th:border prose-th:border-border-default max-w-none w-full',
                  isError ? 'border-danger-default/50 bg-danger-default/5' : 'border-border-subtle'
                )
          )}
        >
          {isError && (
            <div className="flex items-center gap-2 text-danger-default mb-2 font-semibold text-sm">
              <AlertCircle className="w-4 h-4" />
              <span>System Error</span>
            </div>
          )}

          {isUser ? (
            <div className="whitespace-pre-wrap">{message.content}</div>
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          )}

          {!isUser && isError && message.traceback && isDev && (
            <div className="mt-4 pt-4 border-t border-danger-default/20">
              <button
                onClick={() => setShowDetails(!showDetails)}
                className="flex items-center gap-2 text-xs font-mono text-text-tertiary hover:text-text-secondary transition-colors"
              >
                <Terminal className="w-3 h-3" />
                <span>TECHNICAL DETAILS</span>
                {showDetails ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
              
              {showDetails && (
                <div className="mt-2 p-3 bg-black/40 rounded border border-white/5 overflow-x-auto">
                  <pre className="text-[10px] leading-tight font-mono text-danger-default/80 whitespace-pre">
                    {message.traceback}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {isUser && (
        <Avatar
          fallback="US"
          className="w-7 h-7 bg-primary-800 text-white shrink-0"
        />
      )}
    </div>
  );
}
