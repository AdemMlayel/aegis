import {
  Activity,
  BookOpen,
  Brain,
  ChevronRight,
  Cloud,
  Cpu,
  Database,
  History,
  RefreshCw,
  ShieldCheck,
  SlidersHorizontal
} from "lucide-react";
import type {
  AgentModelProfile,
  AgentModelRoute,
  AgentRoutingCatalog,
  EmbeddingProvider,
  IntegrationProfile,
  LLMProvider,
  OllamaHealth,
  ProviderCatalog,
  WorkflowMode
} from "../types";

export function AgentConfigPanel({
  routing,
  providers,
  embeddingProviders,
  routes,
  mode,
  embeddingProvider,
  embeddingModel,
  providerCatalog,
  integrationProfile,
  ollamaHealth,
  smokeBusy,
  onClose,
  onModeChange,
  onApplyPreset,
  onProviderChange,
  onModelChange,
  onEmbeddingProviderChange,
  onEmbeddingModelChange,
  onSmokeTest,
  onOpenLogs,
  onOpenMemory
}: {
  routing: AgentRoutingCatalog | null;
  providers: LLMProvider[];
  embeddingProviders: EmbeddingProvider[];
  routes: Record<string, AgentModelRoute>;
  mode: WorkflowMode;
  embeddingProvider: string;
  embeddingModel: string;
  providerCatalog: ProviderCatalog | null;
  integrationProfile: IntegrationProfile | null;
  ollamaHealth: OllamaHealth | null;
  smokeBusy: boolean;
  onClose: () => void;
  onModeChange: (mode: WorkflowMode) => void;
  onApplyPreset: (preset: "safe" | "local" | "hybrid") => void;
  onProviderChange: (profile: AgentModelProfile, provider: string) => void;
  onModelChange: (profile: AgentModelProfile, model: string) => void;
  onEmbeddingProviderChange: (provider: string) => void;
  onEmbeddingModelChange: (model: string) => void;
  onSmokeTest: () => void;
  onOpenLogs: () => void;
  onOpenMemory: () => void;
}) {
  return (
    <aside className="config-panel">
      <div className="config-header">
        <div>
          <span className="panel-kicker">Runtime</span>
          <h2>Agent configuration</h2>
        </div>
        <button className="icon-command" onClick={onClose} title="Collapse configuration">
          <ChevronRight />
        </button>
      </div>

      <ConfigSection icon={<SlidersHorizontal />} title="Execution mode">
        <div className="segmented-control">
          {([
            ["autonomous", "Auto"],
            ["approval_required", "Review"],
            ["step_by_step", "Step"]
          ] as Array<[WorkflowMode, string]>).map(([value, label]) => (
            <button
              type="button"
              key={value}
              className={mode === value ? "active" : ""}
              onClick={() => onModeChange(value)}
            >
              {label}
            </button>
          ))}
        </div>
      </ConfigSection>

      <ConfigSection icon={<Brain />} title="Routing presets">
        <div className="preset-list">
          <button type="button" onClick={() => onApplyPreset("safe")}>
            <ShieldCheck />
            <span><strong>Safe demo</strong><small>Deterministic and offline</small></span>
          </button>
          <button type="button" onClick={() => onApplyPreset("local")}>
            <Cpu />
            <span><strong>Private local</strong><small>Ollama role routing</small></span>
          </button>
          <button type="button" onClick={() => onApplyPreset("hybrid")}>
            <Cloud />
            <span><strong>Hybrid best</strong><small>External reasoning, local RAG</small></span>
          </button>
        </div>
      </ConfigSection>

      <ConfigSection icon={<Cpu />} title="Agent models">
        <div className="agent-config-list">
          {(routing?.agents ?? []).map((profile) => {
            const route = routes[profile.agent_name] ?? {
              provider: profile.recommended_provider ?? "mock_llm",
              model: profile.recommended_model
            };
            return (
              <div className="agent-config-row" key={profile.agent_name}>
                <div className="agent-config-title">
                  <span className={`agent-dot ${profile.uses_llm ? "enabled" : "fixed"}`} />
                  <div>
                    <strong>{profile.label}</strong>
                    <small>{profile.uses_llm ? profile.rationale : "Deterministic tool boundary"}</small>
                  </div>
                </div>
                {profile.uses_llm ? (
                  <div className="agent-config-controls">
                    <select
                      aria-label={`${profile.label} provider`}
                      value={route.provider}
                      onChange={(event) => onProviderChange(profile, event.target.value)}
                    >
                      {providers.map((provider) => (
                        <option
                          key={provider.name}
                          value={provider.name}
                          disabled={!provider.selectable}
                        >
                          {provider.mode} - {provider.name}
                          {provider.selectable ? "" : ` - ${provider.configuration_status}`}
                        </option>
                      ))}
                    </select>
                    <input
                      aria-label={`${profile.label} model`}
                      value={route.model ?? ""}
                      onChange={(event) => onModelChange(profile, event.target.value)}
                      placeholder={
                        route.provider === "ollama"
                          ? profile.local_model ?? "role default"
                          : profile.external_model ?? "provider default"
                      }
                    />
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      </ConfigSection>

      <ConfigSection icon={<Database />} title="RAG embeddings">
        <label className="config-field">
          <span>Provider</span>
          <select
            value={embeddingProvider}
            onChange={(event) => onEmbeddingProviderChange(event.target.value)}
          >
            {embeddingProviders.map((provider) => (
              <option
                key={provider.name}
                value={provider.name}
                disabled={!provider.selectable}
              >
                {provider.name}
              </option>
            ))}
          </select>
        </label>
        <label className="config-field">
          <span>Model</span>
          <input
            value={embeddingModel}
            onChange={(event) => onEmbeddingModelChange(event.target.value)}
            placeholder={routing?.embedding.recommended_model ?? "nomic-embed-text"}
          />
        </label>
        <p className="config-note">
          {routing?.embedding.rationale ?? "Local embeddings keep ticket and knowledge text on this machine."}
        </p>
      </ConfigSection>

      <ConfigSection icon={<BookOpen />} title="Knowledge sources">
        <SourceRow label="Local documentation" status="ready" />
        <SourceRow label="Historical test memory" status="ready" />
        <SourceRow
          label="Ticket provider"
          status={integrationName(integrationProfile, "ticket_connector") ?? "jira_mock"}
        />
        <SourceRow
          label="External connectors"
          status={providerCatalog?.external_connectors_enabled ? "enabled" : "disabled"}
          muted={!providerCatalog?.external_connectors_enabled}
        />
      </ConfigSection>

      <ConfigSection icon={<Activity />} title="Provider status">
        <div className="provider-health">
          <span className={ollamaHealth?.available ? "status-light ready" : "status-light warning"} />
          <div>
            <strong>Ollama</strong>
            <small>{ollamaHealth?.message ?? "Not checked"}</small>
          </div>
        </div>
        <button className="command-button subtle" onClick={onSmokeTest} disabled={smokeBusy}>
          <RefreshCw className={smokeBusy ? "spin" : ""} /> Test local models
        </button>
      </ConfigSection>

      <ConfigSection icon={<History />} title="Session">
        <div className="session-links">
          <button type="button" onClick={onOpenLogs}><Activity /> View logs</button>
          <button type="button" onClick={onOpenMemory}><Brain /> Agent memory</button>
        </div>
      </ConfigSection>
    </aside>
  );
}

function ConfigSection({
  icon,
  title,
  children
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="config-section">
      <div className="config-section-title">{icon}<h3>{title}</h3></div>
      {children}
    </section>
  );
}

function SourceRow({
  label,
  status,
  muted = false
}: {
  label: string;
  status: string;
  muted?: boolean;
}) {
  return (
    <div className={`source-row ${muted ? "muted" : ""}`}>
      <span>{label}</span>
      <strong>{status}</strong>
    </div>
  );
}

function integrationName(
  profile: IntegrationProfile | null,
  key: string
): string | null {
  const value = profile?.[key];
  if (!value || typeof value === "string" || typeof value === "boolean") return null;
  return value.name;
}
