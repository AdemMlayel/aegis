import {
  Activity,
  AlertTriangle,
  Brain,
  CheckCircle2,
  ClipboardCheck,
  Database,
  ExternalLink,
  FileCode2,
  GitPullRequest,
  History,
  Loader2,
  Play,
  Plug,
  RefreshCw,
  RotateCcw,
  Search,
  ShieldCheck,
  XCircle
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  decideApproval,
  executeSuite,
  getAutomationFile,
  getIntegrationProfile,
  getProviderCatalog,
  getWorkflow,
  listLlmProviders,
  listExecutionEvents,
  listExecutionRuns,
  listMockTickets,
  listPromptTemplates,
  listWorkflows,
  searchKnowledge,
  searchMemory,
  startWorkflow,
  startWorkflowFromMockTicket
} from "./api";
import type {
  ApprovalStatus,
  AutomationBlock,
  ExecutionEvent,
  ExecutionRunRecord,
  IntegrationProfile,
  KnowledgeSearchItem,
  LLMProvider,
  MemorySearchItem,
  PromptTemplate,
  ProviderCatalog,
  TestCase,
  TestContext,
  TicketData,
  WorkflowSummary
} from "./types";

const DEFAULT_TICKET: TicketData = {
  id: "FAKE-001",
  title: "Money Transfer Feature",
  description: "As an authenticated customer, I want to transfer money.",
  acceptance_criteria: [
    "Transfer completes within 3 seconds",
    "Balance updates immediately"
  ],
  priority: "high",
  labels: ["banking", "payments"],
  source: "fake"
};

function splitLines(value: string): string[] {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function splitLabels(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function fileName(path: string): string {
  return path.split("/").pop() ?? path;
}

function formatDate(value?: string | null): string {
  if (!value) return "Not set";
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
    day: "2-digit"
  }).format(new Date(value));
}

function statusTone(status: string): "good" | "warn" | "bad" | "info" {
  if (status.includes("complete") || status === "approved" || status === "passed") return "good";
  if (status.includes("blocked") || status.includes("failed")) return "bad";
  if (status.includes("pending") || status.includes("review") || status === "skipped") return "warn";
  return "info";
}

function formatProviderKind(value: string): string {
  return value.replaceAll("_", " ");
}

function isFinalRunStatus(status: string): boolean {
  return !["queued", "running"].includes(status);
}

function upsertExecutionRun(runs: ExecutionRunRecord[], run: ExecutionRunRecord): ExecutionRunRecord[] {
  return [run, ...runs.filter((item) => item.run_id !== run.run_id)].sort(
    (left, right) => new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime()
  );
}

function toWebSocketUrl(path: string): string {
  const url = new URL(path, window.location.origin);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return url.toString();
}

function StatusPill({ value }: { value: string }) {
  return <span className={`status-pill ${statusTone(value)}`}>{value.replaceAll("_", " ")}</span>;
}

function ValidationIcon({ automation }: { automation?: AutomationBlock }) {
  if (!automation) return <AlertTriangle aria-hidden="true" />;
  if (automation.validation.dry_run_passed) return <CheckCircle2 aria-hidden="true" />;
  if (automation.validation.dry_run_passed === false) return <XCircle aria-hidden="true" />;
  return <AlertTriangle aria-hidden="true" />;
}

