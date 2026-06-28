# AegisQA Next Evolution Plan v2  
## NTF-Aligned Domain Grounding, Conversational Copilot, and Governed Multi-Agent QA Workflow

**Prepared for:** AegisQA / NTF AI project discussion  
**Purpose:** Define the next evolution of the current AegisQA implementation, aligned with the NTF AI Architecture Blueprint and the NTF AI Program Roadmap.  
**Scope:** Local/demo-first implementation, using sanitized examples only, while preparing the architecture for future enterprise integration.

---

## 1. Executive Summary

AegisQA has moved beyond a simple proof of concept. The current implementation already has a strong local architecture foundation:

- Workflow orchestration.
- Agent → Skill → Tool separation.
- Local/demo ticket provider.
- Deterministic demo mode.
- LLM provider abstraction.
- Ollama/local model readiness.
- RAG and memory foundations.
- Robot Framework generation and validation.
- Execution adapters.
- Investigation and report generation foundations.
- Human approval flow.
- Governance, audit, and observability foundations.
- PM-demo frontend.

The next evolution should not focus on adding more abstract architecture. The project now needs to become:

> A governed conversational QA copilot, backed by a deterministic workflow engine, specialized agents, sanitized project knowledge, Robot Framework grounding, execution evidence, and human approval gates.

This plan updates the previous evolution plan by aligning it explicitly with:

1. The NTF AI Architecture Blueprint.
2. The NTF AI Program Roadmap.
3. The Telefónica AI Agent Framework direction.
4. The current practical constraint: no real company systems or sensitive data yet.

---

## 2. Alignment with the NTF AI Architecture Blueprint

The NTF AI Architecture Blueprint defines the target system as:

- Vendor-agnostic.
- On-premise.
- Multi-agent.
- Deterministic-first.
- Human-gated.
- Physically isolated per operator.
- Governed through an Agent Gateway.
- Supported by RAG, memory, tool registries, observability, and lifecycle controls.

The blueprint also defines four specialized agents:

1. Assistant.
2. Failure Analysis.
3. Classification.
4. Test Generation.

AegisQA should align to this by treating the current implementation as the shared platform foundation and gradually mapping the current workflow agents to the NTF agent fleet.

---

## 3. Alignment with the NTF AI Program Roadmap

The roadmap defines four subprojects over a ten-month program:

| Subproject | Purpose | AegisQA Alignment |
|---|---|---|
| SP1 — Multilingual Assistant | Operational assistant and orchestration | Chatbot/copilot layer, ticket Q&A, workflow control |
| SP2 — Automated Failure Analysis | Failure investigation and remediation support | Execution evidence, failed-run parsing, Investigation Agent |
| SP3 — Failure Classification | Intelligent classification and routing | Failure categories, confidence scoring, routing recommendations |
| SP4 — Test Case Generation | Regression optimization and scenario generation | Test design, Robot generation, regression recommendations |

The current AegisQA system mostly supports the foundations of SP1, with early pieces of SP2 and SP4. The next work should therefore be staged as:

1. Strengthen SP1 as a conversational assistant and workflow cockpit.
2. Ground SP2 and SP4 using sanitized Robot, report, and execution examples.
3. Add classification logic later once enough failure examples are available.

---

## 4. Core Architectural Principles

The following principles should guide all next work.

### 4.1 Deterministic orchestrator

The orchestrator should decide routes using explicit workflow state, rules, capabilities, and policies.

The LLM should not freely decide which system action to perform.

### 4.2 Model drafts, system validates

LLMs may draft:

- Requirement analysis.
- Coverage proposals.
- Test case suggestions.
- Report summaries.
- Failure explanations.

But the system must validate, structure, and gate outputs before they affect execution or artifacts.

### 4.3 Execution is not agentic

The LLM must never directly execute tests against a system-under-test.

Execution must be:

- Deterministic.
- Policy-authorized.
- Human-gated when required.
- Performed through controlled execution adapters.

### 4.4 Human-in-the-loop is mandatory

Human approval should exist before sensitive actions such as:

- Executing generated tests.
- Creating Git handoff.
- Writing back to external systems.
- Archiving important memory.
- Confirming uncertain classifications.

### 4.5 Real structure, sanitized content

The next grounding corpus should preserve real project shape while removing all sensitive values.

