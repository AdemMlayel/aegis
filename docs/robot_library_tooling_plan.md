# Robot Library Tooling Plan

This document defines how AegisQA will use the ignored `custom_libs/` folder as
reference material while building safe, sanitized Robot Framework tool
capabilities.

`custom_libs/` must remain quarantined. Do not commit, import, or execute raw
files from that folder in the product path. Treat it as reference input for
capability discovery and wrapper design only.

## Goal

Move from generic generated Robot files that mostly log steps to executable
Robot automation that uses approved custom-library-style keywords against local
sanitized fixtures.

Target flow:

```text
structured ticket
  -> agent workflow
  -> skill/tool capability catalog
  -> generated Robot Framework suite
  -> approved Robot library keywords
  -> sanitized local fixture validation
  -> Robot output/report/evidence
```

## Safety Rules

- Never commit raw `custom_libs/` content.
- Never import or execute raw `custom_libs/` modules directly from backend code.
- Never use real IP addresses, hostnames, subscriber IDs, customer data,
  credentials, tokens, internal URLs, or live network captures.
- Use placeholders such as:
  - `INTERNAL_SERVICE_A`
  - `INTERNAL_API_ENDPOINT`
  - `TEST_ENVIRONMENT`
  - `DATABASE_REFERENCE`
  - `NETWORK_SEGMENT_PLACEHOLDER`
  - `AUTH_PROVIDER_PLACEHOLDER`
  - `TEST_SUBSCRIBER_A`
  - `SANITIZED_CALL_TRACE_FIXTURE`
- Start with local fixture validation only. No live systems, no SSH, no device
  farms, no portals, no network calls.
- Promote capabilities into Aegis only through approved sanitized adapters.

## Reference Buckets From `custom_libs/`

Use these buckets to guide wrapper design. They are not approved imports.

| Bucket | Reference Files | First-Phase Use |
| --- | --- | --- |
| Trace and pcap validation | `PcapValidation.py`, `Wireshark_validation.py`, `TextQuery.py`, `TextFilter.py`, `VolteCall.py` | Highest priority reference for safe local fixture validation |
| SIP and call-flow execution | `SippRunner.py`, `ImsTestCase.py`, `CallControl.py`, `fixedimscall.py` | Later, after fixture-only trace validation works |
| Web and portal automation | `seleniumfunctions.py`, `web_actions.py`, `CNOMServer.py`, `AnritsuServer.py` | Later, requires strict browser/fixture isolation |
| Node and network commands | `NodeBase.py`, `CMGServer.py`, `MrfServer.py`, `SMFTBServer.py`, `EMFTBServer.py` | High risk; do not wire until sandboxing and secrets are mature |
| Data access | `MongoAccess.py`, `DynamoDBLibrary.py` | High risk; use local fixture adapters first |
| Mobile/device | `mobile_cloud.robot`, `MobileCloudLibrary.py`, `OpenStf.py`, `LocationLibrary.py` | Later Appium/device phase, not first slice |

## Phase 1: Sanitized Telecom Trace Slice

Build a safe executable demo path for `DEMO-TELCO-IMS-001`.

### Files To Add

```text
fixtures/telecom/sanitized_call_trace.json
backend/robot_libraries/__init__.py
backend/robot_libraries/telecom_trace_library.py
backend/robot_libraries/registry.py
backend/tools/robot_keywords.py
tests/test_robot_library_registry.py
tests/test_telecom_automation_generation.py
```

### Sanitized Fixture

Create `fixtures/telecom/sanitized_call_trace.json` with placeholder events:

```json
{
  "fixture_id": "SANITIZED_CALL_TRACE_FIXTURE",
  "environment": "TEST_ENVIRONMENT",
  "events": [
    {
      "id": "EVT-001",
      "protocol": "SIP",
      "message": "INVITE",
      "source": "TEST_SUBSCRIBER_A",
      "target": "INTERNAL_SERVICE_A",
      "headers": ["To", "From", "Call-ID", "CSeq", "Via", "Max-Forwards", "P-Asserted-Identity"]
    },
    {
      "id": "EVT-002",
      "protocol": "Diameter",
      "message": "LIR",
      "source": "INTERNAL_SERVICE_B",
      "target": "INTERNAL_SERVICE_C",
      "session_id": "SESSION_PLACEHOLDER_A"
    },
    {
      "id": "EVT-003",
      "protocol": "Diameter",
      "message": "LIA",
      "source": "INTERNAL_SERVICE_C",
      "target": "INTERNAL_SERVICE_B",
      "session_id": "SESSION_PLACEHOLDER_A",
      "result_code": "SUCCESS_RESULT_CODE_PLACEHOLDER"
    }
  ],
  "flexible_order_groups": [["EVT-002", "EVT-003"]]
}
```

Keep this fixture small at first. Add events only when tests require them.

### Approved Demo Robot Library

Create `backend/robot_libraries/telecom_trace_library.py`.

Approved keywords:

- `Load Sanitized Trace`
- `Verify SIP Header Present`
- `Verify Diameter Session Match`
- `Verify Diameter Result Code`
- `Verify Flexible Sequence`

Implementation rules:

