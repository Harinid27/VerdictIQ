import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
  Plus,
  Brain,
  Clock,
  Landmark,
  AlertTriangle,
  CheckSquare,
} from 'lucide-react';

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
  caseId: string;
  completed: boolean;
  priority: 'Low' | 'Medium' | 'High';
}

interface CalendarPageProps {
  hearings: Hearing[];
  tasks: Task[];
  onCreateHearing: () => void;
}

export const CalendarPage: React.FC<CalendarPageProps> = ({ hearings, tasks = [], onCreateHearing }) => {
  const [currentDate, setCurrentDate] = useState(new Date(2026, 5, 1)); // June 2026 as per local time
  const [selectedDay, setSelectedDay] = useState<number | null>(3); // Default June 3rd (User's current day)

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  // Days in month
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  // First day of month index (0 = Sun, 1 = Mon, ...)
  const firstDayIndex = new Date(year, month, 1).getDay();

  const handlePrevMonth = () => {
    setCurrentDate(new Date(year, month - 1, 1));
    setSelectedDay(null);
  };

  const handleNextMonth = () => {
    setCurrentDate(new Date(year, month + 1, 1));
    setSelectedDay(null);
  };

  // Helper to extract hearings for a specific day in this month
  const getHearingsForDay = (day: number) => {
    return hearings.filter((h) => {
      if (!h.date) return false;
      const datePart = h.date.split('T')[0];
      const parts = datePart.split('-');
      if (parts.length !== 3) return false;
      const hYear = parseInt(parts[0], 10);
      const hMonth = parseInt(parts[1], 10) - 1;
      const hDay = parseInt(parts[2], 10);
      return hYear === year && hMonth === month && hDay === day;
    });
  };

  // Helper to extract tasks for a specific day in this month
  const getTasksForDay = (day: number) => {
    return tasks.filter((t) => {
      if (!t.dueDate) return false;
      const parts = t.dueDate.split('-');
      if (parts.length !== 3) return false;
      const tYear = parseInt(parts[0], 10);
      const tMonth = parseInt(parts[1], 10) - 1;
      const tDay = parseInt(parts[2], 10);
      return tYear === year && tMonth === month && tDay === day;
    });
  };

  // Build cells
  const calendarCells = [];
  // Empty slots for padding
  for (let i = 0; i < firstDayIndex; i++) {
    calendarCells.push(<div key={`empty-${i}`} className="h-20 border border-white/[0.02] bg-transparent opacity-25" />);
  }
  // Days slots
  for (let d = 1; d <= daysInMonth; d++) {
    const dayHearings = getHearingsForDay(d);
    const dayTasks = getTasksForDay(d);
    const isSelected = selectedDay === d;
    const isToday = d === 3 && month === 5 && year === 2026; // June 3, 2026
    const hasEvents = dayHearings.length > 0 || dayTasks.length > 0;

    calendarCells.push(
      <div
        key={`day-${d}`}
        onClick={() => setSelectedDay(d)}
        className={`h-20 border border-white/5 p-2 flex flex-col justify-between transition-all duration-300 relative cursor-pointer group ${
          isSelected
            ? 'bg-brand-blue/[0.04] border-brand-blue/30 shadow-[inset_0_0_10px_rgba(79,140,255,0.05)]'
            : 'bg-brand-dark/20 hover:bg-brand-dark/40 hover:border-white/10'
        } ${isToday ? 'bg-brand-purple/[0.03] border-brand-purple/20' : ''}`}
      >
        <div className="flex items-center justify-between">
          <span
            className={`text-xs font-semibold select-none ${
              isToday
                ? 'w-5 h-5 flex items-center justify-center rounded-full bg-brand-purple text-white text-[10px] font-bold shadow-[0_0_8px_#7B61FF]'
                : isSelected
                ? 'text-brand-blue font-bold'
                : 'text-brand-textMuted'
            }`}
          >
            {d}
          </span>
          {hasEvents && (
            <span className={`w-1.5 h-1.5 rounded-full animate-pulse ${
              dayHearings.length > 0 ? 'bg-amber-400 shadow-[0_0_6px_#f59e0b]' : 'bg-brand-blue shadow-[0_0_6px_#4f8cff]'
            }`} />
          )}
        </div>

        {/* Short event summaries inside cells */}
        <div className="space-y-1 overflow-hidden max-h-11">
          {dayHearings.slice(0, 1).map((h) => (
            <div
              key={h.id}
              className={`text-[8px] truncate px-1 rounded font-bold uppercase tracking-wide border ${
                h.priority === 'High'
                  ? 'bg-red-500/10 border-red-500/20 text-red-400'
                  : 'bg-amber-500/10 border-amber-500/20 text-amber-400'
              }`}
            >
              H: {h.caseName}
            </div>
          ))}
          {dayTasks.slice(0, 1).map((t) => (
            <div
              key={t.id}
              className={`text-[8px] truncate px-1 rounded font-bold uppercase tracking-wide border ${
                t.completed
                  ? 'bg-zinc-800/40 border-zinc-700/50 text-zinc-500/60 line-through decoration-zinc-500/60'
                  : t.priority === 'High'
                  ? 'bg-red-500/10 border-red-500/20 text-red-400'
                  : 'bg-brand-blue/10 border-brand-blue/20 text-brand-blue'
              }`}
            >
              T: {t.title}
            </div>
          ))}
          {dayHearings.length + dayTasks.length > 2 && (
            <div className="text-[7px] text-brand-textMuted/50 font-mono tracking-wider text-right uppercase">
              + {dayHearings.length + dayTasks.length - 2} more
            </div>
          )}
        </div>
      </div>
    );
  }

  // Selected Day Details
  const selectedDayHearings = selectedDay ? getHearingsForDay(selectedDay) : [];
  const selectedDayTasks = selectedDay ? getTasksForDay(selectedDay) : [];

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 select-none">
        <div>
          <h2 className="text-xl font-bold uppercase tracking-wider text-white font-display flex items-center gap-2">
            <CalendarIcon className="w-5 h-5 text-brand-blue" />
            AI Hearings & Deadlines Schedule
          </h2>
          <p className="text-xs text-brand-textMuted mt-0.5">
            Monitor court hearings, track intelligence deadlines, and receive automated AI reminders.
          </p>
        </div>

        <motion.button
          whileHover={{ y: -1 }}
          whileTap={{ scale: 0.98 }}
          onClick={onCreateHearing}
          className="relative h-10 px-5 rounded-xl text-xs font-semibold tracking-wider text-white overflow-hidden shadow-button-glow transition-all duration-300 flex items-center justify-center gap-1.5 font-display uppercase shrink-0"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-brand-blue to-brand-purple" />
          <Plus className="w-4 h-4 relative z-10" />
          <span className="relative z-10">Add Hearing</span>
        </motion.button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Calendar Grid Container */}
        <div className="lg:col-span-2 rounded-2xl bg-brand-dark/45 border border-white/5 p-5 md:p-6 shadow-premium-card flex flex-col">
          {/* Header controls */}
          <div className="flex items-center justify-between pb-4 border-b border-white/5 mb-5 select-none">
            <div className="flex items-center gap-2.5">
              <h3 className="text-sm font-bold uppercase tracking-wider text-white font-display">
                {monthNames[month]} {year}
              </h3>
              {month === 5 && year === 2026 && (
                <span className="px-2 py-0.5 rounded-full bg-brand-purple/10 border border-brand-purple/20 text-[8px] text-brand-purple uppercase tracking-wider font-bold">
                  Active Month
                </span>
              )}
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handlePrevMonth}
                className="w-8 h-8 rounded-lg border border-white/10 hover:border-brand-blue/35 text-brand-textMuted hover:text-white flex items-center justify-center bg-transparent transition-all duration-300"
              >
                <ChevronLeft className="w-4.5 h-4.5" />
              </button>
              <button
                onClick={handleNextMonth}
                className="w-8 h-8 rounded-lg border border-white/10 hover:border-brand-blue/35 text-brand-textMuted hover:text-white flex items-center justify-center bg-transparent transition-all duration-300"
              >
                <ChevronRight className="w-4.5 h-4.5" />
              </button>
            </div>
          </div>

          {/* Days of week titles */}
          <div className="grid grid-cols-7 gap-px text-center mb-2 select-none">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((d) => (
              <span key={d} className="text-[10px] font-bold uppercase tracking-widest text-brand-textMuted/40 py-1.5 font-display">
                {d}
              </span>
            ))}
          </div>

          {/* Month Grid Cells */}
          <div className="grid grid-cols-7 gap-px bg-white/5 border border-white/5 rounded-xl overflow-hidden shadow-inner">
            {calendarCells}
          </div>
        </div>

        {/* Info / AI Reminders Side Panel */}
        <div className="space-y-6">
          {/* Selected Day Agenda */}
          <div className="rounded-2xl bg-brand-dark/30 border border-white/5 p-5 md:p-6 shadow-premium-card">
            <h3 className="text-xs font-bold uppercase tracking-wider text-white font-display border-b border-white/5 pb-2.5 mb-4">
              Schedule: {selectedDay ? `${monthNames[month]} ${selectedDay}, ${year}` : 'Select a Day'}
            </h3>

            {selectedDayHearings.length === 0 && selectedDayTasks.length === 0 ? (
              <div className="text-center py-8">
                <Clock className="w-7 h-7 text-brand-textMuted/30 mx-auto mb-2" />
                <p className="text-[11px] text-brand-textMuted/50">
                  No hearings or deadlines scheduled.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Render Hearings */}
                {selectedDayHearings.map((h) => {
                  const formattedTime = new Date(h.date).toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit',
                  });

                  return (
                    <div
                      key={h.id}
                      className="group p-3 rounded-xl border border-white/5 bg-brand-dark/20 flex flex-col gap-2"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-white group-hover:text-brand-blue transition-colors duration-200 flex items-center gap-1.5">
                          <Landmark className="w-3.5 h-3.5 text-brand-blue shrink-0" />
                          Hearing: {h.caseName}
                        </span>
                        <span
                          className={`text-[8px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${
                            h.priority === 'High'
                              ? 'bg-red-500/10 border-red-500/20 text-red-400'
                              : 'bg-amber-500/10 border-amber-500/20 text-amber-400'
                          }`}
                        >
                          {h.priority} Priority
                        </span>
                      </div>

                      <div className="flex items-center gap-1 text-[10px] text-amber-400 font-mono">
                        <Clock className="w-3.5 h-3.5" />
                        <span>{formattedTime}</span>
                      </div>

                      <div className="flex items-start gap-1.5 text-[10px] text-brand-textMuted/65">
                        <span>Court: {h.court}</span>
                      </div>
                    </div>
                  );
                })}

                {/* Render Tasks */}
                {selectedDayTasks.map((t) => {
                  return (
                    <div
                      key={t.id}
                      className={`group p-3 rounded-xl border border-white/5 bg-brand-dark/20 flex flex-col gap-2 transition-all duration-300 ${t.completed ? 'opacity-55 bg-white/[0.01]' : ''}`}
                    >
                      <div className="flex items-center justify-between">
                        <span className={`text-xs font-bold text-white group-hover:text-brand-blue transition-colors duration-200 flex items-center gap-1.5 ${t.completed ? 'line-through text-zinc-500/60 decoration-zinc-500/60' : ''}`}>
                          <CheckSquare className={`w-3.5 h-3.5 shrink-0 ${t.completed ? 'text-zinc-500/60' : 'text-brand-purple'}`} />
                          Task: {t.title}
                        </span>
                        <span
                          className={`text-[8px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${
                            t.completed
                              ? 'bg-zinc-800/40 border-zinc-700/50 text-zinc-500/60'
                              : t.priority === 'High'
                              ? 'bg-red-500/10 border-red-500/20 text-red-400'
                              : 'bg-brand-blue/10 border-brand-blue/20 text-brand-blue'
                          }`}
                        >
                          {t.completed ? 'Completed' : `${t.priority} Priority`}
                        </span>
                      </div>

                      <div className="flex items-center gap-1 text-[10px] text-brand-textMuted/65 font-mono">
                        <span>Workspace: {t.caseName}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* AI Reminders Panel */}
          <div className="rounded-2xl bg-brand-dark/30 border border-white/5 p-5 md:p-6 shadow-premium-card relative overflow-hidden">
            {/* Background sparkle light */}
            <div className="absolute -right-12 -top-12 w-28 h-28 bg-brand-blue/5 rounded-full blur-2xl pointer-events-none" />

            <h3 className="text-xs font-bold uppercase tracking-wider text-white font-display flex items-center gap-2 border-b border-white/5 pb-2.5 mb-4">
              <Brain className="w-4 h-4 text-brand-blue" />
              VerdictIQ AI Recommendations
            </h3>

            <div className="space-y-4 text-xs leading-relaxed">
              <div className="p-3 rounded-xl bg-brand-blue/[0.02] border border-brand-blue/10 flex gap-2.5">
                <Brain className="w-4 h-4 text-brand-blue shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-bold text-white text-[11px] uppercase tracking-wide">
                    Pre-Trial Prep Alert
                  </h4>
                  <p className="text-[10px] text-brand-textMuted mt-1 leading-normal">
                    AI suggests scheduling a mock cross-examination for **{hearings.length > 0 ? hearings[0].caseName : "your active cases"}** 48 hours prior to the hearing.
                  </p>
                  <button className="text-[9px] text-brand-blue hover:underline mt-2 font-bold uppercase tracking-widest bg-transparent border-none p-0 cursor-pointer">
                    Auto-Schedule Prep
                  </button>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-amber-500/[0.02] border border-amber-500/10 flex gap-2.5">
                <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-bold text-white text-[11px] uppercase tracking-wide">
                    Evidence Disclosure Gap
                  </h4>
                  <p className="text-[10px] text-brand-textMuted mt-1 leading-normal">
                    Docket deadline for expert witness exchange is **June 15**. Initial expert reports need digital signing.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
