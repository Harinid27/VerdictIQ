import React, { useState, useEffect } from 'react';
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
  Trash2,
  Loader,
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
  onDeleteHearing?: (id: string) => void;
  onToggleTaskComplete?: (id: string) => void;
  jumpToDate?: string | null; // ISO date string to auto-navigate calendar to
}

export const CalendarPage: React.FC<CalendarPageProps> = ({ hearings, tasks = [], onCreateHearing, onDeleteHearing, onToggleTaskComplete, jumpToDate }) => {
  const today = new Date();
  const [currentDate, setCurrentDate] = useState(new Date(today.getFullYear(), today.getMonth(), 1));
  const [selectedDay, setSelectedDay] = useState<number | null>(today.getDate());

  // Auto-navigate to a specific date when jumpToDate changes (e.g. after adding a hearing)
  useEffect(() => {
    if (!jumpToDate) return;
    const target = new Date(jumpToDate);
    if (isNaN(target.getTime())) return;
    setCurrentDate(new Date(target.getFullYear(), target.getMonth(), 1));
    setSelectedDay(target.getDate());
  }, [jumpToDate]);

  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loadingRecs, setLoadingRecs] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('verdictiq_token');
    if (!token) return;
    setLoadingRecs(true);
    fetch('http://localhost:8000/api/calendar/recommendations', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success && data.data) {
          setRecommendations(data.data);
        }
        setLoadingRecs(false);
      })
      .catch((err) => {
        console.error("Error fetching recommendations:", err);
        setLoadingRecs(false);
      });
  }, [hearings]);

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

  const isDatePassed = (dateStr: string) => {
    if (!dateStr) return false;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const eventDate = new Date(dateStr);
    eventDate.setHours(0, 0, 0, 0);
    return eventDate < today;
  };

  const isHearingPassed = (dateStr: string) => {
    if (!dateStr) return false;
    return new Date(dateStr) < new Date();
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
    const todayObj = new Date();
    const isToday = d === todayObj.getDate() && month === todayObj.getMonth() && year === todayObj.getFullYear();
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
          {dayHearings.slice(0, 1).map((h) => {
            const isPassed = isHearingPassed(h.date);
            return (
              <div
                key={h.id}
                className={`text-[8px] truncate px-1 rounded font-bold uppercase tracking-wide border ${
                  isPassed
                    ? 'bg-zinc-800/40 border-zinc-700/50 text-zinc-500/60 line-through decoration-zinc-500/60 opacity-50'
                    : h.priority === 'High'
                    ? 'bg-red-500/10 border-red-500/20 text-red-400'
                    : 'bg-amber-500/10 border-amber-500/20 text-amber-400'
                }`}
              >
                H: {h.caseName}
              </div>
            );
          })}
          {dayTasks.slice(0, 1).map((t) => {
            const isPassed = isDatePassed(t.dueDate);
            return (
              <div
                key={t.id}
                className={`text-[8px] truncate px-1 rounded font-bold uppercase tracking-wide border ${
                  t.completed || isPassed
                    ? 'bg-zinc-800/40 border-zinc-700/50 text-zinc-500/60 line-through decoration-zinc-500/60 opacity-50'
                    : t.priority === 'High'
                    ? 'bg-red-500/10 border-red-500/20 text-red-400'
                    : 'bg-brand-blue/10 border-brand-blue/20 text-brand-blue'
                }`}
              >
                T: {t.title}
              </div>
            );
          })}
          {dayHearings.length + dayTasks.length > 2 && (
            <div className="text-[7px] text-brand-textMuted/50 font-mono tracking-wider text-right uppercase">
              + {dayHearings.length + dayTasks.length - 2} more
            </div>
          )}
        </div>
      </div>
    );
  }



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
              {month === new Date().getMonth() && year === new Date().getFullYear() && (
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
          {/* Full Month Agenda */}
          <div className="rounded-2xl bg-brand-dark/30 border border-white/5 p-5 md:p-6 shadow-premium-card">
            <h3 className="text-xs font-bold uppercase tracking-wider text-white font-display border-b border-white/5 pb-2.5 mb-4">
              Schedule: {monthNames[month]} {year}
            </h3>

            {(() => {
              // Collect ALL hearings + tasks for this month and sort by date
              const monthHearings = hearings
                .filter((h) => {
                  if (!h.date) return false;
                  const datePart = h.date.split('T')[0];
                  const parts = datePart.split('-');
                  if (parts.length !== 3) return false;
                  return parseInt(parts[0], 10) === year && parseInt(parts[1], 10) - 1 === month;
                })
                .map((h) => ({ ...h, _type: 'hearing' as const, _sortDate: h.date }));

              const monthTasks = tasks
                .filter((t) => {
                  if (!t.dueDate) return false;
                  const parts = t.dueDate.split('-');
                  if (parts.length !== 3) return false;
                  return parseInt(parts[0], 10) === year && parseInt(parts[1], 10) - 1 === month;
                })
                .map((t) => ({ ...t, _type: 'task' as const, _sortDate: t.dueDate }));

              const allEvents = [...monthHearings, ...monthTasks].sort((a, b) =>
                a._sortDate.localeCompare(b._sortDate)
              );

              if (allEvents.length === 0) {
                return (
                  <div className="text-center py-8">
                    <Clock className="w-7 h-7 text-brand-textMuted/30 mx-auto mb-2" />
                    <p className="text-[11px] text-brand-textMuted/50">
                      No hearings or deadlines in {monthNames[month]}.
                    </p>
                  </div>
                );
              }

              return (
                <div className="space-y-3 max-h-[480px] overflow-y-auto pr-1 scrollbar-thin">
                  {allEvents.map((event) => {
                    if (event._type === 'hearing') {
                      const h = event as typeof monthHearings[0];
                      const isPassed = isHearingPassed(h.date);
                      const eventDate = new Date(h.date);
                      const dateLabel = eventDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                      const timeLabel = eventDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
                      const isSelectedDate = selectedDay !== null && (() => {
                        const datePart = h.date.split('T')[0];
                        const parts = datePart.split('-');
                        return parseInt(parts[2], 10) === selectedDay;
                      })();

                      return (
                        <div
                          key={`h-${h.id}`}
                          className={`group p-3 rounded-xl border transition-all duration-300 flex flex-col gap-1.5 ${
                            isPassed
                              ? 'opacity-40 bg-zinc-900/40 border-zinc-800'
                              : isSelectedDate
                              ? 'border-amber-500/30 bg-amber-500/[0.03]'
                              : 'border-white/5 bg-brand-dark/20 hover:border-amber-500/20'
                          }`}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className={`text-xs font-bold flex items-center gap-1.5 min-w-0 ${isPassed ? 'text-zinc-500 line-through' : 'text-white'}`}>
                              <Landmark className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                              <span className="truncate">{h.caseName}</span>
                            </span>
                            <div className="flex items-center gap-1 shrink-0">
                              <span className={`text-[8px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border ${
                                isPassed
                                  ? 'bg-zinc-800/40 border-zinc-700/50 text-zinc-500'
                                  : h.priority === 'High'
                                  ? 'bg-red-500/10 border-red-500/20 text-red-400'
                                  : 'bg-amber-500/10 border-amber-500/20 text-amber-400'
                              }`}>
                                {h.priority}
                              </span>
                              {onDeleteHearing && (
                                <button
                                  onClick={() => onDeleteHearing(h.id)}
                                  className="opacity-0 group-hover:opacity-100 p-1 rounded bg-red-500/10 hover:bg-red-500 hover:text-white border border-red-500/20 text-red-400 cursor-pointer transition-all duration-300"
                                  title="Delete Hearing"
                                >
                                  <Trash2 className="w-3 h-3" />
                                </button>
                              )}
                            </div>
                          </div>
                          <div className={`flex items-center gap-3 text-[10px] font-mono ${isPassed ? 'text-zinc-600' : 'text-amber-400/80'}`}>
                            <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{dateLabel} · {timeLabel}</span>
                          </div>
                          <div className={`text-[10px] ${isPassed ? 'text-zinc-650' : 'text-brand-textMuted/60'}`}>
                            Court: {h.court}
                          </div>
                        </div>
                      );
                    } else {
                      const t = event as typeof monthTasks[0];
                      const isPassed = isDatePassed(t.dueDate);
                      const dateLabel = new Date(t.dueDate + 'T00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                      const isSelectedDate = selectedDay !== null && (() => {
                        const parts = t.dueDate.split('-');
                        return parseInt(parts[2], 10) === selectedDay;
                      })();

                      return (
                        <div
                          key={`t-${t.id}`}
                          onClick={() => onToggleTaskComplete && onToggleTaskComplete(t.id)}
                          title={onToggleTaskComplete ? (t.completed ? 'Click to mark incomplete' : 'Click to mark complete') : undefined}
                          className={`group p-3 rounded-xl border flex flex-col gap-1.5 transition-all duration-300 ${
                            onToggleTaskComplete ? 'cursor-pointer' : ''
                          } ${
                            t.completed
                              ? 'opacity-55 bg-white/[0.01] border-white/5'
                              : isPassed
                              ? 'opacity-40 bg-zinc-900/40 border-zinc-800'
                              : isSelectedDate
                              ? 'border-brand-purple/30 bg-brand-purple/[0.03] hover:border-brand-purple/40'
                              : 'border-white/5 bg-brand-dark/20 hover:border-brand-purple/25 hover:bg-brand-dark/35'
                          }`}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className={`text-xs font-bold flex items-center gap-1.5 min-w-0 ${
                              t.completed ? 'line-through text-zinc-500/60' : isPassed ? 'text-zinc-500' : 'text-white'
                            }`}>
                              <span className={`shrink-0 w-3.5 h-3.5 rounded border flex items-center justify-center transition-all duration-300 ${
                                t.completed ? 'bg-brand-purple border-brand-purple text-white' : 'border-white/20 bg-transparent group-hover:border-brand-purple/50'
                              }`}>
                                {t.completed && (
                                  <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={4}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                  </svg>
                                )}
                              </span>
                              <span className="truncate">{t.title}</span>
                            </span>
                            <span className={`shrink-0 text-[8px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border ${
                              t.completed
                                ? 'bg-zinc-800/40 border-zinc-700/50 text-zinc-500/60'
                                : isPassed
                                ? 'bg-zinc-800/40 border-zinc-700/50 text-zinc-500'
                                : t.priority === 'High'
                                ? 'bg-red-500/10 border-red-500/20 text-red-400'
                                : 'bg-brand-blue/10 border-brand-blue/20 text-brand-blue'
                            }`}>
                              {t.completed ? 'Done' : t.priority}
                            </span>
                          </div>
                          <div className={`text-[10px] font-mono ${isPassed || t.completed ? 'text-zinc-600' : 'text-brand-textMuted/60'}`}>
                            Due: {dateLabel} · {t.caseName}
                            {onToggleTaskComplete && !t.completed && !isPassed && (
                              <span className="ml-2 text-brand-purple/40 opacity-0 group-hover:opacity-100 transition-opacity">· click to complete</span>
                            )}
                          </div>
                        </div>
                      );
                    }
                  })}
                </div>
              );
            })()}
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
              {loadingRecs ? (
                <div className="flex items-center justify-center py-6 text-brand-textMuted/50 font-mono text-[10px] gap-2">
                  <Loader className="w-3.5 h-3.5 animate-spin" />
                  <span>SYNCING RECOMMENDATIONS...</span>
                </div>
              ) : recommendations.length === 0 ? (
                <p className="text-[10px] text-brand-textMuted/50 text-center py-4">No AI recommendations available.</p>
              ) : (
                recommendations.map((rec, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-xl flex gap-2.5 border ${
                      rec.type === 'prep'
                        ? 'bg-brand-blue/[0.02] border-brand-blue/10'
                        : 'bg-amber-500/[0.02] border-amber-500/10'
                    }`}
                  >
                    {rec.type === 'prep' ? (
                      <Brain className="w-4 h-4 text-brand-blue shrink-0 mt-0.5" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    )}
                    <div>
                      <h4 className="font-bold text-white text-[11px] uppercase tracking-wide">
                        {rec.title}
                      </h4>
                      <p className="text-[10px] text-brand-textMuted mt-1 leading-normal" dangerouslySetInnerHTML={{ __html: rec.desc }} />
                      {rec.action && (
                        <button className="text-[9px] text-brand-blue hover:underline mt-2 font-bold uppercase tracking-widest bg-transparent border-none p-0 cursor-pointer">
                          {rec.action}
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