export function App() {
  const [createdBy, setCreatedBy] = useState("qa_engineer_001");
  const [ticketId, setTicketId] = useState(DEFAULT_TICKET.id);
  const [title, setTitle] = useState(DEFAULT_TICKET.title);
  const [description, setDescription] = useState(DEFAULT_TICKET.description);
  const [criteria, setCriteria] = useState(DEFAULT_TICKET.acceptance_criteria.join("\n"));
  const [priority, setPriority] = useState<TicketData["priority"]>(DEFAULT_TICKET.priority);
  const [labels, setLabels] = useState(DEFAULT_TICKET.labels.join(", "));
  const [mockTickets, setMockTickets] = useState<TicketData[]>([]);
  const [mockQuery, setMockQuery] = useState("");
  const [selectedMockTicketId, setSelectedMockTicketId] = useState("");
  const [mockLoading, setMockLoading] = useState(false);
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [workflowQuery, setWorkflowQuery] = useState("");
  const [approvalFilter, setApprovalFilter] = useState<ApprovalStatus | "all">("all");
  const [queueLoading, setQueueLoading] = useState(false);
  const [executionRuns, setExecutionRuns] = useState<ExecutionRunRecord[]>([]);
  const [executionEvents, setExecutionEvents] = useState<ExecutionEvent[]>([]);
  const [selectedRunId, setSelectedRunId] = useState("");
  const [resultsLoading, setResultsLoading] = useState(false);
  const [logsLoading, setLogsLoading] = useState(false);
  const [providerCatalog, setProviderCatalog] = useState<ProviderCatalog | null>(null);
  const [integrationProfile, setIntegrationProfile] = useState<IntegrationProfile | null>(null);
  const [promptTemplates, setPromptTemplates] = useState<PromptTemplate[]>([]);
  const [llmProviders, setLlmProviders] = useState<LLMProvider[]>([]);
  const [knowledgeResults, setKnowledgeResults] = useState<KnowledgeSearchItem[]>([]);
  const [memoryResults, setMemoryResults] = useState<MemorySearchItem[]>([]);
  const [providersLoading, setProvidersLoading] = useState(false);
  const [includeExternalProviders, setIncludeExternalProviders] = useState(false);
  const [intelligenceQuery, setIntelligenceQuery] = useState("banking transfer risk");
  const [executionAdapter, setExecutionAdapter] = useState("mock");
  const [executionEnv, setExecutionEnv] = useState("staging");
  const [executionBranch, setExecutionBranch] = useState("");
  const [executionTags, setExecutionTags] = useState("smoke, generated");
  const [context, setContext] = useState<TestContext | null>(null);
  const [loadId, setLoadId] = useState("");
  const [selectedTestId, setSelectedTestId] = useState<string>("");
  const [robotContent, setRobotContent] = useState("");
  const [reviewer, setReviewer] = useState("qa_engineer_001");
  const [reviewComment, setReviewComment] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const tests = context?.test_cases ?? [];
  const selectedTest: TestCase | undefined =
    tests.find((test) => test.id === selectedTestId) ?? tests[0];
  const selectedAutomation = selectedTest ? context?.automation[selectedTest.id] : undefined;
  const approval = context?.approval ?? null;
  const execution = context?.execution ?? null;
  const canReview = approval?.status === "pending_review";
  const selectedMockTicket = mockTickets.find((ticket) => ticket.id === selectedMockTicketId);
  const executionAdapterOptions =
    providerCatalog?.providers.filter((provider) => provider.kind === "execution_adapter" && provider.enabled) ?? [];
  const selectedProviderNames = new Set(
    providerCatalog?.selected.map((provider) => `${provider.kind}:${provider.selected}`) ?? []
  );

  const validationCounts = useMemo(() => {
    const automation = Object.values(context?.automation ?? {});
    return {
      total: automation.length,
      passed: automation.filter((item) => item.validation.dry_run_passed === true).length,
      failed: automation.filter((item) => item.validation.dry_run_passed === false).length
    };
  }, [context]);
  const executionCounts = execution?.summary ?? {
    total: 0,
    passed: 0,
    failed: 0,
    skipped: 0,
    duration_ms: 0
  };

  useEffect(() => {
    const storedContextId = localStorage.getItem("aegisqa:lastContextId");
    if (storedContextId) {
      setLoadId(storedContextId);
    }
  }, []);

  useEffect(() => {
    void refreshMockTickets();
    void refreshWorkflowQueue();
  }, []);

  useEffect(() => {
    void refreshProviderMetadata();
  }, [includeExternalProviders]);

  useEffect(() => {
    if (!context || selectedTestId) return;
    setSelectedTestId(context.test_cases[0]?.id ?? "");
  }, [context, selectedTestId]);

  useEffect(() => {
    if (!context) {
      setExecutionRuns([]);
      setExecutionEvents([]);
      setSelectedRunId("");
      return;
    }
    void refreshExecutionRuns(context.context_id);
  }, [context?.context_id]);

  useEffect(() => {
    let cancelled = false;
    async function loadRobotFile() {
      if (!context?.ticket || !selectedAutomation) {
        setRobotContent("");
        return;
      }
      setRobotContent("");
      try {
        const content = await getAutomationFile(context.ticket.id, selectedAutomation.robot_file);
        if (!cancelled) setRobotContent(content);
      } catch (err) {
        if (!cancelled) {
          setRobotContent(err instanceof Error ? err.message : "Unable to load Robot file");
        }
      }
    }
    void loadRobotFile();
    return () => {
      cancelled = true;
    };
  }, [context, selectedAutomation]);

  function keepContext(next: TestContext) {
    setContext(next);
    setSelectedTestId((current) => current || next.test_cases[0]?.id || "");
    localStorage.setItem("aegisqa:lastContextId", next.context_id);
    setLoadId(next.context_id);
  }

  function fillTicket(ticket: TicketData) {
    setSelectedMockTicketId(ticket.id);
    setTicketId(ticket.id);
    setTitle(ticket.title);
    setDescription(ticket.description);
    setCriteria(ticket.acceptance_criteria.join("\n"));
    setPriority(ticket.priority);
    setLabels(ticket.labels.join(", "));
  }

  async function refreshMockTickets(query = mockQuery) {
    setMockLoading(true);
    setError(null);
    try {
      const tickets = await listMockTickets({ query: query.trim() || undefined });
      setMockTickets(tickets);
      if (!selectedMockTicketId && tickets[0]) {
        setSelectedMockTicketId(tickets[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Mock tickets failed to load");
    } finally {
      setMockLoading(false);
    }
  }

  async function refreshWorkflowQueue(
    query = workflowQuery,
    nextApprovalFilter = approvalFilter
  ) {
    setQueueLoading(true);
    setError(null);
    try {
      const rows = await listWorkflows({
        query: query.trim() || undefined,
        approvalStatus: nextApprovalFilter === "all" ? undefined : nextApprovalFilter,
        limit: 50
      });
      setWorkflows(rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Workflow queue failed to load");
    } finally {
      setQueueLoading(false);
    }
  }

  async function refreshExecutionRuns(contextId = context?.context_id) {
    if (!contextId) {
      setExecutionRuns([]);
      setExecutionEvents([]);
      setSelectedRunId("");
      return;
    }
    setResultsLoading(true);
    setError(null);
    try {
      const rows = await listExecutionRuns({ contextId, limit: 25 });
      setExecutionRuns(rows);
      const activeRunId =
        selectedRunId && rows.some((run) => run.run_id === selectedRunId)
          ? selectedRunId
          : rows[0]?.run_id ?? "";
      setSelectedRunId(activeRunId);
      if (activeRunId) {
        await refreshExecutionEvents(activeRunId);
      } else {
        setExecutionEvents([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Execution results failed to load");
    } finally {
      setResultsLoading(false);
    }
  }

  async function refreshExecutionEvents(runId = selectedRunId) {
    if (!runId) {
      setExecutionEvents([]);
      return;
    }
    setLogsLoading(true);
    setError(null);
    try {
      setExecutionEvents(await listExecutionEvents(runId));
      setSelectedRunId(runId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Execution logs failed to load");
    } finally {
      setLogsLoading(false);
    }
  }

  async function refreshProviderMetadata(query = intelligenceQuery) {
    const searchText = query.trim() || "banking transfer risk";
    setProvidersLoading(true);
    setError(null);
    try {
      const [catalog, profile, prompts, llms, knowledge, memory] = await Promise.all([
        getProviderCatalog({ includeExternal: includeExternalProviders }),
        getIntegrationProfile(),
        listPromptTemplates(),
        listLlmProviders(),
        searchKnowledge(searchText, 3),
        searchMemory(searchText, 3)
      ]);
      setProviderCatalog(catalog);
      setIntegrationProfile(profile);
      setPromptTemplates(prompts);
      setLlmProviders(llms);
      setKnowledgeResults(knowledge);
      setMemoryResults(memory);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Provider metadata failed to load");
    } finally {
      setProvidersLoading(false);
    }
  }

  async function waitForExecutionRunSocket(runId: string, websocketPath: string): Promise<boolean> {
    return new Promise((resolve) => {
      let settled = false;
      let socket: WebSocket | null = null;
      const timeout = window.setTimeout(() => finish(false), 8000);

      function finish(value: boolean) {
        if (settled) return;
        settled = true;
        window.clearTimeout(timeout);
        socket?.close();
        resolve(value);
      }

      try {
        socket = new WebSocket(toWebSocketUrl(websocketPath));
      } catch {
        finish(false);
        return;
      }

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as {
            run?: ExecutionRunRecord;
            events?: ExecutionEvent[];
          };
          if (!payload.run || payload.run.run_id !== runId) return;
          setExecutionRuns((current) => upsertExecutionRun(current, payload.run as ExecutionRunRecord));
          setSelectedRunId(payload.run.run_id);
          if (payload.events) {
            setExecutionEvents(payload.events);
          }
          if (isFinalRunStatus(payload.run.status)) {
            finish(true);
          }
        } catch {
          finish(false);
        }
      };
      socket.onerror = () => finish(false);
      socket.onclose = () => finish(false);
    });
  }

  async function waitForExecutionRun(runId: string, contextId: string, websocketPath?: string | null) {
    if (websocketPath) {
      const completedFromSocket = await waitForExecutionRunSocket(runId, websocketPath);
      if (completedFromSocket) {
        keepContext(await getWorkflow(contextId));
        return;
      }
    }

    for (let attempt = 0; attempt < 8; attempt += 1) {
      const rows = await listExecutionRuns({ contextId, limit: 25 });
      setExecutionRuns(rows);
      const run = rows.find((item) => item.run_id === runId);
      if (run && isFinalRunStatus(run.status)) {
        keepContext(await getWorkflow(contextId));
        return;
      }
      await new Promise((resolve) => window.setTimeout(resolve, 750));
    }
    keepContext(await getWorkflow(contextId));
  }

  async function runStart() {
    setBusy("start");
    setError(null);
    try {
      const next = await startWorkflow({
        created_by: createdBy,
        ticket: {
          id: ticketId,
          title,
          description,
          acceptance_criteria: splitLines(criteria),
          priority,
          labels: splitLabels(labels),
          source: "fake"
        }
      });
      setSelectedTestId("");
      keepContext(next);
      void refreshWorkflowQueue();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Workflow start failed");
    } finally {
      setBusy(null);
    }
  }

  async function runStartMock(ticket = selectedMockTicket) {
    if (!ticket) return;
    fillTicket(ticket);
    setBusy("start-mock");
    setError(null);
    try {
      const next = await startWorkflowFromMockTicket({
        created_by: createdBy,
        ticket_id: ticket.id
      });
      setSelectedTestId("");
      keepContext(next);
      void refreshWorkflowQueue();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Mock workflow start failed");
    } finally {
      setBusy(null);
    }
  }

  async function runLoad() {
    if (!loadId.trim()) return;
    setBusy("load");
    setError(null);
    try {
      const next = await getWorkflow(loadId.trim());
      setSelectedTestId("");
      keepContext(next);
      void refreshWorkflowQueue();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Workflow load failed");
    } finally {
      setBusy(null);
    }
  }

  async function runRefresh() {
    if (!context) return;
    setBusy("refresh");
    setError(null);
    try {
      keepContext(await getWorkflow(context.context_id));
      void refreshWorkflowQueue();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Refresh failed");
    } finally {
      setBusy(null);
    }
  }

  async function review(decision: "approve" | "request_changes") {
    if (!context) return;
    setBusy(decision);
    setError(null);
    try {
      const next = await decideApproval({
        contextId: context.context_id,
        decision,
        reviewed_by: reviewer,
        comment: reviewComment.trim() || undefined
      });
      keepContext(next);
      if (decision === "request_changes") {
        setReviewComment("");
      }
      void refreshWorkflowQueue();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Review action failed");
    } finally {
      setBusy(null);
    }
  }

  async function runExecution() {
    if (!context) return;
    setBusy("execute");
    setError(null);
    try {
      const run = await executeSuite({
        suite: context.context_id,
        adapter: executionAdapter,
        branch: executionBranch.trim() || null,
        env: executionEnv.trim() || "staging",
        tags: splitLabels(executionTags),
        actor: reviewer
      });
      setSelectedRunId(run.run_id);
      await refreshExecutionRuns(run.context_id);
      await waitForExecutionRun(run.run_id, run.context_id, run.websocket_url);
      void refreshWorkflowQueue();
    } catch (err) {
      setError(err instanceof Error ? err.message : "CI execution failed");
    } finally {
      setBusy(null);
    }
  }

  async function loadWorkflowFromQueue(contextId: string) {
    setBusy("load-history");
    setError(null);
    try {
      const next = await getWorkflow(contextId);
      setSelectedTestId("");
      keepContext(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Workflow load failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar" aria-label="Workflow controls">
        <div className="brand">
          <ShieldCheck aria-hidden="true" />
          <div>
            <h1>AegisQA</h1>
            <span>Review console</span>
          </div>
        </div>

        <section className="panel">
          <div className="section-title">
            <Database aria-hidden="true" />
            <h2>Mock tickets</h2>
          </div>
          <div className="mock-search">
            <label>
              Search
              <input
                value={mockQuery}
                onChange={(event) => setMockQuery(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") void refreshMockTickets();
                }}
              />
            </label>
            <button
              className="icon-button"
              onClick={() => void refreshMockTickets()}
              disabled={mockLoading}
              title="Search mock tickets"
            >
              {mockLoading ? <Loader2 className="spin" aria-hidden="true" /> : <Search aria-hidden="true" />}
            </button>
          </div>
          <div className="mock-ticket-list">
            {mockTickets.map((ticket) => (
              <button
                key={ticket.id}
                className={`mock-ticket ${selectedMockTicketId === ticket.id ? "active" : ""}`}
                onClick={() => fillTicket(ticket)}
              >
                <span>
                  <strong>{ticket.id}</strong>
                  {ticket.title}
                </span>
                <em className={`priority ${ticket.priority}`}>{ticket.priority}</em>
              </button>
            ))}
            {!mockLoading && mockTickets.length === 0 && (
              <p className="empty-state">No mock tickets found.</p>
            )}
          </div>
          <button
            className="secondary-button full-width"
            onClick={() => void runStartMock()}
            disabled={busy !== null || !selectedMockTicket}
          >
            {busy === "start-mock" ? <Loader2 className="spin" aria-hidden="true" /> : <Play aria-hidden="true" />}
            Start selected
          </button>
        </section>

        <section className="panel">
          <div className="section-title">
            <ClipboardCheck aria-hidden="true" />
            <h2>Ticket</h2>
          </div>
          <label>
            Created by
            <input value={createdBy} onChange={(event) => setCreatedBy(event.target.value)} />
          </label>
          <label>
            Ticket ID
            <input value={ticketId} onChange={(event) => setTicketId(event.target.value)} />
          </label>
          <label>
            Title
            <input value={title} onChange={(event) => setTitle(event.target.value)} />
          </label>
          <label>
            Description
            <textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              rows={4}
            />
          </label>
          <label>
            Acceptance criteria
            <textarea value={criteria} onChange={(event) => setCriteria(event.target.value)} rows={4} />
          </label>
          <div className="field-row">
            <label>
              Priority
              <select value={priority} onChange={(event) => setPriority(event.target.value as TicketData["priority"])}>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </label>
            <label>
              Labels
              <input value={labels} onChange={(event) => setLabels(event.target.value)} />
            </label>
          </div>
          <button className="primary-button" onClick={runStart} disabled={busy !== null}>
            {busy === "start" ? <Loader2 className="spin" aria-hidden="true" /> : <Play aria-hidden="true" />}
            Start
          </button>
        </section>

        <section className="panel">
          <div className="section-title">
            <Search aria-hidden="true" />
            <h2>Context</h2>
          </div>
          <label>
            Context ID
            <input value={loadId} onChange={(event) => setLoadId(event.target.value)} />
          </label>
          <div className="button-row">
            <button className="secondary-button" onClick={runLoad} disabled={busy !== null || !loadId.trim()}>
              <Search aria-hidden="true" />
              Load
            </button>
            <button className="icon-button" onClick={runRefresh} disabled={busy !== null || !context} title="Refresh">
              <RefreshCw aria-hidden="true" />
            </button>
          </div>
        </section>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <span className="eyebrow">{context?.ticket?.id ?? "No workflow"}</span>
            <h2>{context?.ticket?.title ?? "Start or load a workflow"}</h2>
          </div>
          <div className="topbar-actions">
            {context && <StatusPill value={context.workflow_status} />}
            {approval?.git_pr_url && (
              <a className="link-button" href={approval.git_pr_url} target="_blank" rel="noreferrer">
                <GitPullRequest aria-hidden="true" />
                PR
                <ExternalLink aria-hidden="true" />
              </a>
            )}
          </div>
        </header>

        {error && (
          <div className="error-banner" role="alert">
            <AlertTriangle aria-hidden="true" />
            {error}
          </div>
        )}

        <section className="metrics" aria-label="Workflow summary">
          <div>
            <span>Tests</span>
            <strong>{tests.length}</strong>
          </div>
          <div>
            <span>Validated</span>
            <strong>
              {validationCounts.passed}/{validationCounts.total}
            </strong>
          </div>
          <div>
            <span>Revision</span>
            <strong>{context?.automation_revision ?? 0}</strong>
          </div>
          <div>
            <span>Approval</span>
            <strong>{approval?.status.replaceAll("_", " ") ?? "None"}</strong>
          </div>
          <div>
            <span>Execution</span>
            <strong>{execution?.status ?? "None"}</strong>
          </div>
        </section>

        <section className="panel providers-panel">
          <div className="provider-header">
            <div className="section-title">
              <Plug aria-hidden="true" />
              <h2>Providers</h2>
            </div>
            <div className="provider-controls">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={includeExternalProviders}
                  onChange={(event) => setIncludeExternalProviders(event.target.checked)}
                />
                External
              </label>
              <button
                className="icon-button"
                onClick={() => void refreshProviderMetadata()}
                disabled={providersLoading}
                title="Refresh providers"
              >
                {providersLoading ? <Loader2 className="spin" aria-hidden="true" /> : <RefreshCw aria-hidden="true" />}
              </button>
            </div>
          </div>

          <div className="provider-summary">
            <div>
              <span>Environment</span>
              <strong>{providerCatalog?.environment ?? "local"}</strong>
            </div>
            <div>
              <span>Policy</span>
              <strong>{integrationProfile?.policy.replaceAll("_", " ") ?? "mock only"}</strong>
            </div>
            <div>
              <span>Selected</span>
              <strong>{providerCatalog?.selected.length ?? 0}</strong>
            </div>
            <div>
              <span>Registered</span>
              <strong>{providerCatalog?.providers.length ?? 0}</strong>
            </div>
            <div>
              <span>External</span>
              <strong>{providerCatalog?.external_connectors_enabled ? "on" : "off"}</strong>
            </div>
          </div>

          <div className="provider-layout">
            <div className="selected-provider-panel">
              <h3>Selected</h3>
              <div className="selected-provider-list">
                {(providerCatalog?.selected ?? []).map((provider) => (
                  <article className="selected-provider" key={`${provider.kind}-${provider.selected}`}>
                    <span>{formatProviderKind(provider.kind)}</span>
                    <strong>{provider.selected}</strong>
                    <StatusPill value={provider.status} />
                  </article>
                ))}
                {!providersLoading && !providerCatalog?.selected.length && (
                  <p className="empty-state">No providers selected.</p>
                )}
              </div>
              {integrationProfile && (
                <dl className="profile-facts">
                  <div>
                    <dt>Ticket</dt>
                    <dd>{integrationProfile.ticket_connector?.name ?? "None"}</dd>
                  </div>
                  <div>
                    <dt>Execution</dt>
                    <dd>{integrationProfile.execution_adapter?.name ?? "None"}</dd>
                  </div>
                  <div>
                    <dt>LLM</dt>
                    <dd>{integrationProfile.llm_provider?.name ?? "None"}</dd>
                  </div>
                  <div>
                    <dt>Memory</dt>
                    <dd>{integrationProfile.memory_store?.name ?? "None"}</dd>
                  </div>
                </dl>
              )}
            </div>

            <div className="provider-catalog-panel">
              <h3>Catalog</h3>
              <div className="provider-catalog-list">
                {(providerCatalog?.providers ?? []).map((provider) => (
                  <article
                    className={`provider-card ${provider.enabled ? "" : "disabled"} ${
                      selectedProviderNames.has(`${provider.kind}:${provider.name}`) ? "selected" : ""
                    }`}
                    key={`${provider.kind}-${provider.name}`}
                  >
                    <div className="provider-card-head">
                      <span>
                        <strong>{provider.name}</strong>
                        {formatProviderKind(provider.kind)}
                      </span>
                      <div className="provider-badges">
                        <StatusPill value={provider.mode} />
                        <StatusPill value={provider.enabled ? "ready" : "disabled"} />
                      </div>
                    </div>
                    <p>{provider.description}</p>
                    <em>{provider.config_key ?? "runtime"}</em>
                  </article>
                ))}
                {providersLoading && <p className="empty-state">Loading providers.</p>}
              </div>
            </div>
          </div>

          <div className="intelligence-area">
            <div className="intelligence-toolbar">
              <div className="section-title">
                <Brain aria-hidden="true" />
                <h2>Intelligence</h2>
              </div>
              <div className="intelligence-search">
                <label>
                  Search
                  <input
                    value={intelligenceQuery}
                    onChange={(event) => setIntelligenceQuery(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") void refreshProviderMetadata();
                    }}
                  />
                </label>
                <button
                  className="icon-button"
                  onClick={() => void refreshProviderMetadata()}
                  disabled={providersLoading}
                  title="Search intelligence stores"
                >
                  {providersLoading ? <Loader2 className="spin" aria-hidden="true" /> : <Search aria-hidden="true" />}
                </button>
              </div>
            </div>

            <div className="intelligence-grid">
              <div className="intelligence-column">
                <h3>Prompts</h3>
                {promptTemplates.map((prompt) => (
                  <article className="intelligence-item" key={`${prompt.name}-${prompt.version}`}>
                    <strong>{prompt.name}</strong>
                    <span>{prompt.version}</span>
                    <p>{prompt.description}</p>
                  </article>
                ))}
              </div>
              <div className="intelligence-column">
                <h3>LLM</h3>
                {llmProviders.map((provider) => (
                  <article className="intelligence-item" key={provider.name}>
                    <strong>{provider.name}</strong>
                    <span>{provider.model}</span>
                    <p>{provider.description}</p>
                  </article>
                ))}
                {context?.intelligence_trace && (
                  <article className="intelligence-item trace">
                    <strong>{context.intelligence_trace.llm_provider}</strong>
                    <span>{context.intelligence_trace.llm_calls.length} calls</span>
                    <p>
                      {context.intelligence_trace.knowledge_refs.length} knowledge refs,
                      {" "}
                      {context.intelligence_trace.memory_refs.length} memory refs
                    </p>
                  </article>
                )}
              </div>
              <div className="intelligence-column">
                <h3>Knowledge</h3>
                {knowledgeResults.map((result) => (
                  <article className="intelligence-item" key={result.ref_id}>
                    <strong>{result.title}</strong>
                    <span>{result.source}</span>
                    <p>{result.excerpt}</p>
                  </article>
                ))}
              </div>
              <div className="intelligence-column">
                <h3>Memory</h3>
                {memoryResults.map((result) => (
                  <article className="intelligence-item" key={result.ref_id}>
                    <strong>{result.title}</strong>
                    <span>{result.tags.join(", ") || result.ref_id}</span>
                    <p>{result.summary}</p>
                  </article>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="panel queue-panel">
          <div className="queue-header">
            <div className="section-title">
              <History aria-hidden="true" />
              <h2>Workflow queue</h2>
            </div>
            <div className="queue-controls">
              <label>
                Search
                <input
                  value={workflowQuery}
                  onChange={(event) => setWorkflowQuery(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") void refreshWorkflowQueue();
                  }}
                />
              </label>
              <label>
                Approval
                <select
                  value={approvalFilter}
                  onChange={(event) => {
                    const nextFilter = event.target.value as ApprovalStatus | "all";
                    setApprovalFilter(nextFilter);
                    void refreshWorkflowQueue(workflowQuery, nextFilter);
                  }}
                >
                  <option value="all">All</option>
                  <option value="pending_review">Pending review</option>
                  <option value="approved">Approved</option>
                  <option value="changes_requested">Changes requested</option>
                  <option value="not_ready">Not ready</option>
                </select>
              </label>
              <button
                className="icon-button"
                onClick={() => void refreshWorkflowQueue()}
                disabled={queueLoading}
                title="Refresh workflow queue"
              >
                {queueLoading ? <Loader2 className="spin" aria-hidden="true" /> : <RefreshCw aria-hidden="true" />}
              </button>
            </div>
          </div>
          <div className="queue-list">
            {workflows.map((workflow) => (
              <button
                key={workflow.context_id}
                className={`queue-row ${context?.context_id === workflow.context_id ? "active" : ""}`}
                onClick={() => void loadWorkflowFromQueue(workflow.context_id)}
                disabled={busy !== null}
              >
                <span className="queue-ticket">
                  <strong>{workflow.ticket_id ?? "Untitled"}</strong>
                  {workflow.ticket_title ?? workflow.context_id}
                </span>
                <span>{formatDate(workflow.updated_at)}</span>
                <StatusPill value={workflow.workflow_status} />
                <span>{workflow.approval_status?.replaceAll("_", " ") ?? "No approval"}</span>
                <span>{workflow.execution_status ?? "Not run"}</span>
                <span>{workflow.test_count} tests</span>
                <span>r{workflow.automation_revision}</span>
              </button>
            ))}
            {!queueLoading && workflows.length === 0 && (
              <p className="empty-state">No workflows found.</p>
            )}
          </div>
        </section>

        <div className="content-grid">
          <section className="panel test-list">
            <div className="section-title">
              <ClipboardCheck aria-hidden="true" />
              <h2>Tests</h2>
            </div>
            <div className="scroll-area">
              {tests.map((test) => {
                const automation = context?.automation[test.id];
                return (
                  <button
                    key={test.id}
                    className={`test-card ${selectedTest?.id === test.id ? "active" : ""}`}
                    onClick={() => setSelectedTestId(test.id)}
                  >
                    <ValidationIcon automation={automation} />
                    <span>
                      <strong>{test.id}</strong>
                      {test.title}
                    </span>
                    <em>{test.type}</em>
                  </button>
                );
              })}
            </div>
          </section>

          <section className="panel robot-panel">
            <div className="section-title">
              <FileCode2 aria-hidden="true" />
              <h2>{selectedAutomation ? fileName(selectedAutomation.robot_file) : "Robot file"}</h2>
            </div>
            {selectedTest && (
              <div className="test-detail">
                <div>
                  <span>Expected</span>
                  <p>{selectedTest.expected_outcome}</p>
                </div>
                <div>
                  <span>Validation</span>
                  <p>
                    {selectedAutomation?.validation.dry_run_passed
                      ? "Dry-run passed"
                      : selectedAutomation?.validation.errors[0] ??
                        selectedAutomation?.validation.dry_run_skipped_reason ??
                        "Pending"}
                  </p>
                </div>
              </div>
            )}
            <pre className="robot-view">{robotContent || "No generated file selected."}</pre>
          </section>

          <section className="panel review-panel">
            <div className="section-title">
              <GitPullRequest aria-hidden="true" />
              <h2>Review</h2>
            </div>
            <div className="review-state">
              <span>Status</span>
              <strong>{approval?.status.replaceAll("_", " ") ?? "None"}</strong>
            </div>
            <label>
              Reviewer
              <input value={reviewer} onChange={(event) => setReviewer(event.target.value)} />
            </label>
            <label>
              Comment
              <textarea
                value={reviewComment}
                onChange={(event) => setReviewComment(event.target.value)}
                rows={5}
              />
            </label>
            <div className="approval-actions">
              <button className="primary-button" onClick={() => review("approve")} disabled={!canReview || busy !== null}>
                {busy === "approve" ? <Loader2 className="spin" aria-hidden="true" /> : <CheckCircle2 aria-hidden="true" />}
                Approve
              </button>
              <button
                className="secondary-button"
                onClick={() => review("request_changes")}
                disabled={!canReview || busy !== null || !reviewComment.trim()}
              >
                {busy === "request_changes" ? <Loader2 className="spin" aria-hidden="true" /> : <RotateCcw aria-hidden="true" />}
                Changes
              </button>
            </div>
            {approval?.git_branch && (
              <dl className="git-facts">
                <div>
                  <dt>Branch</dt>
                  <dd>{approval.git_branch}</dd>
                </div>
                <div>
                  <dt>Git</dt>
                  <dd>{approval.git_status}</dd>
                </div>
                {approval.git_commit_sha && (
                  <div>
                    <dt>Commit</dt>
                    <dd>{approval.git_commit_sha.slice(0, 10)}</dd>
                  </div>
                )}
              </dl>
            )}
          </section>

          <section className="panel execution-panel">
            <div className="execution-header">
              <div className="section-title">
                <Activity aria-hidden="true" />
                <h2>Execution</h2>
              </div>
              <button
                className="icon-button"
                onClick={() => void refreshExecutionRuns()}
                disabled={resultsLoading || !context}
                title="Refresh execution results"
              >
                {resultsLoading ? <Loader2 className="spin" aria-hidden="true" /> : <RefreshCw aria-hidden="true" />}
              </button>
            </div>
            <div className="execution-topline">
              <div>
                <span>Status</span>
                <strong>{execution?.status ?? "Not run"}</strong>
              </div>
              <div>
                <span>Passed</span>
                <strong>{executionCounts.passed}</strong>
              </div>
              <div>
                <span>Failed</span>
                <strong>{executionCounts.failed}</strong>
              </div>
              <div>
                <span>Skipped</span>
                <strong>{executionCounts.skipped}</strong>
              </div>
            </div>

            <div className="execution-config">
              <label>
                Adapter
                <select value={executionAdapter} onChange={(event) => setExecutionAdapter(event.target.value)}>
                  {executionAdapterOptions.length === 0 && <option value="mock">mock</option>}
                  {executionAdapterOptions.map((provider) => (
                    <option value={provider.name} key={provider.name}>
                      {provider.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Env
                <input value={executionEnv} onChange={(event) => setExecutionEnv(event.target.value)} />
              </label>
              <label>
                Branch
                <input value={executionBranch} onChange={(event) => setExecutionBranch(event.target.value)} />
              </label>
              <label>
                Tags
                <input value={executionTags} onChange={(event) => setExecutionTags(event.target.value)} />
              </label>
              <button
                className="primary-button"
                onClick={() => void runExecution()}
                disabled={busy !== null || !context || Object.keys(context.automation).length === 0}
              >
                {busy === "execute" ? <Loader2 className="spin" aria-hidden="true" /> : <Play aria-hidden="true" />}
                Run CI
              </button>
            </div>

            <div className="execution-layout">
              <div className="execution-current">
                <h3>Current result</h3>
                <div className="execution-list">
                  {(execution?.results ?? []).map((result) => (
                    <article className="execution-result" key={result.test_case_id}>
                      <span className={`result-status ${result.status}`}>{result.status}</span>
                      <div>
                        <strong>{result.test_case_id}</strong>
                        <p>{result.title}</p>
                        <em>{result.message}</em>
                      </div>
                      <span>{result.duration_ms} ms</span>
                    </article>
                  ))}
                  {!execution && <p className="empty-state">No execution results yet.</p>}
                </div>
              </div>

              <div className="run-history">
                <h3>Run history</h3>
                <div className="run-list">
                  {executionRuns.map((run) => {
                    const summary = run.execution?.summary;
                    const statusUrl = `/api/v1/results/${encodeURIComponent(run.run_id)}`;
                    return (
                      <article
                        className={`run-row ${selectedRunId === run.run_id ? "active" : ""}`}
                        key={run.run_id}
                      >
                        <div className="run-main">
                          <StatusPill value={run.status} />
                          <span>
                            <strong>{run.run_id}</strong>
                            {formatDate(run.updated_at)}
                          </span>
                        </div>
                        <div className="run-meta">
                          <span>{run.request.adapter}</span>
                          <span>{run.request.env}</span>
                          <span>{run.request.branch || "No branch"}</span>
                          <span>{summary ? `${summary.passed}/${summary.total} passed` : "No summary"}</span>
                        </div>
                        <div className="artifact-links">
                          <button type="button" onClick={() => void refreshExecutionEvents(run.run_id)}>
                            Logs
                          </button>
                          <a href={statusUrl} target="_blank" rel="noreferrer">
                            JSON
                            <ExternalLink aria-hidden="true" />
                          </a>
                          {run.execution && (
                            <>
                              <a href={`${statusUrl}/junit.xml`} target="_blank" rel="noreferrer">
                                JUnit
                                <ExternalLink aria-hidden="true" />
                              </a>
                              <a href={`${statusUrl}/report.html`} target="_blank" rel="noreferrer">
                                HTML
                                <ExternalLink aria-hidden="true" />
                              </a>
                            </>
                          )}
                        </div>
                      </article>
                    );
                  })}
                  {!resultsLoading && executionRuns.length === 0 && (
                    <p className="empty-state">No persisted execution runs yet.</p>
                  )}
                  {resultsLoading && (
                    <p className="empty-state">Loading execution runs.</p>
                  )}
                </div>
              </div>

              <div className="execution-log-panel">
                <div className="log-header">
                  <h3>Live logs</h3>
                  <button
                    className="icon-button"
                    onClick={() => void refreshExecutionEvents()}
                    disabled={logsLoading || !selectedRunId}
                    title="Refresh execution logs"
                  >
                    {logsLoading ? <Loader2 className="spin" aria-hidden="true" /> : <RefreshCw aria-hidden="true" />}
                  </button>
                </div>
                <div className="execution-log-list">
                  {executionEvents.map((event) => (
                    <article className={`execution-log ${event.level}`} key={event.id}>
                      <span>{formatDate(event.created_at)}</span>
                      <strong>{event.phase.replaceAll("_", " ")}</strong>
                      <em>{event.test_case_id ?? event.status ?? event.level}</em>
                      <p>{event.message}</p>
                    </article>
                  ))}
                  {!logsLoading && executionEvents.length === 0 && (
                    <p className="empty-state">No execution logs yet.</p>
                  )}
                  {logsLoading && <p className="empty-state">Loading execution logs.</p>}
                </div>
              </div>
            </div>
          </section>

          <section className="panel audit-panel">
            <div className="section-title">
              <History aria-hidden="true" />
              <h2>Audit</h2>
            </div>
            <div className="scroll-area">
              {(context?.audit_log ?? []).slice().reverse().map((event) => (
                <article className="audit-item" key={event.id}>
                  <span>{formatDate(event.created_at)}</span>
                  <strong>{event.event_type.replaceAll("_", " ")}</strong>
                  <p>{event.summary}</p>
                  <em>{event.actor}</em>
                </article>
              ))}
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}
