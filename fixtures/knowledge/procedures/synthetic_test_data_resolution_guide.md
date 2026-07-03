# Synthetic Test Data Resolution Guide

Synthetic guidance for how the Test Data Resolution layer declares, provides, and tears
down data for generated test cases. All values are sanitized placeholders.

## Strategies

Data needs are declared per test case and resolved through one of five strategies:

- factory — construct objects in code from a template (preferred for demos).
- fixture — load a static sanitized fixture file.
- db_seed — seed a local non-production database reference.
- api_bootstrap — create state through an internal API placeholder.
- masked_prod — never used in demo mode; reserved for a future controlled environment
  where production data would be masked before use.

## Declaration

Each declaration names the data, the strategy, the sanitized value or fixture reference,
and a teardown action. Example: a refund test declares `refund_request` via factory using
`REFUND_REQUEST_FIXTURE_HIGH_VALUE`, with teardown that removes the created request so the
next test starts clean.

## Teardown discipline

Every stateful declaration must declare teardown. No test may leave state that pollutes
another. Suites without teardown for stateful data are rejected at review.

## Sanitization

Resolved values use placeholders such as `TEST_SUBSCRIBER_A`, `TEST_USER_APPROVER`,
`THRESHOLD_PLACEHOLDER`, and `DATABASE_REFERENCE`. No real customer identifiers, payment
references, addresses, or credentials are ever materialized.

## Pitfalls

- Do not share mutable fixture state across tests without teardown.
- Do not select masked_prod in demo mode.
- Keep factory templates free of real values; they are structural shapes only.
