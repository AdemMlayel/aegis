import type {
  AgentModelRoute,
  AgentRoutingCatalog,
  AgentGovernanceCatalog,
  ApprovalStatus,
  ArtifactRevision,
  EmbeddingProvider,
  ExecutionEvent,
  ExecutionRunRecord,
  ExecutionRunStatus,
  LLMProvider,
  OllamaHealth,
  OllamaModelProfiles,
  OllamaSmokeTestResult,
  ObservabilitySummary,
  OperationalHealth,
  ProviderCatalog,
  ReportPackageManifest,
  TestContext,
  TicketData,
  TicketStatus,
  TokenBudgetStatus,
  WorkflowEvent,
  WorkflowMode,
  WorkflowStageName,
  WorkflowSummary,
  ChatSession,
  ChatMessage,
  ChatAction
} from "./types";
import { API_ROOT } from "./config";

type IntelligenceConfigPayload = {
  llm_provider?: string;
  embedding_provider?: string;
  llm_model?: string | null;
  embedding_model?: string | null;
  agent_routes?: Record<string, AgentModelRoute>;
};

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail ?? response.statusText;
    throw new Error(Array.isArray(detail) ? detail[0]?.msg ?? response.statusText : String(detail));
  }
  return response.json() as Promise<T>;
}

export async function getProviderCatalog(): Promise<ProviderCatalog> {
  const response = await fetch(`${API_ROOT}/integrations/providers?include_external=true`);
  return parseResponse<ProviderCatalog>(response);
}

export async function getLLMProviders(): Promise<LLMProvider[]> {
  const response = await fetch(`${API_ROOT}/intelligence/llm-providers`);
  return parseResponse<LLMProvider[]>(response);
}

export async function getEmbeddingProviders(): Promise<EmbeddingProvider[]> {
  const response = await fetch(`${API_ROOT}/intelligence/embedding-providers`);
  return parseResponse<EmbeddingProvider[]>(response);
}

export async function getAgentModelProfiles(): Promise<AgentRoutingCatalog> {
  const response = await fetch(`${API_ROOT}/intelligence/agent-model-profiles`);
  return parseResponse<AgentRoutingCatalog>(response);
}

export async function getAgentGovernanceCatalog(): Promise<AgentGovernanceCatalog> {
  const response = await fetch(`${API_ROOT}/governance/agents`);
  return parseResponse<AgentGovernanceCatalog>(response);
}

export async function getObservabilitySummary(): Promise<ObservabilitySummary> {
  const response = await fetch(`${API_ROOT}/observability/summary`);
  return parseResponse<ObservabilitySummary>(response);
}

export async function getTokenBudgetStatus(): Promise<TokenBudgetStatus> {
  const response = await fetch(`${API_ROOT}/observability/token-budget`);
  return parseResponse<TokenBudgetStatus>(response);
}

export async function getOperationalHealth(): Promise<OperationalHealth> {
  const response = await fetch(`${API_ROOT}/observability/health`);
  return parseResponse<OperationalHealth>(response);
}

export async function getOllamaHealth(): Promise<OllamaHealth> {
  const response = await fetch(`${API_ROOT}/intelligence/ollama/health`);
  return parseResponse<OllamaHealth>(response);
}

export async function getOllamaProfiles(): Promise<OllamaModelProfiles> {
  const response = await fetch(`${API_ROOT}/intelligence/ollama/profiles`);
  return parseResponse<OllamaModelProfiles>(response);
}

export async function smokeTestOllamaProfiles(payload: {
  roles?: string[] | null;
  prompt?: string;
} = {}): Promise<OllamaSmokeTestResult[]> {
  const response = await fetch(`${API_ROOT}/intelligence/ollama/profiles/smoke-test`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      roles: payload.roles ?? null,
      prompt: payload.prompt ?? "Return only OK if this model is ready for AegisQA."
    })
  });
  const body = await parseResponse<{ results: OllamaSmokeTestResult[] }>(response);
  return body.results;
}

export async function listDemoTickets(payload: {
  query?: string;
  priority?: TicketData["priority"];
  status?: TicketStatus;
  assignee?: string;
  label?: string;
} = {}): Promise<TicketData[]> {
  const params = new URLSearchParams();
  if (payload.query) params.set("q", payload.query);
  if (payload.priority) params.set("priority", payload.priority);
  if (payload.status) params.set("status", payload.status);
  if (payload.assignee) params.set("assignee", payload.assignee);
  if (payload.label) params.set("label", payload.label);
  const response = await fetch(`${API_ROOT}/tickets/demo${params.toString() ? `?${params}` : ""}`);
  const body = await parseResponse<{ tickets: TicketData[] }>(response);
  return body.tickets;
}

