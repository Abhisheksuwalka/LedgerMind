import { useState } from 'react';
import { Menu, X } from 'lucide-react';
import { Button } from '../ui/Button';
import { Sidebar } from './Sidebar';
import { useUploadModal } from '../../hooks/useUploadModal';
import { cn } from '../../lib/cn';

export function Topbar() {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const { openModal } = useUploadModal();

  const closeDrawer = () => setIsDrawerOpen(false);

  return (
    <>
      <header className="sticky top-0 z-40 h-14 bg-bg-raised border-b border-border-subtle flex items-center justify-between px-4 lg:hidden">
        <button 
          onClick={() => setIsDrawerOpen(true)}
          className="p-2 text-secondary hover:text-primary transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 rounded-md"
          aria-label="Open menu"
        >
          <Menu size={24} />
        </button>

        <div className="text-xl font-bold text-primary flex items-center">
          <span className="mr-2 text-[18px]">💰</span>
          CashPilot
        </div>

        <Button onClick={openModal} size="sm" intent="primary">
          Upload
        </Button>
      </header>

      {/* Mobile Drawer Overlay */}
      {isDrawerOpen && (
        <div 
          className="fixed inset-0 z-50 bg-black/50 backdrop-blur-[4px] animate-in fade-in duration-300 lg:hidden"
          onClick={closeDrawer}
          aria-hidden="true"
        />
      )}

      {/* Mobile Drawer Panel */}
      <div
        className={cn(
          "fixed top-0 bottom-0 left-0 z-50 w-[280px] bg-bg-raised transform transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] lg:hidden",
          isDrawerOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <Sidebar className="border-r-0" onNavigate={closeDrawer} />
        
        {/* Close Button overlayed inside drawer */}
        <button
          onClick={closeDrawer}
          className="absolute top-4 right-4 p-2 text-tertiary hover:text-primary transition-colors bg-bg-raised/80 rounded-full backdrop-blur-sm"
          aria-label="Close menu"
        >
          <X size={20} />
        </button>
      </div>
    </>
  );
}
