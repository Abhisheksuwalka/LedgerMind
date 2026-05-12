import { useEffect, useRef } from 'react';
import { Message } from '@/types/chat';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';

interface MessageFeedProps {
  messages: Message[];
  isStreaming: boolean;
}

export function MessageFeed({ messages, isStreaming }: MessageFeedProps) {
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  return (
    <div className="flex-1 overflow-y-auto scroll-smooth p-6 pb-2 custom-scrollbar">
      <div className="flex flex-col gap-4 max-w-4xl mx-auto w-full">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isStreaming && <TypingIndicator />}
        <div ref={endOfMessagesRef} className="h-1" />
      </div>
    </div>
  );
}
