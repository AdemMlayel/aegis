from __future__ import annotations

from backend.graph.state import TicketSource


STRUCTURED_DEMO_TICKETS: tuple[dict[str, object], ...] = (
    {
        "id": "DEMO-TELCO-IMS-001",
        "title": "IMS fixed access to mobile voice call trace validation",
        "description": (
            "Validate that a fixed access subscriber can establish and terminate "
            "a voice session with a mobile subscriber across the sanitized IMS "
            "call-control path in TEST_ENVIRONMENT."
        ),
        "business_objective": (
            "Protect release quality for voice-session setup and teardown without "
            "exposing any production network topology."
        ),
        "test_objective": (
            "Generate Robot Framework automation that validates SIP and Diameter "
            "trace evidence using placeholder components, abstract interfaces, "
            "and deterministic validation rules."
        ),
        "system_under_test": "IMS_CALL_CONTROL_PLATFORM_PLACEHOLDER",
        "feature_or_service_name": "Fixed-to-mobile voice session orchestration",
        "test_scope": [
            "Validate sanitized SIP session setup, provisional response, answer, ACK, and BYE flow.",
            "Validate mandatory SIP headers on applicable request and response messages.",
            "Validate Diameter lookup, policy, accounting, and termination interactions.",
            "Validate session identifiers and success result codes across related Diameter exchanges.",
        ],
        "out_of_scope": [
            "Production endpoint discovery.",
            "Real subscriber identity validation.",
            "Live network capture from restricted environments.",
            "Performance benchmarking beyond trace-level sequencing checks.",
        ],
        "preconditions": [
            "TEST_ENVIRONMENT contains sanitized trace artifacts for the call scenario.",
            "TEST_SUBSCRIBER_A and TEST_SUBSCRIBER_B are provisioned as non-production placeholders.",
            "Robot Framework execution host can access sanitized pcap/log fixtures only.",
            "No production credentials, addresses, or customer identifiers are required.",
        ],
        "assumptions": [
            "Packet order can vary for selected provisional and accounting messages.",
            "Missing optional Diameter packets should be reported as warnings when the configured capture filter excludes them.",
            "All endpoint names are abstract identifiers resolved by the test fixture, not real hostnames.",
        ],
        "environment": "TEST_ENVIRONMENT",
        "interfaces_involved": [
            "SIP_ACCESS_INTERFACE",
            "SIP_CORE_INTERFACE",
            "DIAMETER_CX_INTERFACE",
            "DIAMETER_SH_INTERFACE",
            "DIAMETER_RX_INTERFACE",
            "DIAMETER_RF_INTERFACE",
            "NETWORK_SEGMENT_PLACEHOLDER",
        ],
        "input_data": [
            {
                "name": "caller_identity",
                "value": "TEST_SUBSCRIBER_A",
                "description": "Sanitized fixed access subscriber reference.",
            },
            {
                "name": "callee_identity",
                "value": "TEST_SUBSCRIBER_B",
                "description": "Sanitized mobile subscriber reference.",
            },
            {
                "name": "trace_fixture",
                "value": "SANITIZED_CALL_TRACE_FIXTURE",
                "description": "Local pcap/log fixture with placeholders only.",
            },
        ],
        "expected_outputs": [
            "SIP INVITE reaches INTERNAL_SERVICE_A and INTERNAL_SERVICE_B through the expected abstract path.",
            "Mandatory SIP headers are present where applicable.",
            "Identity header validation uses AUTH_PROVIDER_PLACEHOLDER and sanitized subscriber aliases.",
            "Diameter request/answer exchanges retain matching session identifiers.",
            "Diameter success answers use SUCCESS_RESULT_CODE_PLACEHOLDER.",
            "Accounting start and stop records are present for the sanitized session.",
            "Session teardown completes with BYE and final success response.",
        ],
        "validation_rules": [
            {
                "id": "VR-SIP-001",
                "description": "Verify mandatory SIP headers on INVITE, provisional response, success response, ACK, and BYE where applicable.",
                "applies_to": "SIP messages",
                "severity": "critical",
            },
            {
                "id": "VR-SIP-002",
                "description": "Verify the sanitized calling-party identity header is present on the originating INVITE.",
                "applies_to": "Originating INVITE",
                "severity": "high",
            },
            {
                "id": "VR-DIA-001",
                "description": "Verify Diameter answer Session-Id matches the related request Session-Id.",
                "applies_to": "Diameter request/answer pairs",
                "severity": "critical",
            },
            {
                "id": "VR-DIA-002",
                "description": "Verify Diameter success answers carry SUCCESS_RESULT_CODE_PLACEHOLDER.",
                "applies_to": "Diameter answer messages",
                "severity": "critical",
            },
            {
                "id": "VR-TRACE-001",
                "description": "Permit configured flexible ordering for non-causal provisional and accounting packets.",
                "applies_to": "Trace sequence",
                "severity": "warning",
            },
        ],
        "test_steps": [
            {
                "order": 1,
                "action": "Load sanitized call trace fixture SANITIZED_CALL_TRACE_FIXTURE.",
                "expected_result": "Trace fixture is readable and contains SIP and Diameter records.",
                "validation_refs": ["VR-TRACE-001"],
            },
            {
                "order": 2,
                "action": "Validate originating INVITE from TEST_SUBSCRIBER_A through SIP_ACCESS_INTERFACE.",
                "expected_result": "INVITE contains mandatory headers and sanitized calling-party identity.",
                "validation_refs": ["VR-SIP-001", "VR-SIP-002"],
            },
            {
                "order": 3,
                "action": "Validate SIP routing through INTERNAL_SERVICE_A, INTERNAL_SERVICE_B, and INTERNAL_SERVICE_C.",
                "expected_result": "Expected provisional and success messages are present across abstract components.",
                "validation_refs": ["VR-SIP-001", "VR-TRACE-001"],
            },
            {
                "order": 4,
                "action": "Validate Diameter subscriber lookup and user-data exchanges.",
                "expected_result": "Request and answer pairs match session identifiers and success result codes.",
                "validation_refs": ["VR-DIA-001", "VR-DIA-002"],
            },
            {
                "order": 5,
                "action": "Validate policy authorization and accounting start records.",
                "expected_result": "Policy answer and accounting start records are present for sanitized session aliases.",
                "validation_refs": ["VR-DIA-001", "VR-DIA-002"],
            },
            {
                "order": 6,
                "action": "Validate ACK and BYE teardown flow.",
                "expected_result": "Session teardown completes with final success response and accounting stop records.",
                "validation_refs": ["VR-SIP-001", "VR-DIA-002"],
            },
        ],
        "acceptance_criteria": [
            "Automation identifies all mandatory SIP header validation points.",
            "Automation identifies all mandatory Diameter AVP validation points.",
            "Generated Robot artifacts use only placeholder component names and fixture references.",
            "Validation results distinguish hard failures from allowed flexible-order warnings.",
        ],
        "risks_or_constraints": [
            "Trace artifacts must stay sanitized before entering the workflow.",
            "Packet order may vary between fixture captures.",
            "Optional packets may be absent when capture filters exclude them.",
            "Robot automation must not embed credentials, real addresses, or real subscriber identities.",
        ],
        "dependencies": [
            "SANITIZED_TRACE_FIXTURE_REPOSITORY",
            "ROBOT_CUSTOM_LIBRARY_PLACEHOLDER",
            "TSHARK_TOOL_PLACEHOLDER",
            "TEST_ENVIRONMENT",
        ],
        "required_tools": [
            "Robot Framework",
            "Custom telecom trace Robot library",
            "tshark or Wireshark CLI placeholder",
            "Local artifact store",
        ],
        "priority": "critical",
        "status": "ready",
        "created_date": "2026-06-01",
        "last_updated_date": "2026-06-20",
        "labels": ["telecom", "ims", "sip", "diameter", "trace-validation"],
        "assignee": "qa_automation_lead",
        "source": TicketSource.DEMO,
        "raw_url": "demo://tickets/DEMO-TELCO-IMS-001",
        "technical": {
            "architecture_summary": (
                "A fixed access subscriber initiates a voice session that traverses "
                "abstract access, call-control, application, policy, subscriber-data, "
                "and accounting components before reaching a mobile subscriber alias."
            ),
            "components_involved": [
                "FIXED_ACCESS_DEVICE_PLACEHOLDER",
                "ACCESS_GATEWAY_PLACEHOLDER",
                "CALL_SESSION_CONTROL_PLACEHOLDER",
                "APPLICATION_SERVER_PLACEHOLDER",
                "SUBSCRIBER_DATA_SERVICE_PLACEHOLDER",
                "POLICY_CONTROL_SERVICE_PLACEHOLDER",
                "ACCOUNTING_SERVICE_PLACEHOLDER",
                "MOBILE_ACCESS_DEVICE_PLACEHOLDER",
            ],
            "data_flow": [
                "TEST_SUBSCRIBER_A sends sanitized INVITE through SIP_ACCESS_INTERFACE.",
                "CALL_SESSION_CONTROL_PLACEHOLDER resolves routing using subscriber-data interactions.",
                "APPLICATION_SERVER_PLACEHOLDER applies service logic using sanitized user-data checks.",
                "POLICY_CONTROL_SERVICE_PLACEHOLDER confirms policy authorization.",
                "ACCOUNTING_SERVICE_PLACEHOLDER records start and stop events.",
                "TEST_SUBSCRIBER_B answers and later receives sanitized teardown.",
            ],
            "api_or_service_interactions": [
                {
                    "name": "SIP session setup",
                    "source": "FIXED_ACCESS_DEVICE_PLACEHOLDER",
                    "target": "ACCESS_GATEWAY_PLACEHOLDER",
                    "protocol": "SIP",
                    "operation": "INVITE",
                    "expected_result": "Mandatory headers and sanitized identity are present.",
                    "validation_refs": ["VR-SIP-001", "VR-SIP-002"],
                },
                {
                    "name": "Subscriber routing lookup",
                    "source": "CALL_SESSION_CONTROL_PLACEHOLDER",
                    "target": "SUBSCRIBER_DATA_SERVICE_PLACEHOLDER",
                    "protocol": "Diameter",
                    "operation": "Location and user-data request/answer",
                    "expected_result": "Session identifiers match and success result code is present.",
                    "validation_refs": ["VR-DIA-001", "VR-DIA-002"],
                },
                {
                    "name": "Policy authorization",
                    "source": "ACCESS_GATEWAY_PLACEHOLDER",
                    "target": "POLICY_CONTROL_SERVICE_PLACEHOLDER",
                    "protocol": "Diameter",
                    "operation": "Authorization request/answer",
                    "expected_result": "Policy authorization succeeds for sanitized subscriber alias.",
                    "validation_refs": ["VR-DIA-001", "VR-DIA-002"],
                },
                {
                    "name": "Accounting lifecycle",
                    "source": "APPLICATION_SERVER_PLACEHOLDER",
                    "target": "ACCOUNTING_SERVICE_PLACEHOLDER",
                    "protocol": "Diameter",
                    "operation": "Accounting start and stop",
                    "expected_result": "Start and stop records are present with placeholder user references.",
                    "validation_refs": ["VR-DIA-002", "VR-TRACE-001"],
                },
            ],
            "configuration_requirements": [
                "Use TEST_ENVIRONMENT profile only.",
                "Read trace fixtures from SANITIZED_TRACE_FIXTURE_REPOSITORY.",
                "Map abstract component aliases through COMPONENT_ALIAS_MAP_PLACEHOLDER.",
            ],
            "security_constraints": [
                "Do not store real subscriber identifiers.",
                "Do not embed real hostnames, addresses, or credentials in generated Robot files.",
                "Mask all trace values before persistence.",
            ],
            "logging_requirements": [
                "Log validation rule IDs, fixture reference, and abstract component aliases.",
                "Do not log packet payloads containing sensitive data.",
            ],
            "monitoring_requirements": [
                "Capture validation pass/fail count by rule severity.",
                "Capture flexible-order warnings separately from hard failures.",
            ],
            "error_handling_expectations": [
                "Missing critical SIP headers fail the test.",
                "Mismatched Diameter session identifiers fail the test.",
                "Allowed flexible-order differences are warnings.",
                "Missing optional packets are warnings when explicitly configured.",
            ],
            "test_data_requirements": [
                "Sanitized pcap fixture.",
                "Sanitized component alias map.",
                "Expected message sequence template with placeholders.",
            ],
        },
        "comments": [
            {
                "author": "domain_expert",
                "body": "Use placeholder components only; no production topology may appear in generated automation.",
            },
            {
                "author": "qa_lead",
                "body": "Prioritize SIP header and Diameter session matching rules for the first executable slice.",
            },
        ],
        "linked_requirements": [
            {
                "id": "REQ-DEMO-TELCO-001",
                "title": "Generated automation validates sanitized SIP call-flow evidence.",
                "status": "approved",
                "source": "demo",
            },
            {
                "id": "REQ-DEMO-TELCO-002",
                "title": "Generated automation validates Diameter request/answer consistency.",
                "status": "approved",
                "source": "demo",
            },
        ],
    },
    {
        "id": "DEMO-FIN-REFUND-002",
        "title": "High-value refund approval audit flow",
        "description": (
            "Validate a sanitized high-value refund approval workflow across "
            "internal service, audit, and notification boundaries."
        ),
        "business_objective": (
            "Ensure risk-controlled refunds leave a complete audit trail before "
            "finance operations promote the workflow."
        ),
        "test_objective": (
            "Generate API and audit validation automation from a structured ticket "
            "without depending on external ticket endpoints."
        ),
        "system_under_test": "REFUND_ORCHESTRATION_SERVICE_PLACEHOLDER",
        "feature_or_service_name": "Refund approval and audit lifecycle",
        "test_scope": [
            "Validate manager approval requirement for high-value refund requests.",
            "Validate requester and approver separation of duties.",
            "Validate immutable audit event creation for approve and reject outcomes.",
            "Validate notification event publication to INTERNAL_SERVICE_B.",
        ],
        "out_of_scope": [
            "Real payment settlement.",
            "Production ledger access.",
            "Third-party provider callbacks.",
        ],
        "preconditions": [
            "TEST_ENVIRONMENT contains sanitized refund fixture data.",
            "AUTH_PROVIDER_PLACEHOLDER can issue local demo identities.",
            "DATABASE_REFERENCE points to a local non-production fixture.",
        ],
        "assumptions": [
            "Refund amount thresholds are represented by placeholder configuration.",
            "Audit checks use local fixture records, not production data.",
        ],
        "environment": "TEST_ENVIRONMENT",
        "interfaces_involved": [
            "INTERNAL_API_ENDPOINT",
            "AUTH_PROVIDER_PLACEHOLDER",
            "DATABASE_REFERENCE",
            "AUDIT_EVENT_STREAM_PLACEHOLDER",
        ],
        "input_data": [
            {
                "name": "refund_request",
                "value": "REFUND_REQUEST_FIXTURE_HIGH_VALUE",
                "description": "Sanitized high-value refund request fixture.",
            },
            {
                "name": "requester_identity",
                "value": "TEST_USER_REQUESTER",
                "description": "Placeholder user who creates the refund request.",
            },
            {
                "name": "approver_identity",
                "value": "TEST_USER_APPROVER",
                "description": "Placeholder manager identity.",
            },
        ],
        "expected_outputs": [
            "High-value refund requires approval by TEST_USER_APPROVER.",
            "Requester cannot approve their own refund.",
            "Approve and reject outcomes write immutable audit events.",
            "Rejected refunds do not mutate settlement state in DATABASE_REFERENCE.",
        ],
        "validation_rules": [
            {
                "id": "VR-REFUND-001",
                "description": "Reject approval when requester and approver identities are the same placeholder.",
                "applies_to": "Approval API",
                "severity": "critical",
            },
            {
                "id": "VR-REFUND-002",
                "description": "Persist audit event with actor, timestamp, amount class, and outcome.",
                "applies_to": "Audit store",
                "severity": "critical",
            },
            {
                "id": "VR-REFUND-003",
                "description": "Publish sanitized notification event after terminal decision.",
                "applies_to": "Event stream",
                "severity": "high",
            },
        ],
        "test_steps": [
            {
                "order": 1,
                "action": "Create sanitized high-value refund request through INTERNAL_API_ENDPOINT.",
                "expected_result": "Request enters pending approval state.",
                "validation_refs": ["VR-REFUND-002"],
            },
            {
                "order": 2,
                "action": "Attempt self-approval with TEST_USER_REQUESTER.",
                "expected_result": "Approval is rejected without settlement mutation.",
                "validation_refs": ["VR-REFUND-001"],
            },
            {
                "order": 3,
                "action": "Approve with TEST_USER_APPROVER.",
                "expected_result": "Approval succeeds and immutable audit event is created.",
                "validation_refs": ["VR-REFUND-002", "VR-REFUND-003"],
            },
            {
                "order": 4,
                "action": "Reject a second sanitized request.",
                "expected_result": "Original payment reference remains unchanged and rejection audit is available.",
                "validation_refs": ["VR-REFUND-002"],
            },
        ],
        "acceptance_criteria": [
            "Refunds above THRESHOLD_PLACEHOLDER require independent manager approval.",
            "Approver cannot be the same placeholder identity that created the request.",
            "Approved refunds create an audit entry with actor, timestamp, amount class, and outcome.",
            "Rejected refunds leave the original payment reference unchanged.",
        ],
        "risks_or_constraints": [
            "Audit records must be immutable once written.",
            "Credentials must be referenced through AUTH_PROVIDER_PLACEHOLDER only.",
            "Fixture data must not include real customer or payment identifiers.",
        ],
        "dependencies": [
            "INTERNAL_API_ENDPOINT",
            "AUTH_PROVIDER_PLACEHOLDER",
            "DATABASE_REFERENCE",
            "AUDIT_EVENT_STREAM_PLACEHOLDER",
        ],
        "required_tools": [
            "Robot Framework",
            "RequestsLibrary placeholder",
            "Database validation helper placeholder",
            "Audit stream fixture reader",
        ],
        "priority": "critical",
        "status": "in_progress",
        "created_date": "2026-06-03",
        "last_updated_date": "2026-06-21",
        "labels": ["finance", "refund", "audit", "api"],
        "assignee": "qa_lead",
        "source": TicketSource.DEMO,
        "raw_url": "demo://tickets/DEMO-FIN-REFUND-002",
        "technical": {
            "architecture_summary": (
                "A requester creates a sanitized refund request through an internal "
                "API boundary. Approval policy, audit persistence, and notification "
                "publication are validated through local fixtures."
            ),
            "components_involved": [
                "REFUND_ORCHESTRATION_SERVICE_PLACEHOLDER",
                "AUTH_PROVIDER_PLACEHOLDER",
                "AUDIT_STORE_PLACEHOLDER",
                "NOTIFICATION_SERVICE_PLACEHOLDER",
                "DATABASE_REFERENCE",
            ],
            "data_flow": [
                "TEST_USER_REQUESTER submits refund request fixture.",
                "REFUND_ORCHESTRATION_SERVICE_PLACEHOLDER evaluates threshold and separation-of-duties policy.",
                "TEST_USER_APPROVER records approve or reject decision.",
                "AUDIT_STORE_PLACEHOLDER persists immutable decision evidence.",
                "NOTIFICATION_SERVICE_PLACEHOLDER receives sanitized terminal event.",
            ],
            "api_or_service_interactions": [
                {
                    "name": "Create refund request",
                    "source": "Robot automation",
                    "target": "INTERNAL_API_ENDPOINT",
                    "protocol": "HTTPS placeholder",
                    "operation": "POST refund request",
                    "expected_result": "Pending approval response with sanitized request reference.",
                    "validation_refs": ["VR-REFUND-002"],
                },
                {
                    "name": "Approval decision",
                    "source": "Robot automation",
                    "target": "INTERNAL_API_ENDPOINT",
                    "protocol": "HTTPS placeholder",
                    "operation": "POST approval decision",
                    "expected_result": "Policy-compliant approve/reject response.",
                    "validation_refs": ["VR-REFUND-001", "VR-REFUND-002"],
                },
                {
                    "name": "Audit verification",
                    "source": "Robot automation",
                    "target": "AUDIT_STORE_PLACEHOLDER",
                    "protocol": "Fixture query",
                    "operation": "Read immutable audit event",
                    "expected_result": "Actor, timestamp, amount class, and outcome are present.",
                    "validation_refs": ["VR-REFUND-002"],
                },
            ],
            "configuration_requirements": [
                "Use THRESHOLD_PLACEHOLDER for high-value classification.",
                "Use local fixture identities from AUTH_PROVIDER_PLACEHOLDER.",
                "Route all storage checks to DATABASE_REFERENCE.",
            ],
            "security_constraints": [
                "Never embed credentials in generated Robot files.",
                "Never use production account, customer, or payment identifiers.",
                "Record only placeholder amount classes in logs.",
            ],
            "logging_requirements": [
                "Log request reference aliases and validation rule IDs.",
                "Mask authorization details and fixture payload bodies.",
            ],
            "monitoring_requirements": [
                "Capture count of approval policy failures.",
                "Capture count of audit event validation failures.",
            ],
            "error_handling_expectations": [
                "Self-approval returns a policy error and does not mutate settlement state.",
                "Missing audit event is a critical failure.",
                "Notification delay is a warning until retry budget is exhausted.",
            ],
            "test_data_requirements": [
                "High-value refund request fixture.",
                "Requester and approver placeholder identities.",
                "Audit store fixture.",
                "Notification stream fixture.",
            ],
        },
        "comments": [
            {
                "author": "risk_manager",
                "body": "Audit evidence must include actor, timestamp, amount class, and outcome.",
            }
        ],
        "linked_requirements": [
            {
                "id": "REQ-DEMO-REFUND-001",
                "title": "High-value refunds require independent approval.",
                "status": "approved",
                "source": "demo",
            },
            {
                "id": "REQ-DEMO-REFUND-002",
                "title": "Refund decisions produce immutable audit records.",
                "status": "needs_clarification",
                "source": "demo",
            },
        ],
    },
)
