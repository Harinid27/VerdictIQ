import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  UploadCloud,
  File,
  X,
  ChevronLeft,
  ChevronRight,
  Brain,
  Scale,
  AlertTriangle,
  CheckCircle,
  FileText,
  Activity,
  Zap,
  Layers
} from 'lucide-react';

interface CreateWorkspaceWizardProps {
  onClose: () => void;
  onSubmit: (data: any) => void;
  casesList: Array<{ id: string; name: string }>;
}

interface EvidenceFile {
  id: string;
  name: string;
  size: string;
  type: string;
  title: string;
  evidenceType: string;
  description: string;
  relatedClaim: string;
  importanceLevel: string;
  uploadProgress: number;
  isUploaded: boolean;
}

export const CreateWorkspaceWizard: React.FC<CreateWorkspaceWizardProps> = ({
  onClose,
  onSubmit,
}) => {
  const [step, setStep] = useState(1);
  const [error, setError] = useState('');

  // Generate a client-side workspace ID (MongoDB-compatible 24-char hex string)
  const [workspaceId] = useState(() => {
    const chars = 'abcdef0123456789';
    let id = '';
    for (let i = 0; i < 24; i++) {
      id += chars[Math.floor(Math.random() * chars.length)];
    }
    return id;
  });

  // STEP 1 State: Basic Case Info
  const [caseName, setCaseName] = useState('');
  const [caseType, setCaseType] = useState('Corporate Dispute');
  const [lawyerSide, setLawyerSide] = useState<'Plaintiff' | 'Defense'>('Plaintiff');
  const [courtType, setCourtType] = useState('');
  const [clientName, setClientName] = useState('');
  const [opposingParty, setOpposingParty] = useState('');
  const [incidentDate, setIncidentDate] = useState('');
  const [casePriority, setCasePriority] = useState('Medium');

  // STEP 2 State: Case Description & Objectives
  const [description, setDescription] = useState('');
  const [claims, setClaims] = useState('');
  const [concerns, setConcerns] = useState('');
  const [expectedOutcome, setExpectedOutcome] = useState('');

  // STEP 3 State: Evidence Upload
  const [evidenceFiles, setEvidenceFiles] = useState<EvidenceFile[]>([]);
  const [dragOver, setDragOver] = useState(false);

  // STEP 4 State: AI Preferences
  const [analysisDepth, setAnalysisDepth] = useState<'Quick' | 'Standard' | 'Advanced'>('Standard');
  const [focusAreas, setFocusAreas] = useState({
    evidenceStrength: true,
    loopholeDetection: true,
    counterarguments: false,
    legalSections: true,
    riskAnalysis: false,
  });

  // STEP 5 State: AI Processing
  const [stagesStatus, setStagesStatus] = useState<('pending' | 'processing' | 'done')[]>([
    'pending', 'pending', 'pending', 'pending', 'pending', 'pending'
  ]);

  const stages = [
    'Processing Documents',
    'Extracting Evidence',
    'Building Legal Context',
    'Detecting Loopholes',
    'Simulating Courtroom Arguments',
    'Generating Legal Intelligence Report'
  ];

  // Run AI processing stages sequence when reaching step 5
  useEffect(() => {
    if (step === 5) {
      const runPipeline = async () => {
        const token = localStorage.getItem('verdictiq_token');
        const headers = {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        };

        try {
          setError('');
          setStagesStatus(['processing', 'pending', 'pending', 'pending', 'pending', 'pending']);
          
          // Step 1: Create Case record
          const createPayload = {
            id: workspaceId,
            name: caseName,
            caseType,
            lawyerSide,
            courtType,
            client: clientName,
            opposingParty,
            incidentDate,
            riskLevel: casePriority === 'Critical' || casePriority === 'High' ? 'High' : casePriority === 'Medium' ? 'Medium' : 'Low',
            evidenceCount: evidenceFiles.length || 0,
            description,
            claims,
            concerns,
            expectedOutcome
          };

          const createRes = await fetch('http://localhost:8000/api/cases/create', {
            method: 'POST',
            headers,
            body: JSON.stringify(createPayload)
          });
          const createData = await createRes.json();
          if (!createRes.ok || !createData.success) {
            throw new Error(createData.message || "Failed to initialize case workspace.");
          }

          // Step 2: Agent 0 (Intake & OCR - represents stages 1, 2, 3)
          setStagesStatus(['done', 'processing', 'pending', 'pending', 'pending', 'pending']);
          const a0Res = await fetch(`http://localhost:8000/api/agent0/process/${workspaceId}`, {
            method: 'POST',
            headers
          });
          const a0Data = await a0Res.json();
          if (!a0Res.ok || !a0Data.success) {
            throw new Error(a0Data.message || "Agent 0 intake processing failed.");
          }

          setStagesStatus(['done', 'done', 'done', 'processing', 'pending', 'pending']);

          // Step 3: Agent 1 (Evidence Auditing - represents stage 4)
          const a1Res = await fetch(`http://localhost:8000/api/agent1/analyze/${workspaceId}`, {
            method: 'POST',
            headers
          });
          const a1Data = await a1Res.json();
          if (!a1Res.ok || !a1Data.success) {
            throw new Error(a1Data.message || "Agent 1 analysis failed.");
          }

          setStagesStatus(['done', 'done', 'done', 'done', 'processing', 'pending']);

          // Step 4: Agent 2 (Courtroom Strategy - represents stage 5)
          const a2Res = await fetch(`http://localhost:8000/api/agent2/generate-strategy/${workspaceId}`, {
            method: 'POST',
            headers
          });
          const a2Data = await a2Res.json();
          if (!a2Res.ok || !a2Data.success) {
            throw new Error(a2Data.message || "Agent 2 strategy simulation failed.");
          }

          setStagesStatus(['done', 'done', 'done', 'done', 'done', 'processing']);

          // Step 5: Agent 3 (Synthesis Report - represents stage 6)
          const a3Res = await fetch(`http://localhost:8000/api/agent3/generate-report/${workspaceId}`, {
            method: 'POST',
            headers
          });
          const a3Data = await a3Res.json();
          if (!a3Res.ok || !a3Data.success) {
            throw new Error(a3Data.message || "Agent 3 report synthesis failed.");
          }

          setStagesStatus(['done', 'done', 'done', 'done', 'done', 'done']);

          // Pipeline finished successfully
          setTimeout(() => {
            const finalData = {
              type: 'case_completed',
              id: workspaceId,
              name: caseName,
              caseType,
              lawyerSide,
              courtType,
              client: clientName,
              opposingParty,
              incidentDate,
              riskLevel: createPayload.riskLevel,
              evidenceCount: createPayload.evidenceCount,
              description,
              claims,
              concerns,
              expectedOutcome
            };
            onSubmit(finalData);
          }, 1500);

        } catch (err: any) {
          setError(err.message || "An unexpected error occurred during pipeline execution.");
          setStagesStatus(['pending', 'pending', 'pending', 'pending', 'pending', 'pending']);
        }
      };

      runPipeline();
    }
  }, [step]);

  const handleNext = () => {
    setError('');
    if (step === 1) {
      if (!caseName.trim() || !clientName.trim() || !opposingParty.trim()) {
        setError('Please fill in Case Name, Client Name, and Opposing Party Name.');
        return;
      }
    }
    if (step === 2) {
      if (!description.trim() || !claims.trim()) {
        setError('Please enter Case Description and Claims/Objectives.');
        return;
      }
    }
    setStep(prev => prev + 1);
  };

  const handleBack = () => {
    setError('');
    setStep(prev => prev - 1);
  };

  // Drag and Drop handlers
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

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(Array.from(e.target.files));
    }
  };

  const uploadFileToServer = (file: File, tempId: string) => {
    const token = localStorage.getItem('verdictiq_token');
    if (!token) return;

    const xhr = new XMLHttpRequest();
    xhr.open('POST', 'http://localhost:8000/api/files/upload', true);
    xhr.setRequestHeader('Authorization', `Bearer ${token}`);

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const percent = Math.round((event.loaded / event.total) * 100);
        setEvidenceFiles(prev =>
          prev.map(f => f.id === tempId ? { ...f, uploadProgress: percent } : f)
        );
      }
    };

    xhr.onload = () => {
      if (xhr.status === 200 || xhr.status === 201) {
        try {
          const res = JSON.parse(xhr.responseText);
          if (res.success && res.data) {
            setEvidenceFiles(prev =>
              prev.map(f => f.id === tempId ? {
                ...f,
                id: res.data._id || res.data.id,
                uploadProgress: 100,
                isUploaded: true
              } : f)
            );
          }
        } catch (e) {
          console.error("Upload response error", e);
        }
      }
    };

    const formData = new FormData();
    formData.append('file', file);
    formData.append('workspace_id', workspaceId);
    formData.append('evidence_type', 'Contract');
    formData.append('description', 'Evidence file uploaded via workspace initialization flow.');
    formData.append('importance_level', 'Important');

    xhr.send(formData);
  };

  const handleFiles = (files: File[]) => {
    const validExtensions = ['pdf', 'png', 'jpg', 'jpeg', 'docx', 'txt'];
    files
      .filter(file => {
        const ext = file.name.split('.').pop()?.toLowerCase() || '';
        return validExtensions.includes(ext);
      })
      .forEach(file => {
        const tempId = `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const sizeStr = file.size > 1024 * 1024
          ? `${(file.size / (1024 * 1024)).toFixed(1)} MB`
          : `${(file.size / 1024).toFixed(0)} KB`;

        const newFile: EvidenceFile = {
          id: tempId,
          name: file.name,
          size: sizeStr,
          type: file.name.split('.').pop()?.toUpperCase() || 'TXT',
          title: file.name.replace(/\.[^/.]+$/, ""),
          evidenceType: 'Contract',
          description: '',
          relatedClaim: '',
          importanceLevel: 'Important',
          uploadProgress: 0,
          isUploaded: false
        };

        setEvidenceFiles(prev => [...prev, newFile]);
        uploadFileToServer(file, tempId);
      });
  };

  const updateEvidenceField = (id: string, field: keyof EvidenceFile, value: any) => {
    setEvidenceFiles(prev =>
      prev.map(f => f.id === id ? { ...f, [field]: value } : f)
    );
  };

  const removeEvidenceFile = (id: string) => {
    setEvidenceFiles(prev => prev.filter(f => f.id !== id));

    const token = localStorage.getItem('verdictiq_token');
    if (token && !id.startsWith('file-')) {
      fetch(`http://localhost:8000/api/files/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            console.log("File deleted successfully from DB & Cloudinary:", id);
          }
        })
        .catch(err => console.error("Error deleting file:", err));
    }
  };

  const toggleFocusArea = (key: keyof typeof focusAreas) => {
    setFocusAreas(prev => ({ ...prev, [key]: !prev[key] }));
  };

  // Render components inside the Wizard steps
  return (
    <div className="relative text-left text-gray-100 font-sans w-full max-w-5xl mx-auto h-[90vh] flex flex-col justify-between rounded-2xl border border-white/10 bg-[#0B0F19]/95 backdrop-blur-xl shadow-2xl overflow-hidden">
      
      {/* Absolute Glow Background Blobs */}
      <div className="absolute top-0 right-1/4 w-96 h-96 bg-brand-purple/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-1/4 w-96 h-96 bg-brand-blue/10 rounded-full blur-3xl pointer-events-none" />
      
      {/* Top Banner Indicator */}
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-brand-blue/50 to-brand-purple/50 opacity-80 z-20" />

      {/* Header */}
      <div className="px-6 py-5 border-b border-white/5 flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-gradient-to-br from-brand-blue/20 to-brand-purple/20 border border-brand-blue/30 text-brand-blue">
            <Brain className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h2 className="text-lg font-bold font-display tracking-wide text-white uppercase">
              Initialize AI Legal Workspace
            </h2>
            <p className="text-xs text-brand-textMuted mt-0.5">
              VerdictIQ Quantum Intellect Pipeline // Step {step} of 5
            </p>
          </div>
        </div>

        {/* Step Progress Dots */}
        {step < 5 && (
          <div className="flex items-center gap-2">
            {[1, 2, 3, 4].map(idx => (
              <div key={idx} className="flex items-center">
                <div
                  className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold font-mono transition-all duration-500 border ${
                    step === idx
                      ? 'bg-brand-blue/20 border-brand-blue text-white shadow-[0_0_12px_rgba(79,140,255,0.4)]'
                      : step > idx
                      ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                      : 'bg-white/5 border-white/10 text-brand-textMuted'
                  }`}
                >
                  {step > idx ? '✓' : idx}
                </div>
                {idx < 4 && (
                  <div
                    className={`w-6 h-[2px] mx-1 transition-all duration-500 ${
                      step > idx ? 'bg-emerald-500/30' : 'bg-white/5'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        )}

        {step < 5 && (
          <button
            onClick={onClose}
            className="text-brand-textMuted hover:text-white transition-colors duration-200 p-1.5 rounded-lg hover:bg-white/5 border border-transparent hover:border-white/10"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Main Body Viewport */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6 z-10 relative">
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-3 bg-red-950/40 border border-red-500/30 rounded-xl text-red-400 text-xs flex items-center gap-2"
          >
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </motion.div>
        )}

        <AnimatePresence mode="wait">
          {step === 1 && (
            <motion.div
              key="step-1"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
              className="space-y-6"
            >
              <div className="text-left border-l-2 border-brand-blue pl-3 py-1">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Basic Case Information
                </h3>
                <p className="text-xs text-brand-textMuted mt-0.5">
                  Input Case details to frame legal parameters.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* Case Name Input */}
                <div className="relative group">
                  <input
                    type="text"
                    required
                    id="caseName"
                    value={caseName}
                    onChange={(e) => setCaseName(e.target.value)}
                    className="w-full bg-[#111827]/70 border border-white/10 rounded-xl px-4 py-3.5 text-sm text-white focus:outline-none focus:border-brand-blue focus:ring-1 focus:ring-brand-blue/30 transition-all duration-300 placeholder-transparent peer"
                    placeholder="Case Name"
                  />
                  <label
                    htmlFor="caseName"
                    className="absolute left-4 top-[-10px] text-xs text-brand-textMuted bg-[#0B0F19] px-1 transition-all duration-300 transform translate-y-[-4px] select-none pointer-events-none peer-placeholder-shown:text-sm peer-placeholder-shown:top-3.5 peer-placeholder-shown:translate-y-0 peer-focus:top-[-10px] peer-focus:text-xs peer-focus:text-brand-blue peer-focus:translate-y-[-4px]"
                    style={{ transformOrigin: 'top left' }}
                  >
                    Workspace / Case Name <span className="text-brand-blue">*</span>
                  </label>
                </div>

                {/* Case Type Dropdown */}
                <div className="relative">
                  <label className="block text-[11px] font-semibold text-brand-textMuted uppercase tracking-wider mb-2">
                    Case Type
                  </label>
                  <select
                    value={caseType}
                    onChange={(e) => setCaseType(e.target.value)}
                    className="w-full bg-[#111827]/70 border border-white/10 rounded-xl px-4 py-3.5 text-sm text-white focus:outline-none focus:border-brand-blue transition-all duration-300 appearance-none cursor-pointer"
                  >
                    <option value="Cybercrime">Cybercrime</option>
                    <option value="Financial Fraud">Financial Fraud</option>
                    <option value="Property Dispute">Property Dispute</option>
                    <option value="Corporate Dispute">Corporate Dispute</option>
                    <option value="Criminal Case">Criminal Case</option>
                    <option value="Contract Breach">Contract Breach</option>
                    <option value="Civil Litigation">Civil Litigation</option>
                    <option value="Harassment">Harassment</option>
                    <option value="Family Dispute">Family Dispute</option>
                  </select>
                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 pt-6 text-brand-textMuted">
                    <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
                  </div>
                </div>

                {/* Side Toggle Selector */}
                <div>
                  <label className="block text-[11px] font-semibold text-brand-textMuted uppercase tracking-wider mb-2">
                    Lawyer / Counsel Side
                  </label>
                  <div className="flex bg-[#111827]/70 p-1.5 rounded-xl border border-white/10 gap-2">
                    <button
                      type="button"
                      onClick={() => setLawyerSide('Plaintiff')}
                      className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all duration-300 ${
                        lawyerSide === 'Plaintiff'
                          ? 'bg-brand-blue/20 border border-brand-blue/30 text-white shadow-[0_0_8px_rgba(79,140,255,0.15)]'
                          : 'text-brand-textMuted hover:text-white'
                      }`}
                    >
                      Plaintiff
                    </button>
                    <button
                      type="button"
                      onClick={() => setLawyerSide('Defense')}
                      className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all duration-300 ${
                        lawyerSide === 'Defense'
                          ? 'bg-brand-purple/20 border border-brand-purple/30 text-white shadow-[0_0_8px_rgba(123,97,255,0.15)]'
                          : 'text-brand-textMuted hover:text-white'
                      }`}
                    >
                      Defense
                    </button>
                  </div>
                </div>

                {/* Court Type Input */}
                <div className="relative group">
                  <input
                    type="text"
                    id="courtType"
                    value={courtType}
                    onChange={(e) => setCourtType(e.target.value)}
                    className="w-full bg-[#111827]/70 border border-white/10 rounded-xl px-4 py-3.5 text-sm text-white focus:outline-none focus:border-brand-blue focus:ring-1 focus:ring-brand-blue/30 transition-all duration-300 placeholder-transparent peer"
                    placeholder="Court Type"
                  />
                  <label
                    htmlFor="courtType"
                    className="absolute left-4 top-[-10px] text-xs text-brand-textMuted bg-[#0B0F19] px-1 transition-all duration-300 transform translate-y-[-4px] select-none pointer-events-none peer-placeholder-shown:text-sm peer-placeholder-shown:top-3.5 peer-placeholder-shown:translate-y-0 peer-focus:top-[-10px] peer-focus:text-xs peer-focus:text-brand-blue peer-focus:translate-y-[-4px]"
                    style={{ transformOrigin: 'top left' }}
                  >
                    Court Jurisdiction
                  </label>
                </div>

                {/* Client Name Input */}
                <div className="relative group">
                  <input
                    type="text"
                    required
                    id="clientName"
                    value={clientName}
                    onChange={(e) => setClientName(e.target.value)}
                    className="w-full bg-[#111827]/70 border border-white/10 rounded-xl px-4 py-3.5 text-sm text-white focus:outline-none focus:border-brand-blue focus:ring-1 focus:ring-brand-blue/30 transition-all duration-300 placeholder-transparent peer"
                    placeholder="Client Name"
                  />
                  <label
                    htmlFor="clientName"
                    className="absolute left-4 top-[-10px] text-xs text-brand-textMuted bg-[#0B0F19] px-1 transition-all duration-300 transform translate-y-[-4px] select-none pointer-events-none peer-placeholder-shown:text-sm peer-placeholder-shown:top-3.5 peer-placeholder-shown:translate-y-0 peer-focus:top-[-10px] peer-focus:text-xs peer-focus:text-brand-blue peer-focus:translate-y-[-4px]"
                    style={{ transformOrigin: 'top left' }}
                  >
                    Client Name <span className="text-brand-blue">*</span>
                  </label>
                </div>

                {/* Opposing Party Name Input */}
                <div className="relative group">
                  <input
                    type="text"
                    required
                    id="opposingParty"
                    value={opposingParty}
                    onChange={(e) => setOpposingParty(e.target.value)}
                    className="w-full bg-[#111827]/70 border border-white/10 rounded-xl px-4 py-3.5 text-sm text-white focus:outline-none focus:border-brand-blue focus:ring-1 focus:ring-brand-blue/30 transition-all duration-300 placeholder-transparent peer"
                    placeholder="Opposing Party Name"
                  />
                  <label
                    htmlFor="opposingParty"
                    className="absolute left-4 top-[-10px] text-xs text-brand-textMuted bg-[#0B0F19] px-1 transition-all duration-300 transform translate-y-[-4px] select-none pointer-events-none peer-placeholder-shown:text-sm peer-placeholder-shown:top-3.5 peer-placeholder-shown:translate-y-0 peer-focus:top-[-10px] peer-focus:text-xs peer-focus:text-brand-blue peer-focus:translate-y-[-4px]"
                    style={{ transformOrigin: 'top left' }}
                  >
                    Opposing Party <span className="text-brand-blue">*</span>
                  </label>
                </div>

                {/* Incident Date Input */}
                <div className="relative group">
                  <input
                    type="date"
                    id="incidentDate"
                    value={incidentDate}
                    onChange={(e) => setIncidentDate(e.target.value)}
                    className="w-full bg-[#111827]/70 border border-white/10 rounded-xl px-4 py-3.5 text-sm text-white focus:outline-none focus:border-brand-blue transition-all duration-300 peer"
                  />
                  <label
                    htmlFor="incidentDate"
                    className="absolute left-4 top-[-10px] text-xs text-brand-textMuted bg-[#0B0F19] px-1 select-none transition-all duration-300 transform translate-y-[-4px] peer-focus:text-brand-blue"
                  >
                    Incident Date
                  </label>
                </div>

                {/* Case Priority Options */}
                <div className="relative">
                  <label className="block text-[11px] font-semibold text-brand-textMuted uppercase tracking-wider mb-2">
                    Case Priority
                  </label>
                  <select
                    value={casePriority}
                    onChange={(e) => setCasePriority(e.target.value)}
                    className="w-full bg-[#111827]/70 border border-white/10 rounded-xl px-4 py-3.5 text-sm text-white focus:outline-none focus:border-brand-blue transition-all duration-300 appearance-none cursor-pointer"
                  >
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                    <option value="Critical">Critical</option>
                  </select>
                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 pt-6 text-brand-textMuted">
                    <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
                  </div>
                </div>

              </div>
            </motion.div>
          )}

          {step === 2 && (
            <motion.div
              key="step-2"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
              className="space-y-6"
            >
              <div className="text-left border-l-2 border-brand-purple pl-3 py-1">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Case Description & Objectives
                </h3>
                <p className="text-xs text-brand-textMuted mt-0.5">
                  Elaborate on case context to train the cognitive parser.
                </p>
              </div>

              <div className="space-y-5">
                
                {/* Description Textarea */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-brand-textMuted uppercase tracking-wider flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5 text-brand-blue" />
                    Detailed Case Description <span className="text-brand-blue">*</span>
                  </label>
                  <textarea
                    rows={4}
                    required
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Explain the case in detail, timeline of events, and legal issue."
                    className="w-full bg-[#111827]/60 border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-brand-blue focus:ring-1 focus:ring-brand-blue/30 transition-all duration-300 placeholder-white/20 resize-none hover:border-white/15"
                  />
                </div>

                {/* Claims / Objectives */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-brand-textMuted uppercase tracking-wider flex items-center gap-1.5">
                    <Scale className="w-3.5 h-3.5 text-brand-purple" />
                    Claims / Objectives <span className="text-brand-purple">*</span>
                  </label>
                  <textarea
                    rows={3}
                    required
                    value={claims}
                    onChange={(e) => setClaims(e.target.value)}
                    placeholder="What are you trying to prove or defend?"
                    className="w-full bg-[#111827]/60 border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-brand-purple focus:ring-1 focus:ring-brand-purple/30 transition-all duration-300 placeholder-white/20 resize-none hover:border-white/15"
                  />
                </div>

                {/* Risks / Concerns */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-brand-textMuted uppercase tracking-wider flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                    Existing Concerns / Risks
                  </label>
                  <textarea
                    rows={3}
                    value={concerns}
                    onChange={(e) => setConcerns(e.target.value)}
                    placeholder="Mention any weaknesses or legal concerns you suspect."
                    className="w-full bg-[#111827]/60 border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-amber-500/70 focus:ring-1 focus:ring-amber-500/20 transition-all duration-300 placeholder-white/20 resize-none hover:border-white/15"
                  />
                </div>

                {/* Expected Outcome */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-brand-textMuted uppercase tracking-wider flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-emerald-500" />
                    Expected Outcome
                  </label>
                  <textarea
                    rows={2}
                    value={expectedOutcome}
                    onChange={(e) => setExpectedOutcome(e.target.value)}
                    placeholder="What legal outcome are you aiming for?"
                    className="w-full bg-[#111827]/60 border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-emerald-500/70 focus:ring-1 focus:ring-emerald-500/20 transition-all duration-300 placeholder-white/20 resize-none hover:border-white/15"
                  />
                </div>

              </div>
            </motion.div>
          )}

          {step === 3 && (
            <motion.div
              key="step-3"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
              className="space-y-6"
            >
              <div className="text-left border-l-2 border-emerald-500 pl-3 py-1">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Evidence Upload System
                </h3>
                <p className="text-xs text-brand-textMuted mt-0.5">
                  Attach files and supply semantic tags. Supports PDF, PNG, JPG, DOCX, TXT.
                </p>
              </div>

              {/* Upload Drop Zone */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`relative border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center transition-all duration-300 ${
                  dragOver
                    ? 'border-brand-blue bg-brand-blue/5 shadow-[0_0_15px_rgba(79,140,255,0.15)] scale-[1.01]'
                    : 'border-white/10 bg-[#111827]/30 hover:border-white/20'
                }`}
              >
                <input
                  type="file"
                  multiple
                  accept=".pdf,.png,.jpg,.jpeg,.docx,.txt"
                  onChange={handleFileChange}
                  className="absolute inset-0 opacity-0 cursor-pointer z-10"
                />
                
                <div className="p-4 rounded-full bg-white/5 border border-white/10 mb-4 animate-bounce">
                  <UploadCloud className="w-8 h-8 text-brand-blue" />
                </div>
                
                <p className="text-sm font-bold text-white uppercase tracking-wider text-center">
                  Drag and drop files here
                </p>
                <p className="text-xs text-brand-textMuted mt-1.5 text-center">
                  or click to browse from local drive
                </p>
                <div className="flex items-center gap-3 mt-4 text-[10px] text-brand-textMuted/60 uppercase font-mono">
                  <span>PDF</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-white/15" />
                  <span>Images</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-white/15" />
                  <span>DOCX</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-white/15" />
                  <span>TXT</span>
                </div>
              </div>

              {/* Uploaded Files grid */}
              {evidenceFiles.length > 0 && (
                <div className="space-y-4">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                    Evidence Repository ({evidenceFiles.length})
                  </h4>
                  
                  <div className="grid grid-cols-1 gap-4 max-h-[260px] overflow-y-auto pr-1">
                    {evidenceFiles.map(file => (
                      <div
                        key={file.id}
                        className="relative rounded-xl border border-white/10 bg-[#111827]/70 p-4 shadow-sm hover:border-brand-blue/30 transition-all duration-300 flex flex-col md:flex-row md:items-start gap-4"
                      >
                        {/* File Details Sidebar */}
                        <div className="flex items-center gap-3 shrink-0 md:w-44 truncate">
                          <div className="p-2 rounded-lg bg-white/5 border border-white/10 text-brand-blue">
                            {file.type === 'PDF' ? <FileText className="w-5 h-5" /> : <File className="w-5 h-5" />}
                          </div>
                          <div className="min-w-0">
                            <p className="text-xs font-bold text-white truncate" title={file.name}>
                              {file.name}
                            </p>
                            <p className="text-[10px] text-brand-textMuted mt-0.5 font-mono">
                              {file.size} // {file.type}
                            </p>
                          </div>
                        </div>

                        {/* Card input forms */}
                        <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                          
                          {/* Evidence Title */}
                          <div>
                            <label className="block text-[10px] text-brand-textMuted uppercase mb-1">
                              Evidence Title
                            </label>
                            <input
                              type="text"
                              value={file.title}
                              onChange={(e) => updateEvidenceField(file.id, 'title', e.target.value)}
                              className="w-full bg-[#0B0F19] border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-brand-blue"
                            />
                          </div>

                          {/* Evidence Type */}
                          <div>
                            <label className="block text-[10px] text-brand-textMuted uppercase mb-1">
                              Evidence Type
                            </label>
                            <select
                              value={file.evidenceType}
                              onChange={(e) => updateEvidenceField(file.id, 'evidenceType', e.target.value)}
                              className="w-full bg-[#0B0F19] border border-white/10 rounded-lg px-2 py-1.5 text-xs text-white focus:outline-none focus:border-brand-blue cursor-pointer"
                            >
                              <option value="Financial Record">Financial Record</option>
                              <option value="Witness Statement">Witness Statement</option>
                              <option value="Digital Screenshot">Digital Screenshot</option>
                              <option value="Contract">Contract</option>
                              <option value="Email Evidence">Email Evidence</option>
                              <option value="Call Record">Call Record</option>
                              <option value="Government Document">Government Document</option>
                              <option value="Medical Report">Medical Report</option>
                              <option value="Timeline Evidence">Timeline Evidence</option>
                              <option value="Other">Other</option>
                            </select>
                          </div>

                          {/* Related Claim */}
                          <div>
                            <label className="block text-[10px] text-brand-textMuted uppercase mb-1">
                              Related Claim / Issue
                            </label>
                            <input
                              type="text"
                              value={file.relatedClaim}
                              onChange={(e) => updateEvidenceField(file.id, 'relatedClaim', e.target.value)}
                              placeholder="e.g. Contract breach timeline"
                              className="w-full bg-[#0B0F19] border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-brand-blue"
                            />
                          </div>

                          {/* Importance Level */}
                          <div>
                            <label className="block text-[10px] text-brand-textMuted uppercase mb-1">
                              Importance Level
                            </label>
                            <select
                              value={file.importanceLevel}
                              onChange={(e) => updateEvidenceField(file.id, 'importanceLevel', e.target.value)}
                              className="w-full bg-[#0B0F19] border border-white/10 rounded-lg px-2 py-1.5 text-xs text-white focus:outline-none focus:border-brand-blue cursor-pointer"
                            >
                              <option value="Critical">Critical</option>
                              <option value="Important">Important</option>
                              <option value="Supporting">Supporting</option>
                              <option value="Optional">Optional</option>
                            </select>
                          </div>

                          {/* Purpose / Description (Highly Important) */}
                          <div className="sm:col-span-2">
                            <label className="block text-[10px] text-brand-blue uppercase font-bold mb-1 tracking-wider">
                              Description / Purpose *
                            </label>
                            <textarea
                              rows={2}
                              value={file.description}
                              onChange={(e) => updateEvidenceField(file.id, 'description', e.target.value)}
                              placeholder="Explain how this evidence supports the case."
                              className="w-full bg-[#0B0F19] border border-white/10 rounded-lg px-2.5 py-2 text-xs text-white focus:outline-none focus:border-brand-blue placeholder-white/20 resize-none"
                            />
                          </div>

                        </div>

                        {/* Progress Bar & Actions */}
                        <div className="flex flex-row md:flex-col items-center justify-between shrink-0 h-full gap-2 self-center md:self-stretch">
                          <button
                            onClick={() => removeEvidenceFile(file.id)}
                            className="p-1.5 rounded-lg border border-white/5 hover:border-red-500/20 text-brand-textMuted/60 hover:text-red-400 bg-transparent transition-all duration-300"
                            title="Delete file"
                          >
                            <X className="w-4 h-4" />
                          </button>

                          {!file.isUploaded && (
                            <div className="w-12 text-right">
                              <span className="text-[10px] font-mono text-brand-blue font-semibold">
                                {file.uploadProgress}%
                              </span>
                              <div className="w-12 h-[3px] bg-white/5 rounded-full overflow-hidden mt-1">
                                <div
                                  className="h-full bg-gradient-to-r from-brand-blue to-brand-purple transition-all duration-150"
                                  style={{ width: `${file.uploadProgress}%` }}
                                />
                              </div>
                            </div>
                          )}

                          {file.isUploaded && (
                            <div className="p-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                              <CheckCircle className="w-4 h-4" />
                            </div>
                          )}
                        </div>

                      </div>
                    ))}
                  </div>
                </div>
              )}

            </motion.div>
          )}

          {step === 4 && (
            <motion.div
              key="step-4"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
              className="space-y-6"
            >
              <div className="text-left border-l-2 border-amber-500 pl-3 py-1">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  AI Analysis Preferences
                </h3>
                <p className="text-xs text-brand-textMuted mt-0.5">
                  Tailor the cognitive focus of the legal AI engine.
                </p>
              </div>

              {/* Analysis Depth Section */}
              <div className="space-y-3">
                <label className="block text-xs font-semibold text-brand-textMuted uppercase tracking-wider">
                  Analysis Depth Selection
                </label>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {[
                    {
                      name: 'Quick' as const,
                      desc: 'Instant scanning for key terms and quick claim checking. Estimated time: ~10 seconds.',
                      icon: Zap
                    },
                    {
                      name: 'Standard' as const,
                      desc: 'Balanced assessment. Checks timelines, legal citation references, and core evidence strength. Estimated time: ~1 min.',
                      icon: Layers
                    },
                    {
                      name: 'Advanced' as const,
                      desc: 'Deep cognitive audit. Simulates trial arguments, flags loophole hazards, and compiles reports. Estimated time: ~3 mins.',
                      icon: Brain
                    }
                  ].map(depth => {
                    const Icon = depth.icon;
                    return (
                      <button
                        key={depth.name}
                        type="button"
                        onClick={() => setAnalysisDepth(depth.name)}
                        className={`relative text-left p-4 rounded-xl border flex flex-col justify-between h-36 transition-all duration-300 bg-[#111827]/40 ${
                          analysisDepth === depth.name
                            ? 'border-brand-blue bg-[#111827]/70 shadow-[0_0_15px_rgba(79,140,255,0.15)] ring-1 ring-brand-blue/30'
                            : 'border-white/5 hover:border-white/10 hover:bg-[#111827]/60'
                        }`}
                      >
                        <div className="flex items-center justify-between w-full">
                          <span className={`text-xs font-bold uppercase tracking-wider ${
                            analysisDepth === depth.name ? 'text-brand-blue' : 'text-white'
                          }`}>
                            {depth.name}
                          </span>
                          <Icon className={`w-4 h-4 ${
                            analysisDepth === depth.name ? 'text-brand-blue animate-pulse' : 'text-brand-textMuted'
                          }`} />
                        </div>
                        <p className="text-[11px] text-brand-textMuted/80 mt-2 leading-relaxed">
                          {depth.desc}
                        </p>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Analysis Focus Areas */}
              <div className="space-y-3">
                <label className="block text-xs font-semibold text-brand-textMuted uppercase tracking-wider">
                  AI Focus Grids
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                  {[
                    { key: 'evidenceStrength' as const, title: 'Evidence Strength Audit', desc: 'Analyzes files for weight, chain of custody, and relevance.' },
                    { key: 'loopholeDetection' as const, title: 'Loophole Discovery', desc: 'Identifies contract breaches, timeline flaws, and discrepancies.' },
                    { key: 'counterarguments' as const, title: 'Simulate Opposing counsel', desc: 'Forecasts defense strategies and courtroom objections.' },
                    { key: 'legalSections' as const, title: 'Jurisdiction Citation Map', desc: 'Maps statutory elements to state/federal legal codes.' },
                    { key: 'riskAnalysis' as const, title: 'Exculpatory Risk Gauge', desc: 'Evaluates critical vulnerabilities and penalty estimates.' }
                  ].map(item => (
                    <button
                      key={item.key}
                      type="button"
                      onClick={() => toggleFocusArea(item.key)}
                      className={`text-left p-3.5 rounded-xl border transition-all duration-300 bg-[#111827]/30 flex gap-3 ${
                        focusAreas[item.key]
                          ? 'border-brand-purple bg-[#111827]/70 shadow-[0_0_12px_rgba(123,97,255,0.1)]'
                          : 'border-white/5 hover:border-white/10'
                      }`}
                    >
                      <div className="pt-0.5">
                        <div className={`w-4.5 h-4.5 rounded border flex items-center justify-center transition-all duration-300 ${
                          focusAreas[item.key]
                            ? 'bg-brand-purple/20 border-brand-purple text-brand-purple'
                            : 'border-white/20 bg-transparent text-transparent'
                        }`}>
                          <CheckCircle className="w-3 h-3" />
                        </div>
                      </div>
                      <div>
                        <p className={`text-xs font-bold tracking-wide uppercase ${
                          focusAreas[item.key] ? 'text-brand-purple' : 'text-white'
                        }`}>
                          {item.title}
                        </p>
                        <p className="text-[10px] text-brand-textMuted/70 mt-1 leading-snug">
                          {item.desc}
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

            </motion.div>
          )}

          {step === 5 && (
            <motion.div
              key="step-5"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4 }}
              className="flex flex-col items-center justify-center py-12 text-center"
            >
              {/* Radar loading simulation */}
              <div className="relative flex items-center justify-center mb-8 h-28 w-28">
                <div className="absolute w-24 h-24 rounded-full border border-brand-blue/30 animate-ping opacity-75" />
                <div className="absolute w-18 h-18 rounded-full border border-brand-purple/30 animate-spin" />
                <div className="absolute w-12 h-12 rounded-full bg-gradient-to-tr from-brand-blue to-brand-purple flex items-center justify-center shadow-[0_0_20px_rgba(123,97,255,0.4)]">
                  <Brain className="w-6 h-6 text-white animate-pulse" />
                </div>
              </div>

              <h3 className="text-lg font-bold text-white uppercase tracking-[0.2em] font-display">
                Initializing Intelligence Workspace
              </h3>
              <p className="text-xs text-brand-textMuted mt-1 max-w-sm">
                Compiling files, setting vector databases, and spinning up analysis nodes.
              </p>

              {/* Progress Stage Nodes */}
              <div className="mt-8 space-y-3.5 w-full max-w-md text-left bg-[#111827]/40 border border-white/5 p-5 rounded-2xl">
                {stages.map((stage, idx) => {
                  const status = stagesStatus[idx];
                  return (
                    <div key={idx} className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-3">
                        <div className={`w-5 h-5 rounded-lg flex items-center justify-center font-bold text-[10px] border transition-all duration-300 ${
                          status === 'done'
                            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                            : status === 'processing'
                            ? 'bg-brand-blue/10 border-brand-blue/40 text-brand-blue animate-pulse'
                            : 'bg-white/5 border-white/10 text-brand-textMuted/40'
                        }`}>
                          {status === 'done' ? '✓' : idx + 1}
                        </div>
                        <span className={`transition-colors duration-300 ${
                          status === 'done'
                            ? 'text-gray-400 line-through decoration-white/10'
                            : status === 'processing'
                            ? 'text-white font-semibold'
                            : 'text-brand-textMuted/40'
                        }`}>
                          {stage}
                        </span>
                      </div>
                      
                      {status === 'processing' && (
                        <div className="flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-brand-blue animate-bounce [animation-delay:-0.3s]" />
                          <span className="w-1.5 h-1.5 rounded-full bg-brand-blue animate-bounce [animation-delay:-0.15s]" />
                          <span className="w-1.5 h-1.5 rounded-full bg-brand-blue animate-bounce" />
                        </div>
                      )}

                      {status === 'done' && (
                        <span className="text-[10px] text-emerald-400 font-mono">COMPLETE</span>
                      )}

                      {status === 'pending' && (
                        <span className="text-[10px] text-brand-textMuted/20 font-mono">QUEUED</span>
                      )}
                    </div>
                  );
                })}
              </div>

            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer Navigation */}
      {step < 5 && (
        <div className="px-6 py-4 border-t border-white/5 flex items-center justify-between bg-[#111827]/25 shrink-0 z-10">
          
          {/* Back button */}
          {step > 1 ? (
            <button
              onClick={handleBack}
              className="px-4 py-2.5 rounded-xl border border-white/10 hover:border-white/20 text-brand-textMuted hover:text-white transition-all duration-300 flex items-center gap-2 text-xs font-semibold"
            >
              <ChevronLeft className="w-4 h-4" />
              <span>Back</span>
            </button>
          ) : (
            <div />
          )}

          {/* Next / Initialize button */}
          <button
            onClick={handleNext}
            className="px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-brand-blue to-brand-purple shadow-button-glow hover:translate-y-[-1px] active:translate-y-[0] transition-all duration-300 flex items-center gap-2 font-display uppercase tracking-wider"
          >
            <span>{step === 4 ? 'Initialize Workspace' : 'Continue'}</span>
            {step < 4 ? <ChevronRight className="w-4 h-4" /> : <Brain className="w-4 h-4" />}
          </button>

        </div>
      )}

    </div>
  );
};
