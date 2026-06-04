import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Briefcase,
  Calendar,
  CheckSquare,
  AlertTriangle,
  FileBarChart2,
  ChevronRight,
  TrendingUp,
  Brain,
  Scale,
  Activity,
  Award,
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

interface Hearing {
  id: string;
  caseName: string;
  date: string;
  court: string;
  priority: 'Low' | 'Medium' | 'High';
}

interface Task {
  id: string;
  title: string;
  dueDate: string;
  caseName: string;
  completed: boolean;
  priority: 'Low' | 'Medium' | 'High';
}

interface Insight {
  id: string;
  title: string;
  desc: string;
  time: string;
  type: 'critical' | 'strength' | 'strategy';
}

interface DashboardOverviewProps {
  cases: Case[];
  hearings: Hearing[];
  tasks: Task[];
  insights: Insight[];
  reportsCount: number;
  toggleTaskComplete: (id: string) => void;
  onViewAllCases: () => void;
  onViewAllTasks: () => void;
  onViewAllHearings: () => void;
  onQuickAccessCase: (caseId: string) => void;
}

// Simple CountUp Utility
const CountUp: React.FC<{ value: number }> = ({ value }) => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let start = 0;
    const end = value;
    if (start === end) return;

    const totalDuration = 1000; // 1s duration
    const incrementTime = Math.abs(Math.floor(totalDuration / end));

    const timer = setInterval(() => {
      start += 1;
      setCount(start);
      if (start >= end) clearInterval(timer);
    }, Math.max(incrementTime, 20));

    return () => clearInterval(timer);
  }, [value]);

  return <>{count}</>;
};

