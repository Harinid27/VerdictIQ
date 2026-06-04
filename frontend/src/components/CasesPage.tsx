import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Grid,
  List,
  Search,
  Plus,
  ArrowUpRight,
  FolderOpen,
  Briefcase,
  Trash2,
} from 'lucide-react';

interface Case {
  id: string;
  name: string;
  caseType: string;
  lawyerSide: string;
  lastUpdated: string;
  riskLevel: 'Low' | 'Medium' | 'High';
  evidenceCount: number;
  status: string;
  client: string;
}

interface CasesPageProps {
  cases: Case[];
  onCreateClick: () => void;
  onSelectCase: (caseId: string) => void;
  onDeleteCase: (caseId: string) => void;
  searchQuery: string;
}

export const CasesPage: React.FC<CasesPageProps> = ({
  cases,
  onCreateClick,
  onSelectCase,
  onDeleteCase,
  searchQuery,
}) => {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [statusFilter, setStatusFilter] = useState('All');
  const [riskFilter, setRiskFilter] = useState('All');
  const [typeFilter, setTypeFilter] = useState('All');
  const [localSearch, setLocalSearch] = useState('');

  // Filter cases based on global navbar search OR page local search
  const activeSearch = (localSearch || searchQuery).toLowerCase();

  const filteredCases = cases.filter((c) => {
    const matchesSearch =
      c.name.toLowerCase().includes(activeSearch) ||
      c.client.toLowerCase().includes(activeSearch) ||
      c.caseType.toLowerCase().includes(activeSearch);
    const matchesStatus = statusFilter === 'All' || c.status === statusFilter;
    const matchesRisk = riskFilter === 'All' || c.riskLevel === riskFilter;
    const matchesType = typeFilter === 'All' || c.caseType === typeFilter;

    return matchesSearch && matchesStatus && matchesRisk && matchesType;
  });

  const uniqueTypes = ['All', ...new Set(cases.map((c) => c.caseType))];
  const statuses = ['All', 'Pre-Trial Audit', 'Discovery Phase', 'Trial Active', 'Settled'];

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.04,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, scale: 0.95, y: 15 },
    show: { opacity: 1, scale: 1, y: 0, transition: { type: 'spring' as const, stiffness: 350, damping: 25 } },
  };

  return (
    <div className="space-y-6 select-none">
      {/* Header and Add Workspace Trigger */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold uppercase tracking-wider text-white font-display flex items-center gap-2">
            <FolderOpen className="w-5 h-5 text-brand-blue" />
            Legal Intelligence Workspaces
          </h2>
          <p className="text-xs text-brand-textMuted mt-0.5">
            Manage your AI legal operating systems, case files, and cross-reference repositories.
          </p>
        </div>

        <motion.button
          whileHover={{ y: -1 }}
          whileTap={{ scale: 0.98 }}
          onClick={onCreateClick}
          className="relative h-10 px-5 rounded-xl text-xs font-semibold tracking-wider text-white overflow-hidden shadow-button-glow transition-all duration-300 flex items-center justify-center gap-1.5 font-display uppercase shrink-0"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-brand-blue to-brand-purple" />
          <Plus className="w-4 h-4 relative z-10" />
          <span className="relative z-10">Initialize Workspace</span>
        </motion.button>
      </div>

      {/* Filter and Control Bar */}
      <div className="p-4 rounded-xl bg-brand-dark/45 border border-white/5 flex flex-col lg:flex-row items-center justify-between gap-4">
        <div className="w-full lg:w-auto flex flex-col sm:flex-row items-center gap-3 flex-wrap">
          {/* Internal search */}
          <div className="relative w-full sm:w-60">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-textMuted/40" />
            <input
              type="text"
              placeholder="Search case name or client..."
              value={localSearch}
              onChange={(e) => setLocalSearch(e.target.value)}
              className="w-full bg-[#161f30]/65 border border-white/10 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-brand-textMuted/40 focus:outline-none focus:border-brand-blue/50 transition-all duration-300"
            />
          </div>

          {/* Status Filter */}
          <div className="w-full sm:w-auto flex items-center gap-2">
            <span className="text-[10px] text-brand-textMuted/60 uppercase font-semibold">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-[#161f30] border border-white/10 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-brand-blue/50"
            >
              {statuses.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          {/* Risk Level Filter */}
          <div className="w-full sm:w-auto flex items-center gap-2">
            <span className="text-[10px] text-brand-textMuted/60 uppercase font-semibold">Risk:</span>
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="bg-[#161f30] border border-white/10 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-brand-blue/50"
            >
              <option value="All">All Risk</option>
              <option value="Low">Low Risk</option>
              <option value="Medium">Medium Risk</option>
              <option value="High">High Risk</option>
            </select>
          </div>

          {/* Case Type Filter */}
          <div className="w-full sm:w-auto flex items-center gap-2">
            <span className="text-[10px] text-brand-textMuted/60 uppercase font-semibold">Type:</span>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="bg-[#161f30] border border-white/10 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-brand-blue/50"
            >
              {uniqueTypes.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* View Mode Toggle */}
        <div className="flex items-center gap-2 shrink-0 self-end lg:self-auto">
          <button
            onClick={() => setViewMode('grid')}
            className={`w-9 h-9 rounded-xl border flex items-center justify-center transition-all duration-300 ${
              viewMode === 'grid'
                ? 'bg-brand-blue/10 border-brand-blue/30 text-brand-blue shadow-[0_0_10px_rgba(79,140,255,0.1)]'
                : 'border-white/10 text-brand-textMuted hover:text-white hover:border-white/15'
            }`}
          >
            <Grid className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`w-9 h-9 rounded-xl border flex items-center justify-center transition-all duration-300 ${
              viewMode === 'list'
                ? 'bg-brand-blue/10 border-brand-blue/30 text-brand-blue shadow-[0_0_10px_rgba(79,140,255,0.1)]'
                : 'border-white/10 text-brand-textMuted hover:text-white hover:border-white/15'
            }`}
          >
            <List className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Workspaces List/Grid */}
      {filteredCases.length === 0 ? (
        <div className="text-center py-20 bg-brand-dark/20 rounded-2xl border border-white/5">
          <Briefcase className="w-10 h-10 text-brand-textMuted/30 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-white uppercase tracking-wider">
            No Workspaces Found
          </h3>
          <p className="text-xs text-brand-textMuted/60 mt-1 max-w-sm mx-auto">
            Change your search filters or initialize a new workspace grid using the button above.
          </p>
        </div>
      ) : viewMode === 'grid' ? (
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {filteredCases.map((item) => (
            <motion.div
              key={item.id}
              variants={itemVariants}
              whileHover={{ y: -4 }}
              className="relative group rounded-2xl border border-white/5 bg-[#0e1424]/45 p-6 hover:border-brand-blue/30 transition-all duration-300 shadow-premium-card flex flex-col justify-between"
            >
              {/* Glow accent */}
              <div className="absolute top-0 right-12 w-28 h-[1px] bg-gradient-to-r from-transparent via-brand-blue/20 to-transparent" />

              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-[9px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-brand-textMuted font-bold">
                    {item.caseType}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        item.riskLevel === 'High'
                          ? 'bg-red-500 animate-pulse'
                          : item.riskLevel === 'Medium'
                          ? 'bg-amber-500'
                          : 'bg-emerald-500'
                      }`}
                    />
                    <span className="text-[9px] font-bold text-white uppercase tracking-wider">
                      {item.riskLevel} Risk
                    </span>
                  </div>
                </div>

                <h3
                  onClick={() => onSelectCase(item.id)}
                  className="text-sm font-bold text-white group-hover:text-brand-blue transition-colors duration-300 cursor-pointer line-clamp-2"
                >
                  {item.name}
                </h3>

                <div className="mt-4 space-y-2 border-y border-white/5 py-3 text-[11px] text-brand-textMuted/65">
                  <div className="flex items-center justify-between">
                    <span>Client:</span>
                    <span className="text-white font-medium">{item.client}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Counsel Side:</span>
                    <span className="text-white font-medium">{item.lawyerSide}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Evidence files:</span>
                    <span className="text-brand-blue font-mono font-semibold">
                      {item.evidenceCount} sources
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between mt-5 pt-1">
                <div className="flex flex-col">
                  <span
                    className={`text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border self-start ${
                      item.status === 'Trial Active'
                        ? 'bg-amber-500/10 border-amber-500/20 text-amber-400'
                        : item.status === 'Discovery Phase'
                        ? 'bg-brand-blue/10 border-brand-blue/20 text-brand-blue'
                        : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                    }`}
                  >
                    {item.status}
                  </span>
                  <span className="text-[8px] text-brand-textMuted/40 font-mono mt-1">
                    UPDATED: {item.lastUpdated}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onDeleteCase(item.id)}
                    className="p-2 rounded-lg border border-white/5 hover:border-red-500/20 text-brand-textMuted/55 hover:text-red-400 bg-transparent transition-all duration-300 cursor-pointer"
                    title="Delete Case"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => onSelectCase(item.id)}
                    className="p-2 rounded-lg border border-brand-blue/20 hover:border-brand-blue bg-brand-blue/10 text-brand-blue group-hover:bg-brand-blue group-hover:text-white transition-all duration-300 cursor-pointer flex items-center justify-center"
                  >
                    <ArrowUpRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      ) : (
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="space-y-3.5"
        >
          {filteredCases.map((item) => (
            <motion.div
              key={item.id}
              variants={itemVariants}
              className="relative group rounded-xl border border-white/5 bg-[#0e1424]/45 px-5 py-4 hover:border-brand-blue/30 hover:bg-[#0e1424]/60 transition-all duration-300 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3
                    onClick={() => onSelectCase(item.id)}
                    className="text-xs font-bold text-white group-hover:text-brand-blue transition-colors duration-300 cursor-pointer truncate max-w-[280px]"
                  >
                    {item.name}
                  </h3>
                  <span className="text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-brand-textMuted font-bold">
                    {item.caseType}
                  </span>
                </div>

                <div className="flex items-center gap-3.5 text-[10px] text-brand-textMuted/55 mt-1.5 flex-wrap">
                  <span>
                    Client: <span className="text-brand-textMuted">{item.client}</span>
                  </span>
                  <span className="w-1 h-1 rounded-full bg-white/20" />
                  <span>
                    Counsel: <span className="text-brand-textMuted">{item.lawyerSide}</span>
                  </span>
                  <span className="w-1 h-1 rounded-full bg-white/20" />
                  <span>
                    Evidence Sources:{' '}
                    <span className="text-brand-blue font-mono font-bold">
                      {item.evidenceCount} files
                    </span>
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-4 justify-between sm:justify-end shrink-0">
                <div className="flex flex-col items-start sm:items-end gap-1 select-none">
                  <span
                    className={`text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${
                      item.status === 'Trial Active'
                        ? 'bg-amber-500/10 border-amber-500/20 text-amber-400'
                        : item.status === 'Discovery Phase'
                        ? 'bg-brand-blue/10 border-brand-blue/20 text-brand-blue'
                        : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                    }`}
                  >
                    {item.status}
                  </span>
                  <span className="text-[8px] text-brand-textMuted/40 font-mono mt-0.5">
                    SYNC: {item.lastUpdated}
                  </span>
                </div>

                <div className="flex items-center gap-1.5 select-none">
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${
                      item.riskLevel === 'High' ? 'bg-red-500' : 'bg-emerald-500'
                    }`}
                  />
                  <span className="text-[9px] font-bold text-white tracking-wider">
                    {item.riskLevel}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onDeleteCase(item.id)}
                    className="p-1.5 rounded-lg border border-white/5 hover:border-red-500/25 text-brand-textMuted/55 hover:text-red-400 bg-transparent transition-all duration-300 cursor-pointer"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => onSelectCase(item.id)}
                    className="p-1.5 rounded-lg border border-brand-blue/20 hover:border-brand-blue bg-brand-blue/10 text-brand-blue group-hover:bg-brand-blue group-hover:text-white transition-all duration-300 cursor-pointer"
                  >
                    <ArrowUpRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  );
};
