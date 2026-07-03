# Ticket Analysis Procedure

This procedure describes how the Requirement / Ticket Understanding Agent converts a
structured ticket into validated requirements before any automation is generated. It is
synthetic guidance modeled on the real QA workflow; it contains no real system names.

## Inputs

A structured ticket record provides title, description, business objective, test
objective, system under test, scope, preconditions, interfaces, input data, expected
outputs, validation rules, acceptance criteria, and technical detail. All values are
sanitized placeholders such as `TEST_ENVIRONMENT`, `INTERNAL_SERVICE_A`, and
`AUTH_PROVIDER_PLACEHOLDER`.

## Completeness checklist

Every ticket is scored against six completeness signals before promotion:

1. Preconditions are defined and reference only non-production fixtures.
2. The acting actor or subscriber alias is identified.
3. A measurable expected outcome is specified.
4. Error and failure scenarios are described.
5. Data inputs and constraints are declared.
6. Performance or sequencing expectations are stated where relevant.

A ticket missing any signal produces targeted clarification questions instead of
invented answers. Clarifications are recorded on the workflow trace so reviewers can
see what was assumed and what was deferred.

## Output

The agent emits structured requirements with one entry per testable behavior, each
tagged to the validation rule it covers. Requirements remain in `draft` until a human
reviewer marks them `approved` or `needs_clarification`. No requirement advances to
coverage planning while it is in `needs_clarification`.

## Pitfalls

- Do not infer thresholds that the ticket does not state; reference
  `THRESHOLD_PLACEHOLDER` and flag the gap.
- Do not treat optional interface interactions as mandatory unless an acceptance
  criterion requires them.
- Keep all generated requirement text free of real hostnames, addresses, and identities.
