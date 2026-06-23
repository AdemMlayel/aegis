import type {
  ApprovalStatus,
  EmbeddingProvider,
  ExecuteRunResponse,
  ExecutionEvent,
  ExecutionRunRecord,
  ExecutionRunRequest,
  ExecutionRunStatus,
  LLMProvider,
  OllamaHealth,
  ProviderCatalog,
  TestContext,
  TicketData,
  TicketStatus,
  WorkflowSummary
} from "./types";

type IntelligenceConfigPayload = {
  llm_provider?: string;
  embedding_provider?: string;
  llm_model?: string | null;
  embedding_model?: string | null;
};

const API_ROOT = "/api/v1";

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

export async function getOllamaHealth(): Promise<OllamaHealth> {
  const response = await fetch(`${API_ROOT}/intelligence/ollama/health`);
  return parseResponse<OllamaHealth>(response);
}

export async function listMockTickets(payload: {
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
  const response = await fetch(`${API_ROOT}/tickets/mock${params.toString() ? `?${params}` : ""}`);
  const body = await parseResponse<{ tickets: TicketData[] }>(response);
  return body.tickets;
}

export async function startWorkflowFromMockTicket(payload: {
  created_by: string;
  ticket_id: string;
  intelligence?: IntelligenceConfigPayload;
}): Promise<TestContext> {
  const response = await fetch(`${API_ROOT}/workflows/start-from-mock-ticket`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const body = await parseResponse<{ context: TestContext }>(response);
  return body.context;
}

export async function getWorkflow(contextId: string): Promise<TestContext> {
  const response = await fetch(`${API_ROOT}/workflows/${contextId}`);
  const body = await parseResponse<{ context: TestContext }>(response);
  return body.context;
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

export async function executeSuite(payload: ExecutionRunRequest): Promise<ExecuteRunResponse> {
  const response = await fetch(`${API_ROOT}/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return parseResponse<ExecuteRunResponse>(response);
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
