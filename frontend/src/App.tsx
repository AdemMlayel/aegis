import {
  AlertTriangle,
  CheckCircle2,
  ClipboardCheck,
  ExternalLink,
  FileCode2,
  GitPullRequest,
  History,
  Loader2,
  Play,
  RefreshCw,
  RotateCcw,
  Search,
  ShieldCheck,
  XCircle
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { decideApproval, getAutomationFile, getWorkflow, startWorkflow } from "./api";
import type { AutomationBlock, TestCase, TestContext, TicketData } from "./types";

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
  if (status.includes("complete") || status === "approved") return "good";
  if (status.includes("blocked") || status.includes("failed")) return "bad";
  if (status.includes("pending") || status.includes("review")) return "warn";
  return "info";
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
  const canReview = approval?.status === "pending_review";

  const validationCounts = useMemo(() => {
    const automation = Object.values(context?.automation ?? {});
    return {
      total: automation.length,
      passed: automation.filter((item) => item.validation.dry_run_passed === true).length,
      failed: automation.filter((item) => item.validation.dry_run_passed === false).length
    };
  }, [context]);

  useEffect(() => {
    const storedContextId = localStorage.getItem("aegisqa:lastContextId");
    if (storedContextId) {
      setLoadId(storedContextId);
    }
  }, []);

  useEffect(() => {
    if (!context || selectedTestId) return;
    setSelectedTestId(context.test_cases[0]?.id ?? "");
  }, [context, selectedTestId]);

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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Workflow start failed");
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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Review action failed");
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
