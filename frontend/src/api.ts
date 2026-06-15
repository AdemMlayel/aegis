import type { ApprovalStatus, TestContext, TicketData, WorkflowSummary } from "./types";

const API_ROOT = "/api/v1";

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail ?? response.statusText;
    throw new Error(Array.isArray(detail) ? detail[0]?.msg ?? response.statusText : detail);
  }
  return response.json() as Promise<T>;
}

export async function startWorkflow(payload: {
  created_by: string;
  ticket: TicketData;
}): Promise<TestContext> {
  const response = await fetch(`${API_ROOT}/workflows/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const body = await parseResponse<{ context: TestContext }>(response);
  return body.context;
}

export async function listMockTickets(payload: {
  query?: string;
  priority?: TicketData["priority"];
} = {}): Promise<TicketData[]> {
  const params = new URLSearchParams();
  if (payload.query) params.set("q", payload.query);
  if (payload.priority) params.set("priority", payload.priority);
  const suffix = params.toString();
  const response = await fetch(`${API_ROOT}/tickets/mock${suffix ? `?${suffix}` : ""}`);
  const body = await parseResponse<{ tickets: TicketData[] }>(response);
  return body.tickets;
}

export async function startWorkflowFromMockTicket(payload: {
  created_by: string;
  ticket_id: string;
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
  const suffix = params.toString();
  const response = await fetch(`${API_ROOT}/workflows${suffix ? `?${suffix}` : ""}`);
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

export async function getAutomationFile(ticketId: string, robotFile: string): Promise<string> {
  const fileName = robotFile.split("/").pop();
  if (!fileName) {
    throw new Error("Robot file path is empty");
  }
  const response = await fetch(
    `${API_ROOT}/automation/files/${encodeURIComponent(ticketId)}/${encodeURIComponent(fileName)}`
  );
  const body = await parseResponse<{ content: string }>(response);
  return body.content;
}
