import { Bot, Send, ShieldCheck, Sparkles } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ChatSession } from "../types";

type CopilotPanelProps = {
  session: ChatSession | null;
  busy: boolean;
  disabled: boolean;
  onSend: (message: string) => void;
  onConfirmAction: (actionId: string) => void;
};

const SUGGESTIONS = [
  "What is mocked and what is real?",
  "What is missing in this ticket?",
  "Where are we in the workflow?",
  "Explain the generated Robot file"
];

export function CopilotPanel({
  session,
  busy,
  disabled,
  onSend,
  onConfirmAction
}: CopilotPanelProps) {
  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [session?.messages.length]);

  function submit(message = draft) {
    const trimmed = message.trim();
    if (!trimmed || disabled || busy) return;
    onSend(trimmed);
    setDraft("");
  }

  return (
    <aside className="copilot-panel" aria-label="AegisQA Copilot">
      <header className="copilot-header">
        <span className="copilot-mark"><Bot /></span>
        <div>
          <strong>AegisQA Copilot</strong>
          <span>Chat-driven workflow control</span>
        </div>
      </header>

      <div className="copilot-suggestions">
        {SUGGESTIONS.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            disabled={disabled || busy}
            onClick={() => submit(suggestion)}
          >
            <Sparkles />
            {suggestion}
          </button>
        ))}
      </div>

      <div className="copilot-messages" ref={scrollRef}>
        {(session?.messages ?? []).map((message) => (
          <article key={message.message_id} className={`copilot-message ${message.role}`}>
            <p>{message.content}</p>
            {message.actions.length ? (
              <div className="copilot-actions">
                {message.actions.map((action) => (
                  <button
                    key={action.action_id}
                    type="button"
                    disabled={busy || action.status !== "pending_confirmation"}
                    onClick={() => onConfirmAction(action.action_id)}
                  >
                    <ShieldCheck />
                    {action.label}
                  </button>
                ))}
              </div>
            ) : null}
          </article>
        ))}
      </div>

      <form className="copilot-input" onSubmit={(event) => { event.preventDefault(); submit(); }}>
        <input
          value={draft}
          disabled={disabled || busy}
          placeholder="Ask about tickets, workflow, Robot, validation..."
          onChange={(event) => setDraft(event.target.value)}
        />
        <button type="submit" disabled={disabled || busy || !draft.trim()}>
          <Send />
        </button>
      </form>
    </aside>
  );
}
