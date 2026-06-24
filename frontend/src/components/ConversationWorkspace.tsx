import {
  Activity,
  Bot,
  Check,
  CheckCircle2,
  ChevronRight,
  CircleDashed,
  Clock3,
  Code2,
  FileCheck2,
  FileText,
  Gauge,
  GitCompareArrows,
  Loader2,
  MessageSquare,
  PanelRightOpen,
  Pause,
  Play,
  RotateCcw,
  Save,
  Send,
  ShieldCheck,
  Sparkles,
  TestTube2,
  TriangleAlert,
  X
} from "lucide-react";
import { useMemo, useState } from "react";
import {
  lineDiffSummary,
  RobotCodeView,
  RobotDiffView
} from "./RobotArtifactViewer";
import type {
  ArtifactRevision,
  ExecutionEvent,
  ExecutionRunRecord,
  TestCase,
  TestContext,
  WorkflowEvent,
  WorkflowStageName
} from "../types";

export type WorkspaceView =
  | "conversation"
  | "tests"
  | "artifacts"
  | "validation"
  | "evidence";

const STAGES: Array<{ name: WorkflowStageName; label: string }> = [
  { name: "ticket", label: "Ticket" },
  { name: "requirements", label: "Requirements" },
  { name: "coverage", label: "Coverage" },
  { name: "tests", label: "Tests" },
  { name: "automation", label: "Automation" },
  { name: "validation", label: "Validation" },
  { name: "approval", label: "Approval" },
  { name: "report", label: "Report" }
];

