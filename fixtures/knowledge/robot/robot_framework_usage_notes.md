# Robot Framework Usage Notes

Synthetic guidance for generating and structuring Robot Framework automation in AegisQA.
All examples use placeholder libraries and fixtures only.

## Suite structure

Generated suites separate three concerns:

- Test cases — one scenario per case, tagged to the requirement and validation rule.
- Keywords / resources — reusable steps shared across cases.
- Data references — variables and fixtures resolved by the test data layer, never
  hardcoded secrets.

## Settings discipline

Declare `Library`, `Resource`, `Suite Setup`, `Suite Teardown`, `Test Setup`, and
`Test Teardown` explicitly. Setup loads sanitized fixtures; teardown releases them so no
test pollutes another. A suite without teardown for stateful data is rejected at review.

## Tags

Each test carries tags for the requirement id, the coverage type (`functional`,
`negative`, `boundary`, `edge`), and the domain (for example `telecom`, `finance`,
`api`). Tags drive the coverage matrix and let reviewers filter execution.

## Custom libraries

Custom Robot libraries are referenced as placeholders such as
`ROBOT_CUSTOM_LIBRARY_PLACEHOLDER`. The keyword registry derived from the sanitized
reference corpus lists available keyword names, argument shapes, and return hints — it is
static-parse-only and never executes imported code.

## Example skeleton

```robotframework
*** Settings ***
Library           CustomTelecomTraceLibrary
Resource          common_keywords.resource
Suite Setup       Load Sanitized Trace Fixture    SANITIZED_CALL_TRACE_FIXTURE
Suite Teardown    Release Trace Fixture

*** Test Cases ***
Validate Mandatory SIP Headers On INVITE
    [Tags]    REQ-DEMO-TELCO-001    functional    telecom
    Given a sanitized originating INVITE
    Then mandatory SIP headers are present
```

## Pitfalls

- Never embed credentials, real hostnames, or real subscriber identities.
- Prefer data-driven cases over duplicated literals.
- Keep keyword names aligned with the reference style profile for review consistency.
