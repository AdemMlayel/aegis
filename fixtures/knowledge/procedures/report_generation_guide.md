# Report Generation Guide

Synthetic guidance for the Report Generation Agent. Reports must be traceable, severity
ordered, and free of sensitive data.

## Audiences

Two reports are produced from the same evidence:

- Technical report — for QA engineers. Includes the traceability matrix
  (ticket -> requirement -> test case -> robot file -> result), per-test results,
  coverage matrix, and the investigation findings with evidence references.
- Executive summary — for stakeholders. Leads with the verdict, then a short rationale,
  the confidence level, and recommended next steps.

## Structure

Preferred sections, in order: executive summary, scope, coverage, results, investigation,
risks, recommendations. The report profile derived from the sanitized reference corpus
supplies the preferred section list and tone.

## Traceability

Every result row cites the requirement and validation rule it covers and the robot file
that produced it. A coverage gap (a requirement with no passing functional case) is
called out explicitly rather than hidden.

## Severity ordering

Findings are listed most severe first. A critical assertion failure is never buried under
style or ordering nitpicks. Genuinely good results are acknowledged briefly to calibrate
the rest.

## Confidence

The report states the investigation confidence and what evidence supports it. It never
presents a model-generated percentage as if it were measured.

## Pitfalls

- Do not include raw logs, payloads, real addresses, or identities.
- Do not claim real integration readiness in a demo report.
- Do not omit skipped suites; report them as skipped with the reason.
