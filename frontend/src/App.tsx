import { X, XCircle } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  cancelChatAction,
  confirmChatAction,
  createChatSession,
  createWorkflowSession,
  decideApproval,
  downloadWorkflowReport,
  editAutomationArtifact,
  executeWorkflow,
  getAgentGovernanceCatalog,
  getAgentModelProfiles,
  getAutomationFile,
  getEmbeddingProviders,
  getLLMProviders,
  getOllamaHealth,
  getOllamaProfiles,
  getObservabilitySummary,
  getOperationalHealth,
  getProviderCatalog,
  getReportPackageManifest,
  getTokenBudgetStatus,
  getWorkflow,
  listArtifactRevisions,
  listDemoTickets,
  listExecutionEvents,
  listExecutionRuns,
  listWorkflowTimeline,
  listWorkflows,
  pauseWorkflowSession,
  regenerateWorkflowStage,
  resumeWorkflowSession,
  reviewWorkflowStage,
  runNextWorkflowStage,
  sendChatMessage,
  sendWorkflowMessage,
  smokeTestOllamaProfiles
} from "./api";
import { AgentConfigPanel } from "./components/AgentConfigPanel";
import { CopilotPanel } from "./components/CopilotPanel";
import {
  ConversationWorkspace,
  type WorkspaceView
} from "./components/ConversationWorkspace";
import {
  WorkspaceNav,
  type WorkspaceFilter
} from "./components/WorkspaceNav";
import { OPERATOR_ID } from "./config";
import type {
  AgentModelProfile,
  AgentModelRoute,
  AgentRoutingCatalog,
  AgentGovernanceCatalog,
  ArtifactRevision,
  EmbeddingProvider,
  ExecutionEvent,
  ExecutionRunRecord,
  LLMProvider,
  OllamaHealth,
  OllamaModelProfiles,
  ObservabilitySummary,
  OperationalHealth,
  ProviderCatalog,
  ReportPackageManifest,
  TestContext,
  TicketData,
  TokenBudgetStatus,
  WorkflowEvent,
  WorkflowMode,
  WorkflowStageName,
  WorkflowSummary,
  ChatSession
} from "./types";

