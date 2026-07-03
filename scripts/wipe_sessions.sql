-- Wipe all runtime session/chat/telemetry state so ticket testing starts clean.
-- KEEPS: mock_tickets (demo tickets), schema_migrations, sqlite_sequence, table schemas.
-- Everything below is per-run data that accumulates across testing.

PRAGMA foreign_keys = OFF;

DELETE FROM chat_sessions;        -- conversations (messages live in payload_json)
DELETE FROM workflow_contexts;    -- workflow sessions / TestContext rows
DELETE FROM workflow_events;      -- per-stage timeline events
DELETE FROM execution_runs;       -- robot/playwright/k6 run records
DELETE FROM execution_events;     -- execution step events
DELETE FROM artifact_revisions;   -- generated artifact history
DELETE FROM agent_invocations;    -- per-agent call telemetry
DELETE FROM model_invocations;    -- per-LLM-call telemetry (incl. fallback markers)
DELETE FROM token_reservations;   -- gateway token budget ledger
DELETE FROM request_observations; -- request-level observability rows
DELETE FROM audit_events;         -- audit trail

PRAGMA foreign_keys = ON;
