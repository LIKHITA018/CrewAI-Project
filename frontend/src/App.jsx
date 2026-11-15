
import { useEffect, useMemo, useState } from "react";
import {
  LayoutDashboard,
  Bot,
  History,
  Activity,
  Settings,
  Search,
  Bell,
  ChevronDown,
  ArrowUpRight,
  Sparkles,
  Clock3,
  CheckCircle2,
  CircleAlert,
  Zap,
  Menu,
  X,
  Play,
  Copy,
  Download,
  Trash2,
  RefreshCw,
  FileText,
  Filter,
  ExternalLink,
  Moon,
  Sun,
  Check,
  AlertTriangle,
  Eye,
  RotateCcw,
  ShieldCheck,
  Users,
  UserPlus,
  ScrollText,
} from "lucide-react";
import "./App.css";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "/api";
  
const HISTORY_STORAGE_KEY = "worksphere_task_history_v1";
const SETTINGS_STORAGE_KEY = "worksphere_settings_v1";
const ADMIN_STORAGE_KEY = "worksphere_admin_v1";

const agents = [
  { id: 1, name: "Blog Post Generator", category: "Content", icon: "✍️", color: "purple", description: "Create engaging professional blog posts." },
  { id: 2, name: "Competitor Analysis", category: "Research", icon: "📊", color: "blue", description: "Research competitors and business strategies." },
  { id: 3, name: "Meeting Notes", category: "Productivity", icon: "📝", color: "orange", description: "Convert meeting transcripts into summaries." },
  { id: 4, name: "Data Report", category: "Analytics", icon: "📈", color: "green", description: "Generate insightful business reports." },
  { id: 5, name: "Customer Support", category: "Support", icon: "🎧", color: "pink", description: "Process customer support requests." },
  { id: 6, name: "Resume Screening", category: "HR", icon: "👥", color: "blue", description: "Evaluate and screen candidate resumes." },
  { id: 7, name: "Bug Triage", category: "Development", icon: "🐞", color: "orange", description: "Analyze and prioritize software bugs." },
  { id: 8, name: "Content Repurposing", category: "Marketing", icon: "📱", color: "purple", description: "Transform content into multiple formats." },
  { id: 9, name: "Lead Qualification", category: "Sales", icon: "🎯", color: "green", description: "Evaluate and qualify potential leads." },
  { id: 10, name: "Approval Report", category: "Management", icon: "✅", color: "pink", description: "Create approval workflow reports." },
];

const navigation = [
  { name: "Dashboard", icon: LayoutDashboard },
  { name: "AI Agents", icon: Bot },
  { name: "Task History", icon: History },
  { name: "Performance", icon: Activity },
  { name: "Workspace Admin", icon: ShieldCheck },
];

const defaultAdminData = {
  members: [
    {
      id: "owner",
      name: "Workspace Admin",
      email: "Owner account",
      role: "Admin",
      isOwner: true,
    },
  ],
  enabledAgentIds: agents.map((agent) => agent.id),
  auditLogs: [],
};

function readStoredValue(key, fallback) {
  try {
    const value = localStorage.getItem(key);
    return value ? JSON.parse(value) : fallback;
  } catch {
    return fallback;
  }
}

function formatDate(value) {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}

function formatDuration(value) {
  if (typeof value !== "number") return "—";
  return value >= 1000
    ? `${(value / 1000).toFixed(2)} sec`
    : `${Math.round(value)} ms`;
}

