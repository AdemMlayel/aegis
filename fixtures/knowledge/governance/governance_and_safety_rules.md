# Governance and Safety Rules

Synthetic statement of the governance and safety rules enforced by the AegisQA backend.
These rules are implemented in code; this document makes them retrievable so the
assistant can explain them.

## Agent and tool permissions

Each agent has a registered identity and policy. A policy declares the skills the agent
may run, the providers it may call, and per-call and per-workflow token budgets. A skill
may only invoke tools that the active agent execution explicitly allows. A tool call made
outside a governed skill, or for a tool not in the allow-list, is denied.

## Controlled tool execution

Tools never run directly from model output. Every tool call goes through the typed tool
registry, which authorizes the call against policy, then records attempts, duration, and
input/output hashes for audit. The model proposes; the backend decides and executes.

## Model selection control

Providers are restricted per agent. An agent configured for local demo uses the mock LLM
and local hash embeddings. Ollama and OpenAI-compatible providers are allowed only when
the agent policy lists them. An attempt to use a provider outside the policy is denied.

## Context and token monitoring

The governance gateway tracks model calls and token consumption per workflow against the
policy limits. Exceeding a limit raises a gateway error rather than silently continuing.

## Redaction and sensitive data

Sensitive values are redacted or replaced with placeholders before reaching a model
prompt. Generated artifacts must contain no real hostnames, addresses, credentials,
tokens, customer names, or internal identifiers.

## Human approval gate

Generated automation stays in pending review until validation passes and a human reviewer
approves it. Reviewers may approve, request changes, or block execution before any Git
handoff or execution promotion.

## Deterministic demo mode

When deterministic demo mode is enabled, the system selects safe local providers: mock
LLM, local hash embeddings, mock execution, and the demo ticket source. This makes
presentations reproducible without external services.

## Role-based access

API access is capability based. Viewer, QA engineer, QA lead, and admin roles map to
explicit capabilities such as reading tickets, starting a workflow, approving a workflow,
and reading audit data. Strict auth mode requires a token or explicit identity headers.
