# AegisQA Next Evolution Plan  
## Domain Grounding, Conversational Copilot, and Fully Orchestrated Intelligent QA Workflow

**Document purpose:**  
This document summarizes the proposed next direction for AegisQA after the current architecture-hardening phase. It explains how sanitized project examples should be used to shape the agents, how a chatbot layer should be added, what should be improved, and which implementation phases should follow.

---

## 1. Current Project Position

AegisQA has reached a strong architecture-proof state. The system is no longer only a basic proof of concept. It already contains the core technical foundations needed for a controlled intelligent QA automation platform.

### Current strengths

- Backend workflow graph is implemented.
- Agent → Skill → Tool separation exists.
- Local/demo ticket provider exists.
- LLM provider abstraction exists.
- Ollama, mock, and OpenAI-compatible provider modes exist.
- RAG and memory foundations exist.
- Robot Framework generation and validation exist.
- Execution adapters exist.
- Investigation and report generation foundations exist.
- Human approval flow exists.
- Governance, audit, and observability foundations exist.
- Frontend is usable for PM-facing demonstrations.
- Deterministic demo mode exists for safe local presentations.
- External company systems are intentionally not required yet.

### Current limitation

The architecture is credible, but the generated outputs are still not sufficiently grounded in the real project style.

The next value does not come from adding more abstract modules. It comes from teaching AegisQA how real QA work looks by using a very small, sanitized reference corpus.

---

## 2. Strategic Direction

The next target should be:

> Transform AegisQA from an architecture-proof workflow into a domain-grounded, interactive QA copilot.

This means two major improvements:

1. **Use sanitized real structures to ground the agents.**
2. **Add a chatbot/copilot layer on top of the existing workflow cockpit.**

The final system should not be only a “select ticket and run workflow” tool. It should become an intelligent assistant that can answer questions, explain outputs, guide the user, propose actions, and execute controlled workflow steps.

---

## 3. Sanitized Reference Corpus

The user can currently provide:

- 5 Robot Framework test files.
- Custom libraries.
- 1 report example.
- 1 successful execution example.
- 1 failed execution example.

This is enough for the next milestone.

The goal is not to collect a large dataset. The goal is to capture structure, style, conventions, keywords, evidence patterns, and expected output formats.

### Recommended corpus structure

```text
fixtures/
  reference_corpus/
    raw_sanitized/
      robot_tests/
      robot_resources/
      custom_libs/
      reports/
      executions/
        successful/
        failed/

    normalized/
      robot_keywords/
      robot_style_profile/
      report_profile/
      execution_evidence_profile/

    metadata/
      corpus_manifest.json
```

### Corpus manifest example

```json
{
  "id": "robot-test-001",
  "type": "robot_test",
  "source": "sanitized_reference",
  "sensitivity": "sanitized",
  "allowed_for_demo": true,
  "contains_real_customer_data": false,
  "contains_credentials": false,
  "notes": "Sanitized representative Robot Framework test"
}
```

---

## 4. Sanitization Rules

All reference material must keep the real structure but remove sensitive values.

### Remove or replace

- IP addresses.
- Hostnames.
- Internal URLs.
- Credentials.
- Tokens.
- Customer names.
- Usernames.
- Emails.
- Real device names.
- Real environment names.
- Production IDs.
- Private comments.
- Internal topology details.

### Replace with safe placeholders

```text
DEMO_HOST_01
DEMO_SERVICE_A
DEMO_CUSTOMER
DEMO_ENV
DEMO_API_ENDPOINT
DEMO_TICKET_001
DEMO_USER
DEMO_TOKEN_REFERENCE
```

### Main rule

> Keep the shape. Remove the sensitivity.

---

## 5. How the Sanitized Files Shape the Agents

The sanitized files should not be hardcoded into prompts or business logic. They should be converted into reusable project knowledge, validation rules, examples, and evaluation fixtures.

### 5.1 Robot tests

The 5 Robot tests should be used to extract:

- Naming conventions.
- Suite setup and teardown patterns.
- Test case structure.
- Tags.
- Variable style.
- Resource imports.
- Keyword composition.
- Assertion style.
- Data-driven patterns.
- Common success and failure checks.

This creates a **Robot style profile**.

### 5.2 Custom libraries

The custom libraries should be used to extract:

- Available keyword names.
- Source library or resource file.
- Keyword arguments.
- Keyword documentation.
- Expected return behavior.
- Exceptions and failure behavior.
- Common usage examples.

This creates a **Robot keyword capability registry**.

The Automation Agent should then generate Robot tests using known keywords instead of inventing generic or unrealistic keywords.

### 5.3 Report example

The report example should be used to extract:

- Expected report sections.
- Summary style.
- Technical detail level.
- PM-level explanation style.
- Evidence formatting.
- Failure classification format.
- Recommendation format.

This creates a **report template profile**.

The Report Generator should then produce outputs closer to the expected project communication style.

### 5.4 Successful execution example

The successful execution example should be used to understand:

- What a normal execution artifact set looks like.
- Which files matter.
- How success is represented.
- What evidence should be stored.
- Which execution metadata should be shown in the UI.

This improves the Execution Agent and the evidence model.

### 5.5 Failed execution example

The failed execution example should be used to understand:

- Where errors appear.
- How failed Robot executions are structured.
- Which logs are useful.
- What failure patterns are common.
- How to classify root-cause hints.
- How to build useful investigation summaries.

This improves the Investigation Agent and the Memory Agent.

---

## 6. Target Final Workflow

The final AegisQA workflow should be fully orchestrated and interactive.

```text
1. Ticket / LLD intake
   ↓
2. Requirement understanding
   ↓
3. Clarification gate if needed
   ↓
4. Knowledge and memory retrieval
   ↓
5. Coverage planning
   ↓
6. Test case generation
   ↓
7. Test data resolution
   ↓
8. Robot automation generation
   ↓
9. Robot validation
   ↓
10. Human review, edit, approve
   ↓
11. Execution
   ↓
12. Failure investigation
   ↓
13. Technical and PM report
   ↓
14. Memory archive
   ↓
15. Feedback into future workflows
```

The system should not be fully automatic by default. It should be controlled, explainable, and human-supervised.

---

## 7. Chatbot + Workflow Cockpit Direction

A chatbot layer should be added, but it should not replace the workflow cockpit.

The ideal product experience is:

```text
Chatbot + Workflow Cockpit
```

### Why a chatbot is useful

A chatbot makes the system more interactive. It allows the user to ask questions, guide the workflow, request explanations, and trigger controlled actions.

Examples:

```text
Analyze this ticket.
What is missing in this requirement?
Which tests would you generate?
Why is this scenario high risk?
Show only negative test cases.
Regenerate the Robot file using known custom keywords.
Explain this Robot validation error.
Why did this execution fail?
Have we seen a similar failure before?
Generate a PM-friendly summary.
```

### Why the cockpit is still needed

The workflow cockpit provides:

- Workflow status.
- Agent progress.
- Evidence references.
- Generated artifacts.
- Validation output.
- Approval state.
- Execution result.
- Investigation evidence.
- Report view.
- Memory archive.

The chatbot gives interaction.  
The cockpit gives visibility and governance.

---

## 8. Proposed Chatbot Architecture

The chatbot should sit above the current workflow engine.

```text
User
  ↓
Chat UI
  ↓
Assistant Orchestrator / Intent Router
  ↓
Workflow Service / Tools / RAG / Memory
  ↓
Governed actions and visible workflow state
```

The LLM should not directly perform uncontrolled actions. It should classify intent and request backend-controlled actions.

### Suggested backend modules

```text
backend/chat/
  router.py
  intent_classifier.py
  conversation_state.py
  response_builder.py
  action_planner.py
  safety.py
```

### Suggested API endpoints

```text
POST /api/v1/chat/sessions
POST /api/v1/chat/sessions/{session_id}/messages
GET  /api/v1/chat/sessions/{session_id}
POST /api/v1/chat/actions/{action_id}/confirm
```

