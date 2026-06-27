import {
  Archive,
  CheckCircle2,
  CircleDashed,
  Clock3,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  TriangleAlert
} from "lucide-react";
import { useMemo } from "react";
import type { TicketData, WorkflowSummary } from "../types";

export type WorkspaceFilter = "all" | "active" | "approval" | "completed" | "failed";

type WorkspaceItem = {
  key: string;
  ticketId: string;
  title: string;
  status: string;
  category: Exclude<WorkspaceFilter, "all">;
  updatedAt?: string;
  progress: number;
  contextId?: string;
};

export function WorkspaceNav({
  tickets,
  workflows,
  selectedContextId,
  selectedTicketId,
  query,
  filter,
  busy,
  onQueryChange,
  onFilterChange,
  onSelectTicket,
  onOpenWorkflow,
  onCreateWorkspace,
  onRefresh
}: {
  tickets: TicketData[];
  workflows: WorkflowSummary[];
  selectedContextId: string | null;
  selectedTicketId: string;
  query: string;
  filter: WorkspaceFilter;
  busy: boolean;
  onQueryChange: (value: string) => void;
  onFilterChange: (value: WorkspaceFilter) => void;
  onSelectTicket: (ticketId: string) => void;
  onOpenWorkflow: (contextId: string) => void;
  onCreateWorkspace: () => void;
  onRefresh: () => void;
}) {
  const items = useMemo(
    () => buildWorkspaceItems(tickets, workflows),
    [tickets, workflows]
  );
  const visibleItems = items.filter((item) => {
    const needle = query.trim().toLowerCase();
    const matchesQuery = !needle
      || `${item.ticketId} ${item.title} ${item.status}`.toLowerCase().includes(needle);
    return matchesQuery && (filter === "all" || item.category === filter);
  });

  return (
    <aside className="workspace-nav">
      <div className="brand-lockup">
        <span className="brand-mark"><ShieldCheck /></span>
        <div>
          <strong>AegisQA</strong>
          <span>Agent operations</span>
        </div>
      </div>

      <button className="command-button primary" onClick={onCreateWorkspace} disabled={busy}>
        <Plus /> New workspace
      </button>

      <div className="search-field">
        <Search />
        <input
          aria-label="Search workspaces"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Search tickets"
        />
      </div>

      <div className="filter-strip" aria-label="Workspace filters">
        {([
          ["all", "All"],
          ["active", "Active"],
          ["approval", "Review"],
          ["completed", "Done"],
          ["failed", "Failed"]
        ] as Array<[WorkspaceFilter, string]>).map(([value, label]) => (
          <button
            key={value}
            className={filter === value ? "active" : ""}
            onClick={() => onFilterChange(value)}
            type="button"
          >
            {label}
          </button>
        ))}
      </div>

      <div className="workspace-list" aria-label="Test case workspaces">
        {visibleItems.map((item) => {
          const selected = item.contextId
            ? item.contextId === selectedContextId
            : !selectedContextId && item.ticketId === selectedTicketId;
          const Icon = statusIcon(item.category);
          return (
            <button
              type="button"
              className={`workspace-row ${selected ? "selected" : ""}`}
              key={item.key}
              onClick={() => {
                onSelectTicket(item.ticketId);
                if (item.contextId) onOpenWorkflow(item.contextId);
              }}
            >
              <span className={`workspace-status ${item.category}`}><Icon /></span>
              <span className="workspace-copy">
                <span className="workspace-ticket">{item.ticketId}</span>
                <strong>{item.title}</strong>
                <span className="workspace-meta">
                  {humanStatus(item.status)}
                  {item.updatedAt ? ` - ${relativeTime(item.updatedAt)}` : ""}
                </span>
                <span className="progress-track">
                  <span style={{ width: `${item.progress}%` }} />
                </span>
              </span>
            </button>
          );
        })}
        {!visibleItems.length ? (
          <div className="nav-empty">
            <Archive />
            <span>No matching workspaces</span>
          </div>
        ) : null}
      </div>

      <div className="nav-footer">
        <button className="icon-command" onClick={onRefresh} disabled={busy} title="Refresh workspaces">
          <RefreshCw className={busy ? "spin" : ""} />
        </button>
        <span>{items.length} workspaces</span>
      </div>
    </aside>
  );
}

function buildWorkspaceItems(
  tickets: TicketData[],
  workflows: WorkflowSummary[]
): WorkspaceItem[] {
  const latestByTicket = new Map<string, WorkflowSummary>();
  for (const workflow of workflows) {
    if (!workflow.ticket_id || latestByTicket.has(workflow.ticket_id)) continue;
    latestByTicket.set(workflow.ticket_id, workflow);
  }

  const items: WorkspaceItem[] = workflows.map((workflow) => {
    const category = workflowCategory(workflow);
    return {
      key: workflow.context_id,
      ticketId: workflow.ticket_id ?? "UNTITLED",
      title: workflow.ticket_title ?? "Untitled workflow",
      status: workflow.approval_status === "pending_review"
        ? "waiting approval"
        : workflow.execution_status ?? workflow.workflow_status,
      category,
      updatedAt: workflow.updated_at,
      progress: workflowProgress(workflow),
      contextId: workflow.context_id
    };
  });

  for (const ticket of tickets) {
    if (latestByTicket.has(ticket.id)) continue;
    items.push({
      key: `ticket:${ticket.id}`,
      ticketId: ticket.id,
      title: ticket.title,
      status: ticket.status ?? "ready",
      category: "active",
      updatedAt: ticket.updated_at ?? ticket.last_updated_date,
      progress: 4
    });
  }
  return items;
}

function workflowCategory(workflow: WorkflowSummary): Exclude<WorkspaceFilter, "all"> {
  if (
    workflow.execution_status === "failed"
    || workflow.execution_status === "blocked"
    || workflow.workflow_status.includes("failed")
    || workflow.workflow_status.includes("blocked")
  ) return "failed";
  if (workflow.approval_status === "pending_review") return "approval";
  if (
    workflow.workflow_status.includes("completed")
    || workflow.workflow_status === "report_generated"
    || workflow.approval_status === "approved"
  ) return "completed";
  return "active";
}

function workflowProgress(workflow: WorkflowSummary): number {
  if (workflow.execution_status && workflow.execution_status !== "skipped") return 100;
  if (workflow.approval_status === "approved") return 94;
  if (workflow.approval_status === "pending_review") return 78;
  if (workflow.automation_revision > 0) return 66;
  if (workflow.test_count > 0) return 48;
  return 18;
}

function statusIcon(category: Exclude<WorkspaceFilter, "all">) {
  if (category === "completed") return CheckCircle2;
  if (category === "approval") return Clock3;
  if (category === "failed") return TriangleAlert;
  return CircleDashed;
}

function humanStatus(value: string): string {
  return value.replaceAll("_", " ");
}

function relativeTime(value: string): string {
  const elapsed = Date.now() - new Date(value).getTime();
  if (!Number.isFinite(elapsed) || elapsed < 0) return "just now";
  const minutes = Math.floor(elapsed / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}