export function ConversationWorkspace({
  context,
  timeline,
  view,
  selectedTestId,
  artifactContent,
  artifactDraft,
  artifactEditing,
  artifactRevisions,
  executionRuns,
  executionEvents,
  busy,
  configCollapsed,
  onViewChange,
  onSelectTest,
  onOpenConfig,
  onCreateWorkspace,
  onResume,
  onNext,
  onPause,
  onReviewStage,
  onRegenerateStage,
  onApproveWorkflow,
  onExecuteWorkflow,
  onSendMessage,
  onStartArtifactEdit,
  onCancelArtifactEdit,
  onArtifactDraftChange,
  onSaveArtifact
}: {
  context: TestContext | null;
  timeline: WorkflowEvent[];
  view: WorkspaceView;
  selectedTestId: string;
  artifactContent: string;
  artifactDraft: string;
  artifactEditing: boolean;
  artifactRevisions: ArtifactRevision[];
  executionRuns: ExecutionRunRecord[];
  executionEvents: ExecutionEvent[];
  busy: string | null;
  configCollapsed: boolean;
  onViewChange: (view: WorkspaceView) => void;
  onSelectTest: (testId: string) => void;
  onOpenConfig: () => void;
  onCreateWorkspace: () => void;
  onResume: () => void;
  onNext: () => void;
  onPause: () => void;
  onReviewStage: (
    stage: WorkflowStageName,
    decision: "approve" | "request_changes",
    comment?: string
  ) => void;
  onRegenerateStage: (stage: WorkflowStageName, comment: string) => void;
  onApproveWorkflow: () => void;
  onExecuteWorkflow: () => void;
  onSendMessage: (message: string) => void;
  onStartArtifactEdit: () => void;
  onCancelArtifactEdit: () => void;
  onArtifactDraftChange: (value: string) => void;
  onSaveArtifact: (comment?: string) => void;
}) {
  const [message, setMessage] = useState("");
  const [reviewComment, setReviewComment] = useState("");
  const [artifactComment, setArtifactComment] = useState("");
  const pendingReview = pendingStageReview(context);
  const selectedTest = context?.test_cases.find((test) => test.id === selectedTestId)
    ?? context?.test_cases[0]
    ?? null;

  if (!context) {
    return (
      <main className="operations-workspace empty-workspace">
        <div className="empty-workspace-content">
          <span className="empty-workspace-icon"><Bot /></span>
          <h1>Choose a ticket workspace</h1>
          <p>Create a controlled session to begin requirement analysis, coverage planning, and automation.</p>
          <button className="command-button primary" onClick={onCreateWorkspace}>
            <Play /> Start selected ticket
          </button>
        </div>
      </main>
    );
  }

  const control = context.workflow_control;
  const displayEvents = timeline.length ? timeline : eventsFromTrace(context);

  return (
    <main className="operations-workspace">
      <header className="workspace-header">
        <div className="workspace-heading">
          <div className="workspace-title-row">
            <span className="ticket-key">{context.ticket?.id ?? "UNTITLED"}</span>
            <StatusPill value={control.state} />
          </div>
          <h1>{context.ticket?.title ?? "Untitled workflow"}</h1>
          <p>{context.ticket?.description || "No ticket description available."}</p>
        </div>
        <div className="workspace-header-actions">
          <WorkflowControls
            context={context}
            busy={busy}
            onResume={onResume}
            onNext={onNext}
            onPause={onPause}
            onApprove={onApproveWorkflow}
            onExecute={onExecuteWorkflow}
          />
          {configCollapsed ? (
            <button className="icon-command" onClick={onOpenConfig} title="Open agent configuration">
              <PanelRightOpen />
            </button>
          ) : null}
        </div>
      </header>

      <AgentActivityRail context={context} timeline={displayEvents} />

      <nav className="workspace-tabs" aria-label="Workspace views">
        <TabButton active={view === "conversation"} icon={<MessageSquare />} label="Activity" onClick={() => onViewChange("conversation")} />
        <TabButton active={view === "tests"} icon={<TestTube2 />} label={`Tests ${context.test_cases.length || ""}`} onClick={() => onViewChange("tests")} />
        <TabButton active={view === "artifacts"} icon={<Code2 />} label="Artifacts" onClick={() => onViewChange("artifacts")} />
        <TabButton active={view === "validation"} icon={<Gauge />} label="Validation" onClick={() => onViewChange("validation")} />
        <TabButton active={view === "evidence"} icon={<FileText />} label="Evidence" onClick={() => onViewChange("evidence")} />
      </nav>

      {view === "conversation" ? (
        <section className="conversation-view">
          <OperationalSummary context={context} timeline={displayEvents} />

          {pendingReview ? (
            <ApprovalRequest
              stage={pendingReview}
              comment={reviewComment}
              busy={busy !== null}
              onCommentChange={setReviewComment}
              onApprove={() => {
                onReviewStage(pendingReview, "approve", reviewComment);
                setReviewComment("");
              }}
              onRequestChanges={() => {
                if (!reviewComment.trim()) return;
                onReviewStage(pendingReview, "request_changes", reviewComment);
                setReviewComment("");
              }}
              onRegenerate={() => {
                if (!reviewComment.trim()) return;
                onRegenerateStage(pendingReview, reviewComment);
                setReviewComment("");
              }}
            />
          ) : null}

          <div className="conversation-stream">
            {displayEvents.map((event) => (
              <TimelineEntry event={event} key={`${event.sequence}-${event.id}`} />
            ))}
            {!displayEvents.length ? (
              <div className="conversation-empty">
                <CircleDashed />
                <span>No operational events yet. Start or resume the workflow.</span>
              </div>
            ) : null}
          </div>

          <LatestDeliverable
            context={context}
            onOpenArtifacts={() => onViewChange("artifacts")}
          />

          <form
            className="message-composer"
            onSubmit={(event) => {
              event.preventDefault();
              if (!message.trim()) return;
              onSendMessage(message.trim());
              setMessage("");
            }}
          >
            <textarea
              aria-label="Message the workflow"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Add guidance or a decision note to this workspace..."
              rows={2}
            />
            <button className="composer-send" type="submit" disabled={!message.trim() || busy !== null} title="Send message">
              <Send />
            </button>
          </form>
        </section>
      ) : null}

      {view === "tests" ? (
        <TestCaseWorkspace
          tests={context.test_cases}
          selectedTest={selectedTest}
          onSelect={onSelectTest}
        />
      ) : null}

      {view === "artifacts" ? (
        <ArtifactWorkspace
          context={context}
          selectedTest={selectedTest}
          artifactContent={artifactContent}
          draft={artifactDraft}
          editing={artifactEditing}
          revisions={artifactRevisions}
          comment={artifactComment}
          busy={busy !== null}
          onSelectTest={onSelectTest}
          onStartEdit={onStartArtifactEdit}
          onCancelEdit={() => {
            setArtifactComment("");
            onCancelArtifactEdit();
          }}
          onDraftChange={onArtifactDraftChange}
          onCommentChange={setArtifactComment}
          onSave={() => {
            onSaveArtifact(artifactComment.trim() || undefined);
            setArtifactComment("");
          }}
          onReviewAutomation={(comment) => {
            onReviewStage("automation", "approve", comment);
          }}
          onRegenerateAutomation={(comment) => {
            onRegenerateStage("automation", comment);
          }}
        />
      ) : null}

      {view === "validation" ? (
        <ValidationWorkspace
          context={context}
          timeline={displayEvents}
          busy={busy !== null}
          onApprove={(comment) => onReviewStage("validation", "approve", comment)}
          onRequestChanges={(comment) => onReviewStage("validation", "request_changes", comment)}
          onRegenerate={(comment) => onRegenerateStage("validation", comment)}
          onEditArtifacts={() => onViewChange("artifacts")}
        />
      ) : null}

      {view === "evidence" ? (
        <EvidenceWorkspace
          context={context}
          executionRuns={executionRuns}
          executionEvents={executionEvents}
        />
      ) : null}
    </main>
  );
}

function WorkflowControls({
  context,
  busy,
  onResume,
  onNext,
  onPause,
  onApprove,
  onExecute
}: {
  context: TestContext;
  busy: string | null;
  onResume: () => void;
  onNext: () => void;
  onPause: () => void;
  onApprove: () => void;
  onExecute: () => void;
}) {
  const control = context.workflow_control;
  const running = busy === "resume" || busy === "next";
  if (context.approval?.status === "approved") {
    return (
      <button className="command-button primary" onClick={onExecute} disabled={busy !== null}>
        {busy === "execution" ? <Loader2 className="spin" /> : <Activity />} Execute
      </button>
    );
  }
  if (context.approval?.status === "pending_review" && control.state === "completed") {
    return (
      <button className="command-button primary" onClick={onApprove} disabled={busy !== null}>
        {busy === "approval" ? <Loader2 className="spin" /> : <ShieldCheck />} Approve package
      </button>
    );
  }
  if (control.state === "running") {
    return (
      <button className="command-button secondary" onClick={onPause} disabled={busy === "pause"}>
        <Pause /> Pause
      </button>
    );
  }
  if (control.state === "waiting_review") {
    return <span className="waiting-label"><Clock3 /> Review required</span>;
  }
  if (control.state === "completed") {
    return <span className="waiting-label complete"><CheckCircle2 /> Workflow complete</span>;
  }
  if (control.mode === "step_by_step") {
    return (
      <button className="command-button primary" onClick={onNext} disabled={busy !== null}>
        {running ? <Loader2 className="spin" /> : <Play />} Run next stage
      </button>
    );
  }
  return (
    <button className="command-button primary" onClick={onResume} disabled={busy !== null}>
      {running ? <Loader2 className="spin" /> : <Play />} Resume workflow
    </button>
  );
}

