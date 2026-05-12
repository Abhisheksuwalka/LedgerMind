import { useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';

type WSEvent = 'alert' | 'analysis_progress' | 'chat_tool_call';
type Handler = (payload: unknown) => void;

const BASE_RECONNECT_MS = 1_000;
const MAX_RECONNECT_MS = 30_000;

/**
 * WebSocket hook with exponential-backoff reconnect.
 *
 * On `alert` events:  invalidates the ['alerts'] query so the UI refreshes.
 * On `analysis_progress`: calls the optional handler.
 * On `chat_tool_call`:    calls the optional handler.
 */
export function useWebSocket(handlers: Partial<Record<WSEvent, Handler>>) {
  const ws = useRef<WebSocket | null>(null);
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers;

  const queryClient = useQueryClient();
  const reconnectDelay = useRef(BASE_RECONNECT_MS);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const unmounted = useRef(false);

  useEffect(() => {
    unmounted.current = false;

    function connect() {
      if (unmounted.current) return;

      const url = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
      const socket = new WebSocket(url);
      ws.current = socket;

      socket.onopen = () => {
        reconnectDelay.current = BASE_RECONNECT_MS; // reset backoff on success
      };

      socket.onmessage = (event) => {
        try {
          const { type, payload, data } = JSON.parse(event.data);
          const eventType = type as WSEvent;
          const eventPayload = payload ?? data;

          // Built-in: alert event always invalidates the alerts query
          if (eventType === 'alert') {
            queryClient.invalidateQueries({ queryKey: ['alerts'] });
            queryClient.invalidateQueries({ queryKey: ['snapshot'] });
          }

          // Call custom handler if provided
          handlersRef.current[eventType]?.(eventPayload);
        } catch {
          // ignore malformed messages
        }
      };

      socket.onclose = () => {
        if (unmounted.current) return;
        // Exponential backoff reconnect
        reconnectTimer.current = setTimeout(() => {
          reconnectDelay.current = Math.min(reconnectDelay.current * 2, MAX_RECONNECT_MS);
          connect();
        }, reconnectDelay.current);
      };

      socket.onerror = () => {
        socket.close(); // triggers onclose → reconnect
      };
    }

    connect();

    return () => {
      unmounted.current = true;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      ws.current?.close();
    };
  }, [queryClient]);

  return ws;
}
