import React from 'react';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  Briefcase,
  FileBarChart2,
  Calendar,
  CheckSquare,
  Sparkles,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
  onLogout: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  isCollapsed,
  setIsCollapsed,
  onLogout,
}) => {
  const menuItems = [
    { name: 'Dashboard', icon: LayoutDashboard },
    { name: 'Cases', icon: Briefcase },
    { name: 'Reports', icon: FileBarChart2 },
    { name: 'Calendar', icon: Calendar },
    { name: 'Tasks', icon: CheckSquare },
    { name: 'AI Insights', icon: Sparkles },
    { name: 'Settings', icon: Settings },
  ];

  return (
    <motion.div
      animate={{ width: isCollapsed ? 76 : 260 }}
      transition={{ type: 'spring', damping: 20, stiffness: 200 }}
      className="relative z-30 h-screen flex flex-col border-r border-white/5 bg-[#070A13]/60 backdrop-blur-xl shrink-0"
    >
      {/* Glow border overlay */}
      <div className="absolute top-0 right-0 bottom-0 w-[1px] bg-gradient-to-b from-brand-blue/20 via-white/5 to-brand-purple/20 pointer-events-none" />

      {/* Sidebar Header Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-white/5 relative">
        <div className="flex items-center gap-3 overflow-hidden select-none">
          <div className="relative flex items-center justify-center shrink-0">
            {/* Pulsating background circle */}
            <div className="absolute w-8 h-8 rounded-full bg-brand-blue/20 blur-sm animate-pulse-slow" />
            <svg
              width="28"
              height="28"
              viewBox="0 0 32 32"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="relative z-10 filter drop-shadow-[0_0_6px_rgba(79,140,255,0.4)]"
            >
              <path
                d="M16 2L29.5 9.75V25.25L16 33L2.5 25.25V9.75L16 2Z"
                stroke="url(#sidebar-logo-grad)"
                strokeWidth="2.5"
                strokeLinejoin="round"
              />
              <path
                d="M9 12L16 21L23 12"
                stroke="#4F8CFF"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <circle cx="16" cy="21" r="2" fill="#7B61FF" />
              <defs>
                <linearGradient id="sidebar-logo-grad" x1="2.5" y1="2" x2="29.5" y2="33" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#4F8CFF" />
                  <stop offset="1" stopColor="#7B61FF" />
                </linearGradient>
              </defs>
            </svg>
          </div>

          {!isCollapsed && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              className="flex flex-col"
            >
              <h1 className="text-base font-bold font-display text-white tracking-wide m-0 flex items-center gap-1">
                Verdict<span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-blue to-brand-purple">IQ</span>
              </h1>
              <span className="text-[8px] uppercase tracking-[0.2em] text-brand-blue font-semibold -mt-0.5">
                LEGAL INTEL OS
              </span>
            </motion.div>
          )}
        </div>

        {/* Collapse Button (Desktop Only) */}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="hidden md:flex absolute top-4 -right-3 w-6 h-6 items-center justify-center rounded-full bg-brand-dark border border-white/10 hover:border-brand-blue/50 text-brand-textMuted hover:text-white transition-all duration-300 shadow-[0_0_10px_rgba(0,0,0,0.5)] cursor-pointer"
        >
          {isCollapsed ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto">
        {menuItems.map((item) => {
          const isActive = activeTab === item.name;
          const Icon = item.icon;
          return (
            <button
              key={item.name}
              onClick={() => setActiveTab(item.name)}
              className={`w-full group relative flex items-center gap-3.5 px-3.5 py-3 rounded-xl text-sm transition-all duration-300 font-medium ${
                isActive
                  ? 'text-white bg-white/5 border border-white/10 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]'
                  : 'text-brand-textMuted hover:text-white bg-transparent border border-transparent hover:bg-white/[0.02]'
              }`}
            >
              {/* Active tab glowing pill marker */}
              {isActive && (
                <motion.div
                  layoutId="active-pill"
                  className="absolute left-0 w-[3px] top-3 bottom-3 rounded-r-full bg-gradient-to-b from-brand-blue to-brand-purple"
                  transition={{ type: 'spring', damping: 18, stiffness: 200 }}
                />
              )}

              {/* Glowing Background on hover */}
              <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-brand-blue/5 to-brand-purple/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />

              {/* Icon */}
              <div
                className={`relative z-10 shrink-0 transition-transform duration-300 group-hover:scale-105 ${
                  isActive ? 'text-brand-blue' : 'text-brand-textMuted/70 group-hover:text-brand-blue'
                }`}
              >
                <Icon className="w-5 h-5" />
              </div>

              {/* Text */}
              {!isCollapsed && (
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="relative z-10 text-xs font-semibold tracking-wider font-display uppercase"
                >
                  {item.name}
                </motion.span>
              )}

              {/* Collapsed Tooltip */}
              {isCollapsed && (
                <div className="absolute left-16 px-2.5 py-1.5 rounded-lg bg-[#0E1321] border border-white/10 text-white text-[10px] tracking-wider uppercase font-semibold opacity-0 pointer-events-none group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-300 shadow-xl z-50 whitespace-nowrap">
                  {item.name}
                </div>
              )}
            </button>
          );
        })}
      </nav>

      {/* User Section / Security Seal */}
      <div className="p-3 border-t border-white/5 space-y-2 relative">
        {/* Security Seal */}
        {!isCollapsed && (
          <div className="p-2.5 rounded-xl bg-brand-blue/[0.02] border border-brand-blue/5 flex items-center gap-2 select-none">
            <ShieldCheck className="w-4 h-4 text-brand-blue shrink-0 animate-pulse-slow" />
            <div className="flex flex-col">
              <span className="text-[9px] uppercase tracking-wider text-brand-blue font-bold">
                ENCRYPTED NODES
              </span>
              <span className="text-[7px] font-mono text-brand-textMuted/40 leading-none">
                HASH://VERDICT_SEC_v1.0
              </span>
            </div>
          </div>
        )}

        {/* Logout Button */}
        <button
          onClick={onLogout}
          className="w-full group relative flex items-center gap-3.5 px-3.5 py-3 rounded-xl text-sm text-red-400 hover:text-red-300 transition-all duration-300 font-medium border border-transparent hover:border-red-500/10 hover:bg-red-950/20"
        >
          <div className="relative z-10 shrink-0 group-hover:scale-105 transition-transform duration-300">
            <LogOut className="w-5 h-5 text-red-400/80 group-hover:text-red-300" />
          </div>

          {!isCollapsed && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="relative z-10 text-xs font-semibold tracking-wider font-display uppercase"
            >
              Logout
            </motion.span>
          )}

          {isCollapsed && (
            <div className="absolute left-16 px-2.5 py-1.5 rounded-lg bg-red-950 border border-red-500/20 text-red-300 text-[10px] tracking-wider uppercase font-semibold opacity-0 pointer-events-none group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-300 shadow-xl z-50 whitespace-nowrap">
              Logout
            </div>
          )}
        </button>
      </div>
    </motion.div>
  );
};