function AgentActivityRail({
  context,
  timeline
}: {
  context: TestContext;
  timeline: WorkflowEvent[];
}) {
  const latestByStage = new Map<WorkflowStageName, WorkflowEvent>();
  for (const event of timeline) {
    if (event.stage) latestByStage.set(event.stage, event);
  }
  return (
    <section className="activity-rail" aria-label="Agent activity timeline">
      {STAGES.map((stage) => {
        const state = stageState(context, stage.name);
        const event = latestByStage.get(stage.name);
        const Icon = state === "completed"
          ? Check
          : state === "active"
            ? Activity
            : state === "blocked"
              ? TriangleAlert
              : CircleDashed;
        return (
          <div className={`activity-step ${state}`} key={stage.name}>
            <span className="activity-icon"><Icon /></span>
            <span className="activity-copy">
              <strong>{stage.label}</strong>
              <small>{activityDetail(context, stage.name, event)}</small>
            </span>
          </div>
        );
      })}
    </section>
  );
}

function OperationalSummary({
  context,
  timeline
}: {
  context: TestContext;
  timeline: WorkflowEvent[];
}) {
  const latest = timeline.at(-1);
  const activeStage = context.workflow_control.current_stage
    ?? context.workflow_control.next_stage
    ?? context.workflow_control.completed_stages.at(-1)
    ?? "ticket";
  return (
    <section className="operational-summary">
      <div className="summary-agent">
        <span><Sparkles /></span>
        <div>
          <span className="summary-label">Operational summary</span>
          <strong>{stageLabel(activeStage)}</strong>
        </div>
      </div>
      <dl>
        <div>
          <dt>Current task</dt>
          <dd>{latest?.message ?? "Ready to begin controlled execution."}</dd>
        </div>
        <div>
          <dt>Inputs</dt>
          <dd>{summaryInputs(context, activeStage)}</dd>
        </div>
        <div>
          <dt>Progress</dt>
          <dd>{context.workflow_control.completed_stages.length} of {STAGES.length} stages</dd>
        </div>
        <div>
          <dt>Mode</dt>
          <dd>{context.workflow_control.mode.replaceAll("_", " ")}</dd>
        </div>
      </dl>
    </section>
  );
}

function ApprovalRequest({
  stage,
  comment,
  busy,
  onCommentChange,
  onApprove,
  onRequestChanges,
  onRegenerate
}: {
  stage: WorkflowStageName;
  comment: string;
  busy: boolean;
  onCommentChange: (value: string) => void;
  onApprove: () => void;
  onRequestChanges: () => void;
  onRegenerate: () => void;
}) {
  return (
    <section className="approval-request">
      <div className="approval-heading">
        <span><ShieldCheck /></span>
        <div>
          <span className="summary-label">Human review</span>
          <h2>{stageLabel(stage)} deliverable is ready</h2>
          <p>Approve the current revision or add specific direction before regeneration.</p>
        </div>
      </div>
      <textarea
        rows={2}
        value={comment}
        onChange={(event) => onCommentChange(event.target.value)}
        placeholder="Optional approval note, or required change request..."
      />
      <div className="approval-actions">
        <button className="command-button primary" onClick={onApprove} disabled={busy}>
          <Check /> Approve
        </button>
        <button className="command-button secondary" onClick={onRequestChanges} disabled={busy || !comment.trim()}>
          <X /> Request changes
        </button>
        <button className="icon-command" onClick={onRegenerate} disabled={busy || !comment.trim()} title="Regenerate this stage">
          <RotateCcw />
        </button>
      </div>
    </section>
  );
}

function TimelineEntry({ event }: { event: WorkflowEvent }) {
  const userMessage = event.kind === "message";
  const Icon = event.kind === "error"
    ? TriangleAlert
    : event.kind === "review"
      ? ShieldCheck
      : event.kind === "artifact"
        ? Code2
        : event.kind === "message"
          ? MessageSquare
          : Bot;
  return (
    <article className={`timeline-entry ${userMessage ? "user-entry" : ""}`}>
      <span className="timeline-avatar"><Icon /></span>
      <div className="timeline-body">
        <div className="timeline-meta">
          <strong>{userMessage ? event.actor : event.stage ? `${stageLabel(event.stage)} agent` : "Aegis orchestrator"}</strong>
          <span>{formatTime(event.created_at)}</span>
        </div>
        <p>{event.message}</p>
        {event.status ? <span className={`event-status ${event.status}`}>{event.status.replaceAll("_", " ")}</span> : null}
        {event.metadata.duration_ms ? (
          <small>{String(event.metadata.duration_ms)} ms</small>
        ) : null}
      </div>
    </article>
  );
}

