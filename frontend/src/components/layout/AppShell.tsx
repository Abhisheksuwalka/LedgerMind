import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { UploadModal } from '../modals/UploadModal';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useAlertsContext } from '../../store/AlertsContext';

export function AppShell() {
  const { incrementUnread } = useAlertsContext();

  // Initialize WebSocket connection at the shell level
  useWebSocket({
    alert: (payload) => {
      console.log('WS Alert received:', payload);
      incrementUnread();
    },
    analysis_progress: (payload) => {
      console.log('WS Analysis Progress:', payload);
      // Future: Toast notification
    },
    chat_tool_call: (payload) => {
      console.log('WS Chat Tool Call:', payload);
    }
  });

  return (
    <div className="min-h-[100dvh] bg-bg-base text-primary font-sans antialiased flex flex-col lg:grid lg:grid-cols-[240px_1fr]">
      {/* Desktop Sidebar (hidden on mobile/tablet) */}
      <div className="hidden lg:block sticky top-0 h-[100dvh]">
        <Sidebar />
      </div>

      {/* Mobile/Tablet Topbar (hidden on desktop) */}
      <Topbar />

      {/* Main Content Area */}
      <main className="flex-1 w-full max-w-[1400px] mx-auto flex flex-col min-w-0">
        <Outlet />
      </main>

      {/* Global Modals */}
      <UploadModal />
    </div>
  );
}
