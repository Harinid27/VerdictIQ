import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText,
  Download,
  Search,
  Calendar,
  Lock,
  Loader,
} from 'lucide-react';

interface Report {
  id: string;
  title: string;
  generatedDate: string;
  caseName: string;
  confidenceScore: number; // 0-100
  fileSize: string;
  category: string;
}

interface ReportsPageProps {
  reports: Report[];
}

export const ReportsPage: React.FC<ReportsPageProps> = ({ reports }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [decryptingId, setDecryptingId] = useState<string | null>(null);
  const [decryptionStep, setDecryptionStep] = useState(0);

  const filteredReports = reports.filter(
    (r) =>
      r.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.caseName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const startDecryption = (reportId: string) => {
    setDecryptingId(reportId);
    setDecryptionStep(1);

    // Step 1: establish handshake
    setTimeout(() => {
      setDecryptionStep(2);
      // Step 2: verify signature hash
      setTimeout(() => {
        setDecryptionStep(3);
        // Step 3: compile document payload
        setTimeout(() => {
          setDecryptionStep(4);
          // Step 4: download ready
          setTimeout(() => {
            setDecryptingId(null);
            setDecryptionStep(0);
            alert('Document Decrypted. Mock PDF download payload transmitted successfully.');
          }, 1200);
        }, 1200);
      }, 1000);
    }, 1000);
  };

  return (
    <div className="space-y-6 select-none relative">
      {/* Decryption HUD overlay */}
      <AnimatePresence>
        {decryptingId && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#070A12]/90 backdrop-blur-lg"
          >
            <motion.div
              initial={{ scale: 0.95, y: 15 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 15 }}
              className="w-full max-w-[420px] rounded-2xl bg-brand-dark/95 border border-brand-blue/30 p-6 md:p-8 shadow-2xl relative text-center overflow-hidden"
            >
              {/* Scanline gradient effect */}
              <div className="absolute inset-0 bg-gradient-to-b from-brand-blue/5 via-transparent to-transparent pointer-events-none" />

              <div className="relative mb-5 flex items-center justify-center">
                <div className="absolute w-16 h-16 rounded-full bg-brand-blue/20 blur-md animate-pulse" />
                <Lock className="w-8 h-8 text-brand-blue shrink-0 animate-bounce relative z-10" />
              </div>

              <h3 className="text-sm font-bold font-display text-white uppercase tracking-wider mb-1">
                Decrypting Quantum File Payload
              </h3>
              <p className="text-[10px] text-brand-textMuted/60 uppercase tracking-widest font-mono">
                SECURE HANDSHAKE ACTIVE // v1.0.4
              </p>

              <div className="mt-6 space-y-3.5 text-[11px] font-mono text-left max-w-[280px] mx-auto bg-brand-dark border border-white/5 rounded-xl p-4">
                <div className="flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full ${decryptionStep >= 1 ? 'bg-brand-blue animate-pulse' : 'bg-white/10'}`} />
                  <span className={decryptionStep >= 1 ? 'text-brand-blue' : 'text-brand-textMuted/30'}>
                    [1] Handshake node handshakes...
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full ${decryptionStep >= 2 ? 'bg-brand-blue animate-pulse' : 'bg-white/10'}`} />
                  <span className={decryptionStep >= 2 ? 'text-brand-blue' : 'text-brand-textMuted/30'}>
                    [2] Validating RSA signing tokens...
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full ${decryptionStep >= 3 ? 'bg-brand-blue' : 'bg-white/10'}`} />
                  <span className={decryptionStep >= 3 ? 'text-brand-blue' : 'text-brand-textMuted/30'}>
                    [3] Reassembling encrypted blobs...
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full ${decryptionStep >= 4 ? 'bg-emerald-400' : 'bg-white/10'}`} />
                  <span className={decryptionStep >= 4 ? 'text-emerald-400' : 'text-brand-textMuted/30'}>
                    [4] Decrypted. Transporting packet...
                  </span>
                </div>
              </div>

              <div className="mt-6 flex items-center justify-center gap-2 text-[10px] text-brand-textMuted/40 font-mono">
                <Loader className="w-3.5 h-3.5 animate-spin" />
                <span>PLEASE HOLD SIGNAL INTEGRITY</span>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 select-none">
        <div>
          <h2 className="text-xl font-bold uppercase tracking-wider text-white font-display flex items-center gap-2">
            <FileText className="w-5 h-5 text-brand-blue" />
            AI Analytical Reports
          </h2>
          <p className="text-xs text-brand-textMuted mt-0.5">
            View generated evidentiary reviews, witness cross-examination briefs, and regulatory audits.
          </p>
        </div>

        {/* Local Search input */}
        <div className="relative w-full sm:w-64 shrink-0">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-textMuted/45" />
          <input
            type="text"
            placeholder="Search report titles..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#161f30]/65 border border-white/10 rounded-xl pl-9 pr-4 py-2 text-xs text-white focus:outline-none focus:border-brand-blue/50 transition-all duration-300 placeholder-brand-textMuted/45"
          />
        </div>
      </div>

      {/* Reports Grid */}
      {filteredReports.length === 0 ? (
        <div className="text-center py-20 bg-brand-dark/20 rounded-2xl border border-white/5 select-none">
          <FileText className="w-10 h-10 text-brand-textMuted/30 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-white uppercase tracking-wider">
            No Analytical Briefs
          </h3>
          <p className="text-xs text-brand-textMuted/60 mt-1">
            Generate new intelligence audits within the Cases page workspaces.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredReports.map((report) => (
            <div
              key={report.id}
              className="relative group rounded-2xl border border-white/5 bg-[#0e1424]/45 p-5 hover:border-brand-blue/35 transition-all duration-300 shadow-premium-card flex flex-col justify-between"
            >
              {/* Corner ambient shine gradient */}
              <div className="absolute top-0 right-12 w-20 h-[1px] bg-gradient-to-r from-transparent via-brand-purple/20 to-transparent" />

              <div>
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                  <span className="text-[9px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-brand-textMuted font-bold">
                    {report.category}
                  </span>
                  <span className="text-[9px] font-mono text-brand-textMuted/50">
                    {report.fileSize}
                  </span>
                </div>

                {/* Title */}
                <h3 className="text-xs font-bold text-white group-hover:text-brand-blue transition-colors duration-300 line-clamp-2 leading-relaxed">
                  {report.title}
                </h3>

                {/* Metadata */}
                <div className="mt-4 space-y-2 border-y border-white/5 py-3 text-[10px] text-brand-textMuted/60">
                  <div className="flex items-center justify-between">
                    <span>Connected Case:</span>
                    <span className="text-white font-medium truncate max-w-[150px]">
                      {report.caseName}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1 font-mono">
                      <Calendar className="w-3.5 h-3.5 text-brand-textMuted/30" />
                      Generated:
                    </span>
                    <span className="text-white font-medium">{report.generatedDate}</span>
                  </div>
                </div>
              </div>

              {/* Confidence & Action */}
              <div className="flex items-center justify-between mt-5 pt-1 select-none">
                {/* Confidence radial overlay structure */}
                <div className="flex items-center gap-2">
                  <div className="relative w-8 h-8 flex items-center justify-center">
                    <svg className="w-full h-full transform -rotate-90">
                      <circle
                        cx="16"
                        cy="16"
                        r="12"
                        className="stroke-white/5 fill-transparent"
                        strokeWidth="2.5"
                      />
                      <circle
                        cx="16"
                        cy="16"
                        r="12"
                        className="stroke-brand-blue fill-transparent"
                        strokeWidth="2.5"
                        strokeDasharray={2 * Math.PI * 12}
                        strokeDashoffset={2 * Math.PI * 12 * (1 - report.confidenceScore / 100)}
                        strokeLinecap="round"
                      />
                    </svg>
                    <span className="absolute text-[8px] font-bold text-white font-mono">
                      {report.confidenceScore}%
                    </span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[8px] uppercase tracking-wider text-brand-blue font-bold">
                      AI Confidence
                    </span>
                    <span className="text-[6px] text-brand-textMuted/40 leading-none">
                      VERDICT_INDEX_v2
                    </span>
                  </div>
                </div>

                {/* Download decrypt trigger */}
                <button
                  onClick={() => startDecryption(report.id)}
                  className="px-3 py-2 rounded-lg border border-brand-blue/20 hover:border-brand-blue bg-brand-blue/10 hover:bg-brand-blue text-brand-blue hover:text-white transition-all duration-300 cursor-pointer flex items-center gap-1 text-[9px] font-bold uppercase tracking-wider"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Decrypt</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