The system does not need large datasets. It needs representative structures.

### 4.6 Local/demo first, enterprise later

Until real providers, credentials, and security approvals exist, all integrations remain local/demo adapters.

---

## 5. Current State Assessment

### Current maturity

```text
Architecture-proof ready: yes
PM demo capable: yes
Production ready: no
Enterprise integration ready: partially, through interfaces only
```

### What is already strong

- Local workflow engine.
- Agent/Skill/Tool boundaries.
- Provider abstractions.
- Deterministic demo mode.
- Local model configuration.
- RAG and memory base.
- Workflow traceability.
- Robot generation and validation foundation.
- Execution and investigation placeholders.
- PM-facing frontend foundation.
- Clean packaging and test readiness.

### What needs improvement

- Generated Robot outputs need to reflect project style.
- Automation must use known custom keywords, not invented keywords.
- Validation must understand imports, resources, custom libraries, and keyword arguments.
- Investigation must be grounded in real execution evidence patterns.
- Reports must follow expected project reporting style.
- Chatbot interaction should be added on top of the workflow cockpit.
- Frontend should evolve into a QA command center.
- Evaluation/golden tests should be added from sanitized examples.

---

## 6. Sanitized Reference Corpus Strategy

The user can safely provide a small sanitized corpus:

- 5 Robot Framework test files.
- Custom libraries or keyword manifest.
- 1 report example.
- 1 successful execution example.
- 1 failed execution example.

This is enough for the next milestone.

The goal is not to train a model. The goal is to extract:

- Structure.
- Conventions.
- Keyword vocabulary.
- Validation rules.
- Report style.
- Evidence patterns.
- Failure signals.
- Golden test cases.

### Recommended folder structure

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
      failure_patterns/

    metadata/
      corpus_manifest.json
