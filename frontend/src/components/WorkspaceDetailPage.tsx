import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Scale,
  Brain,
  AlertTriangle,
  Activity,
  FileText,
  UploadCloud,
  Download,
  Send,
  Loader,
  File,
  Trash2,
  ArrowLeft,
  Landmark
} from 'lucide-react';

interface WorkspaceDetailPageProps {
  workspaceId: string;
  onBack: () => void;
}

interface EvidenceFile {
  _id: string;
  file_name: string;
  evidence_type: string;
  description: string;
  importance_level: string;
  file_url: string;
}

interface ChatMessage {
  _id?: string;
  sender: 'user' | 'agent';
  agent_name?: string;
  text: string;
  timestamp: string;
}

export const WorkspaceDetailPage: React.FC<WorkspaceDetailPageProps> = ({ workspaceId, onBack }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'audit' | 'strategy' | 'report' | 'chat' | 'files'>('overview');
  const [loading, setLoading] = useState(true);
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [pipelineStage, setPipelineStage] = useState('');
  const [error, setError] = useState('');

  // Workspace Data states
  const [caseMeta, setCaseMeta] = useState<any>(null);
  const [agent0Context, setAgent0Context] = useState<any>(null);
  const [agent1Audit, setAgent1Audit] = useState<any>(null);
  const [agent2Strategy, setAgent2Strategy] = useState<any>(null);
  const [agent3Report, setAgent3Report] = useState<any>(null);
  const [evidenceFiles, setEvidenceFiles] = useState<EvidenceFile[]>([]);

  // Chat states
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [sendingMessage, setSendingMessage] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // File Upload states
  const [uploadingFile, setUploadingFile] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  // Fetch all case workspace details
  const fetchWorkspaceData = async () => {
    const token = localStorage.getItem('verdictiq_token');
    const headers = { 'Authorization': `Bearer ${token}` };

    try {
      setError('');
      // A. Load structured context & metadata
      const resContext = await fetch(`http://localhost:8000/api/workspace/${workspaceId}/structured-context`, { headers });
      if (!resContext.ok) {
        throw new Error("Case structured context not ready. Please run the AI pipeline.");
      }
      const dataContext = await resContext.json();
      setAgent0Context(dataContext);
      setCaseMeta(dataContext.legal_context);

      // B. Load Agent 1 Auditing results
      const resA1 = await fetch(`http://localhost:8000/api/agent1/results/${workspaceId}`, { headers });
      if (resA1.ok) {
        const dataA1 = await resA1.json();
        setAgent1Audit(dataA1);
      }

      // C. Load Agent 2 Strategy results
      const resA2 = await fetch(`http://localhost:8000/api/agent2/results/${workspaceId}`, { headers });
      if (resA2.ok) {
        const dataA2 = await resA2.json();
        setAgent2Strategy(dataA2);
      }

      // D. Load Agent 3 Report results
      const resA3 = await fetch(`http://localhost:8000/api/agent3/report/${workspaceId}`, { headers });
      if (resA3.ok) {
        const dataA3 = await resA3.json();
        setAgent3Report(dataA3);
      }

      // E. Load uploaded evidence files metadata
      const resFiles = await fetch(`http://localhost:8000/api/files/${workspaceId}`, { headers });
      if (resFiles.ok) {
        const dataFiles = await resFiles.json();
        if (dataFiles.success && dataFiles.data) {
          setEvidenceFiles(dataFiles.data);
        }
      }

      setLoading(false);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to load workspace data.");
      setLoading(false);
    }
  };

  // Fetch chat history
  const fetchChatHistory = async () => {
    const token = localStorage.getItem('verdictiq_token');
    const headers = { 'Authorization': `Bearer ${token}` };
    try {
      const res = await fetch(`http://localhost:8000/api/chat/history/${workspaceId}`, { headers });
      if (res.ok) {
        const data = await res.json();
        if (data.success && data.data) {
          setMessages(data.data);
        }
      }
    } catch (err) {
      console.error("Error loading chat history:", err);
    }
  };

  useEffect(() => {
    // Reset all case-specific states to prevent data bleed/ghosting from prior cases
    setCaseMeta(null);
    setAgent0Context(null);
    setAgent1Audit(null);
    setAgent2Strategy(null);
    setAgent3Report(null);
    setEvidenceFiles([]);
    setMessages([]);
    setError('');
    setActiveTab('overview');

    setLoading(true);
    fetchWorkspaceData();
    fetchChatHistory();
  }, [workspaceId]);

  useEffect(() => {
    // Scroll chat to bottom
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Run full sequential pipeline on-demand
  const handleRunPipeline = async () => {
    const token = localStorage.getItem('verdictiq_token');
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };

    try {
      setError('');
      setPipelineRunning(true);
      
      setPipelineStage('Agent 0: Compiling Case Intake & OCR Extractions...');
      const a0Res = await fetch(`http://localhost:8000/api/agent0/process/${workspaceId}`, { method: 'POST', headers });
      if (!a0Res.ok) throw new Error("Agent 0 intake compilation failed.");

      setPipelineStage('Agent 1: Auditing Evidence Strength & Loopholes...');
      const a1Res = await fetch(`http://localhost:8000/api/agent1/analyze/${workspaceId}`, { method: 'POST', headers });
      if (!a1Res.ok) throw new Error("Agent 1 analysis failed.");

      setPipelineStage('Agent 2: Simulating Opposing Attacks & Arguments...');
      const a2Res = await fetch(`http://localhost:8000/api/agent2/generate-strategy/${workspaceId}`, { method: 'POST', headers });
      if (!a2Res.ok) throw new Error("Agent 2 strategy generation failed.");

      setPipelineStage('Agent 3: Synthesizing Final Case Reports & Precedents...');
      const a3Res = await fetch(`http://localhost:8000/api/agent3/generate-report/${workspaceId}`, { method: 'POST', headers });
      if (!a3Res.ok) throw new Error("Agent 3 report synthesis failed.");

      setPipelineRunning(false);
      setPipelineStage('');
      
      // Reload everything
      fetchWorkspaceData();
      fetchChatHistory();
    } catch (err: any) {
      setError(err.message || "Pipeline execution failed.");
      setPipelineRunning(false);
      setPipelineStage('');
    }
  };

  // Chat Submit
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || sendingMessage) return;

    const userMsg = inputMessage;
    setInputMessage('');
    setSendingMessage(true);

    // Append local user message
    const tempUserMsg: ChatMessage = {
      sender: 'user',
      text: userMsg,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, tempUserMsg]);

    const token = localStorage.getItem('verdictiq_token');
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };

    try {
      const res = await fetch(`http://localhost:8000/api/chat/ask/${workspaceId}`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ message: userMsg })
      });
      const data = await res.json();
      if (res.ok && data.success && data.data) {
        setMessages(prev => [...prev, data.data]);
      } else {
        throw new Error(data.message || "Failed to get response from AI Agents.");
      }
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        sender: 'agent',
        agent_name: 'System Error',
        text: `[System Error] ${err.message || "Communication failed."}`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setSendingMessage(false);
    }
  };

  // PDF Export downloader
  const handleDownloadPDF = () => {
    const token = localStorage.getItem('verdictiq_token');
    window.open(`http://localhost:8000/api/export/pdf/${workspaceId}?token=${token}`, '_blank');
  };

  // DOCX Export downloader
  const handleDownloadDOCX = () => {
    const token = localStorage.getItem('verdictiq_token');
    window.open(`http://localhost:8000/api/export/docx/${workspaceId}?token=${token}`, '_blank');
  };

  // Upload Evidence File inside Workspace
  const handleFiles = (files: File[]) => {
    const token = localStorage.getItem('verdictiq_token');
    if (!token || files.length === 0) return;

    setUploadingFile(true);
    const file = files[0];
    const formData = new FormData();
    formData.append('file', file);
    formData.append('workspace_id', workspaceId);
    formData.append('evidence_type', 'Contract');
    formData.append('description', 'Evidence file uploaded inside workspace detail view.');
    formData.append('importance_level', 'Important');

    fetch('http://localhost:8000/api/workspace/upload-evidence', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    })
      .then(res => res.json())
      .then(data => {
        setUploadingFile(false);
        if (data.success) {
          // Trigger the sequential AI pipeline analysis automatically
          handleRunPipeline();
        } else {
          alert("Upload failed: " + data.message);
        }
      })
      .catch(err => {
        setUploadingFile(false);
        console.error("Upload error:", err);
      });
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleDeleteFile = (fileId: string) => {
    const token = localStorage.getItem('verdictiq_token');
    if (!token) return;

    fetch(`http://localhost:8000/api/files/${fileId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          fetchWorkspaceData(); // reload
        }
      })
      .catch(err => console.error("Error deleting file:", err));
  };

  if (loading) {
    return (
      <div className="h-[70vh] w-full flex flex-col items-center justify-center space-y-4">
        <Loader className="w-8 h-8 text-brand-blue animate-spin" />
        <p className="text-xs text-brand-textMuted font-mono uppercase tracking-widest">
          DECIPHERING WORKSPACE ENCRYPTED METRICS...
        </p>
      </div>
    );
  }

  const isReportReady = !!agent3Report;

  return (
    <div className="space-y-6 select-none relative text-left">
      
      {/* Header Info Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl border border-white/5 bg-[#0e1424]/45 backdrop-blur-xl relative overflow-hidden">
        <div className="absolute top-0 right-1/4 w-72 h-72 bg-brand-blue/5 rounded-full blur-3xl pointer-events-none" />
        
        <div className="space-y-1.5 flex-1">
          <button
            onClick={onBack}
            className="flex items-center gap-1.5 text-[10px] text-brand-blue hover:text-white uppercase font-bold tracking-wider mb-2 font-mono transition-colors duration-200"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to workspaces
          </button>
          
          <h2 className="text-xl font-bold tracking-wide text-white font-display uppercase">
            {caseMeta?.case_title || 'Workspace detail'}
          </h2>
          
          <div className="flex flex-wrap items-center gap-3 text-[10px] text-brand-textMuted/70 font-semibold uppercase">
            <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-white">
              Type: {caseMeta?.case_type}
            </span>
            <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-white">
              Side: {caseMeta?.lawyer_side}
            </span>
            <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-white">
              Client: {caseMeta?.client_name}
            </span>
            <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-white">
              Opponent: {caseMeta?.opposing_party}
            </span>
          </div>
        </div>

        {/* Global Action Buttons */}
        <div className="flex items-center gap-3 self-start md:self-center shrink-0">
          <button
            onClick={handleRunPipeline}
            disabled={pipelineRunning}
            className="h-10 px-4 rounded-xl text-xs font-semibold tracking-wider text-white border border-brand-purple/20 hover:border-brand-purple bg-brand-purple/10 hover:bg-brand-purple/25 transition-all duration-300 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
          >
            {pipelineRunning ? <Loader className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />}
            <span>{pipelineRunning ? 'Analyzing...' : 'Re-Run AI Analysis'}</span>
          </button>
        </div>
      </div>

      {/* Pipeline Loader Overlay */}
      {pipelineRunning && (
        <div className="p-4 bg-brand-purple/10 border border-brand-purple/20 rounded-xl text-brand-purple text-xs font-mono flex items-center gap-3 animate-pulse">
          <Loader className="w-4 h-4 animate-spin" />
          <span>Pipeline Status: {pipelineStage}</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-950/40 border border-red-500/30 rounded-xl text-red-400 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Tab Navigation Controls */}
      <div className="flex border-b border-white/5 overflow-x-auto gap-2 p-1.5 bg-[#0a0f1d] rounded-xl border border-white/5">
        {[
          { id: 'overview', label: 'Evidentiary Context (Agent 0)', icon: FileText },
          { id: 'audit', label: 'Evidentiary Auditing (Agent 1)', icon: AlertTriangle },
          { id: 'strategy', label: 'Courtroom Strategy (Agent 2)', icon: Scale },
          { id: 'report', label: 'Synthesis Report (Agent 3)', icon: Brain },
          { id: 'chat', label: 'AI Conversations (Chat)', icon: Activity, badge: !isReportReady ? 'Locked' : 'Active' },
          { id: 'files', label: 'Evidence Files', icon: File }
        ].map((tab: any) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-semibold tracking-wider uppercase whitespace-nowrap transition-all duration-300 relative cursor-pointer border ${
                isActive
                  ? 'bg-brand-blue/10 border-brand-blue/30 text-white shadow-[0_0_10px_rgba(79,140,255,0.05)]'
                  : 'border-transparent text-brand-textMuted hover:text-white hover:bg-white/[0.02]'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
              {tab.badge && (
                <span className={`text-[8px] font-bold px-1.5 py-0.5 rounded ml-1 ${
                  tab.badge === 'Locked' ? 'bg-red-500/10 border border-red-500/20 text-red-400' : 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 animate-pulse'
                }`}>
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Viewport Panels */}
      <div className="min-h-[50vh] p-6 rounded-2xl border border-white/5 bg-[#0e1424]/30 backdrop-blur-xl relative">
        <AnimatePresence mode="wait">
          
          {/* TAB 1: OVERVIEW */}
          {activeTab === 'overview' && (
            <motion.div
              key="overview"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-6"
            >
              {/* Narrative Case Summary */}
              <div className="space-y-2">
                <h3 className="text-sm font-bold uppercase tracking-wider text-white border-l-2 border-brand-blue pl-2.5">
                  Cognitive Case Narrative Summary
                </h3>
                <p className="text-xs text-brand-textMuted leading-relaxed bg-[#111726]/40 p-4 rounded-xl border border-white/5">
                  {agent0Context?.case_summary || 'No narrative summary compiled.'}
                </p>
              </div>

              {/* Claims & Concerns Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* Claims list */}
                <div className="space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-white flex items-center gap-1.5">
                    <Scale className="w-4 h-4 text-brand-blue" />
                    Legal Claims / Positions
                  </h4>
                  <div className="space-y-2">
                    {agent0Context?.claims?.length > 0 ? (
                      agent0Context.claims.map((claim: string, idx: number) => (
                        <div key={idx} className="p-3 bg-[#111726]/30 border border-white/5 rounded-xl text-xs text-brand-textMuted">
                          {idx + 1}. {claim}
                        </div>
                      ))
                    ) : (
                      <p className="text-xs text-brand-textMuted/50">No claims extracted.</p>
                    )}
                  </div>
                </div>

                {/* Concerns list */}
                <div className="space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-white flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4 text-amber-500" />
                    vulnerabilities / concerns
                  </h4>
                  <div className="space-y-2">
                    {agent0Context?.concerns?.length > 0 ? (
                      agent0Context.concerns.map((con: string, idx: number) => (
                        <div key={idx} className="p-3 bg-[#111726]/30 border border-white/5 rounded-xl text-xs text-brand-textMuted">
                          {idx + 1}. {con}
                        </div>
                      ))
                    ) : (
                      <p className="text-xs text-brand-textMuted/50">No vulnerabilities cataloged.</p>
                    )}
                  </div>
                </div>

              </div>

              {/* Timeline */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-white">
                  Case Event Timeline
                </h4>
                <div className="relative border-l border-white/10 ml-3 pl-4 space-y-4 py-2">
                  {agent0Context?.timeline?.length > 0 ? (
                    agent0Context.timeline.map((evt: any, idx: number) => (
                      <div key={idx} className="relative space-y-1">
                        {/* Timeline dot */}
                        <div className="absolute left-[-21px] top-1 w-2.5 h-2.5 rounded-full bg-brand-blue border border-brand-dark shadow-[0_0_6px_#4f8cff]" />
                        
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-mono font-bold text-brand-blue">{evt.date}</span>
                          {evt.legal_event && (
                            <span className="text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-white/5 text-brand-textMuted font-bold border border-white/5">
                              {evt.legal_event}
                            </span>
                          )}
                        </div>
                        
                        <p className="text-xs text-brand-textMuted leading-relaxed">
                          {evt.incident}
                        </p>
                        {evt.transaction_reference && (
                          <p className="text-[10px] font-mono text-brand-textMuted/40">Ref: {evt.transaction_reference}</p>
                        )}
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-brand-textMuted/50">No timeline data available.</p>
                  )}
                </div>
              </div>

              {/* Key Entities */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-white">
                  Identified Entities
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                  {agent0Context?.key_entities?.length > 0 ? (
                    agent0Context.key_entities.map((ent: any, idx: number) => (
                      <div key={idx} className="p-3 rounded-xl border border-white/5 bg-[#111726]/30 flex flex-col gap-1">
                        <span className="text-xs font-bold text-white truncate">{ent.name}</span>
                        <span className="text-[9px] uppercase font-bold text-brand-blue tracking-wider">{ent.type}</span>
                        <span className="text-[9px] font-mono text-brand-textMuted/50">{ent.role}</span>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-brand-textMuted/50">No entities extracted.</p>
                  )}
                </div>
              </div>
            </motion.div>
          )}

          {/* TAB 2: AUDIT */}
          {activeTab === 'audit' && (
            <motion.div
              key="audit"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-6"
            >
              {!agent1Audit ? (
                <div className="text-center py-10">
                  <AlertTriangle className="w-10 h-10 text-brand-textMuted/30 mx-auto mb-3" />
                  <p className="text-xs text-brand-textMuted">Agent 1 auditing outputs are not available. Please run the AI Pipeline.</p>
                </div>
              ) : (
                <>
                  {/* Evidence Classification Groupings */}
                  <div className="space-y-4">
                    <h3 className="text-sm font-bold uppercase tracking-wider text-white border-l-2 border-brand-purple pl-2.5">
                      Evidentiary Weight Classifications
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      
                      {/* Strong evidence */}
                      <div className="p-4 rounded-xl bg-emerald-500/[0.02] border border-emerald-500/10 space-y-3">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                          Strong Evidentiary Files
                        </h4>
                        <div className="space-y-2">
                          {agent1Audit.strong_evidence?.length > 0 ? (
                            agent1Audit.strong_evidence.map((item: any, idx: number) => (
                              <div key={idx} className="p-2.5 bg-emerald-500/[0.04] border border-emerald-500/5 rounded-lg text-[11px] text-brand-textMuted">
                                <p className="font-bold text-white">{item.file_name}</p>
                                <p className="text-[9px] text-emerald-400 mt-0.5">Supports: {item.supporting_claim}</p>
                                <p className="mt-1 leading-relaxed">{item.reasoning}</p>
                              </div>
                            ))
                          ) : (
                            <p className="text-[10px] text-brand-textMuted/50">No strong evidence cataloged.</p>
                          )}
                        </div>
                      </div>

                      {/* Moderate evidence */}
                      <div className="p-4 rounded-xl bg-amber-500/[0.02] border border-amber-500/10 space-y-3">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                          Moderate Evidentiary Files
                        </h4>
                        <div className="space-y-2">
                          {agent1Audit.moderate_evidence?.length > 0 ? (
                            agent1Audit.moderate_evidence.map((item: any, idx: number) => (
                              <div key={idx} className="p-2.5 bg-amber-500/[0.04] border border-amber-500/5 rounded-lg text-[11px] text-brand-textMuted">
                                <p className="font-bold text-white">{item.file_name}</p>
                                <p className="text-[9px] text-amber-400 mt-0.5">Supports: {item.supporting_claim}</p>
                                <p className="mt-1 leading-relaxed">{item.reasoning}</p>
                              </div>
                            ))
                          ) : (
                            <p className="text-[10px] text-brand-textMuted/50">No moderate evidence cataloged.</p>
                          )}
                        </div>
                      </div>

                      {/* Weak evidence */}
                      <div className="p-4 rounded-xl bg-red-500/[0.02] border border-red-500/10 space-y-3">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-red-400 flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                          Weak / Vulnerable Files
                        </h4>
                        <div className="space-y-2">
                          {agent1Audit.weak_evidence?.length > 0 ? (
                            agent1Audit.weak_evidence.map((item: any, idx: number) => (
                              <div key={idx} className="p-2.5 bg-red-500/[0.04] border border-red-500/5 rounded-lg text-[11px] text-brand-textMuted">
                                <p className="font-bold text-white">{item.file_name}</p>
                                <p className="mt-1 leading-relaxed">{item.reasoning}</p>
                              </div>
                            ))
                          ) : (
                            <p className="text-[10px] text-brand-textMuted/50">No weak evidence items found.</p>
                          )}
                        </div>
                      </div>

                    </div>
                  </div>

                  {/* Loopholes, Contradictions, Missing proof */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    
                    {/* Loopholes & Contradictions */}
                    <div className="space-y-4">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-white">
                        Contractual Loopholes & Contradictions
                      </h4>

                      {/* Loopholes */}
                      <div className="space-y-2">
                        {agent1Audit.loopholes?.map((loop: any, idx: number) => (
                          <div key={idx} className="p-3 bg-[#161a29]/50 border border-white/5 rounded-xl space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold text-white">{loop.title}</span>
                              <span className="text-[8px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20 font-bold">
                                Severity: {loop.severity}
                              </span>
                            </div>
                            <p className="text-[11px] text-brand-textMuted leading-relaxed">{loop.description}</p>
                          </div>
                        ))}
                      </div>

                      {/* Contradictions */}
                      <div className="space-y-2 mt-4">
                        <h5 className="text-[10px] font-bold uppercase tracking-wider text-brand-textMuted">Inconsistencies & Contradictions</h5>
                        {agent1Audit.contradictions?.map((con: any, idx: number) => (
                          <div key={idx} className="p-3 bg-red-950/20 border border-red-500/10 rounded-xl text-xs space-y-1 text-brand-textMuted">
                            <p><strong className="text-white">Conflicting Items:</strong> "{con.item_a}" vs "{con.item_b}"</p>
                            <p className="text-red-400/80 leading-normal"><strong className="text-white">Discrepancy:</strong> {con.discrepancy}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Missing Evidence & Confidence */}
                    <div className="space-y-4">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-white">
                        Missing Evidence & Proof Requirements
                      </h4>
                      <div className="space-y-2">
                        {agent1Audit.missing_evidence?.map((item: any, idx: number) => (
                          <div key={idx} className="p-3 bg-[#161a29]/50 border border-white/5 rounded-xl space-y-1.5">
                            <div className="flex justify-between items-center">
                              <span className="text-xs font-bold text-white">{item.category}</span>
                              <span className="text-[8px] font-mono text-brand-blue uppercase">{item.impact}</span>
                            </div>
                            <p className="text-[11px] text-brand-textMuted leading-relaxed">{item.description}</p>
                          </div>
                        ))}
                      </div>

                      {/* Confidence Scores */}
                      <div className="p-4 bg-[#111726]/30 border border-white/5 rounded-xl mt-4 space-y-3">
                        <h5 className="text-[10px] font-bold uppercase tracking-wider text-white">Claims Evidentiary Reliability Index</h5>
                        <div className="space-y-2">
                          {agent1Audit.confidence_scores?.map((score: any, idx: number) => (
                            <div key={idx} className="space-y-1">
                              <div className="flex justify-between text-[11px] text-brand-textMuted">
                                <span className="truncate max-w-[220px] font-semibold">{score.claim}</span>
                                <span className="font-bold text-white font-mono">{score.confidence_score}%</span>
                              </div>
                              <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-brand-blue"
                                  style={{ width: `${score.confidence_score}%` }}
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                  </div>
                </>
              )}
            </motion.div>
          )}

          {/* TAB 3: STRATEGY */}
          {activeTab === 'strategy' && (
            <motion.div
              key="strategy"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-6"
            >
              {!agent2Strategy ? (
                <div className="text-center py-10">
                  <AlertTriangle className="w-10 h-10 text-brand-textMuted/30 mx-auto mb-3" />
                  <p className="text-xs text-brand-textMuted">Agent 2 strategy outputs are not available. Please run the AI Pipeline.</p>
                </div>
              ) : (
                <>
                  {/* Lawyer arguments & predicted Attacks */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    
                    {/* Lawyer Arguments */}
                    <div className="space-y-4">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                        <Scale className="w-4 h-4 text-emerald-400" />
                        Lawyer Active Arguments ({caseMeta?.lawyer_side})
                      </h4>
                      <div className="space-y-3">
                        {agent2Strategy.strongest_arguments?.map((arg: string, idx: number) => (
                          <div key={idx} className="p-3 bg-emerald-500/[0.02] border border-emerald-500/10 rounded-xl text-xs space-y-1">
                            <span className="font-bold text-white">Argument: {arg}</span>
                            <p className="text-[10px] text-emerald-400/80 uppercase font-mono mt-0.5">Strength: Strongest Argument</p>
                          </div>
                        ))}
                        {agent2Strategy.moderate_arguments?.map((arg: string, idx: number) => (
                          <div key={idx} className="p-3 bg-brand-blue/[0.02] border border-brand-blue/10 rounded-xl text-xs space-y-1">
                            <span className="font-bold text-white">Argument: {arg}</span>
                            <p className="text-[10px] text-brand-blue uppercase font-mono mt-0.5">Strength: Moderate Argument</p>
                          </div>
                        ))}
                        {agent2Strategy.risky_arguments?.map((arg: string, idx: number) => (
                          <div key={idx} className="p-3 bg-red-500/[0.02] border border-red-500/10 rounded-xl text-xs space-y-1">
                            <span className="font-bold text-white">Argument: {arg}</span>
                            <p className="text-[10px] text-red-400 uppercase font-mono mt-0.5">Strength: High Risk Argument</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Opponent Counterarguments */}
                    <div className="space-y-4">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-red-400 flex items-center gap-1.5">
                        <AlertTriangle className="w-4 h-4 text-red-400" />
                        Predicted Opposing Attacks (Defense)
                      </h4>
                      <div className="space-y-3">
                        {agent2Strategy.opponent_counterarguments?.map((opp: any, idx: number) => (
                          <div key={idx} className="p-3 bg-red-950/20 border border-red-500/10 rounded-xl text-xs space-y-1">
                            <span className="font-bold text-white">Attack Vector: {opp.attack_vector}</span>
                            <p className="text-brand-textMuted leading-relaxed mt-1">{opp.explanation}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                  </div>

                  {/* Rebuttal Narrative Strategies */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-white">
                      Rebuttal Narrative Strategies
                    </h4>
                    <div className="space-y-3">
                      {agent2Strategy.rebuttal_strategies?.map((reb: any, idx: number) => (
                        <div key={idx} className="p-4 bg-[#161a29]/40 border border-white/5 rounded-xl space-y-1.5">
                          <p className="text-[11px] font-bold text-brand-blue uppercase">Target Attack: {reb.counterargument_targeted}</p>
                          <p className="text-xs text-brand-textMuted leading-relaxed">{reb.rebuttal_narrative}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Evidence Utilization Presentation sequence */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-white">
                      Recommended Evidence Sequencing & Presentation
                    </h4>
                    <div className="space-y-2">
                      {agent2Strategy.evidence_utilization_strategy?.map((seq: any, idx: number) => (
                        <div key={idx} className="p-3 bg-[#111726]/30 border border-white/5 rounded-xl text-xs flex items-start gap-4">
                          <span className="w-6 h-6 rounded bg-brand-blue/20 border border-brand-blue/30 text-white font-mono font-bold flex items-center justify-center shrink-0">
                            {seq.sequence_order}
                          </span>
                          <div className="space-y-0.5">
                            <p className="text-brand-textMuted font-bold">File: {seq.evidence_id || "Primary Evidence Doc"}</p>
                            <p className="text-[11px] text-brand-textMuted/70 leading-normal">{seq.presentation_guidance}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </motion.div>
          )}

          {/* TAB 4: REPORT */}
          {activeTab === 'report' && (
            <motion.div
              key="report"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-6"
            >
              {!agent3Report ? (
                <div className="text-center py-10">
                  <AlertTriangle className="w-10 h-10 text-brand-textMuted/30 mx-auto mb-3" />
                  <p className="text-xs text-brand-textMuted">Agent 3 synthesis report is not ready. Please run the AI Pipeline.</p>
                </div>
              ) : (
                <>
                  {/* Download Options */}
                  <div className="p-4 rounded-xl bg-brand-blue/[0.02] border border-brand-blue/15 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="space-y-0.5">
                      <h4 className="text-xs font-bold text-white uppercase tracking-wider">Download Intelligence Brief</h4>
                      <p className="text-[10px] text-brand-textMuted">Save a cryptographically compiled local copy of this Legal intelligence Audit.</p>
                    </div>

                    <div className="flex gap-3 shrink-0">
                      <button
                        onClick={handleDownloadPDF}
                        className="px-3.5 py-2 rounded-xl text-[10px] font-bold tracking-wider text-white border border-red-500/20 hover:border-red-500 bg-red-950/20 hover:bg-red-900/30 transition-all duration-300 flex items-center gap-1.5 cursor-pointer uppercase"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Download PDF</span>
                      </button>

                      <button
                        onClick={handleDownloadDOCX}
                        className="px-3.5 py-2 rounded-xl text-[10px] font-bold tracking-wider text-white border border-brand-blue/20 hover:border-brand-blue bg-brand-blue/10 hover:bg-brand-blue/20 transition-all duration-300 flex items-center gap-1.5 cursor-pointer uppercase"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Download DOCX</span>
                      </button>
                    </div>
                  </div>

                  {/* Executive Summary */}
                  <div className="space-y-2">
                    <h3 className="text-sm font-bold uppercase tracking-wider text-white border-l-2 border-brand-blue pl-2.5">
                      Executive Case Summary
                    </h3>
                    <p className="text-xs text-brand-textMuted leading-relaxed bg-[#111726]/40 p-4 rounded-xl border border-white/5">
                      {agent3Report.executive_summary}
                    </p>
                  </div>

                  {/* Legal Precedents & References */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-white flex items-center gap-1.5">
                      <Landmark className="w-4 h-4 text-brand-blue" />
                      Statutory Precedents & Case References
                    </h4>
                    <div className="space-y-2.5">
                      {agent3Report.legal_references?.map((item: any, idx: number) => (
                        <div key={idx} className="p-3.5 bg-[#161a29]/40 border border-white/5 rounded-xl space-y-1">
                          <p className="text-xs font-bold text-white">{item.act_or_statute}</p>
                          <p className="text-[10px] font-mono text-brand-blue uppercase">Section / Clause: {item.section}</p>
                          <p className="text-[11px] text-brand-textMuted leading-relaxed mt-1">{item.relevance}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Case Assessment Summary */}
                  <div className="p-4 bg-[#111726]/30 border border-white/5 rounded-xl space-y-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-white">AI Case Assessment</h4>
                    <p className="text-xs text-brand-textMuted leading-relaxed">{agent3Report.overall_case_assessment}</p>
                  </div>

                  {/* AI Disclaimer */}
                  <div className="p-3 bg-red-950/20 border border-red-500/10 rounded-xl flex items-start gap-2 text-[10px] text-red-400/80 leading-normal">
                    <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                    <span><strong>Disclaimer:</strong> {agent3Report.ai_disclaimer}</span>
                  </div>
                </>
              )}
            </motion.div>
          )}

          {/* TAB 5: CHAT */}
          {activeTab === 'chat' && (
            <motion.div
              key="chat"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex flex-col h-[520px] justify-between relative overflow-hidden"
            >
              {!isReportReady && (
                <div className="absolute inset-0 bg-[#070A12]/90 backdrop-blur-md z-20 flex flex-col items-center justify-center text-center p-6 rounded-2xl select-none">
                  <Brain className="w-12 h-12 text-red-400 animate-pulse mb-3" />
                  <h3 className="text-sm font-bold uppercase tracking-wider text-white">AI Conversation Locked</h3>
                  <p className="text-xs text-brand-textMuted mt-1.5 max-w-sm">
                    Workspace-level chat compiles evidence insights, strategy simulation, and final synthesis reports. Run the AI Pipeline from the top-right button to activate the chat.
                  </p>
                </div>
              )}

              {/* Message scroll container */}
              <div className="flex-1 overflow-y-auto space-y-4 pr-1 mb-4 select-text">
                {messages.length === 0 ? (
                  <div className="text-center py-20">
                    <Brain className="w-10 h-10 text-brand-textMuted/20 mx-auto mb-3" />
                    <p className="text-xs text-brand-textMuted/50">Ask any case-specific follow-up questions. Your conversations will persist in this workspace.</p>
                  </div>
                ) : (
                  messages.map((msg, idx) => {
                    const isUser = msg.sender === 'user';
                    
                    // Assign header/colors to agent responses
                    let headerColor = 'text-brand-purple';
                    let bgAccent = 'bg-brand-purple/5 border-brand-purple/10';
                    if (msg.agent_name?.includes('Agent 1')) {
                      headerColor = 'text-brand-blue';
                      bgAccent = 'bg-brand-blue/5 border-brand-blue/10';
                    } else if (msg.agent_name?.includes('Agent 2')) {
                      headerColor = 'text-amber-500';
                      bgAccent = 'bg-amber-500/5 border-amber-500/10';
                    }

                    return (
                      <div
                        key={idx}
                        className={`flex flex-col max-w-[85%] ${isUser ? 'ml-auto items-end' : 'mr-auto items-start'}`}
                      >
                        {!isUser && (
                          <span className={`text-[9px] font-bold uppercase tracking-wider mb-1 font-mono ${headerColor}`}>
                            {msg.agent_name}
                          </span>
                        )}
                        <div
                          className={`p-3.5 rounded-2xl text-xs leading-relaxed border ${
                            isUser
                              ? 'bg-brand-blue/10 border-brand-blue/20 text-white rounded-tr-none'
                              : `${bgAccent} text-brand-textMuted rounded-tl-none`
                          }`}
                        >
                          {/* Clean multi-line render */}
                          {msg.text.split('\n').map((line, lIdx) => (
                            <p key={lIdx} className={lIdx > 0 ? 'mt-1.5' : ''}>{line}</p>
                          ))}
                        </div>
                        <span className="text-[8px] text-brand-textMuted/30 font-mono mt-1">
                          {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                    );
                  })
                )}
                {sendingMessage && (
                  <div className="flex flex-col mr-auto items-start max-w-[85%] animate-pulse">
                    <span className="text-[9px] font-bold uppercase tracking-wider mb-1 font-mono text-brand-blue">
                      AI Router Processing...
                    </span>
                    <div className="p-3 bg-white/5 border border-white/10 rounded-2xl rounded-tl-none text-xs text-brand-textMuted/60 flex items-center gap-2">
                      <Loader className="w-3.5 h-3.5 animate-spin" />
                      <span>Specialized agent compiling analysis...</span>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              {/* Chat Input form */}
              <form onSubmit={handleSendMessage} className="flex gap-3 bg-brand-dark/50 border border-white/5 p-2 rounded-xl">
                <input
                  type="text"
                  placeholder="Ask a question about claims, evidence loopholes, or trial strategy..."
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  disabled={sendingMessage}
                  className="flex-1 bg-transparent px-3 py-2 text-xs text-white placeholder-brand-textMuted/40 focus:outline-none"
                />
                <button
                  type="submit"
                  disabled={!inputMessage.trim() || sendingMessage}
                  className="w-10 h-10 rounded-lg bg-brand-blue hover:bg-brand-blue/95 text-white flex items-center justify-center cursor-pointer transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            </motion.div>
          )}

          {/* TAB 6: FILES */}
          {activeTab === 'files' && (
            <motion.div
              key="files"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-6"
            >
              <div className="text-left border-l-2 border-brand-blue pl-3 py-1">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Case Evidence Repository
                </h3>
                <p className="text-xs text-brand-textMuted mt-0.5">
                  Upload new evidence files to this case workspace. Supports PDF, DOCX, Images, and Text.
                </p>
              </div>

              {/* Drag and Drop Zone */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`relative border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center transition-all duration-300 ${
                  dragOver
                    ? 'border-brand-blue bg-brand-blue/5 shadow-[0_0_15px_rgba(79,140,255,0.15)]'
                    : 'border-white/10 bg-[#111827]/30 hover:border-white/20'
                }`}
              >
                <input
                  type="file"
                  onChange={(e) => {
                    if (e.target.files && e.target.files.length > 0) {
                      handleFiles(Array.from(e.target.files));
                    }
                  }}
                  className="absolute inset-0 opacity-0 cursor-pointer z-10"
                />
                
                <div className="p-3 rounded-full bg-white/5 border border-white/10 mb-3">
                  {uploadingFile ? <Loader className="w-6 h-6 text-brand-blue animate-spin" /> : <UploadCloud className="w-6 h-6 text-brand-blue" />}
                </div>
                
                <p className="text-xs font-bold text-white uppercase tracking-wider text-center">
                  {uploadingFile ? 'Uploading file...' : 'Drag and drop additional files here'}
                </p>
                <p className="text-[10px] text-brand-textMuted mt-1 text-center">
                  or click to select a file from drive
                </p>
              </div>

              {/* List files */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-white">Uploaded Evidence Files</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {evidenceFiles.length > 0 ? (
                    evidenceFiles.map((file) => (
                      <div key={file._id} className="p-4 rounded-xl border border-white/5 bg-[#111827]/30 flex items-center justify-between gap-3 hover:border-brand-blue/20 transition-all duration-200">
                        <div className="flex items-center gap-3 truncate">
                          <div className="p-2 rounded bg-white/5 text-brand-blue shrink-0">
                            <FileText className="w-4.5 h-4.5" />
                          </div>
                          <div className="min-w-0">
                            <p className="text-xs font-bold text-white truncate" title={file.file_name}>
                              {file.file_name}
                            </p>
                            <p className="text-[9px] text-brand-textMuted uppercase mt-0.5">
                              {file.evidence_type} // {file.importance_level} Importance
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-1.5 shrink-0">
                          <a
                            href={file.file_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-1.5 rounded hover:bg-white/5 text-brand-textMuted hover:text-white"
                          >
                            <Download className="w-3.5 h-3.5" />
                          </a>
                          <button
                            onClick={() => handleDeleteFile(file._id)}
                            className="p-1.5 rounded hover:bg-white/5 text-brand-textMuted hover:text-red-400 cursor-pointer"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-brand-textMuted/50 col-span-2">No evidence documents uploaded.</p>
                  )}
                </div>
              </div>
            </motion.div>
          )}

        </AnimatePresence>
      </div>

    </div>
  );
};
