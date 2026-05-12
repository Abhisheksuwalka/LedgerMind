import { Bell, History, LayoutDashboard, MessageSquare, Moon, Settings, Sun, Upload } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { useTheme } from '../../hooks/useTheme';
import { useUploadModal } from '../../hooks/useUploadModal';
import { cn } from '../../lib/cn';
import { useAlertsContext } from '../../store/AlertsContext';
import { Avatar } from '../ui/Avatar';
import { Switch } from '../ui/Switch';

const NAV_ITEMS = [
  { label: 'Snapshot', path: '/', icon: LayoutDashboard },
  { label: 'Chat', path: '/chat', icon: MessageSquare },
  { label: 'Alerts', path: '/alerts', icon: Bell },
  { label: 'History', path: '/history', icon: History },
  { label: 'Settings', path: '/settings', icon: Settings },
];

interface SidebarProps {
  className?: string;
  onNavigate?: () => void; // Optional callback for mobile drawer closing
}

export function Sidebar({ className, onNavigate }: SidebarProps) {
  const { unreadCount } = useAlertsContext();
  const { theme, toggleTheme } = useTheme();
  const { openModal } = useUploadModal();

  return (
    <aside className={cn("flex flex-col h-full bg-bg-raised border-r border-border-subtle", className)}>
      {/* Brand Header */}
      <div className="flex items-center h-16 px-6 border-b border-border-subtle shrink-0">
        <div className="w-7 h-7 flex items-center justify-center text-[20px]">
          💰
        </div>
        <span className="ml-2 text-xl font-bold text-primary">CashPilot</span>
      </div>

      {/* Upload Button */}
      <div className="px-4 pt-4 pb-2 shrink-0">
        <button
          onClick={openModal}
          className="w-full flex items-center justify-center gap-2 h-9 px-4 rounded-lg bg-primary-600 hover:bg-primary-500 text-white text-sm font-semibold transition-colors"
        >
          <Upload size={15} />
          Upload Data
        </button>
      </div>

      {/* Primary Nav Menu */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            onClick={onNavigate}
            className={({ isActive }) => cn(
              "flex items-center gap-3 h-10 px-3 rounded-md transition-colors relative group",
              isActive 
                ? "bg-primary-500/12 text-primary-400" 
                : "text-secondary hover:bg-bg-hover hover:text-primary bg-transparent"
            )}
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-primary-500 rounded-r-md" />
                )}
                <div className="relative">
                  <item.icon size={18} />
                  {item.label === 'Alerts' && unreadCount > 0 && (
                    <span 
                      className="absolute -top-1.5 -right-1.5 min-w-[18px] h-[18px] bg-danger-default text-white rounded-full text-[10px] font-bold flex items-center justify-center px-1 animate-in zoom-in-50 duration-200"
                    >
                      {unreadCount > 99 ? '99+' : unreadCount}
                    </span>
                  )}
                </div>
                <span className="text-sm font-medium">{item.label}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Theme Toggle */}
      <div className="px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-2 text-secondary">
          {theme === 'dark' ? <Moon size={16} /> : <Sun size={16} />}
          <span className="text-sm font-medium">Dark Mode</span>
        </div>
        <Switch 
          checked={theme === 'dark'} 
          onCheckedChange={toggleTheme} 
          aria-label="Toggle theme"
        />
      </div>

      {/* User Profile Snippet */}
      <div className="h-14 px-4 flex items-center shrink-0">
        <Avatar src="" name="User" fallback="JD" />
        <div className="ml-3 overflow-hidden">
          <p className="text-sm font-medium text-primary truncate">Jane Doe</p>
          <p className="text-xs text-tertiary truncate">jane@example.com</p>
        </div>
      </div>
    </aside>
  );
}
