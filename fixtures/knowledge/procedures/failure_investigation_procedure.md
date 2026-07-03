# Failure Investigation Procedure

This procedure guides the Failure Analysis Agent when a generated test case fails during
execution. It is synthetic guidance aligned with the real investigation workflow and
uses only sanitized references.

## Goal

Produce an evidence-based root cause assessment that distinguishes application defects
from test, data, and environment problems — without guessing. Every conclusion must cite
the evidence item that supports it.

## Evidence collection

Collect, in order:

1. Robot execution result for the failing test case (status, message, duration).
2. Captured logs and any stderr excerpt, truncated to a safe length.
3. Generated keyword and data references used by the test.
4. Retrieved knowledge and memory references that informed generation.
5. The reference execution-evidence profile, when available.

## Classification heuristic

Classify the failure category from the failure message and logs:

- `environment` — timeout, connection, container, or environment terms dominate.
- `data` — variable, fixture, or input terms dominate.
- `test` — keyword, import, syntax, or framework terms dominate.
- `application` — assertion, expected/actual mismatch terms dominate.
- `unknown` — no category matches; escalate for human review.

The category is a hint, not a verdict. A high-severity finding always recommends
inspecting the Robot output and the generated keyword/data references before blaming the
application under test.

## Confidence

Confidence is derived from how much linked evidence supports a finding, not from model
opinion. A finding with directly linked execution evidence carries higher confidence than
one inferred only from logs. When no failures are observed, a clean-execution assessment
is recorded with its own confidence and the supporting evidence count.

## Output

A root cause summary, a list of findings (each with severity, category, evidence
references, confidence, and recommended actions), and the full evidence list. Results are
written to the workflow trace and archived to memory for historical cross-reference.

## Pitfalls

- Do not assume the first error line is the root cause.
- Do not raise confidence without a linked evidence item.
- Never include real payloads, addresses, or identities in evidence excerpts.
