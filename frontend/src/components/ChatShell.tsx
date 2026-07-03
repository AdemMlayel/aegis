import {
  ChevronDown,
   MessageSquarePlus,
  MessagesSquare,
  PanelRightClose,
  Plus,
  RefreshCw,
  Settings2,
  ShieldCheck,
  X
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { STAGES, stageLabel } from "./WorkspaceUtils";
import { workflowProgressRatio } from "../companionView";
import type { ChatSession, TestContext } from "../types";

/* ------------------------------------------------------------------ *
 * Chat-first shell (V2 — Adaptive Companion)
 * One chat column + one detail companion that follows the orchestrator.
 * No persistent left list rail, no persistent right config column, no
 * stacked internal tab chrome. History is a header dropdown; settings is
 * a slide-over.
 * ------------------------------------------------------------------ */

function chatTitle(session: ChatSession): string {
  const firstUser = session.messages.find((message) => message.role === "user");
  if (firstUser && firstUser.content.trim()) {
    const text = firstUser.content.trim();
    return text.length > 44 ? `${text.slice(0, 44)}…` : text;
  }
  return session.title || "New chat";
}

function relativeTime(value?: string): string {
  if (!value) return "";
  const elapsed = Date.now() - new Date(value).getTime();
  if (!Number.isFinite(elapsed) || elapsed < 0) return "just now";
  const minutes = Math.floor(elapsed / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

/** Header session switcher — replaces the whole left nav list. */
export function SessionMenu({
  chatSessions,
  activeChatId,
  busy,
  onOpenChat,
  onNewChat
}: {
  chatSessions: ChatSession[];
  activeChatId: string | null;
  busy: boolean;
  onOpenChat: (sessionId: string) => void;
  onNewChat: () => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);
  const active = chatSessions.find((item) => item.session_id === activeChatId) ?? null;

  useEffect(() => {
    if (!open) return;
    const onDoc = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  return (
    <div className="session-menu" ref={ref}>
      <button
        type="button"
        className="session-trigger"
        onClick={() => setOpen((value) => !value)}
        aria-haspopup="menu"
        aria-expanded={open}
      >
        <MessagesSquare />
        <span>{active ? chatTitle(active) : "New chat"}</span>
        <ChevronDown />
      </button>
      {open ? (
        <div className="session-dropdown" role="menu">
          <button
            type="button"
            className="session-dropdown-new"
            disabled={busy}
            onClick={() => {
              setOpen(false);
              onNewChat();
            }}
          >
            <MessageSquarePlus /> New chat
          </button>
          <div className="session-dropdown-list">
            {chatSessions.length ? (
              chatSessions.map((session) => (
                <button
                  type="button"
                  role="menuitem"
                  key={session.session_id}
                  className={`session-dropdown-row ${session.session_id === activeChatId ? "selected" : ""}`}
                  onClick={() => {
                    setOpen(false);
                    onOpenChat(session.session_id);
                  }}
                >
                  <strong>{chatTitle(session)}</strong>
                  <span>
                    {session.messages.length} message{session.messages.length === 1 ? "" : "s"}
                    {session.ticket_id ? ` · ${session.ticket_id}` : ""}
                    {session.updated_at ? ` · ${relativeTime(session.updated_at)}` : ""}
                  </span>
                </button>
              ))
            ) : (
              <div className="session-dropdown-empty">No chats yet — say hello below.</div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}

/** Mini progress stepper at the top of the companion = orchestrator state. */
export function WorkflowStepper({ context }: { context: TestContext }) {
  const control = context.workflow_control;
  const activeStage = control.current_stage ?? control.next_stage ?? null;
  const ratio = workflowProgressRatio(context);
  return (
    <div className="companion-stepper" aria-label="Workflow progress">
      <div className="stepper-track">
        {STAGES.map((stage) => {
          const done = control.completed_stages.includes(stage.name);
          const active = stage.name === activeStage && !done;
          return (
            <span
              key={stage.name}
              className={`stepper-seg ${done ? "done" : ""} ${active ? "active" : ""}`}
              title={stage.label}
            />
          );
        })}
      </div>
      <span className="stepper-label">
        {activeStage ? `${stageLabel(activeStage)} · ` : ""}
        {Math.round(ratio * 100)}%
      </span>
    </div>
  );
}

/** Adaptive companion frame: slim header + stepper + (children = detail view). */
export function CompanionPanel({
  context,
  collapsed,
  pinned,
  onToggleCollapse,
  onTogglePinned,
  children
}: {
  context: TestContext | null;
  collapsed: boolean;
  pinned: boolean;
  onToggleCollapse: () => void;
  onTogglePinned: () => void;
  children: React.ReactNode;
}) {
  const phase = useMemo(() => {
    if (!context) return "No active workflow";
    const control = context.workflow_control;
    const stage = control.current_stage ?? control.next_stage;
    return stage ? stageLabel(stage) : control.state.replaceAll("_", " ");
  }, [context]);

  if (collapsed) return null;

  return (
    <aside className="companion" aria-label="Workflow companion">
      <div className="companion-head">
        <span className="companion-phase">
          <span className={`companion-dot ${context ? "live" : ""}`} />
          {context ? `${context.ticket?.id ?? "Workflow"} · ${phase}` : phase}
        </span>
        <div className="companion-head-actions">
          <button
            type="button"
            className={`companion-pin ${pinned ? "active" : ""}`}
            onClick={onTogglePinned}
            title={pinned ? "Following the workflow automatically" : "Pinned to this view"}
          >
            {pinned ? "Auto" : "Pinned"}
          </button>
          <button
            type="button"
            className="companion-collapse"
            onClick={onToggleCollapse}
            title="Collapse panel"
          >
            <PanelRightClose />
          </button>
        </div>
      </div>
      {context ? <WorkflowStepper context={context} /> : null}
      <div className="companion-body">{children}</div>
    </aside>
  );
}

/** Settings slide-over wrapping AgentConfigPanel (was a persistent column). */
export function SettingsSheet({
  open,
  onClose,
  children
}: {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
}) {
  return (
    <>
      <div
        className={`sheet-scrim ${open ? "open" : ""}`}
        onClick={onClose}
        aria-hidden={!open}
      />
      <div className={`settings-sheet ${open ? "open" : ""}`} role="dialog" aria-label="Agent and model settings">
        <div className="settings-sheet-head">
          <span><Settings2 /> Agent &amp; model settings</span>
          <button type="button" onClick={onClose} title="Close settings"><X /></button>
        </div>
        <div className="settings-sheet-body">{children}</div>
      </div>
    </>
  );
}

/** Brand + session switcher + actions: the single top bar for the chat column. */
export function ChatHeader({
  chatSessions,
  activeChatId,
  busy,
  companionCollapsed,
  hasWorkflow,
  onOpenChat,
  onNewChat,
  onOpenSettings,
  onShowCompanion,
  onRefresh
}: {
  chatSessions: ChatSession[];
  activeChatId: string | null;
  busy: boolean;
  companionCollapsed: boolean;
  hasWorkflow: boolean;
  onOpenChat: (sessionId: string) => void;
  onNewChat: () => void;
  onOpenSettings: () => void;
  onShowCompanion: () => void;
  onRefresh: () => void;
}) {
  return (
    <header className="chat-header">
      <div className="chat-brand">
        <span className="chat-brand-mark"><ShieldCheck /></span>
        <div className="chat-brand-copy">
          <strong>AegisQA</strong>
          <span>Agent operations</span>
        </div>
      </div>
      <div className="chat-header-center">
        <SessionMenu
          chatSessions={chatSessions}
          activeChatId={activeChatId}
          busy={busy}
          onOpenChat={onOpenChat}
          onNewChat={onNewChat}
        />
      </div>
      <div className="chat-header-actions">
        {hasWorkflow && companionCollapsed ? (
          <button type="button" className="icon-command" onClick={onShowCompanion} title="Show workflow panel">
            <PanelRightClose style={{ transform: "scaleX(-1)" }} />
          </button>
        ) : null}
        <button type="button" className="icon-command" onClick={onNewChat} disabled={busy} title="New chat">
          <Plus />
        </button>
        <button type="button" className="icon-command" onClick={onRefresh} disabled={busy} title="Refresh">
          <RefreshCw className={busy ? "spin" : ""} />
        </button>
        <button type="button" className="icon-command" onClick={onOpenSettings} title="Agent & model settings">
          <Settings2 />
        </button>
      </div>
    </header>
  );
}
