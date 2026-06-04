import React, { useState, useEffect, useRef } from 'react';
import { Search, Plus, Bell, Command, Sparkles, User, Brain, AlertTriangle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface NavbarProps {
  onSearch: (query: string) => void;
  onCreateClick: (mode: 'case' | 'hearing' | 'task') => void;
  onProfileClick: () => void;
  userEmail: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  onSearch,
  onCreateClick,
  onProfileClick,
  userEmail,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifications, setNotifications] = useState([
    {
      id: 1,
      title: 'New Loophole Detected',
      desc: 'Conflict found in SEC Form 10-K deposition schedules vs. cross-examination timelines.',
      time: '2 mins ago',
      type: 'warning',
      read: false,
    },
    {
      id: 2,
      title: 'Evidence Strength Improved',
      desc: 'Patent infringement brief strength index increased by +18% based on recent appellate filings.',
      time: '15 mins ago',
      type: 'success',
      read: false,
    },
    {
      id: 3,
      title: 'Hearing Deadline Approaching',
      desc: 'Motion to dismiss hearing scheduled in U.S. Dist. Court in 48 hours.',
      time: '1 hour ago',
      type: 'info',
      read: true,
    },
  ]);

  const notifRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setShowNotifications(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    onSearch(e.target.value);
  };

  const markAllRead = () => {
    setNotifications(notifications.map(n => ({ ...n, read: true })));
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <header className="h-16 flex items-center justify-between px-6 border-b border-white/5 bg-[#070A13]/40 backdrop-blur-md relative z-20">
      {/* Background Lighting */}
      <div className="absolute top-0 right-1/4 w-96 h-12 bg-brand-blue/5 rounded-full blur-3xl pointer-events-none" />

      {/* Global AI Search Bar */}
      <div className="flex-1 max-w-md relative select-none">
        <div className="relative flex items-center transition-all duration-300 rounded-xl bg-brand-dark/30 backdrop-blur-sm border border-white/10 hover:border-brand-blue/30 focus-within:border-brand-blue/50 focus-within:shadow-[0_0_15px_rgba(79,140,255,0.15)] group">
          <div className="pl-4 pr-1 text-brand-textMuted/60 group-focus-within:text-brand-blue transition-colors duration-300">
            <Search className="w-4 h-4" />
          </div>
          <input
            type="text"
            placeholder="AI Search (Cmd + K) // Find insights, loopholes, evidence..."
            value={searchQuery}
            onChange={handleSearchChange}
            className="block w-full px-3 py-2 text-xs text-white bg-transparent border-none outline-none focus:ring-0 placeholder-brand-textMuted/40"
          />
          {/* AI Sparkle Indicator */}
          {searchQuery && (
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="mr-2 text-brand-blue shrink-0 animate-pulse"
            >
              <Sparkles className="w-3.5 h-3.5" />
            </motion.div>
          )}
          {/* Keycap indicators */}
          <div className="mr-3 flex items-center gap-0.5 px-1.5 py-0.5 rounded border border-white/10 bg-white/5 text-[9px] text-brand-textMuted/40 pointer-events-none select-none font-mono">
            <Command className="w-2.5 h-2.5" />
            <span>K</span>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-4">
        {/* Create Case Button */}
        <motion.button
          whileHover={{ y: -1 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => onCreateClick('case')}
          className="relative h-10 px-4 rounded-xl text-xs font-semibold tracking-wider text-white overflow-hidden shadow-button-glow transition-all duration-300 flex items-center gap-1.5 font-display uppercase group"
        >
          {/* Glowing gradient background */}
          <div className="absolute inset-0 bg-gradient-to-r from-brand-blue to-brand-purple" />
          {/* Shine Sweep Overlay */}
          <div className="absolute top-0 bottom-0 left-[-100%] w-[50%] bg-gradient-to-r from-transparent via-white/20 to-transparent skew-x-[-20deg] group-hover:animate-shine-sweep" />

          <Plus className="w-4 h-4 relative z-10" />
          <span className="relative z-10">New Case</span>
        </motion.button>

        {/* Notifications */}
        <div className="relative" ref={notifRef}>
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className={`w-10 h-10 flex items-center justify-center rounded-xl bg-brand-dark/40 border transition-all duration-300 hover:border-brand-blue/30 text-brand-textMuted hover:text-white ${
              showNotifications ? 'border-brand-blue/40 text-brand-blue bg-brand-blue/5' : 'border-white/10'
            }`}
          >
            <div className="relative">
              <Bell className="w-4.5 h-4.5" />
              {unreadCount > 0 && (
                <span className="absolute -top-1.5 -right-1.5 w-2.5 h-2.5 rounded-full bg-brand-purple border border-[#0B0F19] shadow-[0_0_8px_#7B61FF]" />
              )}
            </div>
          </button>

          {/* Notifications Dropdown Panel */}
          <AnimatePresence>
            {showNotifications && (
              <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                transition={{ duration: 0.2 }}
                className="absolute right-0 mt-2 w-80 md:w-96 rounded-2xl bg-brand-dark border border-white/10 p-4 shadow-2xl z-50 overflow-hidden"
              >
                <div className="flex items-center justify-between border-b border-white/5 pb-2 mb-3">
                  <div className="flex items-center gap-1.5">
                    <Brain className="w-4 h-4 text-brand-blue" />
                    <span className="text-xs font-bold text-white uppercase tracking-wider font-display">
                      Intelligence Alerts
                    </span>
                  </div>
                  {unreadCount > 0 && (
                    <button
                      onClick={markAllRead}
                      className="text-[10px] text-brand-blue hover:underline bg-transparent border-none p-0 cursor-pointer"
                    >
                      Mark all read
                    </button>
                  )}
                </div>

                <div className="space-y-2.5 max-h-[300px] overflow-y-auto pr-1">
                  {notifications.map((n) => (
                    <div
                      key={n.id}
                      className={`p-3 rounded-xl border transition-colors duration-300 flex gap-2.5 ${
                        n.read
                          ? 'bg-white/[0.01] border-white/5'
                          : 'bg-brand-blue/[0.03] border-brand-blue/10 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.02)]'
                      }`}
                    >
                      <div className="shrink-0 mt-0.5">
                        {n.type === 'warning' && (
                          <div className="p-1 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                            <AlertTriangle className="w-3.5 h-3.5" />
                          </div>
                        )}
                        {n.type === 'success' && (
                          <div className="p-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            <Sparkles className="w-3.5 h-3.5" />
                          </div>
                        )}
                        {n.type === 'info' && (
                          <div className="p-1 rounded bg-brand-blue/10 text-brand-blue border border-brand-blue/20">
                            <Brain className="w-3.5 h-3.5" />
                          </div>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-1">
                          <span className="text-xs font-semibold text-white truncate">
                            {n.title}
                          </span>
                          <span className="text-[9px] text-brand-textMuted/40 whitespace-nowrap">
                            {n.time}
                          </span>
                        </div>
                        <p className="text-[10px] text-brand-textMuted leading-normal mt-0.5">
                          {n.desc}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-3.5 border-t border-white/5 pt-2 text-center">
                  <span className="text-[9px] uppercase tracking-wider text-brand-textMuted/30 font-mono">
                    REALTIME LEGAL AI SYNC ACTIVE
                  </span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Profile Avatar Button */}
        <button
          onClick={onProfileClick}
          className="flex items-center gap-2.5 px-3 py-1.5 rounded-xl border border-white/10 hover:border-brand-blue/30 bg-brand-dark/20 hover:bg-brand-dark/40 transition-all duration-300 text-left cursor-pointer group"
        >
          <div className="w-7.5 h-7.5 rounded-lg bg-gradient-to-tr from-brand-blue/20 to-brand-purple/20 border border-brand-blue/30 flex items-center justify-center text-brand-blue group-hover:scale-105 transition-transform duration-300">
            <User className="w-4 h-4" />
          </div>
          <div className="hidden lg:flex flex-col select-none">
            <span className="text-xs font-bold text-white leading-tight font-display">
              {userEmail.split('@')[0]}
            </span>
            <span className="text-[9px] text-brand-textMuted/50 tracking-wider">
              Senior Attorney
            </span>
          </div>
        </button>
      </div>
    </header>
  );
};
