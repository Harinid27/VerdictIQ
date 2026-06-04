import React, { useState } from 'react';
import {
  User,
  Shield,
  Building,
  Key,
  Award,
  Zap,
  Clock,
  CheckCircle,
  FileCheck,
} from 'lucide-react';

interface ProfilePageProps {
  userEmail: string;
  userName: string;
  organizationName: string;
  userRole: string;
}

export const ProfilePage: React.FC<ProfilePageProps> = ({
  userEmail,
  userName,
  organizationName,
  userRole,
}) => {
  const [specialization, setSpecialization] = useState('Corporate Litigation & Intellectual Property');
  const [barNumber, setBarNumber] = useState('BAR-US-CA-897531');

  return (
    <div className="space-y-6 select-none">
      {/* Page Title */}
      <div>
        <h2 className="text-xl font-bold uppercase tracking-wider text-white font-display flex items-center gap-2">
          <User className="w-5 h-5 text-brand-blue" />
          Attorney Credentials & Profile
        </h2>
        <p className="text-xs text-brand-textMuted mt-0.5">
          View your licensed active operating nodes, firm configurations, and digital identity signatures.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Card & Specialization Info */}
        <div className="lg:col-span-2 space-y-6">
          {/* Main Card */}
          <div className="rounded-2xl bg-brand-dark/45 border border-white/5 p-6 md:p-8 shadow-premium-card relative overflow-hidden flex flex-col sm:flex-row items-center sm:items-start gap-6">
            {/* Ambient Lighting */}
            <div className="absolute top-0 right-12 w-32 h-32 bg-brand-purple/5 rounded-full blur-2xl pointer-events-none" />

            {/* Glowing Avatar */}
            <div className="relative shrink-0 flex items-center justify-center select-none">
              <div className="absolute w-24 h-24 rounded-full bg-gradient-to-br from-brand-blue/30 to-brand-purple/30 blur animate-pulse" />
              <div className="w-20 h-20 rounded-full border border-white/10 bg-brand-dark flex items-center justify-center text-white relative z-10">
                <User className="w-10 h-10 text-brand-blue" />
              </div>
            </div>

            {/* Profile Info Details */}
            <div className="flex-1 text-center sm:text-left">
              <div className="flex flex-col sm:flex-row sm:items-baseline gap-2.5 justify-center sm:justify-start">
                <h3 className="text-lg font-bold font-display text-white">{userName}</h3>
                <span className="px-2 py-0.5 rounded-full bg-brand-blue/10 border border-brand-blue/20 text-[8px] text-brand-blue uppercase tracking-wider font-bold select-none self-center sm:self-auto">
                  LICENSED NODES Active
                </span>
              </div>

              <div className="space-y-2 mt-4 text-xs text-brand-textMuted/75">
                <div className="flex items-center justify-center sm:justify-start gap-2">
                  <Building className="w-4 h-4 text-brand-textMuted/45" />
                  <span>Firm: <strong className="text-white font-medium">{organizationName}</strong></span>
                </div>
                <div className="flex items-center justify-center sm:justify-start gap-2">
                  <Shield className="w-4 h-4 text-brand-textMuted/45" />
                  <span>Role: <strong className="text-white font-medium">{userRole || 'Lead Legal Counsel'}</strong></span>
                </div>
                <div className="flex items-center justify-center sm:justify-start gap-2">
                  <Key className="w-4 h-4 text-brand-textMuted/45" />
                  <span>Work Email: <strong className="text-white font-medium">{userEmail}</strong></span>
                </div>
              </div>
            </div>
          </div>

          {/* Specialization and Bar Registration inputs */}
          <div className="rounded-2xl bg-brand-dark/30 border border-white/5 p-5 md:p-6 shadow-premium-card space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-white font-display border-b border-white/5 pb-2.5 mb-4">
              Licensed Attributes
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-brand-textMuted uppercase tracking-wider mb-1.5">
                  Jurisdiction Specialization
                </label>
                <input
                  type="text"
                  value={specialization}
                  onChange={(e) => setSpecialization(e.target.value)}
                  className="w-full bg-[#161f30]/65 border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-brand-blue/50 transition-all duration-300"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-brand-textMuted uppercase tracking-wider mb-1.5">
                  Digital Bar License Number
                </label>
                <input
                  type="text"
                  value={barNumber}
                  onChange={(e) => setBarNumber(e.target.value)}
                  className="w-full bg-[#161f30]/65 border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-brand-blue/50 transition-all duration-300"
                />
              </div>
            </div>
          </div>
        </div>

        {/* AI Performance Statistics */}
        <div className="rounded-2xl bg-brand-dark/30 border border-white/5 p-5 md:p-6 shadow-premium-card relative overflow-hidden flex flex-col justify-between">
          {/* Subtle panel light */}
          <div className="absolute top-0 right-1/4 w-32 h-[1px] bg-gradient-to-r from-transparent via-brand-purple/20 to-transparent" />

          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-white font-display flex items-center gap-2 border-b border-white/5 pb-2.5 mb-5">
              <Award className="w-4 h-4 text-brand-purple" />
              AI Operational Statistics
            </h3>

            <div className="space-y-4">
              {[
                {
                  label: 'Workspaces Tracked',
                  value: '14 Active',
                  icon: FileCheck,
                  color: 'text-brand-blue',
                },
                {
                  label: 'AI Audit Hours Saved',
                  value: '148 Hours',
                  icon: Clock,
                  color: 'text-brand-purple',
                },
                {
                  label: 'Loophole Accuracy',
                  value: '99.4%',
                  icon: Zap,
                  color: 'text-amber-400',
                },
                {
                  label: 'Briefs Signed',
                  value: '42 Files',
                  icon: CheckCircle,
                  color: 'text-emerald-400',
                },
              ].map((stat) => (
                <div key={stat.label} className="p-3 rounded-xl border border-white/5 bg-brand-dark/20 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    <div className={`p-1.5 rounded-lg bg-white/5 border border-white/10 ${stat.color}`}>
                      <stat.icon className="w-4 h-4" />
                    </div>
                    <span className="text-[10px] uppercase tracking-wider text-brand-textMuted/60 font-semibold font-display">
                      {stat.label}
                    </span>
                  </div>
                  <span className="text-xs font-bold text-white font-mono">
                    {stat.value}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 p-3 bg-brand-purple/[0.02] border border-brand-purple/10 rounded-xl flex items-center justify-between">
            <span className="text-[9px] uppercase tracking-wider text-brand-purple font-bold">
              VERDICT KEY VALIDATED
            </span>
            <span className="text-[8px] font-mono text-brand-textMuted/45 leading-none">
              RSA-4096 NODE
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
