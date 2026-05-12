import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type Theme = 'light' | 'dark';

interface AppContextType {
  businessId: string;
  setBusinessId: (id: string) => void;
  theme: Theme;
  setTheme: (theme: Theme) => void;
  isUploadModalOpen: boolean;
  setIsUploadModalOpen: (isOpen: boolean) => void;
  lastSyncedAt: string | null;
  setLastSyncedAt: (timestamp: string | null) => void;
}

export const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppContextProvider({ children }: { children: ReactNode }) {
  const [businessId, setBusinessId] = useState<string>('default-business');
  const [theme, setTheme] = useState<Theme>('dark');
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [lastSyncedAt, setLastSyncedAt] = useState<string | null>(null);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'light') {
      root.setAttribute('data-theme', 'light');
    } else {
      root.removeAttribute('data-theme');
    }
  }, [theme]);

  return (
    <AppContext.Provider
      value={{
        businessId,
        setBusinessId,
        theme,
        setTheme,
        isUploadModalOpen,
        setIsUploadModalOpen,
        lastSyncedAt,
        setLastSyncedAt,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppContextProvider');
  }
  return context;
}
