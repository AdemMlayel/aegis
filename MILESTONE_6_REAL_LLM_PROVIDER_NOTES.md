# Milestone 6 - Real LLM Provider Configuration

## Goal

Move beyond the deterministic mock LLM by adding real provider boundaries that can be enabled through environment configuration without changing workflow code.

## Implemented

- Added `openai_compatible` provider for OpenAI-style `/v1/chat/completions` APIs.
- Added `ollama` provider for local Ollama `/api/chat`.
- Kept `mock_llm` as the default deterministic provider.
- Added provider configuration fields:
  - `AEGISQA_DEFAULT_LLM_PROVIDER`
  - `AEGISQA_OPENAI_COMPATIBLE_BASE_URL`
  - `AEGISQA_OPENAI_COMPATIBLE_API_KEY`
  - `AEGISQA_OPENAI_COMPATIBLE_MODEL`
  - `AEGISQA_OLLAMA_BASE_URL`
  - `AEGISQA_OLLAMA_MODEL`
- Exposed provider configuration status through:
  - `GET /api/v1/intelligence/llm-providers`
  - `GET /api/v1/integrations/providers?include_external=true`
- Added tests with mocked HTTP responses, so no real network calls are made in CI.

## How To Switch

OpenAI-compatible:

```bash
AEGISQA_EXTERNAL_CONNECTORS_ENABLED=true
AEGISQA_DEFAULT_LLM_PROVIDER=openai_compatible
AEGISQA_OPENAI_COMPATIBLE_API_KEY=replace-with-your-key
AEGISQA_OPENAI_COMPATIBLE_MODEL=gpt-4o-mini
```

Ollama:

```bash
AEGISQA_DEFAULT_LLM_PROVIDER=ollama
AEGISQA_OLLAMA_BASE_URL=http://127.0.0.1:11434
AEGISQA_OLLAMA_MODEL=llama3.1
```

## Remaining Work

- Add model-selection controls in the dashboard.
- Add provider health checks with small non-mutating probes.
- Add structured JSON-output parsing for requirements, coverage, and test generation once prompts are stabilized.

## Verification

```bash
python -m pytest -q
# 86 passed
```

```bash
cd frontend
npm run build
```