export async function createWorkflowSession(payload: {
  created_by: string;
  ticket: TicketData;
  mode: WorkflowMode;
  intelligence?: IntelligenceConfigPayload;
}): Promise<TestContext> {
  const response = await fetch(`${API_ROOT}/workflows/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const body = await parseResponse<{ context: TestContext }>(response);
  return body.context;
}

export async function resumeWorkflowSession(payload: {
  contextId: string;
  actor: string;
}): Promise<TestContext> {
  const response = await fetch(`${API_ROOT}/workflows/${payload.contextId}/resume`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ actor: payload.actor })
  });
  const body = await parseResponse<{ context: TestContext }>(response);
  return body.context;
}

export async function runNextWorkflowStage(payload: {
  contextId: string;
  actor: string;
}): Promise<TestContext> {
  const response = await fetch(`${API_ROOT}/workflows/${payload.contextId}/next`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ actor: payload.actor })
  });
  const body = await parseResponse<{ context: TestContext }>(response);
  return body.context;
}

export async function pauseWorkflowSession(payload: {
  contextId: string;
  actor: string;
}): Promise<TestContext> {
  const response = await fetch(`${API_ROOT}/workflows/${payload.contextId}/pause`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ actor: payload.actor })
  });
  const body = await parseResponse<{ context: TestContext }>(response);
  return body.context;
}

export async function reviewWorkflowStage(payload: {
  contextId: string;
  stage: WorkflowStageName;
  decision: "approve" | "request_changes";
  reviewedBy: string;
  comment?: string;
}): Promise<TestContext> {
  const response = await fetch(
    `${API_ROOT}/workflows/${payload.contextId}/stages/${payload.stage}/review`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        decision: payload.decision,
        reviewed_by: payload.reviewedBy,
        comment: payload.comment || null
      })
    }
  );
  const body = await parseResponse<{ context: TestContext }>(response);
  return body.context;
}

export async function regenerateWorkflowStage(payload: {
  contextId: string;
  stage: WorkflowStageName;
  actor: string;
  comment: string;
}): Promise<TestContext> {
  const response = await fetch(
    `${API_ROOT}/workflows/${payload.contextId}/stages/${payload.stage}/regenerate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        actor: payload.actor,
        comment: payload.comment
      })
    }
  );
  const body = await parseResponse<{ context: TestContext }>(response);
  return body.context;
}

export async function listWorkflowTimeline(
  contextId: string,
  afterSequence = 0,
  limit = 200
): Promise<{ events: WorkflowEvent[]; next_sequence: number }> {
  const params = new URLSearchParams({
    after_sequence: String(afterSequence),
    limit: String(limit)
  });
  const response = await fetch(
    `${API_ROOT}/workflows/${contextId}/timeline?${params.toString()}`
  );
  return parseResponse<{ events: WorkflowEvent[]; next_sequence: number }>(response);
}

export async function sendWorkflowMessage(payload: {
  contextId: string;
  actor: string;
  message: string;
}): Promise<WorkflowEvent> {
  const response = await fetch(
    `${API_ROOT}/workflows/${payload.contextId}/timeline/messages`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ actor: payload.actor, message: payload.message })
    }
  );
  const body = await parseResponse<{ event: WorkflowEvent }>(response);
  return body.event;
}

export async function editAutomationArtifact(payload: {
  contextId: string;
  testCaseId: string;
  actor: string;
  content: string;
  comment?: string;
}): Promise<{ context: TestContext; revision: ArtifactRevision }> {
  const response = await fetch(
    `${API_ROOT}/workflows/${payload.contextId}/artifacts/${payload.testCaseId}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        actor: payload.actor,
        content: payload.content,
        comment: payload.comment || null
      })
    }
  );
  return parseResponse<{ context: TestContext; revision: ArtifactRevision }>(response);
}

export async function listArtifactRevisions(
  contextId: string,
  testCaseId: string
): Promise<ArtifactRevision[]> {
  const response = await fetch(
    `${API_ROOT}/workflows/${contextId}/artifacts/${testCaseId}/revisions`
  );
  const body = await parseResponse<{ revisions: ArtifactRevision[] }>(response);
  return body.revisions;
}

export async function getWorkflow(contextId: string): Promise<TestContext> {
  const response = await fetch(`${API_ROOT}/workflows/${contextId}`);
  const body = await parseResponse<{ context: TestContext }>(response);
  return body.context;
}

export async function getReportPackageManifest(
  contextId: string
): Promise<ReportPackageManifest> {
  const response = await fetch(
    `${API_ROOT}/workflows/${encodeURIComponent(contextId)}/package/manifest`
  );
  return parseResponse<ReportPackageManifest>(response);
}

export async function downloadWorkflowReport(
  contextId: string,
  format: "package" | "technical" | "executive"
): Promise<void> {
  const suffix = format === "package"
    ? "package.zip"
    : `package/${format}.md`;
  const response = await fetch(
    `${API_ROOT}/workflows/${encodeURIComponent(contextId)}/${suffix}`
  );
  if (!response.ok) {
    await parseResponse<never>(response);
    return;
  }
  const blob = await response.blob();
  const disposition = response.headers.get("Content-Disposition") ?? "";
  const fileName = disposition.match(/filename="([^"]+)"/)?.[1]
    ?? `aegisqa-${contextId}-${format}`;
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export async function listWorkflows(payload: {
  query?: string;
  approvalStatus?: ApprovalStatus;
  limit?: number;
} = {}): Promise<WorkflowSummary[]> {
  const params = new URLSearchParams();
  if (payload.query) params.set("q", payload.query);
  if (payload.approvalStatus) params.set("approval_status", payload.approvalStatus);
  if (payload.limit) params.set("limit", String(payload.limit));
  const response = await fetch(`${API_ROOT}/workflows${params.toString() ? `?${params}` : ""}`);
  const body = await parseResponse<{ workflows: WorkflowSummary[] }>(response);
  return body.workflows;
}

export async function decideApproval(payload: {
  contextId: string;
  decision: "approve" | "request_changes";
  reviewed_by: string;
  comment?: string;
}): Promise<TestContext> {
  const response = await fetch(`${API_ROOT}/workflows/${payload.contextId}/approval`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      decision: payload.decision,
      reviewed_by: payload.reviewed_by,
      comment: payload.comment || null
    })
  });
  const body = await parseResponse<{ context: TestContext }>(response);
  return body.context;
}

export async function executeWorkflow(payload: {
  contextId: string;
  run_by: string;
}): Promise<TestContext> {
  const response = await fetch(`${API_ROOT}/workflows/${payload.contextId}/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ run_by: payload.run_by })
  });
  const body = await parseResponse<{ context: TestContext }>(response);
  return body.context;
}