function LatestDeliverable({
  context,
  onOpenArtifacts
}: {
  context: TestContext;
  onOpenArtifacts: () => void;
}) {
  if (context.reports) {
    return (
      <section className="deliverable-block">
        <div className="deliverable-title"><FileCheck2 /><h2>Final report</h2></div>
        <p>{context.reports.summary}</p>
        <div className="deliverable-metrics">
          <Metric label="Tests" value={String(context.reports.total_test_cases)} />
          <Metric label="Risk" value={context.reports.highest_risk} />
          <Metric label="Confidence" value={`${Math.round(context.reports.confidence * 100)}%`} />
        </div>
      </section>
    );
  }
  if (context.validation_summary) {
    const summary = context.validation_summary;
    return (
      <section className="deliverable-block">
        <div className="deliverable-title"><Gauge /><h2>Validation gate</h2></div>
        <p>
          Quality score {summary.quality_score}/100 with{" "}
          {summary.passed_artifacts}/{summary.total_artifacts} artifacts passing.
        </p>
        <div className="deliverable-metrics">
          <Metric label="Coverage" value={`${summary.requirement_coverage_percent}%`} />
          <Metric label="Artifacts" value={`${summary.artifact_pass_percent}%`} />
          <Metric label="Status" value={summary.status} />
        </div>
      </section>
    );
  }
  const automationBlocks = Object.values(context.automation);
  if (automationBlocks.length) {
    const validated = automationBlocks.filter(
      (block) => block.validation.dry_run_passed === true
    ).length;
    return (
      <section className="deliverable-block">
        <div className="deliverable-title"><Code2 /><h2>Automation scripts</h2></div>
        <p>
          {automationBlocks.length} Robot Framework artifact
          {automationBlocks.length === 1 ? "" : "s"} generated and ready for review.
        </p>
        <div className="deliverable-metrics">
          <Metric label="Files" value={String(automationBlocks.length)} />
          <Metric label="Validated" value={`${validated}/${automationBlocks.length}`} />
          <Metric label="Revision" value={`v${context.automation_revision}`} />
        </div>
        <button className="command-button secondary" onClick={onOpenArtifacts}>
          <GitCompareArrows /> Review scripts
        </button>
      </section>
    );
  }
  if (context.coverage_plan) {
    return (
      <section className="deliverable-block">
        <div className="deliverable-title"><ShieldCheck /><h2>Coverage plan</h2></div>
        <div className="deliverable-metrics">
          <Metric label="Risk" value={context.coverage_plan.risk_level} />
          <Metric label="Criticality" value={`${context.coverage_plan.business_criticality}/10`} />
          <Metric label="Scenarios" value={String(context.test_cases.length)} />
        </div>
        <BulletList items={context.coverage_plan.risk_rationale} />
      </section>
    );
  }
  if (context.requirement_analysis) {
    return (
      <section className="deliverable-block">
        <div className="deliverable-title"><FileText /><h2>Requirement analysis</h2></div>
        <p>{context.requirement_analysis.llm_summary}</p>
        <BulletList items={context.requirement_analysis.expected_results} />
      </section>
    );
  }
  return null;
}

function TestCaseWorkspace({
  tests,
  selectedTest,
  onSelect
}: {
  tests: TestCase[];
  selectedTest: TestCase | null;
  onSelect: (testId: string) => void;
}) {
  return (
    <section className="split-workspace">
      <div className="item-index">
        <div className="view-heading">
          <div><span className="panel-kicker">Generated output</span><h2>Test scenarios</h2></div>
          <span className="count-badge">{tests.length}</span>
        </div>
        {tests.map((test) => (
          <button
            className={selectedTest?.id === test.id ? "selected" : ""}
            key={test.id}
            onClick={() => onSelect(test.id)}
          >
            <span>{test.id}</span>
            <strong>{test.title}</strong>
            <small>{test.type} - {test.priority}</small>
          </button>
        ))}
      </div>
      <div className="item-detail">
        {selectedTest ? (
          <>
            <div className="detail-title">
              <div><span className="panel-kicker">{selectedTest.id}</span><h2>{selectedTest.title}</h2></div>
              <StatusPill value={selectedTest.priority} />
            </div>
            <DetailSection title="Preconditions" items={selectedTest.preconditions} />
            <DetailSection title="Steps" items={selectedTest.steps} ordered />
            <section className="expected-output">
              <span>Expected outcome</span>
              <p>{selectedTest.expected_outcome}</p>
            </section>
            <DetailSection title="Evidence" items={[...selectedTest.evidence_refs, ...selectedTest.memory_refs]} />
            <DetailSection title="Generation notes" items={selectedTest.generation_notes} />
          </>
        ) : <EmptyView icon={<TestTube2 />} text="Test scenarios appear after the tests stage." />}
      </div>
    </section>
  );
}

