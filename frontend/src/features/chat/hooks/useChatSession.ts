import { apiFetch } from '@/lib/api';
import { Message } from '@/types/chat';
import { useCallback, useEffect, useState } from 'react';

function generateId() {
  return Math.random().toString(36).substring(2, 9);
}

interface ChatResponse {
  response: string;
  tools_used: string[];
  session_id: string;
  message_count: number;
  error?: string;
  traceback?: string;
  is_error?: boolean;
}

export function useChatSession() {
  const [sessionId, setSessionId] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  useEffect(() => {
    // Initialize session ID from sessionStorage or create a new one
    let currentSessionId = sessionStorage.getItem('chat_session_id');
    if (!currentSessionId) {
      currentSessionId = generateId();
      sessionStorage.setItem('chat_session_id', currentSessionId);
    }
    setSessionId(currentSessionId);
  }, []);

  const clearSession = useCallback(async () => {
    const newSessionId = generateId();
    sessionStorage.setItem('chat_session_id', newSessionId);
    setSessionId(newSessionId);
    setMessages([]);
    // Clear session history on backend (fire-and-forget, non-fatal)
    try {
      if (sessionId) {
        await apiFetch(`/chat/${sessionId}`, { method: 'DELETE' });
      }
    } catch {
      // Non-fatal — Redis key will expire anyway
    }
  }, [sessionId]);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isStreaming) return;

    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsStreaming(true);

    try {
      const result = await apiFetch<ChatResponse>('/chat', {
        method: 'POST',
        body: JSON.stringify({
          session_id: sessionId,
          message: content,
        }),
      });

      const assistantMessage: Message = {
        id: generateId(),
        role: 'assistant',
        content: result.response,
        timestamp: new Date().toISOString(),
        // Attach tools_used so the UI can display ToolCallPills
        toolsUsed: result.tools_used ?? [],
        isError: !!result.is_error,
        traceback: result.traceback,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: generateId(),
        role: 'assistant',
        content: `Sorry, I encountered an error. Please check that the backend is running.\n\n_${(error as Error).message}_`,
        timestamp: new Date().toISOString(),
        toolsUsed: [],
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsStreaming(false);
    }
  }, [sessionId, isStreaming]);

  return {
    sessionId,
    messages,
    isStreaming,
    sendMessage,
    clearSession,
  };
}
