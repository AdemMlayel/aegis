import {
  Activity,
  Bot,
  CheckCircle2,
  ClipboardList,
  Cloud,
  Cpu,
  Database,
  FileCode2,
  GitPullRequest,
  History,
  Loader2,
  PlayCircle,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  XCircle
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  decideApproval,
  executeSuite,
  executeWorkflow,
  getAgentModelProfiles,
  getAutomationFile,
  getWorkflow,
  getEmbeddingProviders,
  getLLMProviders,
  getOllamaHealth,
  getOllamaProfiles,
  getProviderCatalog,
  listExecutionEvents,
  listExecutionRuns,
  listMockTickets,
  listWorkflows,
  smokeTestOllamaProfiles,
  startWorkflowFromMockTicket
} from "./api";
import type {
  AgentModelProfile,
  AgentModelRoute,
  AgentRoutingCatalog,
  AutomationBlock,
  EmbeddingProvider,
  ExecutionEvent,
  ExecutionRunRecord,
  LLMProvider,
  OllamaHealth,
  OllamaModelProfile,
  OllamaModelProfiles,
  OllamaSmokeTestResult,
  ProviderCatalog,
  TestCase,
  TestContext,
  TicketData,
  WorkflowSummary
} from "./types";

type DemoStep = {
  label: string;
  status: "done" | "active" | "waiting" | "blocked";
  detail: string;
};

const REVIEWER = "pm-demo-reviewer";