function ArtifactWorkspace({
  context,
  selectedTest,
  artifactContent,
  draft,
  editing,
  revisions,
  comment,
  busy,
  onSelectTest,
  onStartEdit,
  onCancelEdit,
  onDraftChange,
  onCommentChange,
  onSave,
  onReviewAutomation,
  onRegenerateAutomation
}: {
  context: TestContext;
  selectedTest: TestCase | null;
  artifactContent: string;
  draft: string;
  editing: boolean;
  revisions: ArtifactRevision[];
  comment: string;
  busy: boolean;
  onSelectTest: (testId: string) => void;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  onDraftChange: (value: string) => void;
  onCommentChange: (value: string) => void;
  onSave: () => void;
  onReviewAutomation: (comment?: string) => void;
  onRegenerateAutomation: (comment: string) => void;
}) {
  const [sourceView, setSourceView] = useState<"source" | "diff">("source");
  const [selectedRevisionVersion, setSelectedRevisionVersion] = useState<number | null>(null);
  const [reviewComment, setReviewComment] = useState("");
  const block = selectedTest ? context.automation[selectedTest.id] : null;
  const selectedRevision = selectedRevisionVersion === null
    ? null
    : revisions.find((revision) => revision.version === selectedRevisionVersion) ?? null;
  const selectedRevisionIndex = selectedRevision
    ? revisions.findIndex((revision) => revision.id === selectedRevision.id)
    : -1;
  const previousRevision = selectedRevisionIndex > 0
    ? revisions[selectedRevisionIndex - 1]
    : null;
  const baseline = editing
    ? artifactContent
    : previousRevision?.content ?? selectedRevision?.content ?? artifactContent;
  const comparison = editing
    ? draft
    : selectedRevision?.content ?? artifactContent;
  const diff = lineDiffSummary(baseline, draft);
  const automationReview = context.workflow_control.stage_reviews.automation;
  const automationReviewPending = (
    context.workflow_control.state === "waiting_review"
    && automationReview?.status === "pending"
  );
  const needsValidation = (
    block !== null
    && block.validation.dry_run_passed === null
    && context.workflow_control.next_stage === "validation"
  );
  return (
    <section className="artifact-workspace">
      <div className="artifact-toolbar">
        <div className="artifact-selector">
          {context.test_cases.map((test) => (
            <button
              key={test.id}
              className={selectedTest?.id === test.id ? "active" : ""}
              onClick={() => onSelectTest(test.id)}
            >
              {test.id}
            </button>
          ))}
        </div>
        <div className="artifact-actions">
          <div className="artifact-view-switch" aria-label="Artifact view">
            <button
              className={sourceView === "source" ? "active" : ""}
              onClick={() => setSourceView("source")}
              type="button"
            >
              <Code2 /> Source
            </button>
            <button
              className={sourceView === "diff" ? "active" : ""}
              onClick={() => setSourceView("diff")}
              type="button"
            >
              <GitCompareArrows /> Changes
            </button>
          </div>
          {editing ? (
            <>
              <button className="icon-command" onClick={onCancelEdit} title="Cancel editing"><X /></button>
              <button className="command-button primary" onClick={onSave} disabled={busy || !draft.trim()}>
                <Save /> Save revision
              </button>
            </>
          ) : (
            <button
              className="command-button secondary"
              onClick={() => {
                setSelectedRevisionVersion(null);
                setSourceView("source");
                onStartEdit();
              }}
              disabled={!block}
            >
              <Code2 /> Edit artifact
            </button>
          )}
        </div>
      </div>

      {block && selectedTest ? (
        <>
          <div className="artifact-meta">
            <div><span>File</span><strong>{block.robot_file.split("/").at(-1)}</strong></div>
            <div><span>Revision</span><strong>{block.revision}</strong></div>
            <div><span>Validation</span><strong>{validationText(block.validation.dry_run_passed)}</strong></div>
            {editing ? (
              <div><span>Changes</span><strong><GitCompareArrows /> +{diff.added} / -{diff.removed}</strong></div>
            ) : (
              <div>
                <span>Review</span>
                <strong>{automationReview?.status?.replaceAll("_", " ") ?? "not requested"}</strong>
              </div>
            )}
          </div>
          {automationReviewPending ? (
            <section className="artifact-review-bar">
              <div>
                <span className="summary-label">Automation review</span>
                <strong>Approve the generated scripts or request a new revision.</strong>
              </div>
              <input
                value={reviewComment}
                onChange={(event) => setReviewComment(event.target.value)}
                placeholder="Approval note or regeneration direction"
              />
              <div className="artifact-review-actions">
                <button
                  className="command-button primary"
                  disabled={busy}
                  onClick={() => {
                    onReviewAutomation(reviewComment.trim() || undefined);
                    setReviewComment("");
                  }}
                >
                  <Check /> Approve scripts
                </button>
                <button
                  className="command-button secondary"
                  disabled={busy || !reviewComment.trim()}
                  onClick={() => {
                    onRegenerateAutomation(reviewComment.trim());
                    setReviewComment("");
                  }}
                >
                  <RotateCcw /> Regenerate
                </button>
              </div>
            </section>
          ) : needsValidation ? (
            <div className="artifact-review-status warning">
              <TriangleAlert />
              <span>Manual edits saved. Validation must run again before approval.</span>
            </div>
          ) : automationReview?.status === "approved" ? (
            <div className="artifact-review-status approved">
              <CheckCircle2 />
              <span>Automation scripts approved for downstream validation.</span>
            </div>
          ) : null}
          {editing && sourceView === "source" ? (
            <>
              <textarea
                className="code-editor"
                value={draft}
                onChange={(event) => onDraftChange(event.target.value)}
                spellCheck={false}
                aria-label="Robot Framework artifact editor"
              />
              <input
                className="revision-comment"
                value={comment}
                onChange={(event) => onCommentChange(event.target.value)}
                placeholder="Revision note"
              />
            </>
          ) : sourceView === "diff" ? (
            <RobotDiffView before={baseline} after={comparison} />
          ) : (
            <RobotCodeView content={selectedRevision?.content ?? artifactContent} />
          )}
          <div className="revision-history">
            <div className="view-heading">
              <div><span className="panel-kicker">Audit history</span><h2>Artifact revisions</h2></div>
              <span className="count-badge">{revisions.length || block.revision}</span>
            </div>
            {revisions.length ? revisions.map((revision) => (
              <button
                className={`revision-row ${selectedRevisionVersion === revision.version ? "selected" : ""}`}
                key={revision.id}
                onClick={() => {
                  setSelectedRevisionVersion(revision.version);
                  setSourceView("diff");
                }}
                type="button"
              >
                <span>v{revision.version}</span>
                <div><strong>{revision.source === "manual" ? "Manual edit" : "Generated"}</strong><small>{revision.comment ?? "No revision note"} - {formatTime(revision.created_at)}</small></div>
                <GitCompareArrows />
              </button>
            )) : <p className="muted-copy">Revision history starts after the first manual edit.</p>}
          </div>
        </>
      ) : <EmptyView icon={<Code2 />} text="Automation artifacts appear after generation." />}
    </section>
  );
}

