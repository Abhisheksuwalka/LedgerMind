import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import Showcase from './pages/Showcase';
import { AlertsContextProvider } from './store/AlertsContext';
import { AppContextProvider } from './store/AppContext';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Chat } from './features/chat/Chat';
import Snapshot from './features/snapshot/Snapshot';
import Settings from './features/settings/Settings';
import Alerts from './features/alerts/Alerts';
import History from './features/history/History';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContextProvider>
        <AlertsContextProvider>
          <Routes>
            <Route path="/" element={<AppShell />}>
              <Route index element={<Snapshot />} />
              <Route path="chat" element={<Chat />} />
              <Route path="alerts" element={<Alerts />} />
              <Route path="history" element={<History />} />
              <Route path="settings" element={<Settings />} />
            </Route>
            <Route path="/showcase" element={<Showcase />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AlertsContextProvider>
      </AppContextProvider>
    </QueryClientProvider>
  );
}