- Read only files under `fixtures/`.
- Reject absolute paths and parent-directory traversal.
- Return clear Robot assertion failures.
- Do not open sockets.
- Do not shell out.
- Do not read environment secrets.
- Do not log fixture payloads beyond placeholder IDs and validation rule IDs.

### Keyword Registry

Create `backend/robot_libraries/registry.py`.

It should expose static approved metadata:

```python
RobotKeywordCapability(
    name="Verify SIP Header Present",
    library="backend.robot_libraries.telecom_trace_library.TelecomTraceLibrary",
    domain="telecom_trace",
    args=("message", "header"),
    runtime="robot_framework",
    risk_level="low",
    description="Validates a SIP header in a sanitized local trace fixture.",
)
```

Do not introspect `custom_libs/` at runtime. The approved catalog is explicit.

### Aegis Tool Registry Bridge

Create `backend/tools/robot_keywords.py`.

Purpose:

- Register approved Robot keyword capabilities in the Aegis `ToolRegistry`.
- Make them visible to skills and reports as available execution capabilities.
- Do not execute Robot keywords directly inside tools in Phase 1.
- Store metadata only: keyword name, args, domain, library, runtime, risk level.

Expected tool:

```text
RobotKeywordCapabilityTool
```

It returns approved keyword metadata for a requested domain such as
`telecom_trace`.

### Automation Generator Change

Update `backend/tools/automation_heuristics.py`.

Behavior:

- If ticket labels/domain include `telecom`, `ims`, `sip`, `diameter`, or
  `trace-validation`, generate Robot using the telecom trace library keywords.
- Otherwise keep the current generic Robot generation unchanged.

Generated telecom Robot should include:

```robot
*** Settings ***
Library    backend.robot_libraries.telecom_trace_library.TelecomTraceLibrary

*** Variables ***
${TRACE_FIXTURE}    fixtures/telecom/sanitized_call_trace.json

*** Test Cases ***
Validate Sanitized IMS Call Trace
    Load Sanitized Trace    ${TRACE_FIXTURE}
    Verify SIP Header Present    INVITE    Call-ID
    Verify SIP Header Present    INVITE    P-Asserted-Identity
    Verify Diameter Session Match    LIR    LIA
    Verify Diameter Result Code    LIA    SUCCESS_RESULT_CODE_PLACEHOLDER
    Verify Flexible Sequence    IMS_CALL_FLOW_TEMPLATE
```

Use ticket validation rules and test steps to decide which keyword calls to
include.

## Phase 2: Capability Extraction From Reference Libraries

After Phase 1 works, add a script to extract safe metadata from quarantined
libraries without importing them.

Suggested file:

```text
scripts/extract_robot_capabilities.py
```

Default command:

```bash
python scripts/extract_robot_capabilities.py
```

Default output:

```text
generated/robot_capabilities/extracted_capabilities.json
```

Responsibilities:

- Parse Python source with `ast`.
- Extract class names, public method names, argument names, and docstrings.
- Parse `.robot` files for keyword names and arguments.
- Redact sensitive-looking docstrings and default values.
- Output a review-only JSON file under `generated/`, not source control.

Do not execute code during extraction.

## Phase 3: Sanitized Adapter Promotion

For each useful reference capability:

1. Identify the raw reference method or keyword.
2. Remove environment-specific assumptions.
3. Replace live system calls with fixture or sandbox equivalents.
4. Create an approved adapter in `backend/robot_libraries/`.
5. Add explicit keyword metadata in `backend/robot_libraries/registry.py`.
6. Add tests proving:
   - no live network is used,
   - no secrets are required,
   - fixture validation passes,
   - failures are clear and deterministic.

Do not promote broad libraries wholesale. Promote narrow, reviewed capabilities.

## Phase 4: Future Real Integration Mode

Only after security, secrets, sandboxing, and customer approval are ready:

- Enable controlled imports of approved internal libraries.
- Run Robot execution in an isolated container.
- Load secrets only through the secret provider.
- Restrict filesystem/network access.
- Add allowlists for endpoints and commands.
- Capture full audit events for every external call.

This phase is not part of the local demo.

## Tests To Add

Backend:

- `test_robot_keyword_registry_lists_approved_telecom_keywords`
- `test_robot_keyword_registry_rejects_unknown_domain`
- `test_telecom_ticket_generates_keyword_based_robot`
- `test_non_telecom_ticket_keeps_generic_robot_generation`
- `test_telecom_trace_library_validates_sanitized_fixture`
- `test_telecom_trace_library_rejects_path_traversal`
- `test_robot_dryrun_accepts_generated_telecom_suite`

Frontend/API:

- Ensure generated telecom Robot content is visible in artifact view.
- Ensure structured ticket context still appears before workflow creation.

## Definition Of Done For First Slice

- `custom_libs/` remains ignored and unexecuted.
- `DEMO-TELCO-IMS-001` generates Robot with approved telecom keywords.
- Generated Robot dry-run passes.
- Local Robot execution validates the sanitized fixture.
- Generic non-telecom tickets still generate the existing style of Robot file.
- Backend tests pass.
- Frontend typecheck/build passes.

## Recommended First Task

Implement Phase 1:

1. Add sanitized fixture.
2. Add approved telecom Robot library.
3. Add keyword capability registry.
4. Add metadata bridge tool.
5. Generate keyword-based Robot for telecom tickets only.
6. Add tests and run the full verification suite.