function ValidationWorkspace({
  context,
  timeline,
  busy,
  onApprove,
  onRequestChanges,
  onRegenerate,
  onEditArtifacts
}: {
  context: TestContext;
  timeline: WorkflowEvent[];
  busy: boolean;
  onApprove: (comment?: string) => void;
  onRequestChanges: (comment: string) => void;
  onRegenerate: (comment: string) => void;
  onEditArtifacts: () => void;
}) {
  const [comment, setComment] = useState("");
  const summary = context.validation_summary;
  const validationReview = context.workflow_control.stage_reviews.validation;
  const reviewPending = (
    context.workflow_control.state === "waiting_review"
    && validationReview?.status === "pending"
  );
  const retryTrace = context.workflow_trace.filter(
    (event) => (
      event.node_name === "validation_retry_gate"
      && (event.status === "routed" || event.summary?.toLowerCase().includes("validation"))
    )
  );
  const validationEvents = timeline.filter((event) => event.stage === "validation");

  if (!summary) {
    return (
      <section className="validation-workspace">
        <EmptyView
          icon={<Gauge />}
          text="Validation evidence appears after the validation stage runs."
        />
      </section>
    );
  }

  return (
    <section className="validation-workspace">
      <header className="validation-header">
        <div className={`quality-score ${summary.status}`}>
          <span>Quality score</span>
          <strong>{summary.quality_score}</strong>
          <small>out of 100</small>
        </div>
        <div className="validation-heading">
          <span className="panel-kicker">Deterministic validation gate</span>
          <h2>{validationHeadline(summary.status)}</h2>
          <p>
            {summary.passed_artifacts} of {summary.total_artifacts} Robot artifacts
            passed using {summary.validator_mode.replaceAll("_", " ")} validation.
          </p>
        </div>
        <StatusPill value={summary.status} />
      </header>

      <div className="validation-metrics">
        <ValidationMetric
          label="Requirement coverage"
          value={summary.requirement_coverage_percent}
        />
        <ValidationMetric
          label="Artifact pass rate"
          value={summary.artifact_pass_percent}
        />
        <ValidationMetric
          label="Test data references"
          value={summary.data_reference_percent}
        />
        <ValidationMetric
          label="Requirement completeness"
          value={summary.requirement_completeness_percent}
        />
      </div>

      {reviewPending ? (
        <section className="validation-decision">
          <div>
            <span className="summary-label">Validation review</span>
            <strong>
              {summary.status === "failed"
                ? "Resolve failed checks before approval."
                : "Approve this evidence package or direct another iteration."}
            </strong>
          </div>
          <textarea
            rows={2}
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            placeholder="Approval note or required correction..."
          />
          <div className="validation-decision-actions">
            <button
              className="command-button primary"
              disabled={busy || summary.status === "failed"}
              onClick={() => {
                onApprove(comment.trim() || undefined);
                setComment("");
              }}
            >
              <Check /> Approve validation
            </button>
            <button
              className="command-button secondary"
              disabled={busy || !comment.trim()}
              onClick={() => {
                onRequestChanges(comment.trim());
                setComment("");
              }}
            >
              <X /> Request changes
            </button>
            <button
              className="command-button secondary"
              disabled={busy || !comment.trim()}
              onClick={() => {
                onRegenerate(comment.trim());
                setComment("");
              }}
            >
              <RotateCcw /> Regenerate automation
            </button>
            <button className="icon-command" onClick={onEditArtifacts} title="Edit automation artifacts">
              <Code2 />
            </button>
          </div>
        </section>
      ) : null}

      <div className="validation-columns">
        <section className="validation-section">
          <div className="view-heading">
            <div>
              <span className="panel-kicker">Per-file evidence</span>
              <h2>Artifact checks</h2>
            </div>
            <span className="count-badge">
              {summary.passed_artifacts}/{summary.total_artifacts}
            </span>
          </div>
          <div className="validation-artifact-list">
            {Object.values(context.automation).map((block) => {
              const passed = (
                block.validation.artifact_exists
                && block.data_reference_check_passed
                && block.validation.dry_run_passed === true
              );
              return (
                <details className={`validation-artifact ${passed ? "passed" : "failed"}`} key={block.test_case_id}>
                  <summary>
                    <span className="validation-result-icon">
                      {passed ? <CheckCircle2 /> : <TriangleAlert />}
                    </span>
                    <span>
                      <strong>{block.test_case_id}</strong>
                      <small>{block.robot_file.split("/").at(-1)}</small>
                    </span>
                    <StatusPill value={passed ? "passed" : "failed"} />
                  </summary>
                  <dl className="artifact-check-grid">
                    <div><dt>Artifact exists</dt><dd>{yesNo(block.validation.artifact_exists)}</dd></div>
                    <div><dt>Data references</dt><dd>{yesNo(block.data_reference_check_passed)}</dd></div>
                    <div><dt>Dry run</dt><dd>{validationText(block.validation.dry_run_passed)}</dd></div>
                    <div><dt>Attempts</dt><dd>{block.validation.validation_attempts}</dd></div>
                  </dl>
                  {block.validation.dry_run_skipped_reason ? (
                    <p className="validation-note">{block.validation.dry_run_skipped_reason}</p>
                  ) : null}
                  {block.validation.errors.length ? (
                    <ul className="validation-errors">
                      {block.validation.errors.map((error, index) => (
                        <li key={`${block.test_case_id}-${index}`}>{error}</li>
                      ))}
                    </ul>
                  ) : null}
                </details>
              );
            })}
          </div>
        </section>

        <aside className="validation-side">
          <section className="validation-section">
            <div className="view-heading">
              <div>
                <span className="panel-kicker">Traceability</span>
                <h2>Requirements</h2>
              </div>
            </div>
            <div className="traceability-list">
              {Object.entries(context.coverage_plan?.coverage_matrix ?? {}).map(
                ([requirement, testIds]) => {
                  const missing = summary.missing_requirements.includes(requirement);
                  return (
                    <div className={`traceability-row ${missing ? "missing" : ""}`} key={requirement}>
                      <span>{missing ? <TriangleAlert /> : <CheckCircle2 />}</span>
                      <div><strong>{requirement}</strong><small>{testIds.join(", ")}</small></div>
                    </div>
                  );
                }
              )}
            </div>
          </section>

          <section className="validation-section">
            <div className="view-heading">
              <div>
                <span className="panel-kicker">Risk review</span>
                <h2>Open areas</h2>
              </div>
            </div>
            {summary.risk_areas.length ? (
              <ul className="risk-list">
                {summary.risk_areas.map((risk, index) => <li key={`${risk}-${index}`}>{risk}</li>)}
              </ul>
            ) : (
              <p className="validation-clear"><CheckCircle2 /> No validation risks detected.</p>
            )}
          </section>

          <section className="validation-section">
            <div className="view-heading">
              <div>
                <span className="panel-kicker">Execution history</span>
                <h2>Retries and evidence</h2>
              </div>
            </div>
            <dl className="validation-facts">
              <div><dt>Validation attempts</dt><dd>{summary.total_attempts}</dd></div>
              <div><dt>Workflow retries</dt><dd>{summary.retry_count}/{summary.max_retries}</dd></div>
              <div><dt>Stage revision</dt><dd>{context.workflow_control.stage_revisions.validation ?? 1}</dd></div>
              <div><dt>Events recorded</dt><dd>{validationEvents.length}</dd></div>
            </dl>
            {retryTrace.map((event, index) => (
              <div className="retry-entry" key={`${event.timestamp}-${index}`}>
                <RotateCcw />
                <div><strong>Retry {event.iteration}</strong><small>{event.summary ?? "Validation rerouted to automation."}</small></div>
              </div>
            ))}
          </section>
        </aside>
      </div>
    </section>
  );
}

