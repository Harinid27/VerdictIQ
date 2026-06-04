import { useState, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { BackgroundEffects } from './components/BackgroundEffects';
import { LoginCard } from './components/LoginCard';
import { SignupCard } from './components/SignupCard';
import { Sidebar } from './components/Sidebar';
import { Navbar } from './components/Navbar';
import { DashboardOverview } from './components/DashboardOverview';
import { CasesPage } from './components/CasesPage';
import { CalendarPage } from './components/CalendarPage';
import { TasksPage } from './components/TasksPage';
import { ReportsPage } from './components/ReportsPage';
import { ProfilePage } from './components/ProfilePage';
import { SettingsPage } from './components/SettingsPage';
import { CaseModal } from './components/CaseModal';
import { WorkspaceDetailPage } from './components/WorkspaceDetailPage';
import { Menu, X } from 'lucide-react';

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
  caseId: string;
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

interface Report {
  id: string;
  title: string;
  generatedDate: string;
  caseName: string;
  confidenceScore: number;
  fileSize: string;
  category: string;
}

function App() {
  const [activeView, setActiveView] = useState<'login' | 'signup' | 'dashboard'>('login');
  const [isVerifyingSession, setIsVerifyingSession] = useState(true);
  const [user, setUser] = useState({
    email: 'attorney@verdictiq.ai',
    name: 'Alexander Vance',
    organization: 'Vance & Associates LLP',
    role: 'Lead Legal Counsel',
  });

  const [activeTab, setActiveTab] = useState('Dashboard');
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [globalSearch, setGlobalSearch] = useState('');

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    setSelectedCaseId(null);
  };

  // Modal Controls
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<'case' | 'hearing' | 'task'>('case');

  // MOCK DATABASES
  const [cases, setCases] = useState<Case[]>([]);
  const [hearings, setHearings] = useState<Hearing[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [reports, setReports] = useState<Report[]>([]);

  // Handle Collapsed Sidebar on screen resize
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setSidebarCollapsed(true);
      } else {
        setSidebarCollapsed(false);
      }
    };
    window.addEventListener('resize', handleResize);
    handleResize(); // trigger on mount
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Helper to fetch user data from API
  const fetchDatabaseData = (token: string) => {
    const headers = { 'Authorization': `Bearer ${token}` };

    // Fetch Cases
    fetch('http://localhost:8000/api/cases/all', { headers })
      .then((res) => res.json())
      .then((data) => {
        if (data.success && data.data) {
          setCases(data.data.map((c: any) => ({
            id: c._id || c.id,
            name: c.name,
            caseType: c.caseType,
            lawyerSide: c.lawyerSide,
            lastUpdated: c.lastUpdated || 'Just now',
            riskLevel: c.riskLevel || 'Medium',
            evidenceCount: c.evidenceCount || 0,
            status: c.status || 'Pre-Trial Audit',
            client: c.client
          })));
        }
      })
      .catch((err) => console.error("Error loading cases from API:", err));

    // Fetch Tasks
    fetch('http://localhost:8000/api/tasks/all', { headers })
      .then((res) => res.json())
      .then((data) => {
        if (data.success && data.data) {
          setTasks(data.data.map((t: any) => ({
            id: t._id || t.id,
            title: t.title,
            dueDate: t.due_date,
            caseName: t.case_name,
            caseId: t.workspace_id,
            completed: t.completed,
            priority: t.priority
          })));
        }
      })
      .catch((err) => console.error("Error loading tasks from API:", err));

    // Fetch Hearings
    fetch('http://localhost:8000/api/hearings/all', { headers })
      .then((res) => res.json())
      .then((data) => {
        if (data.success && data.data) {
          setHearings(data.data.map((h: any) => ({
            id: h._id || h.id,
            caseName: h.case_name,
            date: h.hearing_time ? `${h.hearing_date}T${h.hearing_time}` : h.hearing_date,
            court: h.court_name,
            priority: h.priority
          })));
        }
      })
      .catch((err) => console.error("Error loading hearings from API:", err));

    // Fetch Reports
    fetch('http://localhost:8000/api/agent3/reports/all', { headers })
      .then((res) => res.json())
      .then((data) => {
        if (data.success && data.data) {
          setReports(data.data);
        }
      })
      .catch((err) => console.error("Error loading reports from API:", err));
  };

  // Verify token session on initial app mount
  useEffect(() => {
    const token = localStorage.getItem('verdictiq_token');
    if (token) {
      fetch('http://localhost:8000/api/auth/me', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.success && data.user) {
            setUser({
              email: data.user.email,
              name: data.user.full_name,
              organization: data.user.organization,
              role: data.user.role,
            });
            setActiveView('dashboard');
            fetchDatabaseData(token);
          } else {
            localStorage.removeItem('verdictiq_token');
          }
          setIsVerifyingSession(false);
        })
        .catch(() => {
          setIsVerifyingSession(false);
        });
    } else {
      setIsVerifyingSession(false);
    }
  }, []);

  // Fetch db data when active view is dashboard
  useEffect(() => {
    const token = localStorage.getItem('verdictiq_token');
    if (activeView === 'dashboard' && token) {
      fetchDatabaseData(token);
    }
  }, [activeView]);

  // Fetch / refresh reports dynamically when switching to Reports tab
  useEffect(() => {
    const token = localStorage.getItem('verdictiq_token');
    if (activeTab === 'Reports' && token) {
      const headers = { 'Authorization': `Bearer ${token}` };
      fetch('http://localhost:8000/api/agent3/reports/all', { headers })
        .then((res) => res.json())
        .then((data) => {
          if (data.success && data.data) {
            setReports(data.data);
          }
        })
        .catch((err) => console.error("Error loading reports from API:", err));
    }
  }, [activeTab]);

  // Auth Handling callbacks
  const handleLoginSuccess = (token: string, userData: any) => {
    localStorage.setItem('verdictiq_token', token);
    setUser({
      email: userData.email,
      name: userData.full_name,
      organization: userData.organization,
      role: userData.role,
    });
    setActiveView('dashboard');
  };

  const handleSignupSuccess = (token: string, userData: any) => {
    localStorage.setItem('verdictiq_token', token);
    setUser({
      email: userData.email,
      name: userData.full_name,
      organization: userData.organization,
      role: userData.role,
    });
    setActiveView('dashboard');
  };

  const handleLogout = () => {
    localStorage.removeItem('verdictiq_token');
    setActiveView('login');
    setActiveTab('Dashboard');
  };

  // Checklist handler
  const handleToggleTaskComplete = (taskId: string) => {
    setTasks(
      tasks.map((t) => (t.id === taskId ? { ...t, completed: !t.completed } : t))
    );

    const token = localStorage.getItem('verdictiq_token');
    if (token && !taskId.startsWith('task-')) {
      fetch(`http://localhost:8000/api/tasks/complete/${taskId}`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .catch((err) => console.error("Error toggling task status:", err));
    }
  };

  // Add items handler
  const handleModalSubmit = (data: any) => {
    const token = localStorage.getItem('verdictiq_token');
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };

    if (data.type === 'case' || data.type === 'case_completed') {
      const payload = {
        id: data.id, // Pass pre-generated workspace ID from wizard
        name: data.name,
        caseType: data.caseType,
        lawyerSide: data.lawyerSide,
        courtType: data.courtType || "State Court",
        client: data.client,
        opposingParty: data.opposingParty || "Opposing Counsel",
        incidentDate: data.incidentDate || "2026-06-03",
        riskLevel: data.riskLevel,
        evidenceCount: data.evidenceCount
      };

      if (data.type === 'case_completed') {
        const newCase: Case = {
          id: data.id,
          name: data.name,
          caseType: data.caseType,
          lawyerSide: data.lawyerSide,
          lastUpdated: 'Just now',
          riskLevel: data.riskLevel,
          evidenceCount: data.evidenceCount,
          status: 'Discovery Phase',
          client: data.client
        };
        setCases((prev) => [newCase, ...prev]);
        setSelectedCaseId(data.id); // Auto-open workspace!
        setModalOpen(false); // Close the wizard modal overlay
        return;
      }

      fetch('http://localhost:8000/api/cases/create', {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
      })
        .then((res) => res.json())
        .then((resData) => {
          if (resData.success && resData.data) {
            const c = resData.data;
            const newCase: Case = {
              id: c._id || c.id,
              name: c.name,
              caseType: c.caseType,
              lawyerSide: c.lawyerSide,
              lastUpdated: 'Just now',
              riskLevel: c.riskLevel,
              evidenceCount: c.evidenceCount,
              status: c.status,
              client: c.client
            };
            setCases((prev) => [newCase, ...prev]);
            setInsights((prev) => [
              {
                id: `insight-${Date.now()}`,
                title: 'Workspace Initialized',
                desc: `AI starting evidentiary audit index for ${c.name}.`,
                time: 'Just now',
                type: 'strategy',
              },
              ...prev
            ]);
          }
        })
        .catch((err) => console.error("Error creating case in database:", err));

    } else if (data.type === 'hearing') {
      const tIndex = data.date.indexOf('T');
      const hDate = tIndex > -1 ? data.date.substring(0, tIndex) : data.date;
      const hTime = tIndex > -1 ? data.date.substring(tIndex + 1, tIndex + 6) : "09:00";

      const payload = {
        workspace_id: data.caseId,
        case_name: data.caseName,
        title: `Court Hearing // ${data.caseName}`,
        court_name: data.court,
        hearing_date: hDate,
        hearing_time: hTime,
        priority: data.priority,
        notes: "Scheduled trial hearing"
      };

      fetch('http://localhost:8000/api/hearings/create', {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
      })
        .then((res) => res.json())
        .then((resData) => {
          if (resData.success && resData.data) {
            const h = resData.data;
            const newHearing: Hearing = {
              id: h._id || h.id,
              caseName: h.case_name,
              date: h.hearing_time ? `${h.hearing_date}T${h.hearing_time}` : h.hearing_date,
              court: h.court_name,
              priority: h.priority
            };
            setHearings((prev) => [newHearing, ...prev]);
            setInsights((prev) => [
              {
                id: `insight-${Date.now()}`,
                title: 'Hearing Scheduled',
                desc: `Hearing briefing compiled for ${data.caseName} at ${data.court}.`,
                time: 'Just now',
                type: 'strategy',
              },
              ...prev
            ]);
          }
        })
        .catch((err) => console.error("Error scheduling hearing in database:", err));

    } else if (data.type === 'task') {
      const payload = {
        workspace_id: data.caseId,
        case_name: data.caseName,
        title: data.title,
        description: "",
        due_date: data.dueDate,
        priority: data.priority,
        task_type: "Miscellaneous"
      };

      fetch('http://localhost:8000/api/tasks/create', {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
      })
        .then((res) => res.json())
        .then((resData) => {
          if (resData.success && resData.data) {
            const t = resData.data;
            const newTask: Task = {
              id: t._id || t.id,
              title: t.title,
              dueDate: t.due_date,
              caseName: t.case_name,
              caseId: t.workspace_id,
              completed: t.completed,
              priority: t.priority
            };
            setTasks((prev) => [newTask, ...prev]);
          }
        })
        .catch((err) => console.error("Error creating task in database:", err));
    }
  };

  const handleDeleteCase = (caseId: string) => {
    setCases(cases.filter((c) => c.id !== caseId));

    const token = localStorage.getItem('verdictiq_token');
    if (token && !caseId.startsWith('case-')) {
      fetch(`http://localhost:8000/api/cases/delete/${caseId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .catch((err) => console.error("Error deleting case from API:", err));
    }
  };

  const handleDeleteTask = (taskId: string) => {
    setTasks(tasks.filter((t) => t.id !== taskId));

    const token = localStorage.getItem('verdictiq_token');
    if (token && !taskId.startsWith('task-')) {
      fetch(`http://localhost:8000/api/tasks/delete/${taskId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .catch((err) => console.error("Error deleting task from API:", err));
    }
  };


  const openCreateModal = (mode: 'case' | 'hearing' | 'task') => {
    setModalMode(mode);
    setModalOpen(true);
  };

  if (isVerifyingSession) {
    return (
      <div className="relative min-h-screen w-full flex flex-col items-center justify-center bg-[#0B0F19]">
        <BackgroundEffects />
        <div className="relative z-10 text-center select-none space-y-4">
          <div className="relative flex items-center justify-center">
            <div className="absolute w-16 h-16 rounded-full bg-brand-blue/20 blur-md animate-pulse" />
            <svg
              width="48"
              height="48"
              viewBox="0 0 32 32"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="relative z-10 filter drop-shadow-[0_0_8px_rgba(79,140,255,0.4)] animate-spin"
            >
              <path
                d="M16 2L29.5 9.75V25.25L16 33L2.5 25.25V9.75L16 2Z"
                stroke="url(#loading-grad)"
                strokeWidth="2"
                strokeLinejoin="round"
              />
              <defs>
                <linearGradient id="loading-grad" x1="2.5" y1="2" x2="29.5" y2="33" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#4F8CFF" />
                  <stop offset="1" stopColor="#7B61FF" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <p className="text-[10px] tracking-[0.25em] text-brand-blue uppercase font-bold animate-pulse font-mono">
            SECURE AUTHENTICATION HANDSHAKE ACTIVE...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen w-full flex overflow-hidden bg-[#0B0F19] text-gray-100 font-sans">
      {/* Background elements */}
      <BackgroundEffects />

      {activeView === 'login' || activeView === 'signup' ? (
        // AUTHENTICATION VIEW
        <div className="relative z-10 w-full flex flex-col items-center justify-center px-4 py-12 md:py-16 overflow-hidden">
          <div className="relative w-full flex items-center justify-center min-h-[600px]">
            <AnimatePresence mode="wait">
              {activeView === 'login' ? (
                <LoginCard
                  key="login"
                  onSwitchToSignup={() => setActiveView('signup')}
                  onLoginSuccess={handleLoginSuccess}
                />
              ) : (
                <SignupCard
                  key="signup"
                  onSwitchToLogin={() => setActiveView('login')}
                  onSignupSuccess={handleSignupSuccess}
                />
              )}
            </AnimatePresence>
          </div>
          {/* Secured quantum indicator */}
          <div className="relative mt-8 text-center pointer-events-none select-none">
            <p className="text-[10px] tracking-[0.25em] text-brand-textMuted/30 uppercase">
              SECURE QUANTUM ENCRYPTED CHANNEL // VERDICTIQ v1.0.4-PROD
            </p>
          </div>
        </div>
      ) : (
        // DASHBOARD WORKSPACE VIEW
        <div className="relative z-10 flex w-full h-screen overflow-hidden">
          {/* Side Drawer menu for Mobile devices */}
          <AnimatePresence>
            {isMobileMenuOpen && (
              <>
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="fixed inset-0 z-40 bg-[#070A12]/80 backdrop-blur-sm md:hidden"
                />
                <motion.div
                  initial={{ x: -280 }}
                  animate={{ x: 0 }}
                  exit={{ x: -280 }}
                  transition={{ type: 'spring', damping: 25, stiffness: 280 }}
                  className="fixed left-0 top-0 bottom-0 z-50 w-64 bg-brand-dark/95 md:hidden"
                >
                  <Sidebar
                    activeTab={activeTab}
                    setActiveTab={(tab) => {
                      handleTabChange(tab);
                      setIsMobileMenuOpen(false);
                    }}
                    isCollapsed={false}
                    setIsCollapsed={() => {}}
                    onLogout={handleLogout}
                  />
                  {/* Close trigger inside sidebar drawer */}
                  <button
                    onClick={() => setIsMobileMenuOpen(false)}
                    className="absolute top-4 right-4 text-brand-textMuted hover:text-white p-1 rounded-lg border border-white/10"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </motion.div>
              </>
            )}
          </AnimatePresence>

          {/* Desktop Left Sidebar */}
          <div className="hidden md:flex h-full">
            <Sidebar
              activeTab={activeTab}
              setActiveTab={handleTabChange}
              isCollapsed={sidebarCollapsed}
              setIsCollapsed={setSidebarCollapsed}
              onLogout={handleLogout}
            />
          </div>

          {/* Dashboard Right Content Container */}
          <div className="flex-1 flex flex-col h-full overflow-hidden">
            {/* Top Navbar */}
            <div className="flex items-center">
              {/* Mobile hamburger menu toggle */}
              <button
                onClick={() => setIsMobileMenuOpen(true)}
                className="md:hidden ml-4 p-2.5 rounded-xl bg-brand-dark/50 border border-white/10 text-brand-textMuted hover:text-white transition-all duration-300"
              >
                <Menu className="w-5 h-5" />
              </button>
              <div className="flex-1">
                <Navbar
                  onSearch={setGlobalSearch}
                  onCreateClick={openCreateModal}
                  onProfileClick={() => setActiveTab('AI Insights')} // Links to profile (mocked inside tab switches/or redirect to settings)
                  userEmail={user.email}
                />
              </div>
            </div>

            {/* Scrollable Subpage Content viewport */}
            <main className="flex-1 overflow-y-auto p-4 md:p-6 bg-transparent">
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeTab}
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -15 }}
                  transition={{ duration: 0.3, ease: 'easeInOut' }}
                  className="max-w-[1400px] mx-auto w-full"
                >
                  {selectedCaseId ? (
                    <WorkspaceDetailPage
                      workspaceId={selectedCaseId}
                      onBack={() => setSelectedCaseId(null)}
                    />
                  ) : (
                    <>
                      {activeTab === 'Dashboard' && (
                        <DashboardOverview
                          cases={cases}
                          hearings={hearings}
                          tasks={tasks}
                          insights={insights}
                          reportsCount={reports.length}
                          toggleTaskComplete={handleToggleTaskComplete}
                          onViewAllCases={() => setActiveTab('Cases')}
                          onViewAllTasks={() => setActiveTab('Tasks')}
                          onViewAllHearings={() => setActiveTab('Calendar')}
                          onQuickAccessCase={() => {
                            setActiveTab('Cases');
                            // Option to focus cases filter
                          }}
                        />
                      )}

                      {activeTab === 'Cases' && (
                        <CasesPage
                          cases={cases}
                          onCreateClick={() => openCreateModal('case')}
                          onSelectCase={(id) => {
                            setSelectedCaseId(id);
                          }}
                          onDeleteCase={handleDeleteCase}
                          searchQuery={globalSearch}
                        />
                      )}

                      {activeTab === 'Calendar' && (
                        <CalendarPage
                          hearings={hearings}
                          tasks={tasks}
                          onCreateHearing={() => openCreateModal('hearing')}
                        />
                      )}

                      {activeTab === 'Tasks' && (
                        <TasksPage
                          tasks={tasks}
                          casesList={cases.map((c) => ({ id: c.id, name: c.name }))}
                          onToggleComplete={handleToggleTaskComplete}
                          onCreateTask={() => openCreateModal('task')}
                          onDeleteTask={handleDeleteTask}
                        />
                      )}

                      {activeTab === 'Reports' && <ReportsPage reports={reports} />}

                      {activeTab === 'AI Insights' && (
                        <ProfilePage
                          userEmail={user.email}
                          userName={user.name}
                          organizationName={user.organization}
                          userRole={user.role}
                        />
                      )}

                      {activeTab === 'Settings' && <SettingsPage />}
                    </>
                  )}
                </motion.div>
              </AnimatePresence>
            </main>
          </div>

          {/* Unified dynamic Creation Dialog */}
          <CaseModal
            isOpen={modalOpen}
            onClose={() => setModalOpen(false)}
            mode={modalMode}
            casesList={cases.map((c) => ({ id: c.id, name: c.name }))}
            onSubmit={handleModalSubmit}
          />
        </div>
      )}
    </div>
  );
}

export default App;
