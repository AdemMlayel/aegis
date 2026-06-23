# AegisQA PM Demo Script

## Goal

Show that AegisQA is a concrete AI-native QA orchestration solution, even without company APIs connected yet.

## Demo setup

Start backend:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e .[dev]
uvicorn backend.main:app --reload
```

Start frontend:

```bash
cd frontend
npm install
npm run dev
```

Open the frontend URL printed by Vite, usually:

```text
http://127.0.0.1:5173
```

## Optional Ollama setup

```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

Default demo mode does not require Ollama. The UI shows whether Ollama is reachable.

## Presentation flow

1. **Dashboard opening**
   - Explain that this is a local/demo-safe architecture proof.
   - External company systems are intentionally disabled.

2. **Provider panel**
   - Show selected providers:
     - `jira_mock`
     - `mock_llm` or `ollama`
     - `local_hash_embeddings` or `ollama_nomic_embed_text`
     - `local_knowledge`
     - `local_episodic_memory`
   - Explain that these can later be swapped for real Jira, Vault, vector DB, and model providers.

3. **Ticket selection**
   - Select a local demo ticket such as `MOCK-101`.
   - Explain this represents a future Jira/Azure ticket provider boundary.

4. **Run full workflow**
   - Click **Run full local workflow**.
   - Show the workflow step cards becoming populated:
     - Ticket
     - Requirement
     - Coverage
     - Tests
     - Automation
     - Approval
     - Execution
     - Memory

5. **Requirement analysis**
   - Show domain, actor, confidence, expected results, clarification questions, and AI summary.
   - Explain that RAG and memory references are attached to the context.

6. **Coverage plan**
   - Show risk level, criticality, required test types, and rationale.
   - Explain that previous failure memory can drive regression hints.

7. **Generated test cases**
   - Open each test case tab.
   - Show functional, negative, boundary, and possible regression coverage.

8. **Automation output**
   - Show generated Robot Framework artifact.
   - Explain validation behavior:
     - real dry-run if Robot is installed,
     - deterministic local validation fallback otherwise.

9. **Approval**
   - Click **Approve**.
   - Explain Git handoff is behind a tool boundary and safely blocks if no real repo/remote is configured.

10. **Execution**
    - Click **Execute**.
    - Show execution result, case results, investigation, report, and memory archive.

11. **Report & memory**
    - Explain this closes the blueprint loop: generated evidence becomes future memory.

## What is real today

- API server
- React dashboard
- Workflow graph
- Agent/Skill/Tool structure
- Local ticket provider
- RAG/memory architecture
- Provider catalog
- Local model configuration
- Generated Robot artifacts
- Validation gate
- Approval gate
- Local/mock execution
- Investigation placeholder
- Memory archive placeholder
- Tests and clean packaging

## What is intentionally local/demo

- Jira/Azure/GitLab
- Vault
- Git PR creation
- Company documents
- Company execution environments
- Enterprise identity
- Production vector database