function EvidenceWorkspace({
  context,
  executionRuns,
  executionEvents
}: {
  context: TestContext;
  executionRuns: ExecutionRunRecord[];
  executionEvents: ExecutionEvent[];
}) {
  return (
    <section className="evidence-workspace">
      <EvidenceSection title="Knowledge evidence" icon={<FileText />}>
        {context.intelligence_trace.knowledge_refs.map((ref) => (
          <EvidenceRow key={ref.ref_id} title={ref.title} detail={`${ref.ref_id} - ${Math.round(ref.score * 100)}%`} body={ref.excerpt} />
        ))}
      </EvidenceSection>
      <EvidenceSection title="Agent memory" icon={<Sparkles />}>
        {context.intelligence_trace.memory_refs.map((ref) => (
          <EvidenceRow key={ref.ref_id} title={ref.title} detail={`${ref.ref_id} - ${Math.round(ref.score * 100)}%`} body={ref.excerpt} />
        ))}
        {context.memory_archive?.summary ? <p className="evidence-summary">{context.memory_archive.summary}</p> : null}
      </EvidenceSection>
      <EvidenceSection title="Model trace" icon={<Bot />}>
        {context.intelligence_trace.llm_calls.map((call, index) => (
          <EvidenceRow
            key={`${call.prompt_name}-${index}`}
            title={call.agent_name?.replace("Agent", "") ?? call.prompt_name}
            detail={`${call.provider} - ${call.model}`}
            body={call.summary}
          />
        ))}
      </EvidenceSection>
      <EvidenceSection title="Execution logs" icon={<Activity />}>
        {executionEvents.slice(-12).map((event) => (
          <EvidenceRow key={event.id} title={event.phase} detail={event.status ?? event.level} body={event.message} />
        ))}
        {!executionEvents.length && executionRuns.length ? (
          <p className="evidence-summary">Latest run: {executionRuns[0].run_id} - {executionRuns[0].status}</p>
        ) : null}
      </EvidenceSection>
    </section>
  );
}

function EvidenceSection({
  title,
  icon,
  children
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="evidence-section">
      <div className="deliverable-title">{icon}<h2>{title}</h2></div>
      <div className="evidence-list">{children}</div>
    </section>
  );
}

