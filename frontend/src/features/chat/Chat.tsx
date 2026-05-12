import { useEffect } from 'react';
import { Trash2 } from 'lucide-react';
import { useChatSession } from './hooks/useChatSession';
import { MessageFeed } from './components/MessageFeed';
import { ChatInput } from './components/ChatInput';
import { SuggestedPrompts } from './components/SuggestedPrompts';

export function Chat() {
  const { messages, isStreaming, sendMessage, clearSession } = useChatSession();

  // Pick up pre-filled prompt set by AnomalyWidget's "Ask CashPilot" button
  useEffect(() => {
    const initialPrompt = sessionStorage.getItem('chat_initial_prompt');
    if (initialPrompt) {
      sessionStorage.removeItem('chat_initial_prompt');
      // Small delay to ensure session ID is initialised
      const timer = setTimeout(() => sendMessage(initialPrompt), 200);
      return () => clearTimeout(timer);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSend = (content: string) => {
    sendMessage(content);
  };

  return (
    <main className="flex flex-col h-[calc(100dvh-56px)] lg:h-dvh overflow-hidden bg-bg-base">
      {/* Header */}
      <header className="flex-shrink-0 flex items-center justify-between px-6 py-4 border-b border-border-subtle bg-bg-base">
        <h1 className="text-2xl font-bold text-primary">Chat with CashPilot</h1>
        <button
          onClick={clearSession}
          className="flex items-center gap-2 px-3 py-1.5 text-sm text-text-tertiary hover:text-danger-default transition-colors rounded-md hover:bg-danger-subtle focus:outline-none focus:ring-2 focus:ring-danger-default"
          aria-label="Clear Session"
        >
          <Trash2 className="w-4 h-4" />
          <span className="hidden sm:inline">Clear Session</span>
        </button>
      </header>

      {/* Main Content Area */}
      {messages.length === 0 ? (
        <SuggestedPrompts onSelect={handleSend} />
      ) : (
        <MessageFeed messages={messages} isStreaming={isStreaming} />
      )}

      {/* Input Area */}
      <ChatInput
        onSend={handleSend}
        isStreaming={isStreaming}
        onStop={() => {
          // Abort controller can be wired here if needed
        }}
      />
    </main>
  );
}