export default function App() {
  const [tickets, setTickets] = useState<TicketData[]>([]);
  const [selectedTicketId, setSelectedTicketId] = useState("MOCK-101");
  const [context, setContext] = useState<TestContext | null>(null);
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [providerCatalog, setProviderCatalog] = useState<ProviderCatalog | null>(null);
  const [llmProviders, setLlmProviders] = useState<LLMProvider[]>([]);
  const [embeddingProviders, setEmbeddingProviders] = useState<EmbeddingProvider[]>([]);
  const [agentRouting, setAgentRouting] = useState<AgentRoutingCatalog | null>(null);
  const [agentRoutes, setAgentRoutes] = useState<Record<string, AgentModelRoute>>({});
  const [ollamaHealth, setOllamaHealth] = useState<OllamaHealth | null>(null);
  const [ollamaProfiles, setOllamaProfiles] = useState<OllamaModelProfiles | null>(null);
  const [smokeResults, setSmokeResults] = useState<OllamaSmokeTestResult[]>([]);
  const [selectedLlmProvider, setSelectedLlmProvider] = useState("mock_llm");
  const [selectedEmbeddingProvider, setSelectedEmbeddingProvider] = useState("local_hash_embeddings");
  const [llmModelOverride, setLlmModelOverride] = useState("");
  const [embeddingModelOverride, setEmbeddingModelOverride] = useState("");
  const [automationContent, setAutomationContent] = useState("");
  const [selectedTestId, setSelectedTestId] = useState("");
  const [executionRuns, setExecutionRuns] = useState<ExecutionRunRecord[]>([]);
  const [executionEvents, setExecutionEvents] = useState<ExecutionEvent[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedTicket = useMemo(
    () => tickets.find((ticket) => ticket.id === selectedTicketId) ?? tickets[0] ?? null,
    [tickets, selectedTicketId]
  );

  const selectedTest: TestCase | null = useMemo(
    () => context?.test_cases.find((test) => test.id === selectedTestId) ?? context?.test_cases[0] ?? null,
    [context, selectedTestId]
  );

  const selectedAutomation: AutomationBlock | null = selectedTest && context
    ? context.automation[selectedTest.id] ?? null
    : null;

  const steps = useMemo(() => buildSteps(context), [context]);

  useEffect(() => {
    void refreshAll();
  }, []);

  useEffect(() => {
    if (!context) return;
    localStorage.setItem("aegisqa:lastContextId", context.context_id);
    if (!selectedTestId && context.test_cases.length > 0) {
      setSelectedTestId(context.test_cases[0].id);
    }
    void refreshExecutionRuns(context.context_id);
  }, [context, selectedTestId]);

  useEffect(() => {
    if (!context?.ticket || !selectedAutomation) {
      setAutomationContent("");
      return;
    }
    getAutomationFile(context.ticket.id, selectedAutomation.robot_file)
      .then(setAutomationContent)
      .catch((err: Error) => setAutomationContent(`Unable to load generated file: ${err.message}`));
  }, [context?.ticket?.id, selectedAutomation?.robot_file]);

  async function runAction<T>(name: string, action: () => Promise<T>): Promise<T | null> {
    setBusy(name);
    setError(null);
    try {
      return await action();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      return null;
    } finally {
      setBusy(null);
    }
  }

  async function refreshAll() {
    await runAction("refresh", async () => {
      const [ticketList, queue, catalog, llms, embeddings, routing, health, profiles] = await Promise.all([
        listMockTickets(),
        listWorkflows({ limit: 8 }),
        getProviderCatalog(),
        getLLMProviders(),
        getEmbeddingProviders(),
        getAgentModelProfiles(),
        getOllamaHealth(),
        getOllamaProfiles()
      ]);
      setTickets(ticketList);
      setWorkflows(queue);
      setProviderCatalog(catalog);
      setLlmProviders(llms);
      setEmbeddingProviders(embeddings);
      setAgentRouting(routing);
      setOllamaHealth(health);
      setOllamaProfiles(profiles);
      setSelectedLlmProvider((current) => current || llms[0]?.name || "mock_llm");
      setSelectedEmbeddingProvider((current) => current || embeddings[0]?.name || "local_hash_embeddings");
      const stored = localStorage.getItem("aegisqa:lastContextId");
      if (stored) {
        const loaded = await getWorkflow(stored).catch(() => null);
        if (loaded) {
          setContext(loaded);
          setAgentRoutes(loaded.intelligence_config.agent_routes);
          setSelectedLlmProvider(loaded.intelligence_config.llm_provider);
          setSelectedEmbeddingProvider(loaded.intelligence_config.embedding_provider);
          setLlmModelOverride(loaded.intelligence_config.llm_model ?? "");
          setEmbeddingModelOverride(loaded.intelligence_config.embedding_model ?? "");
        }
      }
    });
  }

  async function refreshExecutionRuns(contextId: string) {
    const runs = await listExecutionRuns({ contextId, limit: 5 }).catch(() => []);
    setExecutionRuns(runs);
    const latest = runs[0];
    if (latest) {
      const events = await listExecutionEvents(latest.run_id).catch(() => []);
      setExecutionEvents(events);
    } else {
      setExecutionEvents([]);
    }
  }

  async function startDemoWorkflow() {
    if (!selectedTicket) return;
    const next = await runAction("workflow", () =>
      startWorkflowFromMockTicket({
        created_by: "pm-demo",
        ticket_id: selectedTicket.id,
        intelligence: {
          llm_provider: selectedLlmProvider,
          embedding_provider: selectedEmbeddingProvider,
          llm_model: llmModelOverride.trim() || null,
          embedding_model: embeddingModelOverride.trim() || null,
          agent_routes: Object.fromEntries(
            (agentRouting?.agents ?? [])
              .filter((profile) => profile.uses_llm)
              .map((profile) => [
                profile.agent_name,
                agentRoutes[profile.agent_name] ?? {
                  provider: selectedLlmProvider,
                  model: llmModelOverride.trim() || null
                }
              ])
          )
        }
      })
    );
    if (next) {
      setContext(next);
      setSelectedTestId(next.test_cases[0]?.id ?? "");
      await refreshAll();
    }
  }

  async function approveWorkflow() {
    if (!context) return;
    const next = await runAction("approval", () =>
      decideApproval({
        contextId: context.context_id,
        decision: "approve",
        reviewed_by: REVIEWER,
        comment: "Approved for local architecture demo execution."
      })
    );
    if (next) setContext(next);
  }

  async function executeApprovedWorkflow() {
    if (!context) return;
    const next = await runAction("execution", () =>
      executeWorkflow({ contextId: context.context_id, run_by: "pm-demo-runner" })
    );
    if (next) {
      setContext(next);
      await refreshExecutionRuns(next.context_id);
    }
  }

  async function runCiStyleExecution() {
    const ticketId = context?.ticket?.id ?? selectedTicket?.id ?? "MOCK-101";
    const response = await runAction("ci", () =>
      executeSuite({
        suite: ticketId,
        adapter: "mock",
        branch: context?.approval?.git_branch ?? "local/demo",
        env: "local",
        tags: ["demo", "generated"],
        actor: "pm-demo-ci"
      })
    );
    if (response && context) await refreshExecutionRuns(context.context_id);
  }

  async function runOllamaSmokeTest() {
    const roles = ollamaProfiles?.profiles.map((profile) => profile.role) ?? null;
    const results = await runAction("smoke", () => smokeTestOllamaProfiles({ roles }));
    if (results) setSmokeResults(results);
    const profiles = await getOllamaProfiles().catch(() => null);
    if (profiles) setOllamaProfiles(profiles);
  }

  function useOllamaProfile(profile: OllamaModelProfile) {
    if (profile.kind === "embedding") {
      setSelectedEmbeddingProvider("ollama_nomic_embed_text");
      setEmbeddingModelOverride(profile.model);
      return;
    }
    setSelectedLlmProvider("ollama");
    const matchingAgents = (agentRouting?.agents ?? []).filter(
      (agent) => agent.uses_llm && agent.local_role === profile.role
    );
    setAgentRoutes((current) => {
      const next = { ...current };
      for (const agent of matchingAgents) {
        next[agent.agent_name] = { provider: "ollama", model: profile.model };
      }
      return next;
    });
  }

  function updateAgentProvider(profile: AgentModelProfile, provider: string) {
    const suggestedModel = provider === "openai_compatible"
      ? profile.external_model
      : null;
    setAgentRoutes((current) => ({
      ...current,
      [profile.agent_name]: { provider, model: suggestedModel }
    }));
  }

  function updateAgentModel(profile: AgentModelProfile, model: string) {
    const current = agentRoutes[profile.agent_name] ?? {
      provider: selectedLlmProvider,
      model: null
    };
    setAgentRoutes((routes) => ({
      ...routes,
      [profile.agent_name]: {
        ...current,
        model: model.trim() || null
      }
    }));
  }

  function applyRoutingPreset(preset: "safe" | "local" | "hybrid") {
    const externalReady = llmProviders.some(
      (provider) => provider.name === "openai_compatible" && provider.selectable
    );
    const nextRoutes: Record<string, AgentModelRoute> = {};
    for (const profile of (agentRouting?.agents ?? []).filter((item) => item.uses_llm)) {
      if (preset === "safe") {
        nextRoutes[profile.agent_name] = { provider: "mock_llm", model: null };
      } else if (
        preset === "local"
        || profile.recommended_mode === "local"
        || !externalReady
      ) {
        nextRoutes[profile.agent_name] = { provider: "ollama", model: null };
      } else {
        nextRoutes[profile.agent_name] = {
          provider: "openai_compatible",
          model: profile.external_model
        };
      }
    }
    setAgentRoutes(nextRoutes);
    setLlmModelOverride("");
    if (preset === "safe") {
      setSelectedLlmProvider("mock_llm");
      setSelectedEmbeddingProvider("local_hash_embeddings");
      setEmbeddingModelOverride("");
      return;
    }
    setSelectedLlmProvider(
      preset === "hybrid" && externalReady ? "openai_compatible" : "ollama"
    );
    setSelectedEmbeddingProvider("ollama_nomic_embed_text");
    setEmbeddingModelOverride(
      agentRouting?.embedding.recommended_model ?? "nomic-embed-text"
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <ShieldCheck />
          <div>
            <h1>AegisQA</h1>
            <p>AI-native QA orchestration demo</p>
          </div>
        </div>

        <section className="panel">
          <SectionTitle icon={<ClipboardList />} title="Demo ticket" />
          <label>
            Local provider
            <select value={selectedTicketId} onChange={(event) => setSelectedTicketId(event.target.value)}>
              {tickets.map((ticket) => (
                <option key={ticket.id} value={ticket.id}>{ticket.id} — {ticket.title}</option>
              ))}
            </select>
          </label>
          {selectedTicket ? <TicketPreview ticket={selectedTicket} /> : <Empty text="No local tickets loaded." />}
          <button className="primary-button" disabled={busy !== null || !selectedTicket} onClick={startDemoWorkflow}>
            {busy === "workflow" ? <Loader2 className="spin" /> : <PlayCircle />} Run full workflow
          </button>
        </section>

        <section className="panel">
          <SectionTitle icon={<Bot />} title="Agent model routing" />
          <div className="mode-switch" aria-label="AI routing preset">
            <button type="button" onClick={() => applyRoutingPreset("safe")}><ShieldCheck /> Safe demo</button>
            <button type="button" onClick={() => applyRoutingPreset("local")}><Cpu /> Private local</button>
            <button type="button" onClick={() => applyRoutingPreset("hybrid")}><Cloud /> Hybrid best</button>
          </div>
          <AgentRoutingList
            profiles={agentRouting?.agents ?? []}
            providers={llmProviders}
            routes={agentRoutes}
            fallbackProvider={selectedLlmProvider}
            onProviderChange={updateAgentProvider}
            onModelChange={updateAgentModel}
          />
          <label>
            Default LLM fallback
            <select value={selectedLlmProvider} onChange={(event) => setSelectedLlmProvider(event.target.value)}>
              {llmProviders.map((provider) => (
                <option key={provider.name} value={provider.name} disabled={!provider.selectable}>
                  {provider.name} - {provider.model}
                </option>
              ))}
            </select>
          </label>
          <label>
            Default model override
            <input
              value={llmModelOverride}
              onChange={(event) => setLlmModelOverride(event.target.value)}
              placeholder={ollamaHealth?.chat_model ?? "optional"}
            />
          </label>
          <div className="route-heading embedding-heading">
            <div>
              <strong>RAG and memory embeddings</strong>
              <span>{agentRouting?.embedding.rationale ?? "Local embeddings keep retrieval data private."}</span>
            </div>
            <span className="recommendation local">Best: local</span>
          </div>
          <label>
            Embedding provider
            <select value={selectedEmbeddingProvider} onChange={(event) => setSelectedEmbeddingProvider(event.target.value)}>
              {embeddingProviders.map((provider) => (
                <option key={provider.name} value={provider.name} disabled={!provider.selectable}>
                  {provider.name} - {provider.model}
                </option>
              ))}
            </select>
          </label>
          <label>
            Embedding model override
            <input
              value={embeddingModelOverride}
              onChange={(event) => setEmbeddingModelOverride(event.target.value)}
              placeholder={agentRouting?.embedding.recommended_model ?? ollamaHealth?.embedding_model ?? "optional"}
            />
          </label>
          <ProviderLine label="Catalog LLM" value={selectedProvider(providerCatalog, "llm_provider") ?? "mock_llm"} />
          <ProviderLine label="Catalog embedding" value={selectedProvider(providerCatalog, "embedding_provider") ?? "local_hash_embeddings"} />
          {context?.intelligence_config ? (
            <>
              <ProviderLine label="Run LLM" value={context.intelligence_config.llm_model || context.intelligence_config.llm_provider} />
              <ProviderLine label="Run embedding" value={context.intelligence_config.embedding_model || context.intelligence_config.embedding_provider} />
            </>
          ) : null}
          <ProviderLine label="Ollama" value={ollamaHealth?.message ?? "Not checked"} tone={ollamaHealth?.available ? "good" : "warn"} />
          <ModelProfileList
            profiles={ollamaProfiles?.profiles ?? []}
            smokeResults={smokeResults}
            onUse={useOllamaProfile}
          />
          <TextList
            title="Prompt routing"
            items={(ollamaProfiles?.prompt_routes ?? []).map(
              (route) => `${route.prompt_name}: ${route.role} -> ${route.model}`
            )}
            empty="No prompt routes loaded."
          />
          <button className="secondary-button full-width" onClick={runOllamaSmokeTest} disabled={busy !== null}>
            {busy === "smoke" ? <Loader2 className="spin" /> : <Activity />} Smoke test roles
          </button>
          <details>
            <summary>Available model providers</summary>
            <ul className="compact-list">
              {llmProviders.map((provider) => <li key={provider.name}>{provider.name} — {provider.model}</li>)}
              {embeddingProviders.map((provider) => <li key={provider.name}>{provider.name} — {provider.model}</li>)}
            </ul>
          </details>
        </section>

        <section className="panel">
          <SectionTitle icon={<History />} title="Recent workflows" />
          <div className="workflow-list">
            {workflows.slice(0, 5).map((item) => (
              <button key={item.context_id} className="workflow-item" onClick={async () => {
                const loaded = await runAction("load", () => getWorkflow(item.context_id));
                if (loaded) setContext(loaded);
              }}>
                <strong>{item.ticket_id ?? "Untitled"}</strong>
                <span>{item.workflow_status}</span>
              </button>
            ))}
          </div>
          <button className="secondary-button full-width" onClick={refreshAll} disabled={busy !== null}>
            {busy === "refresh" ? <Loader2 className="spin" /> : <RefreshCw />} Refresh
          </button>
        </section>
      </aside>

      <main className="workspace">
        <header className="hero">
          <div>
            <p className="eyebrow">PM-ready architecture proof</p>
            <h2>{context?.ticket?.title ?? "Run a local workflow to generate an evidence-backed QA package"}</h2>
            <p>
              Routes each AI agent independently across mock, private local, or configured external models,
              while RAG embeddings can remain local.
            </p>
          </div>
          <div className="hero-actions">
            <button className="secondary-button" disabled={!context || context.approval?.status !== "pending_review" || busy !== null} onClick={approveWorkflow}>
              {busy === "approval" ? <Loader2 className="spin" /> : <GitPullRequest />} Approve
            </button>
            <button className="primary-button" disabled={!context || context.approval?.status !== "approved" || busy !== null} onClick={executeApprovedWorkflow}>
              {busy === "execution" ? <Loader2 className="spin" /> : <Activity />} Execute
            </button>
          </div>
        </header>

        {error ? <div className="error-banner"><XCircle /> {error}</div> : null}

        <section className="status-grid">
          {steps.map((step) => <StepCard key={step.label} step={step} />)}
        </section>

        <section className="content-grid">
          <Panel title="Requirement Analysis" icon={<Search />}>
            {context?.requirement_analysis ? (
              <div className="stack">
                <Metric label="Domain" value={context.requirement_analysis.domain} />
                <Metric label="Actor" value={context.requirement_analysis.actor} />
                <Metric label="Confidence" value={`${Math.round(context.requirement_analysis.confidence * 100)}%`} />
                <TextList title="Expected results" items={context.requirement_analysis.expected_results} />
                <TextList title="Clarification questions" items={context.requirement_analysis.clarification_questions} empty="No blocker questions." />
                <p className="callout">{context.requirement_analysis.llm_summary}</p>
              </div>
            ) : <Empty text="Requirement analysis appears after workflow execution." />}
          </Panel>

          <Panel title="Coverage Plan" icon={<ShieldCheck />}>
            {context?.coverage_plan ? (
              <div className="stack">
                <Metric label="Risk" value={context.coverage_plan.risk_level} />
                <Metric label="Criticality" value={`${context.coverage_plan.business_criticality}/10`} />
                <TextList title="Test types" items={context.coverage_plan.test_types_required} />
                <TextList title="Risk rationale" items={context.coverage_plan.risk_rationale} />
              </div>
            ) : <Empty text="Coverage is generated from requirement analysis and local memory." />}
          </Panel>

          <Panel title="Generated Test Cases" icon={<ClipboardList />} wide>
            {context?.test_cases.length ? (
              <div className="test-layout">
                <div className="test-tabs">
                  {context.test_cases.map((test) => (
                    <button key={test.id} className={selectedTest?.id === test.id ? "active" : ""} onClick={() => setSelectedTestId(test.id)}>
                      <strong>{test.id}</strong>
                      <span>{test.type}</span>
                    </button>
                  ))}
                </div>
                {selectedTest ? <TestCaseDetail test={selectedTest} /> : null}
              </div>
            ) : <Empty text="No generated test cases yet." />}
          </Panel>

          <Panel title="Automation Output" icon={<FileCode2 />} wide>
            {selectedAutomation ? (
              <div className="stack">
                <div className="metrics-row">
                  <Metric label="Revision" value={String(selectedAutomation.revision)} />
                  <Metric label="Artifact" value={selectedAutomation.validation.artifact_exists ? "exists" : "missing"} />
                  <Metric label="Validation" value={validationLabel(selectedAutomation)} />
                </div>
                <pre className="code-block">{automationContent || "Loading generated Robot file..."}</pre>
              </div>
            ) : <Empty text="Select a generated test case to inspect its automation artifact." />}
          </Panel>

          <Panel title="Execution Result" icon={<Activity />}>
            {context?.execution ? (
              <div className="stack">
                <div className="metrics-row">
                  <Metric label="Status" value={context.execution.status} />
                  <Metric label="Passed" value={String(context.execution.summary.passed)} />
                  <Metric label="Failed" value={String(context.execution.summary.failed)} />
                  <Metric label="Skipped" value={String(context.execution.summary.skipped)} />
                </div>
                <TextList title="Case results" items={context.execution.results.map((result) => `${result.test_case_id}: ${result.status} — ${result.message}`)} />
                <button className="secondary-button" onClick={runCiStyleExecution} disabled={busy !== null}>
                  {busy === "ci" ? <Loader2 className="spin" /> : <PlayCircle />} Run CI-style API execution
                </button>
              </div>
            ) : (
              <div className="stack">
                <Empty text="Approve the workflow, then run execution. CI-style mock execution can also be triggered for API demos." />
                <button className="secondary-button" onClick={runCiStyleExecution} disabled={busy !== null || !context}>
                  {busy === "ci" ? <Loader2 className="spin" /> : <PlayCircle />} Run CI-style API execution
                </button>
              </div>
            )}
          </Panel>

          <Panel title="Report & Memory" icon={<Database />}>
            {context?.reports ? (
              <div className="stack">
                <p>{context.reports.summary}</p>
                <Metric label="Report confidence" value={`${Math.round(context.reports.confidence * 100)}%`} />
                <TextList title="Next actions" items={context.reports.next_actions} />
                <TextList title="Knowledge refs" items={context.reports.knowledge_refs_used} empty="No knowledge refs." />
                <TextList title="Memory refs" items={context.reports.memory_refs_used} empty="No memory refs." />
                <div className="callout">Memory archive: {context.memory_archive?.status ?? "not started"} {context.memory_archive?.memory_id ? `(${context.memory_archive.memory_id})` : ""}</div>
              </div>
            ) : <Empty text="Report appears after workflow generation and updates after execution." />}
          </Panel>

          <Panel title="Investigation & Events" icon={<Sparkles />} wide>
            <div className="stack">
              {context?.investigation ? <TextList title="Findings" items={context.investigation.findings.map((finding) => `${finding.severity}: ${finding.summary}`)} empty="No investigation findings." /> : <Empty text="Investigation runs after execution." />}
              <TextList title="Latest execution events" items={executionEvents.slice(0, 6).map((event) => `${event.phase}: ${event.message}`)} empty="No CI events captured yet." />
              <TextList title="Recent API runs" items={executionRuns.slice(0, 4).map((run) => `${run.run_id}: ${run.status}`)} empty="No execution runs yet." />
            </div>
          </Panel>
        </section>
      </main>
    </div>
  );
}

function buildSteps(context: TestContext | null): DemoStep[] {
  return [
    { label: "Ticket", status: context?.ticket ? "done" : "waiting", detail: context?.ticket?.id ?? "Local fixture provider" },
    { label: "Requirement", status: context?.requirement_analysis ? "done" : "waiting", detail: context?.requirement_analysis?.domain ?? "AI/RAG analysis" },
    { label: "Coverage", status: context?.coverage_plan ? "done" : "waiting", detail: context?.coverage_plan?.risk_level ?? "Risk plan" },
    { label: "Tests", status: context?.test_cases.length ? "done" : "waiting", detail: `${context?.test_cases.length ?? 0} generated` },
    { label: "Automation", status: context?.automation_revision ? "done" : "waiting", detail: `revision ${context?.automation_revision ?? 0}` },
    { label: "Approval", status: context?.approval?.status === "approved" ? "done" : context?.approval?.status === "pending_review" ? "active" : "waiting", detail: context?.approval?.status ?? "not ready" },
    { label: "Execution", status: context?.execution ? (context.execution.status === "failed" ? "blocked" : "done") : "waiting", detail: context?.execution?.status ?? "deferred" },
    { label: "Memory", status: context?.memory_archive?.status === "archived" ? "done" : "waiting", detail: context?.memory_archive?.status ?? "not archived" }
  ];
}

function selectedProvider(catalog: ProviderCatalog | null, kind: string): string | null {
  return catalog?.selected.find((entry) => entry.kind === kind)?.selected ?? null;
}

function validationLabel(block: AutomationBlock): string {
  if (block.validation.dry_run_passed === true) return "green";
  if (block.validation.dry_run_passed === null) return "local fallback";
  return "failed";
}

function SectionTitle({ icon, title }: { icon: React.ReactNode; title: string }) {
  return <div className="section-title">{icon}<h3>{title}</h3></div>;
}

function Panel({ icon, title, children, wide = false }: { icon: React.ReactNode; title: string; children: React.ReactNode; wide?: boolean }) {
  return <section className={wide ? "panel content-panel wide" : "panel content-panel"}><SectionTitle icon={icon} title={title} />{children}</section>;
}

function StepCard({ step }: { step: DemoStep }) {
  const Icon = step.status === "done" ? CheckCircle2 : step.status === "blocked" ? XCircle : Activity;
  return <div className={`step-card ${step.status}`}><Icon /><strong>{step.label}</strong><span>{step.detail}</span></div>;
}

function TicketPreview({ ticket }: { ticket: TicketData }) {
  return <div className="ticket-preview"><strong>{ticket.title}</strong><p>{ticket.description}</p><div className="tag-row"><span>{ticket.priority}</span>{ticket.labels.map((label) => <span key={label}>{label}</span>)}</div></div>;
}

function ProviderLine({ label, value, tone = "neutral" }: { label: string; value: string; tone?: "neutral" | "good" | "warn" }) {
  return <div className={`provider-line ${tone}`}><span>{label}</span><strong>{value}</strong></div>;
}

function AgentRoutingList({
  profiles,
  providers,
  routes,
  fallbackProvider,
  onProviderChange,
  onModelChange
}: {
  profiles: AgentModelProfile[];
  providers: LLMProvider[];
  routes: Record<string, AgentModelRoute>;
  fallbackProvider: string;
  onProviderChange: (profile: AgentModelProfile, provider: string) => void;
  onModelChange: (profile: AgentModelProfile, model: string) => void;
}) {
  if (!profiles.length) return <Empty text="No agent routing profiles loaded." />;

  return (
    <div className="agent-routing-list">
      {profiles.map((profile) => {
        const route = routes[profile.agent_name] ?? {
          provider: fallbackProvider,
          model: null
        };
        const selectedProvider = providers.find((provider) => provider.name === route.provider);
        const placeholder = route.provider === "ollama"
          ? profile.local_model ?? "automatic local role"
          : route.provider === "openai_compatible"
            ? profile.external_model ?? "configured external model"
            : "provider default";
        return (
          <div className="agent-route" key={profile.agent_name}>
            <div className="route-heading">
              <div>
                <strong>{profile.label}</strong>
                <span>{profile.purpose}</span>
              </div>
              <span className={`recommendation ${profile.recommended_mode}`}>
                {profile.uses_llm ? `Best: ${profile.recommended_mode}` : "Deterministic"}
              </span>
            </div>
            <p className="route-rationale">{profile.rationale}</p>
            {profile.uses_llm ? (
              <div className="route-controls">
                <label>
                  Provider
                  <select
                    value={route.provider}
                    onChange={(event) => onProviderChange(profile, event.target.value)}
                  >
                    {providers.map((provider) => (
                      <option
                        key={provider.name}
                        value={provider.name}
                        disabled={!provider.selectable}
                      >
                        {provider.mode}: {provider.name}
                        {provider.selectable ? "" : ` (${provider.configuration_status})`}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Model
                  <input
                    value={route.model ?? ""}
                    onChange={(event) => onModelChange(profile, event.target.value)}
                    placeholder={placeholder}
                  />
                </label>
                {selectedProvider && !selectedProvider.selectable ? (
                  <p className="provider-warning">
                    Configure {selectedProvider.configuration_keys.join(", ")} on the API server.
                  </p>
                ) : null}
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

function ModelProfileList({
  profiles,
  smokeResults,
  onUse
}: {
  profiles: OllamaModelProfile[];
  smokeResults: OllamaSmokeTestResult[];
  onUse: (profile: OllamaModelProfile) => void;
}) {
  const resultByRole = new Map(smokeResults.map((result) => [result.role, result]));
  if (!profiles.length) return <Empty text="No Ollama model roles loaded." />;

  return (
    <div className="model-profile-list">
      {profiles.map((profile) => {
        const result = resultByRole.get(profile.role);
        const ready = profile.installed || profile.fallback_installed;
        const tone = result ? (result.ok ? "good" : "warn") : ready ? "good" : "warn";
        const status = result
          ? result.ok ? "smoke ok" : "smoke failed"
          : profile.installed ? "installed"
          : profile.fallback_installed ? "fallback ready"
          : "missing";
        return (
          <div className={`model-profile ${tone}`} key={profile.role}>
            <div>
              <strong>{profile.role.replaceAll("_", " ")}</strong>
              <span>{profile.model}</span>
            </div>
            <div className="model-profile-actions">
              <span>{status}</span>
              <button className="mini-button" onClick={() => onUse(profile)} type="button">
                <CheckCircle2 /> Use
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="metric"><span>{label}</span><strong>{value}</strong></div>;
}

function TextList({ title, items, empty = "None." }: { title: string; items: string[]; empty?: string }) {
  return <div><p className="list-title">{title}</p>{items.length ? <ul className="text-list">{items.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}</ul> : <p className="empty-inline">{empty}</p>}</div>;
}

function Empty({ text }: { text: string }) {
  return <p className="empty-state">{text}</p>;
}

function TestCaseDetail({ test }: { test: TestCase }) {
  return <div className="test-detail"><div className="metrics-row"><Metric label="Priority" value={test.priority} /><Metric label="Type" value={test.type} /></div><h4>{test.title}</h4><TextList title="Steps" items={test.steps} /><p className="callout">Expected: {test.expected_outcome}</p><TextList title="Evidence refs" items={[...test.evidence_refs, ...test.memory_refs]} empty="No evidence refs." /></div>;
}