function EvidenceRow({
  title,
  detail,
  body
}: {
  title: string;
  detail: string;
  body: string;
}) {
  return (
    <article className="evidence-row">
      <div><strong>{title}</strong><span>{detail}</span></div>
      <p>{body}</p>
    </article>
  );
}

function TabButton({
  active,
  icon,
  label,
  onClick
}: {
  active: boolean;
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
}) {
  return <button className={active ? "active" : ""} onClick={onClick}>{icon}{label}</button>;
}

function StatusPill({ value }: { value: string }) {
  return <span className={`status-pill ${value}`}>{value.replaceAll("_", " ")}</span>;
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="deliverable-metric"><span>{label}</span><strong>{value}</strong></div>;
}

function ValidationMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="validation-metric">
      <div><span>{label}</span><strong>{value}%</strong></div>
      <span className="metric-track"><span style={{ width: `${value}%` }} /></span>
    </div>
  );
}

function BulletList({ items }: { items: string[] }) {
  return items.length ? <ul className="bullet-list">{items.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}</ul> : null;
}

function DetailSection({
  title,
  items,
  ordered = false
}: {
  title: string;
  items: string[];
  ordered?: boolean;
}) {
  const List = ordered ? "ol" : "ul";
  return (
    <section className="detail-section">
      <h3>{title}</h3>
      {items.length ? <List>{items.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}</List> : <p className="muted-copy">None recorded.</p>}
    </section>
  );
}

function EmptyView({ icon, text }: { icon: React.ReactNode; text: string }) {
  return <div className="view-empty"><span>{icon}</span><p>{text}</p></div>;
}

function pendingStageReview(context: TestContext | null): WorkflowStageName | null {
  if (!context || context.workflow_control.state !== "waiting_review") return null;
  const review = Object.values(context.workflow_control.stage_reviews).find(
    (item) => item.status === "pending"
  );
  return review?.stage ?? null;
}

function stageState(
  context: TestContext,
  stage: WorkflowStageName
): "completed" | "active" | "blocked" | "waiting" {
  if (context.workflow_control.last_error && context.workflow_control.current_stage === stage) return "blocked";
  if (context.workflow_control.current_stage === stage || context.workflow_control.next_stage === stage) return "active";
  if (context.workflow_control.completed_stages.includes(stage)) return "completed";
  return "waiting";
}

function activityDetail(
  context: TestContext,
  stage: WorkflowStageName,
  event?: WorkflowEvent
): string {
  if (context.workflow_control.current_stage === stage) return "Running";
  const review = context.workflow_control.stage_reviews[stage];
  if (review?.status === "pending") return "Waiting review";
  if (review?.status === "changes_requested") return "Changes requested";
  if (context.workflow_control.completed_stages.includes(stage)) {
    const duration = event?.metadata.duration_ms;
    return duration ? `${String(duration)} ms` : `Revision ${context.workflow_control.stage_revisions[stage] ?? 1}`;
  }
  return "Pending";
}

function summaryInputs(context: TestContext, stage: WorkflowStageName): string {
  if (stage === "requirements") return context.ticket?.id ?? "Ticket";
  if (stage === "coverage") return "Approved requirements and memory";
  if (stage === "tests") return "Coverage plan and evidence";
  if (stage === "automation") return `${context.test_cases.length} test scenarios`;
  if (stage === "validation") return `${Object.keys(context.automation).length} Robot artifacts`;
  if (stage === "approval") return "Validated automation package";
  if (stage === "report") return "Workflow evidence and execution state";
  return "Selected ticket";
}

function eventsFromTrace(context: TestContext): WorkflowEvent[] {
  return context.workflow_trace
    .filter((trace) => trace.status === "completed" || trace.status === "failed")
    .map((trace, index) => ({
      sequence: index + 1,
      id: `${trace.node_name}-${index}`,
      context_id: context.context_id,
      kind: trace.status === "failed" ? "error" : "stage",
      stage: nodeStage(trace.node_name),
      status: trace.status,
      actor: "system",
      message: trace.summary ?? `${trace.node_name.replaceAll("_", " ")} ${trace.status}.`,
      metadata: trace.metadata,
      created_at: trace.timestamp
    }));
}

function nodeStage(nodeName: string): WorkflowStageName | null {
  if (nodeName === "load_ticket") return "ticket";
  if (nodeName === "requirement_agent") return "requirements";
  if (nodeName === "coverage_planner") return "coverage";
  if (nodeName === "test_case_generator" || nodeName === "test_data_resolver") return "tests";
  if (nodeName === "automation_generator") return "automation";
  if (nodeName === "validator" || nodeName === "validation_retry_gate") return "validation";
  if (nodeName === "human_approval") return "approval";
  if (["execution_dispatcher", "investigation_coordinator", "memory_archiver", "report_generator"].includes(nodeName)) return "report";
  return null;
}

function stageLabel(stage: WorkflowStageName): string {
  return STAGES.find((item) => item.name === stage)?.label ?? stage;
}

function validationText(value: boolean | null): string {
  if (value === true) return "Passed";
  if (value === false) return "Failed";
  return "Needs validation";
}

function validationHeadline(status: "passed" | "warning" | "failed"): string {
  if (status === "passed") return "Validation passed";
  if (status === "warning") return "Validation passed with review notes";
  return "Validation failed";
}

function yesNo(value: boolean): string {
  return value ? "Passed" : "Failed";
}

function formatTime(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}
