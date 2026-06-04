import React, { useState } from 'react';
import {
  Settings,
  Brain,
  Bell,
  Eye,
  Lock,
  Sparkles,
  Cpu,
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  // AI Settings
  const [selectedModel, setSelectedModel] = useState('Verdict-GPT 4.5 Supreme');
  const [confidenceThreshold, setConfidenceThreshold] = useState(85);
  const [realtimeAudit, setRealtimeAudit] = useState(true);

  // Notification Settings
  const [notifSound, setNotifSound] = useState(true);
  const [loopholeAlerts, setLoopholeAlerts] = useState(true);

  // Appearance Settings
  const [canvasGlowIntensity, setCanvasGlowIntensity] = useState('medium');
  const [glowingParticles, setGlowingParticles] = useState(true);

  return (
    <div className="space-y-6 select-none">
      {/* Title */}
      <div>
        <h2 className="text-xl font-bold uppercase tracking-wider text-white font-display flex items-center gap-2">
          <Settings className="w-5 h-5 text-brand-blue" />
          Workspace Configurations & Preferences
        </h2>
        <p className="text-xs text-brand-textMuted mt-0.5">
          Fine-tune the legal intelligence engine parameters, visual layouts, and security thresholds.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Core Config Columns */}
        <div className="lg:col-span-2 space-y-6">
          {/* AI INTELLIGENCE ENGINE CONFIG */}
          <div className="rounded-2xl bg-brand-dark/45 border border-white/5 p-6 md:p-8 shadow-premium-card space-y-6">
            <h3 className="text-xs font-bold uppercase tracking-wider text-white font-display flex items-center gap-2 border-b border-white/5 pb-2.5">
              <Brain className="w-4 h-4 text-brand-blue" />
              Legal AI Inference Settings
            </h3>

            {/* Model select */}
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-brand-textMuted uppercase tracking-wider">
                Select Language Model Node
              </label>
              <div className="relative">
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full bg-[#161f30] border border-white/10 rounded-xl px-4 py-3 text-xs text-white focus:outline-none focus:border-brand-blue/50 appearance-none cursor-pointer"
                >
                  <option value="Verdict-GPT 4.5 Supreme">Verdict-GPT 4.5 Supreme (Precision Legal Insights)</option>
                  <option value="Constitutional-LLM 2.0">Constitutional-LLM 2.0 (Strict Jurisprudence Audit)</option>
                  <option value="Appellate-Fast-Inference">Appellate-Fast-Inference (Quick Evidentiary Reviews)</option>
                </select>
                <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-brand-textMuted/45">
                  <Cpu className="w-4 h-4" />
                </div>
              </div>
            </div>

            {/* Threshold slider */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-brand-textMuted uppercase tracking-wider">
                  AI Confidence Threshold Limit
                </span>
                <span className="font-mono text-brand-blue font-bold">
                  {confidenceThreshold}%
                </span>
              </div>
              <input
                type="range"
                min="50"
                max="99"
                value={confidenceThreshold}
                onChange={(e) => setConfidenceThreshold(Number(e.target.value))}
                className="w-full h-1 bg-[#161f30] rounded-lg appearance-none cursor-pointer accent-brand-blue"
              />
              <p className="text-[10px] text-brand-textMuted/50 leading-relaxed mt-1">
                Lower values display more suggestive loophole findings; higher values screen only strict logical discrepancies.
              </p>
            </div>

            {/* Realtime toggle */}
            <div className="flex items-center justify-between p-4 rounded-xl bg-brand-dark/20 border border-white/5 select-none">
              <div className="flex flex-col gap-0.5">
                <span className="text-xs font-bold text-white uppercase tracking-wide">
                  Real-time Loophole Auditing
                </span>
                <span className="text-[10px] text-brand-textMuted/65 leading-relaxed">
                  Run constant checks over evidence listings in the background.
                </span>
              </div>
              <button
                onClick={() => setRealtimeAudit(!realtimeAudit)}
                className={`w-11 h-6 rounded-full p-1 transition-colors duration-300 focus:outline-none cursor-pointer ${
                  realtimeAudit ? 'bg-brand-blue' : 'bg-white/10'
                }`}
              >
                <div
                  className={`w-4 h-4 rounded-full bg-white transition-transform duration-300 ${
                    realtimeAudit ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>
          </div>

          {/* NOTIFICATION PREFERENCES */}
          <div className="rounded-2xl bg-brand-dark/30 border border-white/5 p-5 md:p-6 shadow-premium-card space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-white font-display flex items-center gap-2 border-b border-white/5 pb-2.5">
              <Bell className="w-4 h-4 text-brand-purple" />
              Intelligence Notifications
            </h3>

            {/* Loophole alert toggle */}
            <div className="flex items-center justify-between select-none">
              <div className="flex flex-col gap-0.5">
                <span className="text-xs font-bold text-white uppercase tracking-wide">
                  Critical Loophole Audio Pings
                </span>
                <span className="text-[10px] text-brand-textMuted/55">
                  Play high-frequency audio tone when a loop-conflict is discovered.
                </span>
              </div>
              <button
                onClick={() => setNotifSound(!notifSound)}
                className={`w-11 h-6 rounded-full p-1 transition-colors duration-300 focus:outline-none cursor-pointer ${
                  notifSound ? 'bg-brand-purple' : 'bg-white/10'
                }`}
              >
                <div
                  className={`w-4 h-4 rounded-full bg-white transition-transform duration-300 ${
                    notifSound ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>

            {/* Email reports toggle */}
            <div className="flex items-center justify-between select-none pt-3.5 border-t border-white/5">
              <div className="flex flex-col gap-0.5">
                <span className="text-xs font-bold text-white uppercase tracking-wide">
                  Real-time Case Briefings Email
                </span>
                <span className="text-[10px] text-brand-textMuted/55">
                  Send copy of AI insights to work email address.
                </span>
              </div>
              <button
                onClick={() => setLoopholeAlerts(!loopholeAlerts)}
                className={`w-11 h-6 rounded-full p-1 transition-colors duration-300 focus:outline-none cursor-pointer ${
                  loopholeAlerts ? 'bg-brand-purple' : 'bg-white/10'
                }`}
              >
                <div
                  className={`w-4 h-4 rounded-full bg-white transition-transform duration-300 ${
                    loopholeAlerts ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* SIDE BAR / INTERACTIVE CONFIG */}
        <div className="space-y-6">
          {/* VISUAL & EFFECTS CONFIG */}
          <div className="rounded-2xl bg-brand-dark/30 border border-white/5 p-5 md:p-6 shadow-premium-card space-y-4 select-none">
            <h3 className="text-xs font-bold uppercase tracking-wider text-white font-display flex items-center gap-2 border-b border-white/5 pb-2.5">
              <Eye className="w-4 h-4 text-amber-400" />
              Interface Visual Engine
            </h3>

            {/* Canvas scale selects */}
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-brand-textMuted uppercase tracking-wider">
                Glow Canvas Intensity
              </label>
              <div className="grid grid-cols-3 gap-2">
                {['low', 'medium', 'high'].map((intensity) => (
                  <button
                    key={intensity}
                    onClick={() => setCanvasGlowIntensity(intensity)}
                    className={`py-2 rounded-xl text-xs font-bold uppercase border tracking-wider transition-all duration-300 ${
                      canvasGlowIntensity === intensity
                        ? 'bg-amber-500/15 border-amber-500/30 text-white shadow-[0_0_10px_rgba(245,158,11,0.1)]'
                        : 'bg-[#161f30] border-white/5 text-brand-textMuted hover:border-white/15'
                    }`}
                  >
                    {intensity}
                  </button>
                ))}
              </div>
            </div>

            {/* Particle toggling */}
            <div className="flex items-center justify-between select-none pt-3.5 border-t border-white/5">
              <div className="flex flex-col gap-0.5">
                <span className="text-xs font-bold text-white uppercase tracking-wide">
                  Floating Nodes Canvas
                </span>
                <span className="text-[10px] text-brand-textMuted/55">
                  Animate glowing neural particles in background.
                </span>
              </div>
              <button
                onClick={() => setGlowingParticles(!glowingParticles)}
                className={`w-11 h-6 rounded-full p-1 transition-colors duration-300 focus:outline-none cursor-pointer ${
                  glowingParticles ? 'bg-amber-400' : 'bg-white/10'
                }`}
              >
                <div
                  className={`w-4 h-4 rounded-full bg-white transition-transform duration-300 ${
                    glowingParticles ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>
          </div>

          {/* SYSTEM SECURITY CONFIG */}
          <div className="rounded-2xl bg-brand-dark/30 border border-white/5 p-5 md:p-6 shadow-premium-card space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-white font-display flex items-center gap-2 border-b border-white/5 pb-2.5">
              <Lock className="w-4 h-4 text-emerald-400" />
              Quantum Signature Encryption
            </h3>

            <p className="text-[10px] text-brand-textMuted/65 leading-relaxed">
              Ensure RSA encryption parameters are synchronized with local bar registry.
            </p>

            <button
              onClick={() => alert('Encryption keys regenerated and cataloged successfully.')}
              className="w-full py-2.5 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-brand-blue/35 to-brand-purple/35 border border-brand-blue/30 hover:border-brand-blue shadow-[0_0_10px_rgba(79,140,255,0.05)] transition-all duration-300 cursor-pointer text-center uppercase tracking-widest font-display flex items-center justify-center gap-1.5"
            >
              <Sparkles className="w-4 h-4 shrink-0" />
              <span>Regenerate Signature Key</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