---

## 9. Chatbot Intent Types

| Intent | Example | Backend Behavior |
|---|---|---|
| `system_question` | What is mocked and what is real? | Read provider profile and system status |
| `ticket_question` | What is missing in this ticket? | Query ticket and requirement context |
| `workflow_start` | Analyze this ticket | Start workflow |
| `workflow_step` | Generate test cases | Run or resume selected workflow step |
| `artifact_question` | Explain this Robot file | Read artifact and use RAG/context |
| `approval_request` | Approve this workflow | Require explicit confirmation |
| `execution_request` | Run the tests | Require explicit confirmation |
| `investigation_question` | Why did this fail? | Use evidence and memory |
| `report_request` | Generate a PM summary | Use report generator |
| `knowledge_question` | Which Robot keywords are available? | Query keyword registry |

---

## 10. Safety and Governance Rules

The chatbot must follow clear safety rules.

### Read actions

Read-only actions can run directly.

Examples:

- Summarize ticket.
- Search knowledge.
- Explain report.
- Show provider status.
- Show workflow progress.
- Explain validation errors.

### Controlled actions

Actions that modify state or run execution require confirmation.

Examples:

- Generate automation.
- Regenerate files.
- Approve workflow.
- Execute tests.
- Archive memory.
- Create Git handoff.
- Trigger external provider action.

### External actions

External/company actions remain disabled until explicitly configured.

Examples:

- Real Jira update.
- Real Git PR.
- Real CI execution.
- Real Vault access.
- Real internal system calls.

---

## 11. Final Agentic System Vision

The final system should be an orchestrated multi-agent QA platform.

```text
Aegis Orchestrator Agent
│
├── Requirement Agent
├── Knowledge Agent
├── Coverage Agent
├── Test Design Agent
├── Automation Agent
├── Validation Agent
├── Execution Agent
├── Investigation Agent
├── Reporting Agent
└── Memory Agent
```

Each agent should use skills and tools through governed interfaces.

```text
Agent → Skill → Tool → Local Provider / Future External System
```

Agents should not directly call external systems.

Tools should be typed, auditable, retryable, and policy-controlled.

---

## 12. Target Frontend Experience

The frontend should evolve into a **QA command center**.

### Recommended layout

```text
Left panel:
- Ticket selection
- Chat history
- Workflow timeline
- Provider status

Center panel:
- Active agent output
- Requirement analysis
- Coverage plan
- Test cases
- Robot automation
- Execution evidence
- Report

Right panel:
- Evidence references
- Retrieved knowledge
- Memory matches
- Validation warnings
- Human actions
```

### User actions

The user should be able to:

- Ask the agent questions.
- Start a workflow from chat.
- Pause or resume workflow.
- Approve or reject outputs.
- Edit generated test cases.
- Regenerate one section only.
- View why the agent made a decision.
- View evidence.
- Run execution.
- Export reports.
- Archive useful results into memory.

---

## 13. Operating Modes

AegisQA should support three clear operating modes.

### 13.1 Deterministic Demo Mode

Purpose: PM demo and stable local testing.

```text
Mock LLM
Local hash embeddings
Demo tickets
Mock execution
Stable outputs
No external dependency
```

### 13.2 Local AI Mode

Purpose: development and real local AI testing.

```text
Ollama
nomic-embed-text
Local RAG
Local Robot execution
Docker Robot execution if available
```

### 13.3 Enterprise Integration Mode

Purpose: future production pilot.

```text
Jira / Azure
Company knowledge sources
SSO
Vault
Git PRs
CI runners
PostgreSQL
Vector DB
Monitoring
```

Enterprise mode should not be implemented until providers, credentials, security approvals, and data access are available.

---

## 14. Recommended Implementation Phases

### Phase 8A — Robot, Execution, and Report Grounding

Goal: Make generated outputs look and behave closer to the real QA project style.

Tasks:

