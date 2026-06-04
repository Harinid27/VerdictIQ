import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Plus, Calendar, AlertTriangle, Landmark } from 'lucide-react';
import { CreateWorkspaceWizard } from './CreateWorkspaceWizard';
import { SmoothSelect } from './SmoothSelect';

interface CaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  mode: 'case' | 'hearing' | 'task';
  casesList: Array<{ id: string; name: string }>;
  onSubmit: (data: any) => void;
}

export const CaseModal: React.FC<CaseModalProps> = ({
  isOpen,
  onClose,
  mode,
  casesList,
  onSubmit,
}) => {


  // Hearing States
  const [hearingCaseId, setHearingCaseId] = useState('');
  const [hearingDate, setHearingDate] = useState('');
  const [courtName, setCourtName] = useState('');
  const [hearingPriority, setHearingPriority] = useState('High');

  // Task States
  const [taskTitle, setTaskTitle] = useState('');
  const [taskDueDate, setTaskDueDate] = useState('');
  const [taskCaseId, setTaskCaseId] = useState('');
  const [taskPriority, setTaskPriority] = useState('Medium');

  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (mode === 'hearing') {
      if (!hearingCaseId || !hearingDate || !courtName.trim()) {
        setError('Please fill in all required fields.');
        return;
      }
      const selectedCase = casesList.find((c) => c.id === hearingCaseId);
      onSubmit({
        type: 'hearing',
        caseName: selectedCase ? selectedCase.name : 'Unknown Case',
        caseId: hearingCaseId,
        date: hearingDate,
        court: courtName,
        priority: hearingPriority,
      });
      // Reset
      setHearingDate('');
      setCourtName('');
    } else if (mode === 'task') {
      if (!taskTitle.trim() || !taskDueDate || !taskCaseId) {
        setError('Please fill in all required fields.');
        return;
      }
      const selectedCase = casesList.find((c) => c.id === taskCaseId);
      onSubmit({
        type: 'task',
        title: taskTitle,
        dueDate: taskDueDate,
        caseName: selectedCase ? selectedCase.name : 'General',
        caseId: taskCaseId,
        priority: taskPriority,
      });
      // Reset
      setTaskTitle('');
      setTaskDueDate('');
    }

    onClose();
  };

  if (!isOpen) return null;

  if (mode === 'case') {
    return (
      <AnimatePresence>
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-[#070A12]/85 backdrop-blur-md"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: 15 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 15 }}
            transition={{ type: 'spring', damping: 26, stiffness: 320 }}
            className="relative w-full max-w-5xl z-10"
          >
            <CreateWorkspaceWizard
              onClose={onClose}
              onSubmit={onSubmit}
              casesList={casesList}
            />
          </motion.div>
        </div>
      </AnimatePresence>
    );
  }

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Backdrop Glow */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-[#070A12]/80 backdrop-blur-md"
        />

        {/* Modal Container */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ type: 'spring', damping: 25, stiffness: 350 }}
          className="relative w-full max-w-[500px] rounded-2xl bg-brand-dark/95 border border-white/10 p-6 md:p-8 shadow-2xl overflow-hidden z-10"
        >
          {/* Top Radial Glow */}
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-brand-blue/50 to-brand-purple/50 opacity-80" />
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-48 h-12 bg-brand-blue/10 rounded-full blur-2xl pointer-events-none" />

          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-brand-textMuted hover:text-white transition-colors duration-200 p-1.5 rounded-lg hover:bg-white/5 border border-transparent hover:border-white/10"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Title */}
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-xl bg-gradient-to-br from-brand-blue/20 to-brand-purple/20 border border-brand-blue/30 text-brand-blue">
              {mode === 'hearing' && <Landmark className="w-5 h-5" />}
              {mode === 'task' && <Calendar className="w-5 h-5" />}
            </div>
            <div>
              <h2 className="text-xl font-bold font-display text-white">
                {mode === 'hearing' && 'Schedule Hearing'}
                {mode === 'task' && 'Create Intelligence Task'}
              </h2>
              <p className="text-xs text-brand-textMuted mt-0.5">
                {mode === 'hearing' && 'Link an upcoming hearing event to a legal case.'}
                {mode === 'task' && 'Assign tasks to evidence analysis grids.'}
              </p>
            </div>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-950/40 border border-red-500/30 rounded-xl text-red-400 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">


            {mode === 'hearing' && (
              <>
                <div>
                  <label className="block text-xs font-semibold text-brand-textMuted uppercase tracking-wider mb-1.5">
                    Select Connected Case <span className="text-brand-blue">*</span>
                  </label>
                  <SmoothSelect
                    value={hearingCaseId}
                    onChange={setHearingCaseId}
                    options={casesList.map((c) => ({ value: c.id, label: c.name }))}
                    placeholder="-- Select a Workspace --"
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-brand-textMuted uppercase tracking-wider mb-1.5">
                    Hearing Date & Time <span className="text-brand-blue">*</span>
                  </label>
                  <input
                    type="datetime-local"
                    required
                    value={hearingDate}
                    onChange={(e) => setHearingDate(e.target.value)}
                    className="w-full bg-[#161f30] border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-brand-blue/60 transition-all duration-300"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-brand-textMuted uppercase tracking-wider mb-1.5">
                    Court & Jurisdiction <span className="text-brand-blue">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. U.S. District Court, N.D. Cal."
                    value={courtName}
                    onChange={(e) => setCourtName(e.target.value)}
                    className="w-full bg-[#161f30] border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-brand-blue/60 transition-all duration-300 placeholder-white/20 shadow-inner"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-brand-textMuted uppercase tracking-wider mb-1.5">
                    Hearing Priority
                  </label>
                  <div className="flex gap-2">
                    {['Low', 'Medium', 'High'].map((p) => (
                      <button
                        key={p}
                        type="button"
                        onClick={() => setHearingPriority(p)}
                        className={`flex-1 py-2 rounded-xl text-xs font-semibold border transition-all duration-300 ${
                          hearingPriority === p
                            ? 'bg-brand-blue/20 border-brand-blue text-white shadow-[0_0_10px_rgba(79,140,255,0.15)]'
                            : 'bg-[#161f30] border-white/5 text-brand-textMuted hover:border-white/15'
                        }`}
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}

            {mode === 'task' && (
              <>
                <div>
                  <label className="block text-xs font-semibold text-brand-textMuted uppercase tracking-wider mb-1.5">
                    Task Title <span className="text-brand-blue">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Review prosecution expert depositions"
                    value={taskTitle}
                    onChange={(e) => setTaskTitle(e.target.value)}
                    className="w-full bg-[#161f30] border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-brand-blue/60 transition-all duration-300 placeholder-white/20 shadow-inner"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-brand-textMuted uppercase tracking-wider mb-1.5">
                    Connect to Case <span className="text-brand-blue">*</span>
                  </label>
                  <SmoothSelect
                    value={taskCaseId}
                    onChange={setTaskCaseId}
                    options={casesList.map((c) => ({ value: c.id, label: c.name }))}
                    placeholder="-- Select a Workspace --"
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-brand-textMuted uppercase tracking-wider mb-1.5">
                    Due Date <span className="text-brand-blue">*</span>
                  </label>
                  <input
                    type="date"
                    required
                    value={taskDueDate}
                    onChange={(e) => setTaskDueDate(e.target.value)}
                    className="w-full bg-[#161f30] border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-brand-blue/60 transition-all duration-300"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-brand-textMuted uppercase tracking-wider mb-1.5">
                    Task Priority
                  </label>
                  <div className="flex gap-2">
                    {['Low', 'Medium', 'High'].map((p) => (
                      <button
                        key={p}
                        type="button"
                        onClick={() => setTaskPriority(p)}
                        className={`flex-1 py-2 rounded-xl text-xs font-semibold border transition-all duration-300 ${
                          taskPriority === p
                            ? 'bg-brand-purple/20 border-brand-purple text-white shadow-[0_0_10px_rgba(123,97,255,0.15)]'
                            : 'bg-[#161f30] border-white/5 text-brand-textMuted hover:border-white/15'
                        }`}
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4 border-t border-white/5 mt-6">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 h-11 rounded-xl text-xs font-semibold border border-white/10 hover:border-white/20 text-brand-textMuted hover:text-white bg-transparent transition-all duration-300"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 h-11 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-brand-blue to-brand-purple shadow-button-glow hover:translate-y-[-1px] active:translate-y-[0] transition-all duration-300 flex items-center justify-center gap-1.5"
              >
                <Plus className="w-4 h-4" />
                <span>Initialize</span>
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