```

### Corpus manifest fields

Each file should be registered with metadata:

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

## 7. Sanitization Rules

All uploaded examples must be sanitized before being added to the repository.

### Remove or replace

- IP addresses.
- Hostnames.
- Internal URLs.
- Credentials.
- Tokens.
- Customer names.
- Usernames.
- Emails.
- Device names.
- Environment names.
- Production IDs.
- Private comments.
- Internal topology details.

### Safe replacement examples

```text
DEMO_HOST_01
DEMO_SERVICE_A
DEMO_CUSTOMER
DEMO_ENV
DEMO_API_ENDPOINT
DEMO_TICKET_001
DEMO_USER
DEMO_TOKEN_REFERENCE
DEMO_DEVICE_01
DEMO_OPERATOR_A
```

### Main rule

```text
Keep the format and structure.
Remove sensitive values.
```

---

## 8. How the Sanitized Corpus Shapes the Agents

### 8.1 Assistant Agent

The Assistant Agent should use the sanitized corpus to answer questions such as:

- What can the system do?
- Which providers are currently active?
- What is mocked and what is real?
- What does this ticket require?
- Which generated tests were created?
- Why did validation fail?
- Which evidence supports this report?

The Assistant Agent becomes the conversational entry point of SP1.

### 8.2 Failure Analysis Agent

The failed and successful execution examples should shape:

- Evidence extraction.
- Robot output parsing.
- Failure category hints.
- Root-cause summaries.
- Confidence scoring.
- Similar failure retrieval.
- Report recommendations.

This prepares SP2.

### 8.3 Classification Agent

The current corpus has only one failed execution example, so classification should remain light for now.

Recommended current scope:

- Rule-based initial categories.
- Confidence placeholder.
- Human validation.
- Memory-ready structure.

Future scope:

- Train/evaluate classifier once more labelled failures exist.

This prepares SP3 without pretending full classification is ready.

### 8.4 Test Generation Agent

The Robot tests and custom libraries should shape:

- Test case style.
- Robot generation style.
- Keyword selection.
- Resource imports.
- Setup and teardown patterns.
- Tags and naming conventions.
- Positive/negative/boundary/regression generation.

This prepares SP4.

---

## 9. Robot Grounding Strategy

Robot grounding is the highest-value next improvement.

### 9.1 Robot Keyword Capability Registry

Create a registry from:

- Custom Python libraries.
- Robot resource files.
- Existing Robot tests.
- Optional keyword manifest.

The registry should store:

| Field | Description |
|---|---|
| Keyword name | Human-readable Robot keyword |
| Source | Library/resource file |
| Arguments | Required and optional arguments |
| Documentation | Docstring or extracted description |
| Return behavior | Expected return value if known |
| Tags | Domain, protocol, setup, assertion, utility |
| Usage examples | Sanitized usage snippets |
| Sensitivity | Sanitized/demo/internal |

### 9.2 Robot Style Profile

Extract from the 5 Robot tests:

- Suite naming style.
- Test naming style.
- Tag conventions.
- Variables format.
- Imports and resources.
- Setup/teardown pattern.
- Keyword composition pattern.
- Assertion style.
- Data-driven conventions.

### 9.3 AutomationGenerator upgrade

The AutomationGenerator should:

- Retrieve relevant known keywords.
- Generate Robot tests using only available keywords.
- Follow the Robot style profile.
- Include traceability comments or metadata.
- Avoid invented imports and keywords.
- Produce artifacts that can be validated locally.

### 9.4 Validator upgrade

The Validator should check:

- Robot syntax.
- Resource imports.
- Library imports.
- Known keyword availability.
- Keyword argument counts.
- Variable references.
- Setup/teardown existence.
- Data references.
- Style profile compliance.

---

## 10. Execution and Investigation Grounding

### 10.1 Successful execution example

Use it to define what success looks like:

- Expected artifact files.
- Execution status structure.
- Runtime metadata.
- Logs.
- Output XML.
- Report HTML.
- Success indicators.

### 10.2 Failed execution example

Use it to define what failure looks like:

- Error location.
- Failed keyword.
- Stack trace shape.
- Assertion error shape.
- Environment failure hints.
- Product failure hints.
- Automation failure hints.
- Evidence needed for report.

### 10.3 Investigation evidence model

Create structured evidence items:

```text
EvidenceItem
- id
- type
- source_artifact
- severity
- summary
- extracted_text
- related_test
- related_keyword
- confidence
- recommendation
```

Evidence categories:

- Robot syntax failure.
- Missing keyword.
- Keyword argument mismatch.
- Assertion failure.
- Timeout.
- Environment issue.
- Data issue.
- Product behavior issue.
- Unknown.

---

## 11. Report Grounding Strategy

The report example should define a reusable report profile.

### Extracted profile fields

- Report title format.
- Executive summary style.
- Technical details section.
- Evidence section.
- Failure classification section.
- Recommendations section.
- Risk level format.
- Next action format.
- Tone and length.

### ReportGenerator upgrade

The ReportGenerator should produce:

1. PM summary.
2. Technical report.
3. Evidence-backed failure analysis.
4. Recommended next actions.
5. Traceability from ticket → tests → execution → evidence.

The report should clearly distinguish:

- What was generated.
- What was validated.
- What was executed.
- What failed or passed.
- What is inferred.
- What requires human confirmation.

---

## 12. Chatbot + Workflow Cockpit

The system should become:

```text
Chatbot + Workflow Cockpit
```

The chatbot should provide interaction.  
The cockpit should provide visibility, traceability, and governance.

### 12.1 Why add a chatbot

A chatbot allows the user to ask:

```text
Analyze this ticket.
What is missing?
Which tests would you generate?
Why is this scenario high risk?
Show me the generated Robot file.
Which custom keywords are used?
Explain this validation error.
Why did execution fail?
Have we seen this failure before?
Generate a PM summary.
```

This makes AegisQA feel like a QA copilot rather than a simple pipeline.

### 12.2 Why keep the cockpit

The cockpit remains necessary because it shows:

- Workflow timeline.
- Current agent.
- Generated artifacts.
- Validation status.
- Approval status.
- Execution results.
- Evidence.
- Report.
- Memory archive.

### 12.3 Chatbot architecture

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

The chatbot must not bypass the deterministic workflow.

---

## 13. Chatbot Backend Design

Suggested modules:

```text
backend/chat/
  router.py
  intent_classifier.py
  conversation_state.py
  response_builder.py
  action_planner.py
  safety.py
  schemas.py
