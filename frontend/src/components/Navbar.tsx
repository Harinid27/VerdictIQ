import React from 'react';
import { Plus, User } from 'lucide-react';
import { motion } from 'framer-motion';

interface NavbarProps {
  onCreateClick: (mode: 'case' | 'hearing' | 'task') => void;
  onProfileClick: () => void;
  userEmail: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  onCreateClick,
  onProfileClick,
  userEmail,
}) => {
  return (
    <header className="h-16 flex items-center justify-between px-6 border-b border-white/5 bg-[#070A13]/40 backdrop-blur-md relative z-20 w-full">
      {/* Background Lighting */}
      <div className="absolute top-0 right-1/4 w-96 h-12 bg-brand-blue/5 rounded-full blur-3xl pointer-events-none" />

      {/* Spacer to align actions to the right */}
      <div className="flex-1" />

      {/* Actions */}
      <div className="flex items-center gap-4">
        {/* Create Case Button */}
        <motion.button
          whileHover={{ y: -1 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => onCreateClick('case')}
          className="relative h-10 px-4 rounded-xl text-xs font-semibold tracking-wider text-white overflow-hidden shadow-button-glow transition-all duration-300 flex items-center gap-1.5 font-display uppercase group cursor-pointer"
        >
          {/* Glowing gradient background */}
          <div className="absolute inset-0 bg-gradient-to-r from-brand-blue to-brand-purple" />
          {/* Shine Sweep Overlay */}
          <div className="absolute top-0 bottom-0 left-[-100%] w-[50%] bg-gradient-to-r from-transparent via-white/20 to-transparent skew-x-[-20deg] group-hover:animate-shine-sweep" />

          <Plus className="w-4 h-4 relative z-10" />
          <span className="relative z-10">New Case</span>
        </motion.button>

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
