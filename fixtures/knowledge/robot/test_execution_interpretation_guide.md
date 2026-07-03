# Test Execution Interpretation Guide

Synthetic guidance for reading Robot Framework execution output and deciding what the
result means. Uses sanitized examples only.

## Artifacts

A Robot run produces `output.xml` (machine-readable results), `log.html` (step detail),
and `report.html` (summary). The execution layer also records per-test status, message,
duration, and any captured logs. In deterministic demo mode a controlled mock adapter
produces the same shape without a real target.

## Reading a result

For each test case, read in this order:

1. Status — `passed`, `failed`, or `skipped`.
2. Message — the assertion or error text on failure.
3. Duration — unusually long durations near a timeout suggest an environment issue.
4. Logs — the step where execution diverged from the expected flow.

## Status meaning

- `passed` — all assertions held; the validation rules for that case were satisfied.
- `failed` — at least one assertion failed or a keyword errored; route to the Failure
  Analysis Agent with the linked evidence.
- `skipped` — the case did not run (precondition unmet or execution unavailable);
  investigation is recorded as skipped, but retrieved knowledge and model evidence are
  still retained for review.

## Suite-level signals

- A suite that is entirely skipped usually means the target or fixture was unavailable,
  not that the application is broken. Confirm the pre-flight reachability check first.
- A mix of passes and a single failure focuses investigation on the failing case rather
  than the whole suite.

## Pitfalls

- Do not equate a skipped suite with a passing suite.
- Do not treat a flexible-order warning as a hard failure when the ticket explicitly
  allows non-causal packet ordering.
- Never copy raw payloads from logs into reports; summarize and sanitize.
