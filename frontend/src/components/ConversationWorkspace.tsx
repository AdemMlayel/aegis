import {
  Activity,
  Bot,
  Check,
  CheckCircle2,
  CircleDashed,
  Clock3,
  Code2,
  Download,
  FileArchive,
  FileCheck2,
  FileJson2,
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
import { useState } from "react";
import {
  lineDiffSummary,
  RobotCodeView,
  RobotDiffView
} from "./RobotArtifactViewer";
import {
  BulletList,
  DetailSection,
  EmptyView,
  Metric,
  StatusPill,
  TabButton,
  ValidationMetric
} from "./WorkspacePrimitives";
import {
  STAGES,
  activityDetail,
  eventsFromTrace,
  formatBytes,
  formatDuration,
  formatTime,
  pendingStageReview,
  stageLabel,
  stageState,
  summaryInputs,
  validationHeadline,
  validationText,
  yesNo
} from "./WorkspaceUtils";
import type {
  ArtifactRevision,
  ExecutionEvent,
  ExecutionRunRecord,
  ReportPackageManifest,
  TestCase,
  TestContext,
  TicketData,
  WorkflowEvent,
  WorkflowStageName
} from "../types";

export type WorkspaceView =
  | "conversation"
  | "tests"
  | "artifacts"
  | "validation"
  | "report"
  | "evidence";

export function ConversationWorkspace({
  context,
  selectedTicket,
  timeline,
  view,
  selectedTestId,
  artifactContent,
  artifactDraft,
  artifactEditing,
  artifactRevisions,
  executionRuns,
  executionEvents,
  reportPackage,
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
  onSaveArtifact,
  onDownloadReport
}: {
  context: TestContext | null;
  selectedTicket: TicketData | null;
  timeline: WorkflowEvent[];
  view: WorkspaceView;
  selectedTestId: string;
  artifactContent: string;
  artifactDraft: string;
  artifactEditing: boolean;
  artifactRevisions: ArtifactRevision[];
  executionRuns: ExecutionRunRecord[];
  executionEvents: ExecutionEvent[];
  reportPackage: ReportPackageManifest | null;
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
  onDownloadReport: (
    format: "package" | "technical" | "executive"
  ) => void;
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
          <span className="ticket-key">{selectedTicket?.id ?? "NO TICKET SELECTED"}</span>
          <h1>{selectedTicket?.title ?? "Choose a ticket workspace"}</h1>
          <p>
            {selectedTicket?.test_objective
              || selectedTicket?.description
              || "Create a controlled session to begin requirement analysis, coverage planning, and automation."}
          </p>
          <button className="command-button primary" onClick={onCreateWorkspace}>
            <Play /> Start selected ticket
          </button>
        </div>
        <TicketStructuredPanel ticket={selectedTicket} />
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

      <TicketStructuredPanel ticket={context.ticket} />

      <nav className="workspace-tabs" aria-label="Workspace views">
        <TabButton active={view === "conversation"} icon={<MessageSquare />} label="Activity" onClick={() => onViewChange("conversation")} />
        <TabButton active={view === "tests"} icon={<TestTube2 />} label={`Tests ${context.test_cases.length || ""}`} onClick={() => onViewChange("tests")} />
        <TabButton active={view === "artifacts"} icon={<Code2 />} label="Artifacts" onClick={() => onViewChange("artifacts")} />
        <TabButton active={view === "validation"} icon={<Gauge />} label="Validation" onClick={() => onViewChange("validation")} />
        <TabButton active={view === "report"} icon={<FileCheck2 />} label="Report" onClick={() => onViewChange("report")} />
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

      {view === "report" ? (
        <ReportWorkspace
          context={context}
          manifest={reportPackage}
          busy={busy !== null}
          onReviewReport={(decision, comment) => {
            onReviewStage("report", decision, comment);
          }}
          onRegenerateReport={(comment) => {
            onRegenerateStage("report", comment);
          }}
          onApprovePackage={onApproveWorkflow}
          onExecute={onExecuteWorkflow}
          onDownload={onDownloadReport}
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

function TicketStructuredPanel({ ticket }: { ticket: TicketData | null }) {
  if (!ticket) return null;
  const interactions = ticket.technical.api_or_service_interactions.map(
    (interaction) =>
      `${interaction.name}: ${interaction.source} -> ${interaction.target} (${interaction.protocol} ${interaction.operation})`
  );
  const validationRules = ticket.validation_rules.map(
    (rule) => `${rule.id}: ${rule.description}`
  );
  const testSteps = ticket.test_steps.map(
    (step) => `${step.action} Expected: ${step.expected_result}`
  );
  return (
    <section className="ticket-context-panel">
      <div className="deliverable-title"><FileJson2 /><h2>Structured ticket context</h2></div>
      <div className="ticket-context-grid">
        <Metric label="System" value={ticket.system_under_test || "TEST_ENVIRONMENT"} />
        <Metric label="Service" value={ticket.feature_or_service_name || "Not specified"} />
        <Metric label="Priority" value={ticket.priority} />
        <Metric label="Environment" value={ticket.environment} />
      </div>
      <div className="ticket-context-copy">
        <section>
          <h3>Objectives</h3>
          <p>{ticket.business_objective || ticket.description}</p>
          <p>{ticket.test_objective || "No test objective recorded."}</p>
        </section>
        <section>
          <h3>Technical Architecture</h3>
          <p>{ticket.technical.architecture_summary || "No architecture summary recorded."}</p>
        </section>
      </div>
      <div className="ticket-context-columns">
        <DetailSection title="Scope" items={ticket.test_scope} />
        <DetailSection title="Preconditions" items={ticket.preconditions} />
        <DetailSection title="Interfaces" items={ticket.interfaces_involved} />
        <DetailSection title="Validation rules" items={validationRules} />
        <DetailSection title="Test steps" items={testSteps} ordered />
        <DetailSection title="Service interactions" items={interactions} />
        <DetailSection title="Required tools" items={ticket.required_tools} />
        <DetailSection title="Risks and constraints" items={ticket.risks_or_constraints} />
      </div>
    </section>
  );
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

function ReportWorkspace({
  context,
  manifest,
  busy,
  onReviewReport,
  onRegenerateReport,
  onApprovePackage,
  onExecute,
  onDownload
}: {
  context: TestContext;
  manifest: ReportPackageManifest | null;
  busy: boolean;
  onReviewReport: (
    decision: "approve" | "request_changes",
    comment?: string
  ) => void;
  onRegenerateReport: (comment: string) => void;
  onApprovePackage: () => void;
  onExecute: () => void;
  onDownload: (
    format: "package" | "technical" | "executive"
  ) => void;
}) {
  const [comment, setComment] = useState("");
  const report = context.reports;
  const reportReview = context.workflow_control.stage_reviews.report;
  const reportReviewPending = (
    context.workflow_control.state === "waiting_review"
    && reportReview?.status === "pending"
  );
  const packageApprovalPending = (
    context.approval?.status === "pending_review"
    && context.workflow_control.state === "completed"
  );
  const canExecute = context.approval?.status === "approved"
    && (!context.execution || context.execution.status === "skipped");

  if (!report) {
    return (
      <section className="report-workspace">
        <EmptyView
          icon={<FileCheck2 />}
          text="The final package appears after the report stage runs."
        />
      </section>
    );
  }

  const execution = context.execution;
  const investigation = context.investigation;
  const stageReviews = Object.values(context.workflow_control.stage_reviews);

  return (
    <section className="report-workspace">
      <header className="report-header">
        <div className="report-heading">
          <span className="panel-kicker">Final QA package</span>
          <h2>{context.ticket?.title ?? "Workflow report"}</h2>
          <p>{report.summary}</p>
        </div>
        <div className="report-header-actions">
          <StatusPill value={manifest?.package_status ?? "preparing"} />
          <button
            className="command-button primary"
            disabled={busy || !manifest}
            onClick={() => onDownload("package")}
          >
            <FileArchive /> Download package
          </button>
        </div>
      </header>

      <div className="report-metrics">
        <Metric label="Test cases" value={String(report.total_test_cases)} />
        <Metric label="Highest risk" value={report.highest_risk} />
        <Metric
          label="Quality score"
          value={
            context.validation_summary
              ? `${context.validation_summary.quality_score}/100`
              : "Pending"
          }
        />
        <Metric
          label="Execution"
          value={execution?.status ?? "not started"}
        />
        <Metric
          label="Confidence"
          value={`${Math.round(report.confidence * 100)}%`}
        />
      </div>

      {reportReviewPending ? (
        <ReportDecision
          label="Report review"
          title="Review the final report before package approval."
          comment={comment}
          busy={busy}
          approveLabel="Approve report"
          onCommentChange={setComment}
          onApprove={() => {
            onReviewReport("approve", comment.trim() || undefined);
            setComment("");
          }}
          onRequestChanges={() => {
            onReviewReport("request_changes", comment.trim());
            setComment("");
          }}
          onRegenerate={() => {
            onRegenerateReport(comment.trim());
            setComment("");
          }}
        />
      ) : packageApprovalPending ? (
        <section className="package-approval-band">
          <div>
            <span className="summary-label">Final package approval</span>
            <strong>All report stages are reviewed. Approve the Git handoff package.</strong>
            <small>This records the final decision and prepares the approved execution boundary.</small>
          </div>
          <button className="command-button primary" disabled={busy} onClick={onApprovePackage}>
            <ShieldCheck /> Approve package
          </button>
        </section>
      ) : canExecute ? (
        <section className="package-approval-band approved">
          <div>
            <span className="summary-label">Approved package</span>
            <strong>The package is approved and ready for execution.</strong>
            <small>Run the local adapter to add execution and investigation evidence.</small>
          </div>
          <button className="command-button primary" disabled={busy} onClick={onExecute}>
            <Play /> Execute approved tests
          </button>
        </section>
      ) : null}

      <div className="report-columns">
        <div className="report-primary">
          <section className="report-section">
            <div className="report-section-heading">
              <div><span className="panel-kicker">Technical outcome</span><h3>Execution results</h3></div>
              <button className="command-button subtle" disabled={busy} onClick={() => onDownload("technical")}>
                <Download /> Technical report
              </button>
            </div>
            {execution && execution.status !== "skipped" ? (
              <>
                <div className="execution-summary-strip">
                  <span><strong>{execution.summary.total}</strong>Total</span>
                  <span className="passed"><strong>{execution.summary.passed}</strong>Passed</span>
                  <span className="failed"><strong>{execution.summary.failed}</strong>Failed</span>
                  <span><strong>{execution.summary.skipped}</strong>Skipped</span>
                  <span><strong>{formatDuration(execution.summary.duration_ms)}</strong>Duration</span>
                </div>
                <div className="report-result-list">
                  {execution.results.map((result) => (
                    <div className={`report-result-row ${result.status}`} key={result.test_case_id}>
                      <span>{result.status === "passed" ? <CheckCircle2 /> : result.status === "failed" ? <TriangleAlert /> : <CircleDashed />}</span>
                      <div><strong>{result.test_case_id} - {result.title}</strong><small>{result.message}</small></div>
                      <span>{formatDuration(result.duration_ms)}</span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <p className="report-empty-copy">Execution evidence will be added after the approved package runs.</p>
            )}
          </section>

          <section className="report-section">
            <div className="report-section-heading">
              <div><span className="panel-kicker">Failure intelligence</span><h3>Investigation findings</h3></div>
            </div>
            {investigation?.findings.length ? (
              <>
                {investigation.root_cause_summary ? (
                  <p className="root-cause-summary">{investigation.root_cause_summary}</p>
                ) : null}
                <div className="finding-list">
                  {investigation.findings.map((finding, index) => (
                    <article className="finding-row" key={`${finding.test_case_id}-${index}`}>
                      <StatusPill value={finding.severity} />
                      <div>
                        <strong>{finding.test_case_id ?? "Workflow"} - {finding.category}</strong>
                        <p>{finding.summary}</p>
                        <small>Confidence {Math.round(finding.confidence * 100)}%</small>
                      </div>
                    </article>
                  ))}
                </div>
              </>
            ) : (
              <p className="report-empty-copy">No investigation findings are recorded.</p>
            )}
          </section>

          <section className="report-section">
            <div className="report-section-heading">
              <div><span className="panel-kicker">Recommended follow-up</span><h3>Next actions</h3></div>
            </div>
            <ol className="next-action-list">
              {report.next_actions.map((action, index) => (
                <li key={`${action}-${index}`}>{action}</li>
              ))}
            </ol>
          </section>
        </div>

        <aside className="report-side">
          <section className="report-section">
            <div className="report-section-heading">
              <div><span className="panel-kicker">Stakeholder view</span><h3>Executive summary</h3></div>
              <button className="icon-command" disabled={busy} onClick={() => onDownload("executive")} title="Download executive summary">
                <Download />
              </button>
            </div>
            <dl className="executive-facts">
              <div><dt>Ticket</dt><dd>{context.ticket?.id ?? "Untitled"}</dd></div>
              <div><dt>Package</dt><dd>{manifest?.package_status.replaceAll("_", " ") ?? "preparing"}</dd></div>
              <div><dt>Risk</dt><dd>{report.highest_risk}</dd></div>
              <div><dt>Approval</dt><dd>{context.approval?.status.replaceAll("_", " ") ?? "not ready"}</dd></div>
              <div><dt>Memory</dt><dd>{context.memory_archive?.status.replaceAll("_", " ") ?? "not started"}</dd></div>
            </dl>
          </section>

          <section className="report-section">
            <div className="report-section-heading">
              <div><span className="panel-kicker">Audit trail</span><h3>Decisions</h3></div>
            </div>
            <div className="decision-list">
              {stageReviews.map((review) => (
                <div className="decision-row" key={review.stage}>
                  <span className={`decision-dot ${review.status}`} />
                  <div>
                    <strong>{stageLabel(review.stage)}</strong>
                    <small>{review.status.replaceAll("_", " ")}{review.decided_by ? ` by ${review.decided_by}` : ""}</small>
                  </div>
                </div>
              ))}
              {context.approval ? (
                <div className="decision-row">
                  <span className={`decision-dot ${context.approval.status}`} />
                  <div>
                    <strong>Final package</strong>
                    <small>{context.approval.status.replaceAll("_", " ")}{context.approval.decided_by ? ` by ${context.approval.decided_by}` : ""}</small>
                  </div>
                </div>
              ) : null}
            </div>
          </section>

          <section className="report-section">
            <div className="report-section-heading">
              <div><span className="panel-kicker">Export manifest</span><h3>Package contents</h3></div>
              <span className="count-badge">{manifest?.files.length ?? 0}</span>
            </div>
            <div className="package-file-list">
              {manifest?.files.map((file) => (
                <div className="package-file-row" key={file.path}>
                  <FileJson2 />
                  <div><strong>{file.path}</strong><small>{file.description}</small></div>
                  <span>{formatBytes(file.size_bytes)}</span>
                </div>
              ))}
              {!manifest ? <p className="report-empty-copy">Preparing package manifest...</p> : null}
            </div>
            {manifest?.warnings.map((warning, index) => (
              <p className="package-warning" key={`${warning}-${index}`}><TriangleAlert /> {warning}</p>
            ))}
          </section>
        </aside>
      </div>
    </section>
  );
}

function ReportDecision({
  label,
  title,
  comment,
  busy,
  approveLabel,
  onCommentChange,
  onApprove,
  onRequestChanges,
  onRegenerate
}: {
  label: string;
  title: string;
  comment: string;
  busy: boolean;
  approveLabel: string;
  onCommentChange: (value: string) => void;
  onApprove: () => void;
  onRequestChanges: () => void;
  onRegenerate: () => void;
}) {
  return (
    <section className="report-decision">
      <div><span className="summary-label">{label}</span><strong>{title}</strong></div>
      <textarea
        rows={2}
        value={comment}
        onChange={(event) => onCommentChange(event.target.value)}
        placeholder="Optional approval note, or required report correction..."
      />
      <div>
        <button className="command-button primary" disabled={busy} onClick={onApprove}><Check /> {approveLabel}</button>
        <button className="command-button secondary" disabled={busy || !comment.trim()} onClick={onRequestChanges}><X /> Request changes</button>
        <button className="icon-command" disabled={busy || !comment.trim()} onClick={onRegenerate} title="Regenerate report"><RotateCcw /></button>
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
      <EvidenceSection title="Investigation evidence" icon={<FileJson2 />}>
        {context.investigation?.evidence_items?.slice(0, 12).map((item) => (
          <EvidenceRow
            key={item.evidence_id}
            title={item.summary}
            detail={`${item.kind} - ${item.severity_hint}`}
            body={item.content_excerpt || item.source}
          />
        ))}
        {!context.investigation?.evidence_items?.length ? (
          <p className="evidence-summary">Investigation evidence will appear after execution.</p>
        ) : null}
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
