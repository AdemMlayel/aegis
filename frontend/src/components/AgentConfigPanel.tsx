import {
  Activity,
  BookOpen,
  Brain,
  ChevronRight,
  Cloud,
  Cpu,
  Database,
  History,
  LockKeyhole,
  RefreshCw,
  SlidersHorizontal
} from "lucide-react";
import type {
  AgentModelProfile,
  AgentModelRoute,
  AgentRoutingCatalog,
  AgentGovernanceCatalog,
  EmbeddingProvider,
  IntegrationProfile,
  LLMProvider,
  OllamaHealth,
  ObservabilitySummary,
  OperationalHealth,
  ProviderCatalog,
  TokenBudgetStatus,
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
  governance,
  observability,
  tokenBudget,
  operationalHealth,
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
  governance: AgentGovernanceCatalog | null;
  observability: ObservabilitySummary | null;
  tokenBudget: TokenBudgetStatus | null;
  operationalHealth: OperationalHealth | null;
  smokeBusy: boolean;
  onClose: () => void;
  onModeChange: (mode: WorkflowMode) => void;
  onApplyPreset: (preset: "external" | "local") => void;
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
          <button type="button" onClick={() => onApplyPreset("external")}>
            <Cloud />
            <span><strong>External live</strong><small>OpenAI for every LLM agent</small></span>
          </button>
          <button type="button" onClick={() => onApplyPreset("local")}>
            <Cpu />
            <span><strong>Private local</strong><small>Ollama role routing</small></span>
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
                      {providers
                        .filter((provider) => provider.name !== "mock_llm")
                        .map((provider) => (
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

      <ConfigSection icon={<LockKeyhole />} title="Governance">
        <div className="governance-metrics">
          <div><span>Identities</span><strong>{governance?.agents.length ?? 0}</strong></div>
          <div><span>Agent runs</span><strong>{observability?.agents.total ?? 0}</strong></div>
          <div><span>Tokens today</span><strong>{compactNumber(observability?.models.total_tokens ?? 0)}</strong></div>
          <div>
            <span>Token capacity</span>
            <strong>
              {tokenBudget
                ? `${compactNumber(tokenBudget.remaining_tokens)} left`
                : "--"}
            </strong>
          </div>
        </div>
        <div className="governance-status-list">
          <SourceRow
            label="Request gateway"
            status={`${observability?.requests.total ?? 0} requests`}
          />
          <SourceRow
            label="Policy enforcement"
            status="enabled"
          />
          <SourceRow
            label="Provider circuits"
            status={
              observability?.provider_circuits.some((item) => item.state === "open")
                ? "open circuit"
                : "healthy"
            }
            muted={observability?.provider_circuits.some((item) => item.state === "open")}
          />
          <SourceRow
            label="Operational health"
            status={operationalHealth?.status ?? "unknown"}
            muted={operationalHealth?.status === "degraded"}
          />
        </div>
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

function compactNumber(value: number): string {
  if (value < 1000) return String(value);
  if (value < 1_000_000) return `${(value / 1000).toFixed(1)}K`;
  return `${(value / 1_000_000).toFixed(1)}M`;
}