function downloadFile(filename, content, type = "text/plain") {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function escapeCsv(value) {
  const text = String(value ?? "").replace(/"/g, '""');
  return `"${text}"`;
}

function App() {
  const [activePage, setActivePage] = useState("Dashboard");
  const [mobileMenu, setMobileMenu] = useState(false);

  // Agent execution
  const [agentInput, setAgentInput] = useState("");
  const [agentOutput, setAgentOutput] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [agentError, setAgentError] = useState("");
  const [lastRunAgentId, setLastRunAgentId] = useState(null);

  // Persistent task history
  const [taskHistory, setTaskHistory] = useState(() =>
    readStoredValue(HISTORY_STORAGE_KEY, [])
  );
  const [historySearch, setHistorySearch] = useState("");
  const [historyFilter, setHistoryFilter] = useState("All");
  const [selectedTask, setSelectedTask] = useState(null);

  // Backend health
  const [backendHealth, setBackendHealth] = useState(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const [healthError, setHealthError] = useState("");
  const [lastHealthUpdate, setLastHealthUpdate] = useState(null);

  // Header tools
  const [globalSearch, setGlobalSearch] = useState("");
  const [showSearch, setShowSearch] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);

  // Settings
  const [settings, setSettings] = useState(() =>
    readStoredValue(SETTINGS_STORAGE_KEY, {
      darkMode: false,
      autoRefresh: true,
      refreshInterval: 30,
    })
  );

  const [settingsMessage, setSettingsMessage] = useState("");

  // Workspace administration
  const [adminData, setAdminData] = useState(() => {
    const saved = readStoredValue(ADMIN_STORAGE_KEY, defaultAdminData);

    return {
      ...defaultAdminData,
      ...saved,
      members: Array.isArray(saved.members)
        ? saved.members
        : defaultAdminData.members,
      enabledAgentIds: Array.isArray(saved.enabledAgentIds)
        ? saved.enabledAgentIds.filter((id) =>
            agents.some((agent) => agent.id === id)
          )
        : defaultAdminData.enabledAgentIds,
      auditLogs: Array.isArray(saved.auditLogs)
        ? saved.auditLogs
        : defaultAdminData.auditLogs,
    };
  });

  const [memberName, setMemberName] = useState("");
  const [memberEmail, setMemberEmail] = useState("");
  const [memberRole, setMemberRole] = useState("Member");
  const [adminMessage, setAdminMessage] = useState("");

  const selectedAgent = agents.find(
    (agent) => activePage === `Agent ${agent.id}`
  );

  // Keep task history saved after refresh.
  useEffect(() => {
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(taskHistory));
  }, [taskHistory]);

  // Keep settings saved after refresh.
  useEffect(() => {
    localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
  }, [settings]);

  // Keep workspace administration saved after refresh.
  useEffect(() => {
    localStorage.setItem(ADMIN_STORAGE_KEY, JSON.stringify(adminData));
  }, [adminData]);

  // Apply the selected theme.
  useEffect(() => {
    document.documentElement.dataset.theme = settings.darkMode
      ? "dark"
      : "light";
  }, [settings.darkMode]);

  // Fetch backend health and refresh it periodically.
  useEffect(() => {
    let isMounted = true;

    const loadBackendHealth = async () => {
      try {
        const response = await fetch(`${API_BASE}/health`);

        if (!response.ok) {
          throw new Error(`Health check failed (${response.status}).`);
        }

        const data = await response.json();

        if (isMounted) {
          setBackendHealth(data);
          setHealthError("");
          setLastHealthUpdate(new Date().toISOString());
        }
      } catch (error) {
        if (isMounted) {
          setHealthError(
            error.message || "Unable to connect to the backend."
          );
        }
      } finally {
        if (isMounted) setHealthLoading(false);
      }
    };

    loadBackendHealth();

    let intervalId;

    if (settings.autoRefresh) {
      intervalId = window.setInterval(
        loadBackendHealth,
        Math.max(10, Number(settings.refreshInterval) || 30) * 1000
      );
    }

    return () => {
      isMounted = false;
      if (intervalId) window.clearInterval(intervalId);
    };
  }, [settings.autoRefresh, settings.refreshInterval]);

  const completedTasks = taskHistory.filter(
    (task) => task.status === "Success"
  ).length;

  const failedTasks = taskHistory.filter(
    (task) => task.status === "Failed"
  ).length;

  const totalApiCalls = Object.values(backendHealth?.agents || {}).reduce(
    (sum, agent) => sum + (Number(agent.total_calls) || 0),
    0
  );

  const recentTasks = taskHistory.slice(0, 4);

  const filteredHistory = useMemo(() => {
    const query = historySearch.trim().toLowerCase();

    return taskHistory.filter((task) => {
      const matchesSearch =
        !query ||
        task.agentName?.toLowerCase().includes(query) ||
        task.input?.toLowerCase().includes(query) ||
        task.output?.toLowerCase().includes(query) ||
        task.status?.toLowerCase().includes(query);

      const matchesStatus =
        historyFilter === "All" || task.status === historyFilter;

      return matchesSearch && matchesStatus;
    });
  }, [taskHistory, historySearch, historyFilter]);

  const searchResults = useMemo(() => {
    const query = globalSearch.trim().toLowerCase();

    if (!query) return [];

    return agents.filter(
      (agent) =>
        adminData.enabledAgentIds.includes(agent.id) &&
        (
          agent.name.toLowerCase().includes(query) ||
          agent.category.toLowerCase().includes(query) ||
          agent.description.toLowerCase().includes(query)
        )
    );
  }, [globalSearch, adminData.enabledAgentIds]);

  const addTaskToHistory = (task) => {
    setTaskHistory((previous) => [task, ...previous]);
  };

  const openAgent = (agentId) => {
    if (!adminData.enabledAgentIds.includes(agentId)) {
      setAdminMessage(
        "This AI agent is currently disabled by the workspace administrator."
      );
      setActivePage("Workspace Admin");
      return;
    }

    setActivePage(`Agent ${agentId}`);
    setAgentInput("");
    setAgentOutput("");
    setAgentError("");
    setLastRunAgentId(agentId);
    setMobileMenu(false);
    setShowSearch(false);
    setGlobalSearch("");
  };

  const goToPage = (page) => {
    setActivePage(page);
    setMobileMenu(false);
    setShowSearch(false);
    setShowNotifications(false);
    setSelectedTask(null);
  };

  // Run an agent through the existing FastAPI endpoint.
  const runAgent = async (agentId, inputOverride) => {
    const agent = agents.find((item) => item.id === agentId);

    if (!adminData.enabledAgentIds.includes(agentId)) {
      setAgentError(
        "This AI agent is disabled by the workspace administrator."
      );
      return;
    }

    const prompt =
      typeof inputOverride === "string" ? inputOverride : agentInput;

    if (!prompt.trim()) {
      setAgentError("Please enter some input before running the agent.");
      return;
    }

    const startedAt = Date.now();

    setIsRunning(true);
    setAgentError("");
    setAgentOutput("");
    setLastRunAgentId(agentId);

    try {
      const response = await fetch(`${API_BASE}/agent${agentId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input: prompt }),
      });

      const data = await response.json();
      const duration = Date.now() - startedAt;

      if (!response.ok) {
        const detail =
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail || data);

        throw new Error(detail || `Request failed (${response.status}).`);
      }

      const output =
        typeof data.output === "string"
          ? data.output
          : JSON.stringify(data.output ?? data, null, 2);

      setAgentOutput(output);

      addTaskToHistory({
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        agentId,
        agentName: agent?.name || `Agent ${agentId}`,
        input: prompt,
        output,
        status: "Success",
        duration,
        timestamp: new Date().toISOString(),
      });

      // Refresh health after a successful agent execution.
      try {
        const healthResponse = await fetch(`${API_BASE}/health`);

        if (healthResponse.ok) {
          const healthData = await healthResponse.json();
          setBackendHealth(healthData);
          setHealthError("");
          setLastHealthUpdate(new Date().toISOString());
        }
      } catch {
        // Agent result remains successful if health refresh fails.
      }
    } catch (error) {
      const duration = Date.now() - startedAt;
      const message = error.message || "Something went wrong.";

      setAgentError(message);

      addTaskToHistory({
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        agentId,
        agentName: agent?.name || `Agent ${agentId}`,
        input: prompt,
        output: message,
        status: "Failed",
        duration,
        timestamp: new Date().toISOString(),
      });
    } finally {
      setIsRunning(false);
    }
  };

  const retryLastRun = () => {
    if (lastRunAgentId) runAgent(lastRunAgentId);
  };

  const copyText = async (value) => {
    try {
      await navigator.clipboard.writeText(value);
      setSettingsMessage("Copied to clipboard.");
      window.setTimeout(() => setSettingsMessage(""), 2500);
    } catch {
      setSettingsMessage("Clipboard access is unavailable in this browser.");
      window.setTimeout(() => setSettingsMessage(""), 3000);
    }
  };

  const exportHistory = () => {
    const headings = [
      "Agent",
      "Status",
      "Input",
      "Output",
      "Duration (ms)",
      "Timestamp",
    ];

    const rows = taskHistory.map((task) => [
      task.agentName,
      task.status,
      task.input,
      task.output,
      task.duration,
      task.timestamp,
    ]);

    const csv = [
      headings.map(escapeCsv).join(","),
      ...rows.map((row) => row.map(escapeCsv).join(",")),
    ].join("\n");

    downloadFile(
      "worksphere-task-history.csv",
      csv,
      "text/csv;charset=utf-8;"
    );
  };

  const deleteTask = (taskId) => {
    setTaskHistory((previous) =>
      previous.filter((task) => task.id !== taskId)
    );

    if (selectedTask?.id === taskId) setSelectedTask(null);
  };

  const clearHistory = () => {
    const confirmed = window.confirm(
      "Are you sure you want to delete all task history?"
    );

    if (confirmed) {
      setTaskHistory([]);
      setSelectedTask(null);
    }
  };

  const updateSetting = (key, value) => {
    setSettings((previous) => ({ ...previous, [key]: value }));
    setSettingsMessage("Settings saved.");
    window.setTimeout(() => setSettingsMessage(""), 2000);
  };

  const getAgentHealth = (agent) => {
    const healthKeys = {
      1: "blog_post",
      2: "competitor_analysis",
      3: "meeting_notes",
      4: "data_report",
      5: "customer_support",
      6: "resume_screening",
      7: "bug_triage",
      8: "content_repurposing",
      9: "lead_qualification",
      10: "approval_report",
    };

    return backendHealth?.agents?.[healthKeys[agent.id]] || null;
  };

  // Create an audit log entry.
  const recordAdminAction = (action, details) => ({
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    action,
    details,
    timestamp: new Date().toISOString(),
  });

  // Add workspace member.
  const addWorkspaceMember = () => {
    const name = memberName.trim();
    const email = memberEmail.trim().toLowerCase();

    if (!name || !email) {
      setAdminMessage("Please enter both the member name and email.");
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setAdminMessage("Please enter a valid email address.");
      return;
    }

    const alreadyExists = adminData.members.some(
      (member) => member.email.toLowerCase() === email
    );

    if (alreadyExists) {
      setAdminMessage("This email is already in the workspace.");
      return;
    }

    const newMember = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      name,
      email,
      role: memberRole,
      isOwner: false,
    };

    setAdminData((previous) => ({
      ...previous,
      members: [...previous.members, newMember],
      auditLogs: [
        recordAdminAction(
          "Member Added",
          `${name} was added as ${memberRole}.`
        ),
        ...previous.auditLogs,
      ],
    }));

    setMemberName("");
    setMemberEmail("");
    setMemberRole("Member");
    setAdminMessage("Workspace member added successfully.");
  };

  // Change member role.
  const changeMemberRole = (memberId, newRole) => {
    const member = adminData.members.find(
      (item) => item.id === memberId
    );

    if (!member || member.isOwner) return;

    setAdminData((previous) => ({
      ...previous,
      members: previous.members.map((item) =>
        item.id === memberId ? { ...item, role: newRole } : item
      ),
      auditLogs: [
        recordAdminAction(
          "Role Updated",
          `${member.name}'s role changed to ${newRole}.`
        ),
        ...previous.auditLogs,
      ],
    }));

    setAdminMessage("Member role updated.");
  };

  // Remove member.
  const removeWorkspaceMember = (memberId) => {
    const member = adminData.members.find(
      (item) => item.id === memberId
    );

    if (!member || member.isOwner) return;

    if (!window.confirm(`Remove ${member.name} from this workspace?`)) {
      return;
    }

    setAdminData((previous) => ({
      ...previous,
      members: previous.members.filter(
        (item) => item.id !== memberId
      ),
      auditLogs: [
        recordAdminAction(
          "Member Removed",
          `${member.name} was removed.`
        ),
        ...previous.auditLogs,
      ],
    }));

    setAdminMessage("Workspace member removed.");
  };

  // Enable or disable AI agent access.
  const toggleAgentAccess = (agentId) => {
    const agent = agents.find((item) => item.id === agentId);

    if (!agent) return;

    const isEnabled = adminData.enabledAgentIds.includes(agentId);

    setAdminData((previous) => ({
      ...previous,
      enabledAgentIds: isEnabled
        ? previous.enabledAgentIds.filter((id) => id !== agentId)
        : [...previous.enabledAgentIds, agentId],
      auditLogs: [
        recordAdminAction(
          isEnabled ? "Agent Disabled" : "Agent Enabled",
          `${agent.name} access was ${isEnabled ? "disabled" : "enabled"}.`
        ),
        ...previous.auditLogs,
      ],
    }));

    // If currently viewing an agent that gets disabled, return to admin.
    if (isEnabled && activePage === `Agent ${agentId}`) {
      setActivePage("Workspace Admin");
      setAgentInput("");
      setAgentOutput("");
      setAgentError("");
    }

    setAdminMessage(
      `${agent.name} ${isEnabled ? "disabled" : "enabled"} successfully.`
    );
  };

  return (
    <div className={`app-shell ${settings.darkMode ? "dark-mode" : ""}`}>
      <aside className={`sidebar ${mobileMenu ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-logo">
            <Sparkles size={23} />
          </div>

          <div>
            <h2>WorkSphere<span> AI</span></h2>
            <small>INTELLIGENT WORKSPACE</small>
          </div>

          <button
            className="mobile-close"
            onClick={() => setMobileMenu(false)}
            aria-label="Close menu"
          >
            <X size={20} />
          </button>
        </div>

        <div className="workspace-label">WORKSPACE</div>

        <nav className="navigation">
          {navigation.map(({ name, icon: Icon }) => (
            <button
              key={name}
              className={`nav-item ${activePage === name ? "active" : ""}`}
              onClick={() => goToPage(name)}
            >
              <Icon size={19} />
              <span>{name}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <button
            className={`nav-item ${activePage === "Settings" ? "active" : ""}`}
            onClick={() => goToPage("Settings")}
          >
            <Settings size={19} />
            <span>Settings</span>
          </button>

        </div>
      </aside>

      {mobileMenu && (
        <div
          className="mobile-overlay"
          onClick={() => setMobileMenu(false)}
        />
      )}

      <main className="main-content">
        <header className="topbar">
          <button
            className="mobile-menu"
            onClick={() => setMobileMenu(true)}
            aria-label="Open menu"
          >
            <Menu size={22} />
          </button>

          <div className="breadcrumb">
            Workspace <span>/</span> <strong>{activePage}</strong>
          </div>

          <div className="topbar-actions">
            <div className="global-search-wrap">
              {showSearch && (
                <input
                  className="global-search-input"
                  type="search"
                  placeholder="Search AI agents..."
                  value={globalSearch}
                  onChange={(event) => setGlobalSearch(event.target.value)}
                  autoFocus
                />
              )}

              <button
                className="search-button"
                onClick={() => {
                  setShowSearch((value) => !value);
                  setShowNotifications(false);
                }}
                aria-label="Search"
              >
                {showSearch ? <X size={18} /> : <Search size={18} />}
              </button>

              {showSearch && globalSearch.trim() && (
                <div className="header-dropdown search-dropdown">
                  <strong>Search results</strong>

                  {searchResults.length ? (
                    searchResults.map((agent) => (
                      <button
                        key={agent.id}
                        className="dropdown-result"
                        onClick={() => openAgent(agent.id)}
                      >
                        <span>{agent.icon}</span>
                        <span>
                          <strong>{agent.name}</strong>
                          <small>{agent.category}</small>
                        </span>
                        <ArrowUpRight size={15} />
                      </button>
                    ))
                  ) : (
                    <p className="dropdown-empty">
                      No matching available agents found.
                    </p>
                  )}
                </div>
              )}
            </div>

            <div className="notification-wrap">
              <button
                className="notification-button"
                onClick={() => {
                  setShowNotifications((value) => !value);
                  setShowSearch(false);
                }}
                aria-label="Notifications"
              >
                <Bell size={19} />
                {taskHistory.length > 0 && <i />}
              </button>

              {showNotifications && (
                <div className="header-dropdown notification-dropdown">
                  <strong>Recent notifications</strong>

                  {recentTasks.length ? (
                    recentTasks.map((task) => (
                      <button
                        key={task.id}
                        className="notification-item"
                        onClick={() => {
                          goToPage("Task History");
                          setSelectedTask(task);
                        }}
                      >
                        {task.status === "Success" ? (
                          <CheckCircle2 size={17} />
                        ) : (
                          <CircleAlert size={17} />
                        )}

                        <span>
                          <strong>{task.agentName}</strong>
                          <small>
                            {task.status} · {formatDate(task.timestamp)}
                          </small>
                        </span>
                      </button>
                    ))
                  ) : (
                    <p className="dropdown-empty">No notifications yet.</p>
                  )}
                </div>
              )}
            </div>

            <div className="topbar-avatar">W</div>
          </div>
        </header>

        <div className="page-container">
          {/* DASHBOARD */}
          {activePage === "Dashboard" && (
            <>
              <section className="welcome-section">
                <div>
                  <div className="welcome-tag">
                    <Sparkles size={14} /> YOUR AI-POWERED WORKSPACE
                  </div>

                  <h1>Good to see you! <span>👋</span></h1>

                  <p>
                    Manage your work intelligently with your specialized AI workforce.
                  </p>
                </div>

                <div className="date-label">
                  <Clock3 size={16} /> AI Workspace Overview
                </div>
              </section>

              <section className="stats-grid">
                <StatCard
                  title="Total AI Agents"
                  value={agents.length}
                  subtitle="Specialized agents"
                  icon={<Bot />}
                  color="purple"
                />

                <StatCard
                  title="Completed Tasks"
                  value={completedTasks}
                  subtitle="Successfully completed"
                  icon={<CheckCircle2 />}
                  color="green"
                />

                <StatCard
                  title="Active Agents"
                  value={backendHealth?.ready_agents ?? "—"}
                  subtitle="Ready in backend"
                  icon={<Zap />}
                  color="blue"
                />

                <StatCard
                  title="Failed Tasks"
                  value={failedTasks}
                  subtitle="Tasks needing attention"
                  icon={<CircleAlert />}
                  color="orange"
                />
              </section>

              <section className="section-heading">
                <div>
                  <h2>Your AI workforce</h2>
                  <p>Choose an agent to get started with your task.</p>
                </div>

                <button
                  className="view-all"
                  onClick={() => goToPage("AI Agents")}
                >
                  View all agents <ArrowUpRight size={16} />
                </button>
              </section>

              <section className="agent-grid">
                {agents.slice(0, 6).map((agent) => (
                  <AgentCard
                    key={agent.id}
                    agent={agent}
                    enabled={adminData.enabledAgentIds.includes(agent.id)}
                    onClick={() => openAgent(agent.id)}
                  />
                ))}
              </section>

              <section className="section-heading activity-heading">
                <div>
                  <h2>Recent activity</h2>
                  <p>Your latest agent executions.</p>
                </div>

                <button
                  className="view-all"
                  onClick={() => goToPage("Task History")}
                >
                  View history <ArrowUpRight size={16} />
                </button>
              </section>

              {recentTasks.length ? (
                <section className="activity-section">
                  {recentTasks.map((task) => (
                    <div className="activity-item" key={task.id}>
                      <div className="activity-info">
                        <strong>{task.agentName}</strong>
                        <p>
                          {task.input.slice(0, 90)}
                          {task.input.length > 90 ? "..." : ""}
                        </p>
                      </div>

                      <div className="activity-info">
                        <strong
                          className={
                            task.status === "Success"
                              ? "success-text"
                              : "error-text"
                          }
                        >
                          {task.status}
                        </strong>
                        <p>{formatDate(task.timestamp)}</p>
                      </div>
                    </div>
                  ))}
                </section>
              ) : (
                <section className="empty-activity">
                  <div className="empty-icon">
                    <History size={24} />
                  </div>
                  <strong>No activity yet</strong>
                  <p>Run your first AI agent to see your activity here.</p>
                  <button onClick={() => goToPage("AI Agents")}>
                    Explore AI agents
                  </button>
                </section>
              )}
            </>
          )}

          {/* ALL AGENTS */}
          {activePage === "AI Agents" && (
            <>
              <section className="page-title">
                <div className="welcome-tag">
                  <Bot size={14} /> AI WORKFORCE
                </div>

                <h1>AI Agent Workspace</h1>
                <p>Explore and run your 10 specialized AI agents.</p>
              </section>

              <section className="agent-grid full-agent-grid">
                {agents.map((agent) => (
                  <AgentCard
                    key={agent.id}
                    agent={agent}
                    enabled={adminData.enabledAgentIds.includes(agent.id)}
                    onClick={() => openAgent(agent.id)}
                  />
                ))}
              </section>
            </>
          )}

          {/* INDIVIDUAL AGENT EXECUTION */}
          {selectedAgent && (
            <section className="agent-workspace">
              <div className="page-title">
                <div className="welcome-tag">
                  <Bot size={14} /> AI AGENT WORKSPACE
                </div>

                <h1>{selectedAgent.name}</h1>
                <p>{selectedAgent.description}</p>
              </div>

              <div className="agent-execution-card">
                <div className="execution-header">
                  <div className={`agent-icon ${selectedAgent.color}`}>
                    {selectedAgent.icon}
                  </div>

                  <div>
                    <h2>{selectedAgent.name}</h2>
                    <span className="agent-card-footer">
                      <span className="online-dot" /> Ready to execute
                    </span>
                  </div>
                </div>

                <label htmlFor="agent-input">
                  Enter your task or instructions
                </label>

                <textarea
                  id="agent-input"
                  className="agent-textarea"
                  placeholder={`Enter your task for ${selectedAgent.name}...`}
                  value={agentInput}
                  onChange={(event) => {
                    setAgentInput(event.target.value);
                    setAgentError("");
                  }}
                  rows={7}
                  disabled={isRunning}
                />

                {agentError && (
                  <div className="agent-error">
                    <CircleAlert size={18} />
                    <span>{agentError}</span>

                    <button
                      type="button"
                      onClick={retryLastRun}
                      disabled={isRunning || !agentInput.trim()}
                    >
                      <RotateCcw size={15} /> Retry
                    </button>
                  </div>
                )}

                <button
                  className="run-agent-button"
                  onClick={() => runAgent(selectedAgent.id)}
                  disabled={isRunning || !agentInput.trim()}
                >
                  {isRunning ? (
                    <>
                      <RefreshCw size={18} className="spin-icon" />
                      Processing your request...
                    </>
                  ) : (
                    <>
                      <Play size={18} />
                      Run AI Agent
                    </>
                  )}
                </button>

                {isRunning && (
                  <p className="agent-loading">
                    Your AI agent is working. Please wait...
                  </p>
                )}

                {agentOutput && (
                  <div className="agent-output">
                    <div className="output-header">
                      <h3>
                        <CheckCircle2 size={19} />
                        Agent Response
                      </h3>

                      <div>
                        <button onClick={() => copyText(agentOutput)}>
                          <Copy size={15} /> Copy
                        </button>

                        <button
                          onClick={() =>
                            downloadFile(
                              `${selectedAgent.name
                                .toLowerCase()
                                .replace(/\s+/g, "-")}-output.txt`,
                              agentOutput
                            )
                          }
                        >
                          <Download size={15} /> Download
                        </button>
                      </div>
                    </div>

                    <pre>{agentOutput}</pre>
                  </div>
                )}
              </div>

              <button
                className="view-all"
                onClick={() => {
                  setActivePage("AI Agents");
                  setAgentInput("");
                  setAgentOutput("");
                  setAgentError("");
                }}
              >
                ← Back to all agents
              </button>
            </section>
          )}

          {/* TASK HISTORY */}
          {activePage === "Task History" && (
            <section className="page-title">
              <div className="welcome-tag">
                <History size={14} /> ACTIVITY
              </div>

              <h1>Task History</h1>

              <p>
                Review, search, export, and manage your previous AI executions.
              </p>

              <div className="history-toolbar">
                <div className="history-search">
                  <Search size={17} />
                  <input
                    type="search"
                    placeholder="Search by agent, input, output or status..."
                    value={historySearch}
                    onChange={(event) => setHistorySearch(event.target.value)}
                  />
                </div>

                <div className="history-filter">
                  <Filter size={16} />
                  <select
                    value={historyFilter}
                    onChange={(event) => setHistoryFilter(event.target.value)}
                  >
                    <option>All</option>
                    <option>Success</option>
                    <option>Failed</option>
                  </select>
                </div>

                <button className="view-all" onClick={exportHistory}>
                  <Download size={16} /> Export CSV
                </button>
              </div>

              {filteredHistory.length ? (
                <div className="activity-section history-list">
                  {filteredHistory.map((task) => (
                    <div className="activity-item history-row" key={task.id}>
                      <div className="activity-info">
                        <strong>{task.agentName}</strong>
                        <p>
                          {task.input.slice(0, 110)}
                          {task.input.length > 110 ? "..." : ""}
                        </p>
                        <small>{formatDate(task.timestamp)}</small>
                      </div>

                      <div className="activity-info">
                        <strong
                          className={
                            task.status === "Success"
                              ? "success-text"
                              : "error-text"
                          }
                        >
                          {task.status}
                        </strong>
                        <p>{formatDuration(task.duration)}</p>
                      </div>

                      <div className="history-actions">
                        <button
                          title="View details"
                          onClick={() =>
                            setSelectedTask(
                              selectedTask?.id === task.id ? null : task
                            )
                          }
                        >
                          <Eye size={16} />
                        </button>

                        <button
                          title="Run this task again"
                          onClick={() => {
                            if (
                              !adminData.enabledAgentIds.includes(task.agentId)
                            ) {
                              setAdminMessage(
                                "This agent is disabled. Enable it in Workspace Admin first."
                              );
                              goToPage("Workspace Admin");
                              return;
                            }

                            openAgent(task.agentId);
                            setAgentInput(task.input);
                          }}
                        >
                          <RotateCcw size={16} />
                        </button>

                        <button
                          title="Delete task"
                          onClick={() => deleteTask(task.id)}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  ))}

                  {selectedTask && (
                    <div className="task-detail-panel">
                      <div className="section-heading">
                        <div>
                          <h2>{selectedTask.agentName}</h2>
                          <p>{formatDate(selectedTask.timestamp)}</p>
                        </div>

                        <button
                          className="view-all"
                          onClick={() => setSelectedTask(null)}
                        >
                          <X size={17} /> Close
                        </button>
                      </div>

                      <strong>Input</strong>
                      <pre>{selectedTask.input}</pre>

                      <strong>Output / Error</strong>
                      <pre>{selectedTask.output}</pre>

                      <p>
                        Status: <strong>{selectedTask.status}</strong>
                        {" · "}
                        Duration:{" "}
                        <strong>{formatDuration(selectedTask.duration)}</strong>
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="empty-activity">
                  <div className="empty-icon">
                    <History size={24} />
                  </div>

                  <strong>
                    {taskHistory.length ? "No matching tasks" : "No tasks yet"}
                  </strong>

                  <p>
                    {taskHistory.length
                      ? "Try changing your search or filter."
                      : "Run an AI agent and its execution will appear here."}
                  </p>

                  {!taskHistory.length && (
                    <button onClick={() => goToPage("AI Agents")}>
                      Explore AI agents
                    </button>
                  )}
                </div>
              )}

              {taskHistory.length > 0 && (
                <button
                  className="clear-history-button"
                  onClick={clearHistory}
                >
                  <Trash2 size={16} /> Clear all history
                </button>
              )}
            </section>
          )}

          {/* PERFORMANCE MONITOR */}
          {activePage === "Performance" && (
            <section className="page-title">
              <div className="welcome-tag">
                <Activity size={14} /> LIVE MONITORING
              </div>

              <h1>Performance Monitor</h1>

              <p>
                Monitor backend health, agent availability and execution performance.
              </p>

              {healthLoading && !backendHealth && (
                <div className="empty-activity">
                  <RefreshCw size={24} />
                  <strong>Loading backend metrics...</strong>
                </div>
              )}

              {healthError && (
                <div className="agent-error performance-error">
                  <AlertTriangle size={18} />
                  <span>{healthError}</span>

                  <button onClick={() => window.location.reload()}>
                    <RefreshCw size={15} /> Refresh
                  </button>
                </div>
              )}

              {backendHealth && (
                <>
                  <section className="stats-grid">
                    <StatCard
                      title="Total Agents"
                      value={backendHealth.total_agents ?? agents.length}
                      subtitle="Registered agents"
                      icon={<Bot />}
                      color="purple"
                    />

                    <StatCard
                      title="Ready Agents"
                      value={backendHealth.ready_agents ?? "—"}
                      subtitle="Available agents"
                      icon={<CheckCircle2 />}
                      color="green"
                    />

                    <StatCard
                      title="Total API Calls"
                      value={totalApiCalls}
                      subtitle="Backend executions"
                      icon={<Zap />}
                      color="blue"
                    />

                    <StatCard
                      title="Backend Status"
                      value={backendHealth.overall_status || "Unknown"}
                      subtitle={`${backendHealth.not_loaded_agents ?? 0} agents not loaded`}
                      icon={<Activity />}
                      color="green"
                    />
                  </section>

                  <section className="activity-section performance-section">
                    <div className="section-heading">
                      <div>
                        <h2>Agent Performance</h2>
                        <p>Live metrics from your FastAPI backend</p>
                      </div>
                    </div>

                    <div className="performance-table-wrap">
                      <table className="performance-table">
                        <thead>
                          <tr>
                            <th>Agent</th>
                            <th>Function</th>
                            <th>Total Calls</th>
                            <th>Status</th>
                            <th>Successful</th>
                            <th>Failed</th>
                            <th>Avg Response</th>
                          </tr>
                        </thead>

                        <tbody>
                          {agents.map((agent) => {
                            const metrics = getAgentHealth(agent);

                            const responseTime = Number(
                              metrics?.average_response_time_ms || 0
                            );

                            return (
                              <tr key={agent.id}>
                                <td>
                                  <span className="performance-agent-name">
                                    <span>{agent.icon}</span>
                                    {agent.name}
                                  </span>
                                </td>

                                <td>{metrics?.function || "—"}</td>

                                <td>{metrics?.total_calls ?? 0}</td>

                                <td>
                                  <span
                                    className={`performance-status ${
                                      metrics?.status === "Ready"
                                        ? "status-ready"
                                        : "status-other"
                                    }`}
                                  >
                                    <span className="online-dot" />
                                    {metrics?.status || "Unknown"}
                                  </span>
                                </td>

                                <td>{metrics?.successful_calls ?? 0}</td>
                                <td>{metrics?.failed_calls ?? 0}</td>

                                <td>
                                  {responseTime > 0
                                    ? `${responseTime.toFixed(0)} ms`
                                    : "—"}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>

                    <p className="last-updated">
                      Last updated: {formatDate(lastHealthUpdate)}
                    </p>
                  </section>
                </>
              )}
            </section>
          )}

          {/* WORKSPACE ADMIN */}
          {activePage === "Workspace Admin" && (
            <section className="page-title">
              <div className="welcome-tag">
                <ShieldCheck size={14} /> WORKSPACE CONTROL CENTER
              </div>

              <h1>Workspace Administration</h1>

              <p>
                Manage members, permissions, AI agent access and workspace activity.
              </p>

              <section className="stats-grid admin-stats">
                <StatCard
                  title="Workspace Members"
                  value={adminData.members.length}
                  subtitle="Registered members"
                  icon={<Users />}
                  color="purple"
                />

                <StatCard
                  title="Administrators"
                  value={
                    adminData.members.filter((m) => m.role === "Admin").length
                  }
                  subtitle="Admin accounts"
                  icon={<ShieldCheck />}
                  color="blue"
                />

                <StatCard
                  title="Available Agents"
                  value={adminData.enabledAgentIds.length}
                  subtitle={`Out of ${agents.length} agents`}
                  icon={<Bot />}
                  color="green"
                />

                <StatCard
                  title="Audit Events"
                  value={adminData.auditLogs.length}
                  subtitle="Recorded admin actions"
                  icon={<ScrollText />}
                  color="orange"
                />
              </section>

              {adminMessage && (
                <div className="admin-message">
                  <CheckCircle2 size={17} />
                  <span>{adminMessage}</span>

                  <button
                    onClick={() => setAdminMessage("")}
                    aria-label="Dismiss message"
                  >
                    <X size={15} />
                  </button>
                </div>
              )}

              {/* USER MANAGEMENT */}
              <section className="settings-panel admin-panel">
                <div className="admin-section-heading">
                  <div>
                    <h2>
                      <Users size={19} /> User Management
                    </h2>
                    <p>Add and manage your workspace members.</p>
                  </div>
                </div>

                <div className="admin-add-member">
                  <input
                    type="text"
                    placeholder="Member name"
                    value={memberName}
                    onChange={(e) => setMemberName(e.target.value)}
                  />

                  <input
                    type="email"
                    placeholder="Email address"
                    value={memberEmail}
                    onChange={(e) => setMemberEmail(e.target.value)}
                  />

                  <select
                    value={memberRole}
                    onChange={(e) => setMemberRole(e.target.value)}
                  >
                    <option value="Admin">Admin</option>
                    <option value="Manager">Manager</option>
                    <option value="Member">Member</option>
                  </select>

                  <button
                    className="settings-action"
                    onClick={addWorkspaceMember}
                  >
                    <UserPlus size={16} /> Add Member
                  </button>
                </div>

                <div className="admin-member-list">
                  {adminData.members.map((member) => (
                    <div className="admin-member-row" key={member.id}>
                      <div className="admin-member-avatar">
                        {member.name.charAt(0).toUpperCase()}
                      </div>

                      <div className="admin-member-info">
                        <strong>{member.name}</strong>
                        <small>{member.email}</small>
                      </div>

                      <select
                        className="settings-select"
                        value={member.role}
                        disabled={member.isOwner}
                        onChange={(e) =>
                          changeMemberRole(member.id, e.target.value)
                        }
                      >
                        <option value="Admin">Admin</option>
                        <option value="Manager">Manager</option>
                        <option value="Member">Member</option>
                      </select>

                      <button
                        className="history-action-button danger-action"
                        title="Remove member"
                        aria-label={`Remove ${member.name}`}
                        disabled={member.isOwner}
                        onClick={() => removeWorkspaceMember(member.id)}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  ))}
                </div>
              </section>

              {/* ROLES AND PERMISSIONS */}
              <section className="settings-panel admin-panel">
                <div className="admin-section-heading">
                  <div>
                    <h2>
                      <ShieldCheck size={19} /> Roles & Permissions
                    </h2>
                    <p>Workspace access levels and responsibilities.</p>
                  </div>
                </div>

                <div className="admin-role-grid">
                  <div className="admin-role-card">
                    <ShieldCheck size={22} />
                    <strong>Admin</strong>
                    <p>
                      Manage members, roles, agent access and workspace settings.
                    </p>
                  </div>

                  <div className="admin-role-card">
                    <Users size={22} />
                    <strong>Manager</strong>
                    <p>
                      Manage day-to-day workspace activities and monitor agents.
                    </p>
                  </div>

                  <div className="admin-role-card">
                    <UserPlus size={22} />
                    <strong>Member</strong>
                    <p>
                      Use available AI agents and view workspace task activity.
                    </p>
                  </div>
                </div>
              </section>

              {/* AGENT ACCESS CONTROL */}
              <section className="settings-panel admin-panel">
                <div className="admin-section-heading">
                  <div>
                    <h2>
                      <Bot size={19} /> Agent Access Control
                    </h2>
                    <p>Enable or disable agents in this workspace.</p>
                  </div>
                </div>

                <div className="admin-agent-list">
                  {agents.map((agent) => {
                    const enabled = adminData.enabledAgentIds.includes(
                      agent.id
                    );

                    return (
                      <div className="admin-agent-row" key={agent.id}>
                        <div className={`agent-icon ${agent.color}`}>
                          {agent.icon}
                        </div>

                        <div className="admin-agent-info">
                          <strong>{agent.name}</strong>
                          <small>{agent.category}</small>
                        </div>

                        <span
                          className={
                            enabled ? "success-text" : "error-text"
                          }
                        >
                          {enabled ? "Enabled" : "Disabled"}
                        </span>

                        <label className="settings-toggle">
                          <input
                            type="checkbox"
                            checked={enabled}
                            onChange={() => toggleAgentAccess(agent.id)}
                          />
                          <span />
                        </label>
                      </div>
                    );
                  })}
                </div>
              </section>

              {/* AUDIT LOGS */}
              <section className="settings-panel admin-panel">
                <div className="admin-section-heading">
                  <div>
                    <h2>
                      <ScrollText size={19} /> Audit Logs
                    </h2>
                    <p>Review recent administrative changes.</p>
                  </div>
                </div>

                {adminData.auditLogs.length ? (
                  <div className="admin-audit-list">
                    {adminData.auditLogs.map((log) => (
                      <div className="admin-audit-row" key={log.id}>
                        <div className="admin-audit-icon">
                          <Activity size={17} />
                        </div>

                        <div>
                          <strong>{log.action}</strong>
                          <p>{log.details}</p>
                          <small>{formatDate(log.timestamp)}</small>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="empty-activity">
                    <ScrollText size={24} />
                    <strong>No administrative activity yet</strong>
                    <p>
                      Changes made in Workspace Admin will appear here.
                    </p>
                  </div>
                )}
              </section>
            </section>
          )}

          {/* SETTINGS */}
          {activePage === "Settings" && (
            <section className="page-title">
              <div className="welcome-tag">
                <Settings size={14} /> PREFERENCES
              </div>

              <h1>Workspace Settings</h1>

              <p>
                Manage your workspace preferences and local task data.
              </p>

              <div className="settings-panel">
                <div className="settings-row">
                  <div className="settings-description">
                    <div className="settings-icon">
                      {settings.darkMode ? (
                        <Moon size={19} />
                      ) : (
                        <Sun size={19} />
                      )}
                    </div>

                    <div>
                      <strong>Appearance</strong>
                      <p>Switch between light and dark workspace themes.</p>
                    </div>
                  </div>

                  <button
                    className="settings-action"
                    onClick={() =>
                      updateSetting("darkMode", !settings.darkMode)
                    }
                  >
                    {settings.darkMode ? (
                      <Sun size={16} />
                    ) : (
                      <Moon size={16} />
                    )}
                    {settings.darkMode ? "Light mode" : "Dark mode"}
                  </button>
                </div>

                <div className="settings-row">
                  <div className="settings-description">
                    <div className="settings-icon">
                      <RefreshCw size={19} />
                    </div>

                    <div>
                      <strong>Automatic health refresh</strong>
                      <p>Refresh backend metrics automatically.</p>
                    </div>
                  </div>

                  <label className="settings-toggle">
                    <input
                      type="checkbox"
                      checked={settings.autoRefresh}
                      onChange={(event) =>
                        updateSetting("autoRefresh", event.target.checked)
                      }
                    />
                    <span />
                  </label>
                </div>

                <div className="settings-row">
                  <div className="settings-description">
                    <div className="settings-icon">
                      <Clock3 size={19} />
                    </div>

                    <div>
                      <strong>Refresh interval</strong>
                      <p>Choose how often backend metrics refresh.</p>
                    </div>
                  </div>

                  <select
                    className="settings-select"
                    value={settings.refreshInterval}
                    onChange={(event) =>
                      updateSetting(
                        "refreshInterval",
                        Number(event.target.value)
                      )
                    }
                    disabled={!settings.autoRefresh}
                  >
                    <option value={15}>15 seconds</option>
                    <option value={30}>30 seconds</option>
                    <option value={60}>60 seconds</option>
                  </select>
                </div>

                <div className="settings-row">
                  <div className="settings-description">
                    <div className="settings-icon">
                      <FileText size={19} />
                    </div>

                    <div>
                      <strong>Export task history</strong>
                      <p>Download your saved task records as a CSV file.</p>
                    </div>
                  </div>

                  <button className="settings-action" onClick={exportHistory}>
                    <Download size={16} /> Export
                  </button>
                </div>

                <div className="settings-row">
                  <div className="settings-description">
                    <div className="settings-icon">
                      <Trash2 size={19} />
                    </div>

                    <div>
                      <strong>Clear task history</strong>
                      <p>Delete all task records saved in this browser.</p>
                    </div>
                  </div>

                  <button
                    className="settings-action danger-action"
                    onClick={clearHistory}
                  >
                    <Trash2 size={16} /> Clear history
                  </button>
                </div>

                {settingsMessage && (
                  <p className="settings-message">
                    <Check size={15} /> {settingsMessage}
                  </p>
                )}
              </div>

              <div className="settings-panel backend-info">
                <h2>Backend connection</h2>

                <p>
                  API documentation:{" "}
                  <a
                    href="https://agentiai-project-using-crewai.onrender.com/docs"
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open FastAPI Swagger <ExternalLink size={14} />
                  </a>
                </p>

                <p>
                  Health endpoint:{" "}
                  <a
                    href="https://agentiai-project-using-crewai.onrender.com/health"
                    target="_blank"
                    rel="noreferrer"
                  >
                    View backend health <ExternalLink size={14} />
                  </a>
                </p>

                <p>
                  Connection status:{" "}
                  <strong
                    className={
                      backendHealth
                        ? "success-text"
                        : "error-text"
                    }
                  >
                    {backendHealth
                      ? "Connected"
                      : healthLoading
                        ? "Checking..."
                        : "Unavailable"}
                  </strong>
                </p>
              </div>
            </section>
          )}
        </div>

        <footer className="footer">
          <span>© 2026 WorkSphere AI</span>
          <span>Powered by React · FastAPI · CrewAI</span>
        </footer>
      </main>
    </div>
  );
}

function StatCard({ title, value, subtitle, icon, color }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${color}`}>{icon}</div>
      <p>{title}</p>
      <h2>{value}</h2>
      <small>{subtitle}</small>
    </div>
  );
}

function AgentCard({ agent, onClick, enabled = true }) {
  return (
    <button
      className={`agent-card ${!enabled ? "agent-disabled" : ""}`}
      onClick={onClick}
      disabled={!enabled}
    >
      <div className="agent-card-top">
        <div className={`agent-icon ${agent.color}`}>
          {agent.icon}
        </div>

        <span className="agent-arrow">
          <ArrowUpRight size={18} />
        </span>
      </div>

      <span className="agent-category">{agent.category}</span>

      <h3>{agent.name}</h3>

      <p>{agent.description}</p>

      <div className="agent-card-footer">
        <span className="online-dot" />
        {enabled ? "Available" : "Disabled by Admin"}
      </div>
    </button>
  );
}

export default App;

