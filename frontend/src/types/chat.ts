export interface ToolCall {
  id: string;
  name: string;
  status: 'in-progress' | 'complete';
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  toolCall?: ToolCall;
  /** Names of financial tools invoked by the agent (e.g. 'compute_pnl') */
  toolsUsed?: string[];
  isError?: boolean;
  traceback?: string;
}


export interface ChatSession {
  id: string;
  messages: Message[];
}
