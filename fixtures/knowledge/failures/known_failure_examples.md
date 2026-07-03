# Known Failure Examples

Synthetic catalog of recurring failure signatures used for historical cross-reference
during investigation. Each entry is fabricated for demo purposes and contains no real
data. The Failure Analysis Agent matches new failures against these signatures to raise
or lower confidence.

## KF-001 — Missing mandatory SIP header

- Category: application
- Signature: a success or provisional SIP response is missing a mandatory header.
- Typical message: "Expected header not present on response".
- Recommended action: confirm the header rule applies to that message type, then inspect
  the generated keyword that asserts header presence before concluding an application
  defect.

## KF-002 — Diameter session-id mismatch

- Category: application
- Signature: a Diameter answer carries a different Session-Id than its request.
- Typical message: "Session-Id mismatch between request and answer".
- Recommended action: verify the correlation keyword pairs request/answer correctly; a
  real mismatch indicates a routing or correlation defect.

## KF-003 — Self-approval not rejected

- Category: application
- Signature: a refund approval succeeds when requester and approver are the same identity.
- Typical message: "Approval accepted for identical requester and approver".
- Recommended action: high-severity separation-of-duties defect; confirm the test used
  distinct placeholder identities, then escalate.

## KF-004 — Fixture not loaded

- Category: data
- Signature: a suite is skipped or a setup keyword errors because the sanitized fixture
  was not found.
- Typical message: "Fixture reference could not be resolved".
- Recommended action: a test/data problem, not an application defect; check the data
  resolution declaration and teardown.

## KF-005 — Target unreachable

- Category: environment
- Signature: connection timeout or refused during setup against the target.
- Typical message: "Connection timed out".
- Recommended action: run the pre-flight reachability check; if the target is down, report
  immediately rather than attributing failures to the application.

## KF-006 — Keyword import error

- Category: test
- Signature: a custom library keyword cannot be imported or resolved.
- Typical message: "No keyword with name found".
- Recommended action: verify the keyword exists in the reference keyword registry and the
  library import path is declared.
