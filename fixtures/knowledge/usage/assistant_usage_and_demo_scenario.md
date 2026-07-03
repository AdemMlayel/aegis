# Assistant Usage and Demo Scenario Guide

Synthetic guide describing how to drive an AegisQA demonstration end to end and what the
assistant can do. Contains no real data.

## What the assistant does

The assistant orchestrates a multi-agent QA workflow over a structured ticket. It can
analyze a ticket into requirements, plan coverage, generate Robot Framework automation,
resolve sanitized test data, validate artifacts, execute (mock or local Robot),
investigate failures with linked evidence, generate reports, and archive the outcome to
memory. It retrieves synthetic documentation to ground its answers and cites the chunks
it used.

## Recommended demo scenario

1. Open a sanitized demo ticket, for example the fixed-to-mobile voice trace ticket or
   the high-value refund approval ticket.
2. Run requirement analysis and review the completeness checklist result.
3. Plan coverage and generate test cases; show the coverage matrix tagging each case to a
   validation rule.
4. Generate Robot automation and run validation (dry-run where Robot is available).
5. Approve at the human gate.
6. Execute with the mock adapter in deterministic demo mode.
7. Investigate any failures and show the evidence-based findings.
8. Generate the technical report and executive summary.
9. Ask a grounded question and show the retrieved citations.

## Deterministic demo mode

Enable deterministic demo mode for presentations. It selects the mock LLM, local hash
embeddings, mock execution, and the demo ticket source so the run is reproducible without
Ollama or any external service.

## Grounded questions to try

Ask about the completeness checklist, failure classification, tool-execution governance,
or test-data teardown. Each answer should cite the synthetic documentation chunks that
grounded it.

## Pitfalls

- Do not present demo output as real integration readiness.
- Keep all inputs sanitized; never paste real tickets or logs into the demo.