export async function listExecutionRuns(payload: {
  contextId?: string;
  status?: ExecutionRunStatus;
  limit?: number;
} = {}): Promise<ExecutionRunRecord[]> {
  const params = new URLSearchParams();
  if (payload.contextId) params.set("context_id", payload.contextId);
  if (payload.status) params.set("status", payload.status);
  if (payload.limit) params.set("limit", String(payload.limit));
  const response = await fetch(`${API_ROOT}/results${params.toString() ? `?${params}` : ""}`);
  const body = await parseResponse<{ runs: ExecutionRunRecord[] }>(response);
  return body.runs;
}

export async function listExecutionEvents(runId: string, limit = 200): Promise<ExecutionEvent[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  const response = await fetch(`${API_ROOT}/results/${encodeURIComponent(runId)}/logs?${params.toString()}`);
  const body = await parseResponse<{ events: ExecutionEvent[] }>(response);
  return body.events;
}

export async function getAutomationFile(ticketId: string, robotFile: string): Promise<string> {
  const fileName = robotFile.split("/").pop();
  if (!fileName) throw new Error("Robot file path is empty");
  const response = await fetch(`${API_ROOT}/automation/files/${encodeURIComponent(ticketId)}/${encodeURIComponent(fileName)}`);
  const body = await parseResponse<{ content: string }>(response);
  return body.content;
}


export async function createChatSession(payload: {
  created_by: string;
  context_id?: string | null;
  ticket_id?: string | null;
  title?: string | null;
}): Promise<ChatSession> {
  const response = await fetch(`${API_ROOT}/chat/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const body = await parseResponse<{ session: ChatSession }>(response);
  return body.session;
}

export async function listChatSessions(limit = 20): Promise<ChatSession[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  const response = await fetch(`${API_ROOT}/chat/sessions?${params.toString()}`);
  const body = await parseResponse<{ sessions: ChatSession[] }>(response);
  return body.sessions;
}

export async function sendChatMessage(payload: {
  sessionId: string;
  actor: string;
  message: string;
  context_id?: string | null;
  ticket_id?: string | null;
}): Promise<{ session: ChatSession; message: ChatMessage }> {
  const response = await fetch(`${API_ROOT}/chat/sessions/${payload.sessionId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      actor: payload.actor,
      message: payload.message,
      context_id: payload.context_id ?? null,
      ticket_id: payload.ticket_id ?? null
    })
  });
  return parseResponse<{ session: ChatSession; message: ChatMessage }>(response);
}

export async function confirmChatAction(payload: {
  sessionId: string;
  actionId: string;
  actor: string;
}): Promise<{ session: ChatSession; action: ChatAction; message: ChatMessage }> {
  const response = await fetch(
    `${API_ROOT}/chat/sessions/${payload.sessionId}/actions/${payload.actionId}/confirm`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ actor: payload.actor })
    }
  );
  return parseResponse<{ session: ChatSession; action: ChatAction; message: ChatMessage }>(response);
}

export async function cancelChatAction(payload: {
  sessionId: string;
  actionId: string;
  actor: string;
}): Promise<{ session: ChatSession; action: ChatAction; message: ChatMessage }> {
  const response = await fetch(
    `${API_ROOT}/chat/sessions/${payload.sessionId}/actions/${payload.actionId}/cancel`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ actor: payload.actor })
    }
  );
  return parseResponse<{ session: ChatSession; action: ChatAction; message: ChatMessage }>(response);
}
