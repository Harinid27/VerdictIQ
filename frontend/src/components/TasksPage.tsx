import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  CheckSquare,
  Plus,
  Grid,
  List,
  Calendar,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Briefcase,
  Play,
  Check,
} from 'lucide-react';

interface Task {
  id: string;
  title: string;
  dueDate: string;
  caseName: string;
  caseId: string;
  completed: boolean;
  priority: 'Low' | 'Medium' | 'High';
}

interface TasksPageProps {
  tasks: Task[];
  casesList: Array<{ id: string; name: string }>;
  onToggleComplete: (id: string) => void;
  onCreateTask: () => void;
  onDeleteTask?: (id: string) => void;
}

export const TasksPage: React.FC<TasksPageProps> = ({
  tasks,
  casesList,
  onToggleComplete,
  onCreateTask,
  onDeleteTask,
}) => {
  const [viewMode, setViewMode] = useState<'board' | 'list'>('list');
  const [caseFilter, setCaseFilter] = useState('All');
  const [priorityFilter, setPriorityFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All'); // All, Pending, Completed

  // Filter tasks
  const filteredTasks = tasks.filter((t) => {
    const matchesCase = caseFilter === 'All' || t.caseId === caseFilter;
    const matchesPriority = priorityFilter === 'All' || t.priority === priorityFilter;
    const matchesStatus =
      statusFilter === 'All' ||
      (statusFilter === 'Completed' && t.completed) ||
      (statusFilter === 'Pending' && !t.completed);

    return matchesCase && matchesPriority && matchesStatus;
  });

  // Kanban Columns: To Do (Pending Low/Medium), In Progress (Pending High), Completed (Completed)
  const todoTasks = filteredTasks.filter((t) => !t.completed && (t.priority === 'Low' || t.priority === 'Medium'));
  const inProgressTasks = filteredTasks.filter((t) => !t.completed && t.priority === 'High');
  const completedTasks = filteredTasks.filter((t) => t.completed);

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
    hidden: { opacity: 0, y: 12 },
    show: { opacity: 1, y: 0, transition: { type: 'spring' as const, stiffness: 350, damping: 25 } },
  };

  return (
    <div className="space-y-6 select-none">
      {/* Header and Add Task */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold uppercase tracking-wider text-white font-display flex items-center gap-2">
            <CheckSquare className="w-5 h-5 text-brand-blue" />
            Intelligence Tasks Workspace
          </h2>
          <p className="text-xs text-brand-textMuted mt-0.5">
            Audit checklists, analyze loophole reports, and track document signings.
          </p>
        </div>

        <motion.button
          whileHover={{ y: -1 }}
          whileTap={{ scale: 0.98 }}
          onClick={onCreateTask}
          className="relative h-10 px-5 rounded-xl text-xs font-semibold tracking-wider text-white overflow-hidden shadow-button-glow transition-all duration-300 flex items-center justify-center gap-1.5 font-display uppercase shrink-0"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-brand-blue to-brand-purple" />
          <Plus className="w-4 h-4 relative z-10" />
          <span className="relative z-10">Add Checklist Item</span>
        </motion.button>
      </div>

      {/* Control / Filter Bar */}
      <div className="p-4 rounded-xl bg-brand-dark/45 border border-white/5 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="w-full md:w-auto flex flex-col sm:flex-row items-center gap-3 flex-wrap">
          {/* Case Filter */}
          <div className="w-full sm:w-auto flex items-center gap-2">
            <span className="text-[10px] text-brand-textMuted/60 uppercase font-semibold">Case:</span>
            <select
              value={caseFilter}
              onChange={(e) => setCaseFilter(e.target.value)}
              className="bg-[#161f30] border border-white/10 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-brand-blue/50 max-w-[200px]"
            >
              <option value="All">All Cases</option>
              {casesList.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Priority Filter */}
          <div className="w-full sm:w-auto flex items-center gap-2">
            <span className="text-[10px] text-brand-textMuted/60 uppercase font-semibold">Priority:</span>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="bg-[#161f30] border border-white/10 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-brand-blue/50"
            >
              <option value="All">All Priority</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
            </select>
          </div>

          {/* Status Filter */}
          <div className="w-full sm:w-auto flex items-center gap-2">
            <span className="text-[10px] text-brand-textMuted/60 uppercase font-semibold">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-[#161f30] border border-white/10 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-brand-blue/50"
            >
              <option value="All">All Items</option>
              <option value="Pending">Pending</option>
              <option value="Completed">Completed</option>
            </select>
          </div>
        </div>

        {/* View Mode Toggle */}
        <div className="flex items-center gap-2 shrink-0 self-end md:self-auto">
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
          <button
            onClick={() => setViewMode('board')}
            className={`w-9 h-9 rounded-xl border flex items-center justify-center transition-all duration-300 ${
              viewMode === 'board'
                ? 'bg-brand-blue/10 border-brand-blue/30 text-brand-blue shadow-[0_0_10px_rgba(79,140,255,0.1)]'
                : 'border-white/10 text-brand-textMuted hover:text-white hover:border-white/15'
            }`}
          >
            <Grid className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Render Tasks List or Kanban Board */}
      {filteredTasks.length === 0 ? (
        <div className="text-center py-20 bg-brand-dark/20 rounded-2xl border border-white/5">
          <CheckSquare className="w-10 h-10 text-brand-textMuted/30 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-white uppercase tracking-wider">
            No Tasks Found
          </h3>
          <p className="text-xs text-brand-textMuted/60 mt-1 max-w-sm mx-auto">
            Try adjusting your search criteria or add new audit checkpoints.
          </p>
        </div>
      ) : viewMode === 'list' ? (
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="space-y-3.5"
        >
          {filteredTasks.map((task) => (
            <motion.div
              key={task.id}
              variants={itemVariants}
              className={`relative rounded-xl border px-5 py-4 transition-all duration-300 flex items-center justify-between gap-4 ${
                task.completed
                  ? 'bg-white/[0.01] border-white/5 opacity-55'
                  : 'bg-brand-dark/25 border-white/5 hover:border-brand-blue/20 hover:bg-[#0e1424]/40'
              }`}
            >
              <div className="flex items-center gap-4 min-w-0">
                {/* Custom glowing checkbox */}
                <button
                  onClick={() => onToggleComplete(task.id)}
                  className={`shrink-0 w-5 h-5 rounded border transition-all duration-300 flex items-center justify-center cursor-pointer ${
                    task.completed
                      ? 'bg-brand-purple border-brand-purple text-white shadow-[0_0_8px_#7B61FF]'
                      : 'border-white/20 hover:border-brand-purple/50 bg-brand-dark'
                  }`}
                >
                  {task.completed && (
                    <motion.div initial={{ scale: 0.6 }} animate={{ scale: 1 }}>
                      <Check className="w-3.5 h-3.5 stroke-[3px]" />
                    </motion.div>
                  )}
                </button>

                <div className="min-w-0">
                  <p
                    className={`text-xs font-bold text-white transition-all duration-300 truncate ${
                      task.completed ? 'line-through text-brand-textMuted/55' : ''
                    }`}
                  >
                    {task.title}
                  </p>
                  <div className="flex items-center gap-3.5 mt-1.5 text-[10px] text-brand-textMuted/65 flex-wrap">
                    <span className="flex items-center gap-1">
                      <Briefcase className="w-3.5 h-3.5 text-brand-textMuted/45" />
                      <span>{task.caseName}</span>
                    </span>
                    <span className="w-1 h-1 rounded-full bg-white/20" />
                    <span className="flex items-center gap-1 font-mono">
                      <Calendar className="w-3.5 h-3.5 text-brand-textMuted/45" />
                      <span>DUE: {task.dueDate}</span>
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3.5 shrink-0 select-none">
                <span
                  className={`text-[8px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded border ${
                    task.priority === 'High'
                      ? 'bg-red-500/10 border-red-500/20 text-red-400'
                      : task.priority === 'Medium'
                      ? 'bg-brand-purple/10 border-brand-purple/20 text-brand-purple'
                      : 'bg-brand-blue/10 border-brand-blue/20 text-brand-blue'
                  }`}
                >
                  {task.priority} Priority
                </span>

                {onDeleteTask && (
                  <button
                    onClick={() => onDeleteTask(task.id)}
                    className="p-1 rounded text-brand-textMuted/40 hover:text-red-400 bg-transparent border-none cursor-pointer hover:scale-105 transition-all"
                    title="Remove Task"
                  >
                    <AlertTriangle className="w-4 h-4" />
                  </button>
                )}
              </div>
            </motion.div>
          ))}
        </motion.div>
      ) : (
        /* Kanban Board View */
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Column 1: To Do */}
          <div className="rounded-2xl bg-brand-dark/25 border border-white/5 p-4 flex flex-col h-[500px]">
            <div className="flex items-center justify-between pb-3 border-b border-white/5 mb-4 select-none">
              <span className="text-xs font-bold uppercase tracking-wider text-white font-display flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-brand-blue" />
                To Do
              </span>
              <span className="px-2 py-0.5 rounded-full bg-white/5 text-[9px] text-brand-textMuted font-bold">
                {todoTasks.length}
              </span>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3 pr-1">
              {todoTasks.map((t) => (
                <div
                  key={t.id}
                  className="p-4 rounded-xl border border-white/5 bg-brand-dark/30 hover:border-brand-blue/30 transition-all duration-300 flex flex-col justify-between gap-3 group"
                >
                  <div>
                    <h4 className="text-xs font-bold text-white group-hover:text-brand-blue transition-colors leading-relaxed">
                      {t.title}
                    </h4>
                    <p className="text-[9px] text-brand-textMuted/60 mt-1 flex items-center gap-1">
                      <Briefcase className="w-3 h-3" />
                      {t.caseName}
                    </p>
                  </div>

                  <div className="flex items-center justify-between pt-1 border-t border-white/5 text-[9px] text-brand-textMuted/45">
                    <span className="font-mono">DUE: {t.dueDate}</span>
                    <button
                      onClick={() => onToggleComplete(t.id)}
                      className="text-[9px] text-brand-blue hover:underline bg-transparent border-none p-0 cursor-pointer flex items-center gap-0.5"
                    >
                      <Play className="w-2.5 h-2.5 fill-current" />
                      <span>Start</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Column 2: In Progress (High priority items pending) */}
          <div className="rounded-2xl bg-brand-dark/25 border border-white/5 p-4 flex flex-col h-[500px]">
            <div className="flex items-center justify-between pb-3 border-b border-white/5 mb-4 select-none">
              <span className="text-xs font-bold uppercase tracking-wider text-white font-display flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                Critical Priority
              </span>
              <span className="px-2 py-0.5 rounded-full bg-white/5 text-[9px] text-brand-textMuted font-bold">
                {inProgressTasks.length}
              </span>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3 pr-1">
              {inProgressTasks.map((t) => (
                <div
                  key={t.id}
                  className="p-4 rounded-xl border border-red-500/10 bg-brand-dark/30 hover:border-red-500/30 transition-all duration-300 flex flex-col justify-between gap-3 group"
                >
                  <div>
                    <h4 className="text-xs font-bold text-white group-hover:text-red-400 transition-colors leading-relaxed">
                      {t.title}
                    </h4>
                    <p className="text-[9px] text-brand-textMuted/60 mt-1 flex items-center gap-1">
                      <Briefcase className="w-3 h-3" />
                      {t.caseName}
                    </p>
                  </div>

                  <div className="flex items-center justify-between pt-1 border-t border-white/5 text-[9px] text-brand-textMuted/45">
                    <span className="font-mono text-red-400/80 font-bold">DUE: {t.dueDate}</span>
                    <button
                      onClick={() => onToggleComplete(t.id)}
                      className="text-[9px] text-brand-blue hover:underline bg-transparent border-none p-0 cursor-pointer flex items-center gap-0.5"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-brand-blue" />
                      <span>Complete</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Column 3: Completed */}
          <div className="rounded-2xl bg-brand-dark/25 border border-white/5 p-4 flex flex-col h-[500px]">
            <div className="flex items-center justify-between pb-3 border-b border-white/5 mb-4 select-none">
              <span className="text-xs font-bold uppercase tracking-wider text-white font-display flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                Archived Checkpoints
              </span>
              <span className="px-2 py-0.5 rounded-full bg-white/5 text-[9px] text-brand-textMuted font-bold">
                {completedTasks.length}
              </span>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3 pr-1">
              {completedTasks.map((t) => (
                <div
                  key={t.id}
                  className="p-4 rounded-xl border border-white/5 bg-white/[0.01] opacity-60 flex flex-col justify-between gap-3"
                >
                  <div>
                    <h4 className="text-xs font-medium text-white line-through leading-relaxed">
                      {t.title}
                    </h4>
                    <p className="text-[9px] text-brand-textMuted/40 mt-1 flex items-center gap-1">
                      <Briefcase className="w-3 h-3" />
                      {t.caseName}
                    </p>
                  </div>

                  <div className="flex items-center justify-between pt-1 border-t border-white/5 text-[9px] text-brand-textMuted/30">
                    <span className="font-mono">RESOLVED</span>
                    <button
                      onClick={() => onToggleComplete(t.id)}
                      className="text-[9px] text-brand-textMuted/40 hover:text-white hover:underline bg-transparent border-none p-0 cursor-pointer"
                    >
                      Undo
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