export default function App() {
  const [tickets, setTickets] = useState<TicketData[]>([]);
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [context, setContext] = useState<TestContext | null>(null);
  const [selectedTicketId, setSelectedTicketId] = useState("");
  const [workspaceQuery, setWorkspaceQuery] = useState("");
  const [workspaceFilter, setWorkspaceFilter] = useState<WorkspaceFilter>("all");
  const [view, setView] = useState<WorkspaceView>("conversation");
  const [configCollapsed, setConfigCollapsed] = useState(false);
  const [chatSession, setChatSession] = useState<ChatSession | null>(null);

  const [providerCatalog, setProviderCatalog] = useState<ProviderCatalog | null>(null);
  const [llmProviders, setLlmProviders] = useState<LLMProvider[]>([]);
  const [embeddingProviders, setEmbeddingProviders] = useState<EmbeddingProvider[]>([]);
  const [agentRouting, setAgentRouting] = useState<AgentRoutingCatalog | null>(null);
  const [agentGovernance, setAgentGovernance] = useState<AgentGovernanceCatalog | null>(null);
  const [observability, setObservability] = useState<ObservabilitySummary | null>(null);
  const [tokenBudget, setTokenBudget] = useState<TokenBudgetStatus | null>(null);
  const [operationalHealth, setOperationalHealth] = useState<OperationalHealth | null>(null);
  const [agentRoutes, setAgentRoutes] = useState<Record<string, AgentModelRoute>>({});
  const [workflowMode, setWorkflowMode] = useState<WorkflowMode>("approval_required");
  const [selectedLlmProvider, setSelectedLlmProvider] = useState("");
  const [selectedEmbeddingProvider, setSelectedEmbeddingProvider] = useState("local_hash_embeddings");
  const [embeddingModel, setEmbeddingModel] = useState("");
  const [ollamaHealth, setOllamaHealth] = useState<OllamaHealth | null>(null);
  const [ollamaProfiles, setOllamaProfiles] = useState<OllamaModelProfiles | null>(null);

  const [timeline, setTimeline] = useState<WorkflowEvent[]>([]);
  const timelineCursor = useRef(0);
  const [selectedTestId, setSelectedTestId] = useState("");
  const [artifactContent, setArtifactContent] = useState("");
  const [artifactDraft, setArtifactDraft] = useState("");
  const [artifactEditing, setArtifactEditing] = useState(false);
  const [artifactRevisions, setArtifactRevisions] = useState<ArtifactRevision[]>([]);
  const [executionRuns, setExecutionRuns] = useState<ExecutionRunRecord[]>([]);
  const [executionEvents, setExecutionEvents] = useState<ExecutionEvent[]>([]);
  const [reportPackage, setReportPackage] = useState<ReportPackageManifest | null>(null);

  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedTicket = useMemo(
    () => tickets.find((ticket) => ticket.id === selectedTicketId) ?? tickets[0] ?? null,
    [tickets, selectedTicketId]
  );
  const selectedTest = useMemo(
    () => context?.test_cases.find((test) => test.id === selectedTestId)
      ?? context?.test_cases[0]
      ?? null,
    [context, selectedTestId]
  );

  function selectTicket(ticketId: string) {
    setSelectedTicketId(ticketId);
    if (context?.ticket?.id !== ticketId) {
      setContext(null);
      setTimeline([]);
      timelineCursor.current = 0;
    }
  }

  useEffect(() => {
    void refreshBootstrap();
  }, []);

  useEffect(() => {
    if (!context) return;
    localStorage.setItem("aegisqa:lastContextId", context.context_id);
    setSelectedTicketId(context.ticket?.id ?? selectedTicketId);
    if (!context.test_cases.some((test) => test.id === selectedTestId)) {
      setSelectedTestId(context.test_cases[0]?.id ?? "");
    }
  }, [context?.context_id, context?.test_cases.length]);

  useEffect(() => {
    if (!context) {
      setTimeline([]);
      timelineCursor.current = 0;
      return;
    }
    let cancelled = false;
    timelineCursor.current = 0;
    setTimeline([]);

    const poll = async () => {
      const response = await listWorkflowTimeline(
        context.context_id,
        timelineCursor.current
      ).catch(() => null);
      if (!response || cancelled || !response.events.length) return;
      timelineCursor.current = response.next_sequence;
      setTimeline((current) => mergeEvents(current, response.events));
    };

    void poll();
    const interval = window.setInterval(() => void poll(), 2200);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [context?.context_id]);

  useEffect(() => {
    if (!context) {
      setExecutionRuns([]);
      setExecutionEvents([]);
      return;
    }
    void refreshExecution(context.context_id);
  }, [context?.context_id]);

  useEffect(() => {
    if (!context?.reports) {
      setReportPackage(null);
      return;
    }
    let cancelled = false;
    getReportPackageManifest(context.context_id)
      .then((manifest) => {
        if (!cancelled) setReportPackage(manifest);
      })
      .catch(() => {
        if (!cancelled) setReportPackage(null);
      });
    return () => {
      cancelled = true;
    };
  }, [
    context?.context_id,
    context?.updated_at,
    context?.approval?.status,
    context?.execution?.status
  ]);

  useEffect(() => {
    if (!context?.ticket || !selectedTest) {
      setArtifactContent("");
      setArtifactDraft("");
      setArtifactRevisions([]);
      setArtifactEditing(false);
      return;
    }
    const block = context.automation[selectedTest.id];
    if (!block) {
      setArtifactContent("");
      setArtifactDraft("");
      setArtifactRevisions([]);
      setArtifactEditing(false);
      return;
    }
    let cancelled = false;
    Promise.all([
      getAutomationFile(context.ticket.id, block.robot_file),
      listArtifactRevisions(context.context_id, selectedTest.id).catch(() => [])
    ]).then(([content, revisions]) => {
      if (cancelled) return;
      setArtifactContent(content);
      setArtifactDraft(content);
      setArtifactRevisions(revisions);
      setArtifactEditing(false);
    }).catch((reason: Error) => {
      if (!cancelled) setError(reason.message);
    });
    return () => {
      cancelled = true;
    };
  }, [
    context?.context_id,
    context?.automation_revision,
    selectedTest?.id
  ]);

  async function runAction<T>(
    name: string,
    action: () => Promise<T>
  ): Promise<T | null> {
    setBusy(name);
    setError(null);
    try {
      return await action();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
      return null;
    } finally {
      setBusy(null);
    }
  }

  async function refreshBootstrap() {
    await runAction("refresh", async () => {
      const [
        ticketList,
        workflowList,
        catalog,
        providers,
        embeddings,
        routing,
        health,
        profiles,
        governance,
        telemetry,
        budget,
        serviceHealth
      ] = await Promise.all([
        listDemoTickets(),
        listWorkflows({ limit: 20 }),
        getProviderCatalog(),
        getLLMProviders(),
        getEmbeddingProviders(),
        getAgentModelProfiles(),
        getOllamaHealth(),
        getOllamaProfiles(),
        getAgentGovernanceCatalog(),
        getObservabilitySummary(),
        getTokenBudgetStatus(),
        getOperationalHealth()
      ]);
      setTickets(ticketList);
      setWorkflows(workflowList);
      setProviderCatalog(catalog);
      setLlmProviders(providers);
      setEmbeddingProviders(embeddings);
      setAgentRouting(routing);
      setOllamaHealth(health);
      setOllamaProfiles(profiles);
      setAgentGovernance(governance);
      setObservability(telemetry);
      setTokenBudget(budget);
      setOperationalHealth(serviceHealth);
      initializeRuntimeDefaults(routing, providers, embeddings, health);
      const chat = await createChatSession({
        created_by: OPERATOR_ID,
        ticket_id: ticketList[0]?.id ?? null,
        title: "AegisQA Copilot"
      }).catch(() => null);
      if (chat) setChatSession(chat);

      const storedContextId = localStorage.getItem("aegisqa:lastContextId");
      if (storedContextId) {
        const loaded = await getWorkflow(storedContextId).catch(() => null);
        if (loaded) {
          applyContext(loaded);
        } else {
          localStorage.removeItem("aegisqa:lastContextId");
        }
      }
    });
  }

  function initializeRuntimeDefaults(
    routing: AgentRoutingCatalog,
    providers: LLMProvider[],
    embeddings: EmbeddingProvider[],
    health: OllamaHealth
  ) {
    const externalReady = providers.some(
      (provider) => provider.name === "openai_compatible" && provider.selectable
    );
    const localReady = health.available
      && health.chat_model_ready
      && providers.some(
        (provider) => provider.name === "ollama" && provider.selectable
      );
    const defaultProvider = externalReady
      ? "openai_compatible"
      : localReady
        ? "ollama"
        : "";
    const localEmbeddingReady = health.available && health.embedding_model_ready
      && embeddings.some(
        (provider) => provider.name === "ollama_nomic_embed_text" && provider.selectable
      );

    setSelectedLlmProvider(defaultProvider);
    setSelectedEmbeddingProvider(
      localEmbeddingReady ? "ollama_nomic_embed_text" : "local_hash_embeddings"
    );
    setEmbeddingModel(localEmbeddingReady ? health.embedding_model : "");
    setAgentRoutes((current) => {
      if (Object.keys(current).length) return current;
      if (!defaultProvider) return {};
      return Object.fromEntries(
        routing.agents
          .filter((profile) => profile.uses_llm)
          .map((profile) => [
            profile.agent_name,
            {
              provider: defaultProvider,
              model: defaultProvider === "openai_compatible"
                ? profile.external_model
                : null
            }
          ])
      );
    });
  }

  function applyContext(next: TestContext) {
    setContext(next);
    setWorkflowMode(next.workflow_control.mode);
    setAgentRoutes(next.intelligence_config.agent_routes);
    setSelectedLlmProvider(next.intelligence_config.llm_provider);
    setSelectedEmbeddingProvider(next.intelligence_config.embedding_provider);
    setEmbeddingModel(next.intelligence_config.embedding_model ?? "");
    setSelectedTestId(next.test_cases[0]?.id ?? "");
  }

  async function refreshWorkflows() {
    const next = await listWorkflows({ limit: 20 });
    setWorkflows(next);
  }

  async function refreshExecution(contextId: string) {
    const runs = await listExecutionRuns({ contextId, limit: 8 }).catch(() => []);
    setExecutionRuns(runs);
    const latest = runs[0];
    setExecutionEvents(
      latest ? await listExecutionEvents(latest.run_id).catch(() => []) : []
    );
  }

  async function openWorkflow(contextId: string) {
    const loaded = await runAction("load", () => getWorkflow(contextId));
    if (loaded) {
      applyContext(loaded);
      setView("conversation");
    }
  }

  async function createWorkspace() {
    if (!selectedTicket) return;
    if (!selectedLlmProvider) {
      setError("Configure a ready external or local model before starting the workflow.");
      return;
    }
    const created = await runAction("create", () =>
      createWorkflowSession({
        created_by: OPERATOR_ID,
        ticket: selectedTicket,
        mode: workflowMode,
        intelligence: intelligencePayload()
      })
    );
    if (!created) return;
    applyContext(created);
    setView("conversation");
    await refreshWorkflows();
  }

  function intelligencePayload() {
    return {
      llm_provider: selectedLlmProvider,
      embedding_provider: selectedEmbeddingProvider,
      llm_model: null,
      embedding_model: embeddingModel.trim() || null,
      agent_routes: Object.fromEntries(
        (agentRouting?.agents ?? [])
          .filter((profile) => profile.uses_llm)
          .map((profile) => [
            profile.agent_name,
            agentRoutes[profile.agent_name] ?? {
              provider: selectedLlmProvider,
              model: null
            }
          ])
      )
    };
  }

  async function resume() {
    if (!context) return;
    const next = await runAction("resume", () =>
      resumeWorkflowSession({ contextId: context.context_id, actor: OPERATOR_ID })
    );
    if (next) {
      applyContext(next);
      await refreshWorkflows();
    }
  }

  async function runNext() {
    if (!context) return;
    const next = await runAction("next", () =>
      runNextWorkflowStage({ contextId: context.context_id, actor: OPERATOR_ID })
    );
    if (next) {
      applyContext(next);
      await refreshWorkflows();
    }
  }

  async function pause() {
    if (!context) return;
    const next = await runAction("pause", () =>
      pauseWorkflowSession({ contextId: context.context_id, actor: OPERATOR_ID })
    );
    if (next) applyContext(next);
  }

  async function reviewStage(
    stage: WorkflowStageName,
    decision: "approve" | "request_changes",
    comment?: string
  ) {
    if (!context) return;
    const next = await runAction("review", () =>
      reviewWorkflowStage({
        contextId: context.context_id,
        stage,
        decision,
        reviewedBy: OPERATOR_ID,
        comment
      })
    );
    if (next) {
      applyContext(next);
      await refreshWorkflows();
    }
  }

  async function regenerateStage(stage: WorkflowStageName, comment: string) {
    if (!context) return;
    const next = await runAction("regenerate", () =>
      regenerateWorkflowStage({
        contextId: context.context_id,
        stage,
        actor: OPERATOR_ID,
        comment
      })
    );
    if (next) {
      applyContext(next);
      await refreshWorkflows();
    }
  }

  async function approvePackage() {
    if (!context) return;
    const next = await runAction("approval", () =>
      decideApproval({
        contextId: context.context_id,
        decision: "approve",
        reviewed_by: OPERATOR_ID,
        comment: "Approved from the agent operations workspace."
      })
    );
    if (next) {
      applyContext(next);
      await refreshWorkflows();
    }
  }

  async function executeApproved() {
    if (!context) return;
    const next = await runAction("execution", () =>
      executeWorkflow({
        contextId: context.context_id,
        run_by: OPERATOR_ID
      })
    );
    if (next) {
      applyContext(next);
      await Promise.all([
        refreshWorkflows(),
        refreshExecution(next.context_id)
      ]);
    }
  }

  async function downloadReport(
    format: "package" | "technical" | "executive"
  ) {
    if (!context) return;
    await runAction("download", () =>
      downloadWorkflowReport(context.context_id, format)
    );
  }

  async function sendMessage(message: string) {
    if (!context) return;
    const event = await runAction("message", () =>
      sendWorkflowMessage({
        contextId: context.context_id,
        actor: OPERATOR_ID,
        message
      })
    );
    if (event) {
      timelineCursor.current = Math.max(timelineCursor.current, event.sequence);
      setTimeline((current) => mergeEvents(current, [event]));
    }
  }

  async function sendCopilotMessage(message: string) {
    const session = chatSession ?? await runAction("chat", () =>
      createChatSession({
        created_by: OPERATOR_ID,
        context_id: context?.context_id ?? null,
        ticket_id: selectedTicket?.id ?? null,
        title: "AegisQA Copilot"
      })
    );
    if (!session) return;
    const response = await runAction("chat", () =>
      sendChatMessage({
        sessionId: session.session_id,
        actor: OPERATOR_ID,
        message,
        context_id: context?.context_id ?? null,
        ticket_id: selectedTicket?.id ?? null
      })
    );
    if (!response) return;
    setChatSession(response.session);
  }

  async function confirmCopilotAction(actionId: string) {
    if (!chatSession) return;
    const response = await runAction("chat", () =>
      confirmChatAction({
        sessionId: chatSession.session_id,
        actionId,
        actor: OPERATOR_ID
      })
    );
    if (!response) return;
    setChatSession(response.session);
    if (response.session.context_id) {
      const loaded = await getWorkflow(response.session.context_id).catch(() => null);
      if (loaded) {
        applyContext(loaded);
        await refreshWorkflows();
      }
    }
  }


  async function cancelCopilotAction(actionId: string) {
    if (!chatSession) return;
    const response = await runAction("chat", () =>
      cancelChatAction({
        sessionId: chatSession.session_id,
        actionId,
        actor: OPERATOR_ID
      })
    );
    if (!response) return;
    setChatSession(response.session);
  }

  async function saveArtifact(comment?: string) {
    if (!context || !selectedTest) return;
    const response = await runAction("artifact", () =>
      editAutomationArtifact({
        contextId: context.context_id,
        testCaseId: selectedTest.id,
        actor: OPERATOR_ID,
        content: artifactDraft,
        comment
      })
    );
    if (!response) return;
    applyContext(response.context);
    setArtifactContent(artifactDraft);
    setArtifactEditing(false);
    setArtifactRevisions((current) => [...current, response.revision]);
    await refreshWorkflows();
  }

  function updateAgentProvider(profile: AgentModelProfile, provider: string) {
    setAgentRoutes((current) => ({
      ...current,
      [profile.agent_name]: {
        provider,
        model: provider === "openai_compatible" ? profile.external_model : null
      }
    }));
    setSelectedLlmProvider(provider);
  }

  function updateAgentModel(profile: AgentModelProfile, model: string) {
    const recommendedProvider = llmProviders.find(
      (provider) =>
        provider.name === profile.recommended_provider
        && provider.name !== "mock_llm"
        && provider.selectable
    )?.name;
    const fallbackProvider = llmProviders.find(
      (provider) => provider.name !== "mock_llm" && provider.selectable
    )?.name ?? "";
    setAgentRoutes((current) => ({
      ...current,
      [profile.agent_name]: {
        provider: current[profile.agent_name]?.provider
          ?? recommendedProvider
          ?? fallbackProvider,
        model: model.trim() || null
      }
    }));
  }

  function applyRoutingPreset(preset: "external" | "local") {
    const externalReady = llmProviders.some(
      (provider) => provider.name === "openai_compatible" && provider.selectable
    );
    const localReady = Boolean(
      ollamaHealth?.available
      && ollamaHealth.chat_model_ready
      && llmProviders.some(
        (provider) => provider.name === "ollama" && provider.selectable
      )
    );
    const targetProvider = preset === "external"
      ? externalReady
        ? "openai_compatible"
        : localReady
          ? "ollama"
          : ""
      : localReady
        ? "ollama"
        : externalReady
          ? "openai_compatible"
          : "";
    const nextRoutes: Record<string, AgentModelRoute> = {};
    for (const profile of (agentRouting?.agents ?? []).filter((item) => item.uses_llm)) {
      if (!targetProvider) continue;
      nextRoutes[profile.agent_name] = {
        provider: targetProvider,
        model: targetProvider === "openai_compatible"
          ? profile.external_model
          : null
      };
    }
    setAgentRoutes(nextRoutes);
    setSelectedLlmProvider(targetProvider);
    if (!targetProvider) {
      setError("No real LLM provider is ready. Configure OpenAI-compatible access or start Ollama.");
    }
    const localEmbeddingReady = ollamaHealth?.available
      && ollamaHealth.embedding_model_ready;
    setSelectedEmbeddingProvider(
      localEmbeddingReady ? "ollama_nomic_embed_text" : "local_hash_embeddings"
    );
    setEmbeddingModel(
      localEmbeddingReady
        ? ollamaHealth.embedding_model
        : ""
    );
  }

  async function smokeTest() {
    const roles = ollamaProfiles?.profiles.map((profile) => profile.role) ?? null;
    await runAction("smoke", () => smokeTestOllamaProfiles({ roles }));
    const [health, profiles] = await Promise.all([
      getOllamaHealth().catch(() => null),
      getOllamaProfiles().catch(() => null)
    ]);
    if (health) setOllamaHealth(health);
    if (profiles) setOllamaProfiles(profiles);
  }

  return (
    <div className={`app-frame ${configCollapsed ? "config-collapsed" : ""}`}>
      <WorkspaceNav
        tickets={tickets}
        workflows={workflows}
        selectedContextId={context?.context_id ?? null}
        selectedTicketId={selectedTicketId}
        query={workspaceQuery}
        filter={workspaceFilter}
        busy={busy !== null}
        onQueryChange={setWorkspaceQuery}
        onFilterChange={setWorkspaceFilter}
        onSelectTicket={selectTicket}
        onOpenWorkflow={(contextId) => void openWorkflow(contextId)}
        onCreateWorkspace={() => void createWorkspace()}
        onRefresh={() => void refreshBootstrap()}
      />

      <div className="center-column">
        {error ? (
          <div className="global-error">
            <XCircle />
            <span>{error}</span>
            <button onClick={() => setError(null)} title="Dismiss error"><X /></button>
          </div>
        ) : null}
        <CopilotPanel
          session={chatSession}
          busy={busy === "chat"}
          disabled={false}
          onSend={(message) => void sendCopilotMessage(message)}
          onConfirmAction={(actionId) => void confirmCopilotAction(actionId)}
          onCancelAction={(actionId) => void cancelCopilotAction(actionId)}
        />
        <ConversationWorkspace
          context={context}
          selectedTicket={selectedTicket}
          timeline={timeline}
          view={view}
          selectedTestId={selectedTestId}
          artifactContent={artifactContent}
          artifactDraft={artifactDraft}
          artifactEditing={artifactEditing}
          artifactRevisions={artifactRevisions}
          executionRuns={executionRuns}
          executionEvents={executionEvents}
          reportPackage={reportPackage}
          busy={busy}
          configCollapsed={configCollapsed}
          onViewChange={setView}
          onSelectTest={setSelectedTestId}
          onOpenConfig={() => setConfigCollapsed(false)}
          onCreateWorkspace={() => void createWorkspace()}
          onResume={() => void resume()}
          onNext={() => void runNext()}
          onPause={() => void pause()}
          onReviewStage={(stage, decision, comment) => void reviewStage(stage, decision, comment)}
          onRegenerateStage={(stage, comment) => void regenerateStage(stage, comment)}
          onApproveWorkflow={() => void approvePackage()}
          onExecuteWorkflow={() => void executeApproved()}
          onSendMessage={(message) => void sendMessage(message)}
          onStartArtifactEdit={() => {
            setArtifactDraft(artifactContent);
            setArtifactEditing(true);
          }}
          onCancelArtifactEdit={() => {
            setArtifactDraft(artifactContent);
            setArtifactEditing(false);
          }}
          onArtifactDraftChange={setArtifactDraft}
          onSaveArtifact={(comment) => void saveArtifact(comment)}
          onDownloadReport={(format) => void downloadReport(format)}
        />
      </div>

      {!configCollapsed ? (
        <AgentConfigPanel
          routing={agentRouting}
          providers={llmProviders}
          embeddingProviders={embeddingProviders}
          routes={agentRoutes}
          mode={workflowMode}
          embeddingProvider={selectedEmbeddingProvider}
          embeddingModel={embeddingModel}
          providerCatalog={providerCatalog}
          integrationProfile={context?.integration_profile ?? null}
          ollamaHealth={ollamaHealth}
          governance={agentGovernance}
          observability={observability}
          tokenBudget={tokenBudget}
          operationalHealth={operationalHealth}
          smokeBusy={busy === "smoke"}
          onClose={() => setConfigCollapsed(true)}
          onModeChange={setWorkflowMode}
          onApplyPreset={applyRoutingPreset}
          onProviderChange={updateAgentProvider}
          onModelChange={updateAgentModel}
          onEmbeddingProviderChange={setSelectedEmbeddingProvider}
          onEmbeddingModelChange={setEmbeddingModel}
          onSmokeTest={() => void smokeTest()}
          onOpenLogs={() => setView("evidence")}
          onOpenMemory={() => setView("evidence")}
        />
      ) : null}
    </div>
  );
}

function mergeEvents(
  current: WorkflowEvent[],
  incoming: WorkflowEvent[]
): WorkflowEvent[] {
  const byId = new Map(current.map((event) => [event.id, event]));
  for (const event of incoming) byId.set(event.id, event);
  return [...byId.values()].sort((left, right) => left.sequence - right.sequence);
}