export const DashboardOverview: React.FC<DashboardOverviewProps> = ({
  cases,
  hearings,
  tasks,
  insights,
  reportsCount,
  toggleTaskComplete,
  onViewAllCases,
  onViewAllTasks,
  onViewAllHearings,
  onQuickAccessCase,
}) => {
  const pendingTasksCount = tasks.filter((t) => !t.completed).length;
  const highRiskCasesCount = cases.filter((c) => c.riskLevel === 'High').length;

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: 'spring' as const, stiffness: 300, damping: 24 } },
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      {/* SECTION 1 — ANALYTICS OVERVIEW */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {[
          {
            title: 'Total Cases',
            value: cases.length,
            icon: Briefcase,
            glow: 'from-brand-blue/20 to-transparent',
            borderColor: 'hover:border-brand-blue/30',
            iconColor: 'text-brand-blue',
          },
          {
            title: 'Upcoming Hearings',
            value: hearings.length,
            icon: Calendar,
            glow: 'from-amber-500/10 to-transparent',
            borderColor: 'hover:border-amber-500/20',
            iconColor: 'text-amber-400',
          },
          {
            title: 'Pending Tasks',
            value: pendingTasksCount,
            icon: CheckSquare,
            glow: 'from-brand-purple/20 to-transparent',
            borderColor: 'hover:border-brand-purple/30',
            iconColor: 'text-brand-purple',
          },
          {
            title: 'High Risk Cases',
            value: highRiskCasesCount,
            icon: AlertTriangle,
            glow: 'from-red-500/15 to-transparent',
            borderColor: 'hover:border-red-500/25',
            iconColor: 'text-red-400',
          },
          {
            title: 'Generated Reports',
            value: reportsCount,
            icon: FileBarChart2,
            glow: 'from-emerald-500/10 to-transparent',
            borderColor: 'hover:border-emerald-500/20',
            iconColor: 'text-emerald-400',
          },
        ].map((card) => (
          <motion.div
            key={card.title}
            variants={itemVariants}
            whileHover={{ y: -3, scale: 1.01 }}
            className={`relative rounded-2xl bg-brand-dark/45 border border-white/5 p-4 flex flex-col justify-between overflow-hidden cursor-pointer transition-all duration-300 shadow-premium-card ${card.borderColor} group`}
          >
            {/* Ambient inner glow */}
            <div className={`absolute -right-4 -bottom-4 w-20 h-20 bg-gradient-to-br ${card.glow} rounded-full blur-xl pointer-events-none group-hover:scale-125 transition-transform duration-500`} />

            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase tracking-wider text-brand-textMuted/60 font-semibold font-display">
                {card.title}
              </span>
              <div className={`p-1.5 rounded-lg bg-white/5 border border-white/10 ${card.iconColor}`}>
                <card.icon className="w-4 h-4" />
              </div>
            </div>

            <div className="mt-4 flex items-baseline gap-1.5">
              <span className="text-2xl font-bold font-display text-white tracking-tight">
                <CountUp value={card.value} />
              </span>
              <span className="text-[10px] text-brand-textMuted/40 font-mono">
                // SYSTEM_SYNC
              </span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* SECTION 2 & 3: Cases & Hearings Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* SECTION 2 — RECENT CASE WORKSPACES */}
        <motion.div
          variants={itemVariants}
          className="lg:col-span-2 rounded-2xl bg-brand-dark/30 border border-white/5 p-5 md:p-6 shadow-premium-card relative overflow-hidden flex flex-col"
        >
          {/* Subtle panel light */}
          <div className="absolute top-0 right-1/4 w-72 h-[1px] bg-gradient-to-r from-transparent via-brand-blue/20 to-transparent" />

          <div className="flex items-center justify-between mb-5 select-none">
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-white font-display flex items-center gap-2">
                <Scale className="w-4 h-4 text-brand-blue" />
                Active Legal Workspaces
              </h3>
              <p className="text-[10px] text-brand-textMuted mt-0.5">
                AI intelligence and evidence compilation status.
              </p>
            </div>
            <button
              onClick={onViewAllCases}
              className="group flex items-center gap-1 text-[10px] text-brand-blue hover:text-white transition-colors uppercase tracking-widest font-semibold"
            >
              <span>View All</span>
              <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </button>
          </div>

          <div className="space-y-3.5 flex-1">
            {cases.slice(0, 3).map((item) => (
              <div
                key={item.id}
                onClick={() => onQuickAccessCase(item.id)}
                className="group relative rounded-xl border border-white/5 bg-brand-dark/25 p-4 hover:border-brand-blue/30 hover:bg-brand-dark/50 transition-all duration-300 cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                {/* Accent glow on hover */}
                <div className="absolute inset-y-0 left-0 w-[2px] bg-brand-blue scale-y-0 group-hover:scale-y-100 transition-transform duration-300 rounded-l" />

                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h4 className="text-xs font-bold text-white group-hover:text-brand-blue transition-colors truncate max-w-[280px]">
                      {item.name}
                    </h4>
                    <span className="px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-[9px] text-brand-textMuted uppercase font-semibold">
                      {item.caseType}
                    </span>
                  </div>
                  <div className="flex items-center gap-3.5 text-[10px] text-brand-textMuted/60 mt-1.5 flex-wrap">
                    <span>
                      Client:{' '}
                      <span className="text-brand-textMuted font-medium">{item.client}</span>
                    </span>
                    <span className="w-1 h-1 rounded-full bg-white/20" />
                    <span>
                      Side:{' '}
                      <span className="text-brand-textMuted font-medium">{item.lawyerSide}</span>
                    </span>
                    <span className="w-1 h-1 rounded-full bg-white/20" />
                    <span>
                      Evidence:{' '}
                      <span className="text-brand-blue font-mono font-bold">
                        {item.evidenceCount} files
                      </span>
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-4 shrink-0 justify-between md:justify-end">
                  <div className="flex flex-col items-start md:items-end gap-1.5">
                    <span
                      className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider ${
                        item.status === 'Trial Active'
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          : item.status === 'Discovery Phase'
                          ? 'bg-brand-blue/10 text-brand-blue border border-brand-blue/20'
                          : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      }`}
                    >
                      {item.status}
                    </span>
                    <span className="text-[8px] text-brand-textMuted/40 font-mono">
                      SYNCED: {item.lastUpdated}
                    </span>
                  </div>

                  <div className="flex flex-col items-start md:items-end gap-1">
                    <span
                      className={`text-[9px] font-bold tracking-wide flex items-center gap-1 ${
                        item.riskLevel === 'High'
                          ? 'text-red-400'
                          : item.riskLevel === 'Medium'
                          ? 'text-amber-400'
                          : 'text-emerald-400'
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          item.riskLevel === 'High'
                            ? 'bg-red-500 animate-pulse'
                            : item.riskLevel === 'Medium'
                            ? 'bg-amber-500'
                            : 'bg-emerald-500'
                        }`}
                      />
                      {item.riskLevel} Risk
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* SECTION 3 — UPCOMING HEARINGS TIMELINE */}
        <motion.div
          variants={itemVariants}
          className="rounded-2xl bg-brand-dark/30 border border-white/5 p-5 md:p-6 shadow-premium-card flex flex-col relative overflow-hidden"
        >
          {/* Subtle panel light */}
          <div className="absolute top-0 right-1/4 w-40 h-[1px] bg-gradient-to-r from-transparent via-brand-purple/20 to-transparent" />

          <div className="flex items-center justify-between mb-5 select-none">
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-white font-display flex items-center gap-2">
                <Calendar className="w-4 h-4 text-amber-400" />
                Hearings Timeline
              </h3>
              <p className="text-[10px] text-brand-textMuted mt-0.5">
                Next upcoming schedule briefs.
              </p>
            </div>
            <button
              onClick={onViewAllHearings}
              className="group flex items-center gap-1 text-[10px] text-brand-blue hover:text-white transition-colors uppercase tracking-widest font-semibold"
            >
              <span>Schedule</span>
              <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </button>
          </div>

          <div className="flex-1 relative pl-5 space-y-4">
            {/* Timeline connector line */}
            <div className="absolute top-2.5 bottom-2.5 left-2 w-[1px] bg-gradient-to-b from-amber-400/50 via-white/5 to-transparent" />

            {hearings.slice(0, 3).map((item) => {
              const formattedDate = new Date(item.date).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              });

              return (
                <div key={item.id} className="relative group select-none">
                  {/* Timeline dot */}
                  <div
                    className={`absolute -left-[17px] top-1 w-2.5 h-2.5 rounded-full border border-[#0B0F19] transition-transform duration-300 group-hover:scale-125 ${
                      item.priority === 'High'
                        ? 'bg-red-500 shadow-[0_0_8px_#ef4444]'
                        : item.priority === 'Medium'
                        ? 'bg-amber-400 shadow-[0_0_8px_#f59e0b]'
                        : 'bg-brand-blue shadow-[0_0_8px_#3b82f6]'
                    }`}
                  />

                  <div className="flex flex-col">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold text-white group-hover:text-brand-blue transition-colors duration-200">
                        {item.caseName}
                      </span>
                      <span
                        className={`text-[8px] font-bold uppercase tracking-wider ${
                          item.priority === 'High'
                            ? 'text-red-400'
                            : item.priority === 'Medium'
                            ? 'text-amber-400'
                            : 'text-brand-blue'
                        }`}
                      >
                        {item.priority}
                      </span>
                    </div>

                    <span className="text-[10px] text-amber-400/90 font-mono mt-0.5">
                      {formattedDate}
                    </span>

                    <span className="text-[9px] text-brand-textMuted/60 truncate mt-1">
                      {item.court}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>
      </div>

      {/* SECTION 4 & 5: Tasks & Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* SECTION 4 — TASKS PANEL */}
        <motion.div
          variants={itemVariants}
          className="rounded-2xl bg-brand-dark/30 border border-white/5 p-5 md:p-6 shadow-premium-card flex flex-col relative overflow-hidden"
        >
          {/* Subtle panel light */}
          <div className="absolute top-0 right-1/4 w-72 h-[1px] bg-gradient-to-r from-transparent via-brand-purple/20 to-transparent" />

          <div className="flex items-center justify-between mb-5 select-none">
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-white font-display flex items-center gap-2">
                <CheckSquare className="w-4 h-4 text-brand-purple" />
                Intelligence Checklist
              </h3>
              <p className="text-[10px] text-brand-textMuted mt-0.5">
                Task items linking analysis parameters.
              </p>
            </div>
            <button
              onClick={onViewAllTasks}
              className="group flex items-center gap-1 text-[10px] text-brand-blue hover:text-white transition-colors uppercase tracking-widest font-semibold"
            >
              <span>Board</span>
              <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </button>
          </div>

          <div className="space-y-2.5 flex-1">
            {tasks.slice(0, 4).map((task) => (
              <div
                key={task.id}
                className={`relative rounded-xl border p-3 flex.items-start justify-between flex items-center gap-3 transition-all duration-300 select-none ${
                  task.completed
                    ? 'bg-white/[0.01] border-white/5 opacity-55'
                    : 'bg-brand-dark/25 border-white/5 hover:border-brand-purple/25 hover:bg-brand-dark/40'
                }`}
              >
                <div className="flex items-center gap-3 min-w-0">
                  {/* Custom Checkbox */}
                  <button
                    onClick={() => toggleTaskComplete(task.id)}
                    className={`shrink-0 w-4.5 h-4.5 rounded border transition-all duration-300 flex items-center justify-center cursor-pointer ${
                      task.completed
                        ? 'bg-brand-purple border-brand-purple text-white'
                        : 'border-white/20 hover:border-brand-purple/50 bg-brand-dark'
                    }`}
                  >
                    {task.completed && (
                      <motion.svg
                        initial={{ scale: 0.6 }}
                        animate={{ scale: 1 }}
                        className="w-3 h-3 font-bold"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth="4"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </motion.svg>
                    )}
                  </button>

                  <div className="min-w-0">
                    <p
                      className={`text-xs font-medium text-white transition-all duration-300 truncate ${
                        task.completed ? 'line-through text-brand-textMuted/55' : ''
                      }`}
                    >
                      {task.title}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[9px] text-brand-textMuted/40 font-mono">
                        CASE: {task.caseName}
                      </span>
                      <span className="text-[9px] text-brand-textMuted/30 font-mono">//</span>
                      <span className="text-[9px] text-brand-textMuted/40 font-mono">
                        DUE: {task.dueDate}
                      </span>
                    </div>
                  </div>
                </div>

                <span
                  className={`shrink-0 text-[8px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${
                    task.priority === 'High'
                      ? 'bg-red-500/10 border-red-500/20 text-red-400'
                      : task.priority === 'Medium'
                      ? 'bg-brand-purple/10 border-brand-purple/20 text-brand-purple'
                      : 'bg-brand-blue/10 border-brand-blue/20 text-brand-blue'
                  }`}
                >
                  {task.priority}
                </span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* SECTION 5 — AI INSIGHTS FEED */}
        <motion.div
          variants={itemVariants}
          className="rounded-2xl bg-brand-dark/30 border border-white/5 p-5 md:p-6 shadow-premium-card flex flex-col relative overflow-hidden"
        >
          {/* Subtle panel light */}
          <div className="absolute top-0 right-1/4 w-72 h-[1px] bg-gradient-to-r from-transparent via-brand-blue/20 to-transparent" />

          <div className="flex items-center justify-between mb-5 select-none">
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-white font-display flex items-center gap-2">
                <Brain className="w-4 h-4 text-brand-blue" />
                AI Intelligence Activity Feed
              </h3>
              <p className="text-[10px] text-brand-textMuted mt-0.5">
                Real-time legal loophole audit feed.
              </p>
            </div>
            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-brand-blue/10 border border-brand-blue/20 text-[9px] text-brand-blue font-bold uppercase tracking-wider animate-pulse select-none">
              <Activity className="w-3.5 h-3.5" />
              <span>Syncing Live</span>
            </span>
          </div>

          <div className="space-y-3.5 flex-1">
            {insights.slice(0, 3).map((item) => (
              <div
                key={item.id}
                className="group relative rounded-xl border border-white/5 bg-brand-dark/25 p-3.5 hover:border-brand-blue/20 hover:bg-brand-dark/40 transition-all duration-300"
              >
                <div className="flex items-start gap-3">
                  <div className="shrink-0 mt-0.5 select-none">
                    {item.type === 'critical' ? (
                      <span className="flex items-center justify-center w-5.5 h-5.5 rounded bg-red-500/10 border border-red-500/20 text-red-400">
                        <AlertTriangle className="w-3.5 h-3.5" />
                      </span>
                    ) : item.type === 'strength' ? (
                      <span className="flex items-center justify-center w-5.5 h-5.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                        <TrendingUp className="w-3.5 h-3.5" />
                      </span>
                    ) : (
                      <span className="flex items-center justify-center w-5.5 h-5.5 rounded bg-brand-blue/10 border border-brand-blue/20 text-brand-blue">
                        <Award className="w-3.5 h-3.5" />
                      </span>
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1 select-none">
                      <span className="text-xs font-bold text-white">
                        {item.title}
                      </span>
                      <span className="text-[8px] text-brand-textMuted/45 font-mono">
                        {item.time}
                      </span>
                    </div>
                    <p className="text-[10px] text-brand-textMuted/90 leading-relaxed mt-1">
                      {item.desc}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
};