```

Suggested API endpoints:

```text
POST /api/v1/chat/sessions
GET  /api/v1/chat/sessions/{session_id}
POST /api/v1/chat/sessions/{session_id}/messages
POST /api/v1/chat/actions/{action_id}/confirm
```

---

## 14. Chatbot Intent Types

| Intent | Example | Backend Behavior |
|---|---|---|
| `system_question` | What is mocked and what is real? | Read provider profile and system status |
| `ticket_question` | What is missing in this ticket? | Query ticket and requirement context |
| `workflow_start` | Analyze this ticket | Start workflow |
| `workflow_step` | Generate test cases | Run or resume workflow step |
| `artifact_question` | Explain this Robot file | Read artifact and retrieve context |
| `approval_request` | Approve this workflow | Require explicit confirmation |
| `execution_request` | Run the tests | Require explicit confirmation |
| `investigation_question` | Why did this fail? | Use evidence and memory |
| `report_request` | Generate a PM summary | Use report generator |
| `knowledge_question` | Which Robot keywords are available? | Query keyword registry |

---

## 15. Chatbot Safety Model

### Read actions

Can be executed directly:

- Summarize a ticket.
- Search knowledge.
- Explain generated artifacts.
- Explain validation.
- Show workflow status.
- Show provider status.
- Explain report.

### Controlled actions

Require confirmation:

- Generate artifacts.
- Regenerate automation.
- Approve workflow.
- Execute tests.
- Archive memory.
- Create Git handoff.
- Trigger external write-back.

### Disabled until enterprise configuration

Remain unavailable for now:

- Real Jira updates.
- Real Git PRs to company repos.
- Real CI execution.
- Real Vault access.
- Real internal system calls.

---

## 16. Target Frontend Experience

The frontend should evolve into a QA command center.

### Recommended layout

```text
Left panel:
- Chat history
- Ticket selection
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

### User capabilities

The user should be able to:

- Ask questions.
- Start workflow from chat.
- Pause/resume workflow.
- Approve/reject generated outputs.
- Edit generated test cases.
- Regenerate one section only.
- View why an agent made a decision.
- View evidence references.
- Run execution.
- Export reports.
- Archive useful findings.

---

## 17. Operating Modes

### 17.1 Deterministic Demo Mode

Purpose: PM demos and stable local testing.

```text
Mock LLM
Local hash embeddings
Demo tickets
Mock execution
No external dependency
Stable output
```

### 17.2 Local AI Mode

Purpose: local AI testing.

```text
Ollama
nomic-embed-text
Local RAG
Local Robot execution
Docker Robot execution if available
```

