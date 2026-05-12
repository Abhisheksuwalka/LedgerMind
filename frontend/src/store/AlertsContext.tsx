import { createContext, ReactNode, useContext, useState } from 'react';

interface AlertsContextType {
  unreadCount: number;
  setUnreadCount: (count: number) => void;
  decrementUnread: () => void;
  incrementUnread: () => void;
  setToZero: () => void;
}

export const AlertsContext = createContext<AlertsContextType | undefined>(undefined);

export function AlertsContextProvider({ children }: { children: ReactNode }) {
  const [unreadCount, setUnreadCount] = useState<number>(0);

  const decrementUnread = () => setUnreadCount((prev) => Math.max(0, prev - 1));
  const incrementUnread = () => setUnreadCount((prev) => prev + 1);
  const setToZero = () => setUnreadCount(0);

  return (
    <AlertsContext.Provider value={{ unreadCount, setUnreadCount, decrementUnread, incrementUnread, setToZero }}>
      {children}
    </AlertsContext.Provider>
  );
}

export function useAlertsContext() {
  const context = useContext(AlertsContext);
  if (context === undefined) {
    throw new Error('useAlertsContext must be used within an AlertsContextProvider');
  }
  return context;
}
