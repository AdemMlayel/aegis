import { Check, Send, Shield, Sparkles, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ChatAction, ChatMessage, ChatSession } from "../types";

type CopilotPanelProps = {
  session: ChatSession | null;
  busy: boolean;
  disabled: boolean;
  onSend: (message: string) => void;
  onConfirmAction: (actionId: string) => void;
  onCancelAction: (actionId: string) => void;
};

const SUGGESTIONS = [
  "Suggest test cases for this ticket",
  "Resume the workflow",
  "Where are we in the workflow?",
  "What is missing in this ticket?"
];

export function CopilotPanel({
  session,
  busy,
  disabled,
  onSend,
  onConfirmAction,
  onCancelAction
}: CopilotPanelProps) {
  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const messages = session?.messages ?? [];
  const isEmpty = messages.length === 0;

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages.length, busy]);

  // Auto-grow the composer up to a max height (ChatGPT/Claude behavior).
  function autosize(el: HTMLTextAreaElement | null) {
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }

  function submit(message = draft) {
    const trimmed = message.trim();
    if (!trimmed || disabled || busy) return;
    onSend(trimmed);
    setDraft("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  }

  return (
    <div className="chat-thread-wrap" aria-label="AegisQA Copilot">
      <div className="chat-thread" ref={scrollRef}>
        {isEmpty ? (
          <div className="chat-welcome">
            <span className="chat-welcome-mark"><Sparkles /></span>
            <h2>How can I help with your QA workflow?</h2>
            <p>
              Ask me to run a ticket, plan test cases, resume a workflow, inspect a
              result, or explain what the orchestrator is doing.
            </p>
            <div className="chat-welcome-suggestions">
              {SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  disabled={disabled || busy}
                  onClick={() => submit(suggestion)}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="chat-turns">
            {messages.map((message) => (
              <ChatTurn
                key={message.message_id}
                message={message}
                busy={busy}
                onConfirmAction={onConfirmAction}
                onCancelAction={onCancelAction}
              />
            ))}
            {busy ? (
              <div className="chat-turn assistant">
                <span className="chat-avatar"><Shield /></span>
                <div className="chat-bubble assistant">
                  <span className="chat-typing" aria-label="Thinking">
                    <span /><span /><span />
                  </span>
                </div>
              </div>
            ) : null}
          </div>
        )}
      </div>

      <div className="chat-composer-dock">
        <form
          className="chat-composer"
          onSubmit={(event) => {
            event.preventDefault();
            submit();
          }}
        >
          <textarea
            ref={textareaRef}
            value={draft}
            rows={1}
            disabled={disabled}
            maxLength={10000}
            aria-label="Chat message"
            placeholder="Message AegisQA…"
            onChange={(event) => {
              setDraft(event.target.value);
              autosize(event.target);
            }}
            onKeyDown={onKeyDown}
          />
          <button
            type="submit"
            className="chat-send"
            aria-label="Send message"
            disabled={disabled || busy || !draft.trim()}
          >
            <Send />
          </button>
        </form>
        <p className="chat-disclaimer">
          AegisQA runs governed actions — you confirm anything that changes state.
        </p>
      </div>
    </div>
  );
}

function ChatTurn({
  message,
  busy,
  onConfirmAction,
  onCancelAction
}: {
  message: ChatMessage;
  busy: boolean;
  onConfirmAction: (actionId: string) => void;
  onCancelAction: (actionId: string) => void;
}) {
  if (message.role === "user") {
    return (
      <div className="chat-turn user">
        <div className="chat-bubble user">{message.content}</div>
      </div>
    );
  }

  // assistant / system: bare prose with a small avatar (ChatGPT/Claude idiom).
  return (
    <div className="chat-turn assistant">
      <span className="chat-avatar"><Shield /></span>
      <div className="chat-turn-body">
        {message.content ? <div className="chat-prose">{message.content}</div> : null}
        {message.actions.length ? (
          <div className="chat-action-stack">
            {message.actions.map((action) => (
              <ActionCard
                key={action.action_id}
                action={action}
                busy={busy}
                onConfirm={() => onConfirmAction(action.action_id)}
                onCancel={() => onCancelAction(action.action_id)}
              />
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function ActionCard({
  action,
  busy,
  onConfirm,
  onCancel
}: {
  action: ChatAction;
  busy: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const pending = action.status === "pending_confirmation";
  return (
    <div className={`action-card ${action.status}`}>
      <div className="action-card-head">
        <span className="action-card-icon"><Shield /></span>
        <div className="action-card-copy">
          <strong>{action.label}</strong>
          {action.description ? <span>{action.description}</span> : null}
        </div>
        {!pending ? (
          <span className={`action-card-status ${action.status}`}>
            {statusLabel(action.status)}
          </span>
        ) : null}
      </div>
      {pending ? (
        <div className="action-card-actions">
          <button type="button" className="action-confirm" disabled={busy} onClick={onConfirm}>
            <Check /> Confirm &amp; run
          </button>
          <button type="button" className="action-cancel" disabled={busy} onClick={onCancel}>
            <X /> Cancel
          </button>
        </div>
      ) : action.result_summary ? (
        <p className="action-card-result">{action.result_summary}</p>
      ) : null}
    </div>
  );
}

function statusLabel(status: ChatAction["status"]): string {
  if (status === "completed") return "done";
  if (status === "cancelled") return "cancelled";
  if (status === "blocked") return "blocked";
  return status;
}