1. Add sanitized reference corpus structure.
2. Add corpus manifest and sensitivity metadata.
3. Extract Robot keywords from custom libraries and resources.
4. Extract Robot style profile from the 5 Robot tests.
5. Upgrade AutomationGenerator to use known keywords.
6. Upgrade Validator to check imports, keywords, and arguments.
7. Parse successful and failed execution examples.
8. Upgrade InvestigationCoordinator with evidence categories.
9. Upgrade ReportGenerator using report profile.
10. Add tests proving generated Robot follows project style.

### Phase 8B — Conversational QA Copilot

Goal: Add a chatbot layer over the workflow cockpit.

Tasks:

1. Add chat session model.
2. Add chat API endpoints.
3. Add intent classifier.
4. Add action planner.
5. Add confirmation flow for controlled actions.
6. Add ticket Q&A.
7. Add workflow Q&A.
8. Add artifact Q&A.
9. Add investigation Q&A.
10. Add frontend chat panel.
11. Connect chat actions to workflow service.

### Phase 8C — Interactive Review Cockpit

Goal: Make human-in-the-loop review more useful.

Tasks:

1. Add side-by-side review panels.
2. Add diff view for regenerated outputs.
3. Add per-test approval.
4. Add inline comments.
5. Add regenerate-section action.
6. Add validation warning explanations.
7. Add report preview and export actions.

### Phase 8D — Evaluation and Quality Gates

Goal: Prove that agent outputs improve and do not regress.

Tasks:

1. Add golden test cases from sanitized examples.
2. Add Robot style compliance tests.
3. Add report format compliance tests.
4. Add investigation classification tests.
5. Add prompt regression tests.
6. Add RAG retrieval quality checks.
7. Add CI-ready quality gate.

### Phase 9 — Enterprise Readiness

Goal: Prepare for controlled connection to real systems.

Tasks:

1. Add production PostgreSQL adapter.
2. Add production vector DB adapter.
3. Add enterprise identity integration.
4. Add Vault provider.
5. Add real Jira/Azure connector behind existing interface.
6. Add Git PR workflow with company repository policy.
7. Add CI runner integration.
8. Add production observability and monitoring.
9. Add deployment hardening.

---

## 15. What Not to Do Yet

Avoid these mistakes:

- Do not connect real company APIs too early.
- Do not upload large sensitive datasets.
- Do not hardcode sanitized examples into prompts.
- Do not let the LLM directly execute tools.
- Do not let the chatbot bypass approval.
- Do not generate Robot code using invented keywords.
- Do not claim production readiness while providers are local/demo.
- Do not replace the workflow cockpit with only a chat window.

---

## 16. Recommended Immediate Next Step

Once the sanitized files are ready, the next implementation should be:

```text
Milestone 8A — Robot, Execution, and Report Grounding
```

This will make AegisQA more realistic without requiring sensitive data or real company APIs.

The priority should be:

1. Ingest sanitized Robot examples.
2. Build keyword registry.
3. Build Robot style profile.
4. Upgrade automation generation.
5. Upgrade validation.
6. Parse execution examples.
7. Upgrade investigation.
8. Upgrade reports.
9. Add tests.

After that, implement:

```text
Milestone 8B — Conversational QA Copilot
```

This sequence is important because the chatbot will be much more useful once it can answer questions about real project-style Robot tests, execution evidence, and reports.

---

## 17. Final Product Summary

The final AegisQA system should be:

```text
A governed conversational QA copilot
combined with a visible workflow cockpit
powered by specialist agents,
grounded in sanitized project knowledge,
able to generate, validate, execute, investigate, report, and learn.
```

It should allow the user to:

- Ask questions.
- Understand requirements.
- Generate coverage.
- Generate test cases.
- Generate Robot automation.
- Validate artifacts.
- Approve or request changes.
- Execute locally or through controlled adapters.
- Investigate failures.
- Generate reports.
- Store lessons in memory.

This is the target state of a fully orchestrated, interactive, intelligent agentic QA system.