### 17.3 Enterprise Integration Mode

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
Per-operator isolation
```

Enterprise mode must wait until providers, credentials, approvals, and security controls are available.

---

## 18. Data and Security Evolution

The NTF Architecture Blueprint emphasizes physical isolation per operator, redaction at ingest, untrusted input control, and governed egress. AegisQA should evolve toward those controls in stages.

### Current local/demo controls

- Sanitized fixtures.
- Local/demo providers.
- Deterministic demo mode.
- No real external systems.
- Provider interfaces.
- Human approval.
- Basic audit and observability.

### Next controls

- Corpus sensitivity metadata.
- Ingest redaction scanner.
- Prompt-injection scanner for logs and ticket text.
- Evidence classification.
- Explicit trust boundaries in code and docs.
- Per-operator abstraction in storage interfaces.

### Future controls

- Per-operator schema.
- Per-operator vector index.
- Per-operator backups.
- Enterprise auth.
- Vault integration.
- Governed egress.
- Production audit retention.

---

## 19. ADLC: Agent Development Lifecycle

The NTF roadmap emphasizes continuous testing, review gates, evaluation, simulation, deployment, and optimization.

AegisQA should implement this gradually.

### Immediate ADLC additions

- Golden tests from sanitized Robot examples.
- Report format compliance tests.
- Robot style compliance tests.
- Failure evidence parsing tests.
- Chat intent routing tests.
- Prompt structured-output tests.
- RAG retrieval quality tests.

### Future ADLC additions

- Agent simulation scenarios.
- Evaluation benchmark.
- Regression set for agent behavior.
- Model/provider comparison.
- Prompt optimization workflow.
- CI/CD/CT gate before deployment.

---

## 20. Recommended Implementation Phases

### Phase 8A — Robot, Execution, and Report Grounding

Goal: Make AegisQA outputs realistic and project-style aware.

Tasks:

1. Add sanitized reference corpus folder.
2. Add corpus manifest schema.
3. Add corpus ingestion service.
4. Extract Robot keyword registry.
5. Extract Robot style profile.
6. Upgrade AutomationGenerator to use known keywords.
7. Upgrade Validator to validate imports, keywords, and arguments.
8. Parse successful execution example.
9. Parse failed execution example.
10. Upgrade InvestigationCoordinator evidence extraction.
11. Upgrade ReportGenerator using report profile.
12. Add golden tests from sanitized examples.

### Phase 8B — Conversational QA Copilot

Goal: Add chatbot-based interaction over the existing workflow.

Tasks:

1. Add chat session model.
2. Add chat APIs.
3. Add intent classifier.
4. Add action planner.
5. Add confirmation flow.
6. Add system Q&A.
7. Add ticket Q&A.
8. Add workflow Q&A.
9. Add artifact Q&A.
10. Add investigation Q&A.
11. Add frontend chat panel.
12. Connect chat actions to workflow service.

### Phase 8C — Interactive Review Cockpit

Goal: Make human review more useful and PM-demo friendly.

Tasks:

1. Add side-by-side review panels.
2. Add diff view for regenerated artifacts.
3. Add per-test approval.
4. Add inline comments.
5. Add regenerate-section action.
6. Add validation warning explanations.
7. Add report preview/export.
8. Add evidence drill-down.

### Phase 8D — Evaluation and Quality Gates

Goal: Prove that agent outputs improve and do not regress.

Tasks:

1. Add Robot style compliance tests.
2. Add report profile compliance tests.
3. Add investigation classification tests.
4. Add prompt output schema tests.
5. Add chat intent tests.
6. Add RAG retrieval tests.
7. Add full demo workflow regression test.
8. Add CI-ready quality gate.

### Phase 9 — Enterprise Readiness

Goal: Prepare for real provider integration once approved.

Tasks:

1. Add PostgreSQL adapter.
2. Add pgvector or vector DB adapter.
3. Add enterprise identity provider.
4. Add Vault provider.
5. Add real Jira/Azure connector behind current interface.
6. Add Git PR workflow under company policy.
7. Add CI runner integration.
8. Add production observability.
9. Add deployment hardening.
10. Add per-operator isolation.

---

## 21. Mapping to Official NTF Subprojects

| Proposed Phase | Official NTF Subproject |
|---|---|
| Phase 8A Robot/Execution/Report Grounding | SP2 Failure Analysis + SP4 Test Generation |
| Phase 8B Conversational QA Copilot | SP1 Multilingual Assistant |
| Phase 8C Interactive Review Cockpit | SP1 + SP2 + SP4 shared workflow |
| Phase 8D Evaluation and Quality Gates | Shared ADLC across all SPs |
| Phase 9 Enterprise Readiness | Platform foundation for SP1–SP4 |

---

## 22. What Not to Do Yet

Avoid:

- Connecting real company APIs too early.
- Uploading large sensitive datasets.
- Hardcoding examples into prompts.
- Letting the LLM directly execute tools.
- Letting the chatbot bypass approval.
- Generating Robot code with invented keywords.
- Claiming production readiness while providers are local/demo.
- Replacing the workflow cockpit with only a chat window.
- Building classification ML before enough labelled failures exist.
- Building enterprise isolation before storage requirements are validated.

---

## 23. Immediate Next Step

The next implementation should be:

```text
Milestone 8A — Robot, Execution, and Report Grounding
```

Minimum input needed:

```text
5 sanitized Robot tests
1–2 sanitized custom libraries or keyword manifest
1 report example
1 successful execution example
1 failed execution example
```

Expected output:

```text
Robot keyword registry
Robot style profile
Report profile
Execution evidence profile
Improved AutomationGenerator
Improved Validator
Improved InvestigationCoordinator
Improved ReportGenerator
Golden tests
Updated PM demo
```

---

## 24. Final Product Definition

The target final product is:

```text
A governed conversational QA copilot
combined with a visible workflow cockpit
powered by deterministic orchestration,
specialized agents,
typed tools,
sanitized project knowledge,
RAG,
memory,
Robot Framework grounding,
human approval,
controlled execution,
evidence-based investigation,
and reusable learning.
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
- Reuse knowledge for future tickets.

This is the practical path from the current AegisQA implementation to a fully orchestrated, interactive, intelligent, NTF-aligned agentic QA system.
