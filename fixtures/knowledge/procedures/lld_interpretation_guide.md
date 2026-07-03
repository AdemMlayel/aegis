# LLD Interpretation Guide

Synthetic guidance for reading a Low-Level Design (LLD) document and extracting testable
behavior. All component names are abstract placeholders.

## What an LLD provides

An LLD describes how a feature is realized: components involved, data flow between them,
API or protocol interactions, configuration requirements, security constraints, logging
and monitoring expectations, error handling, and test data requirements. In AegisQA the
LLD content appears inside a ticket's `technical` block.

## Extracting test points

Walk the LLD in this order:

1. Components — list each placeholder component and the role it plays.
2. Data flow — trace the request from origin to terminal component; each hop is a
   candidate verification point.
3. Interactions — for every API/protocol interaction, capture source, target, protocol,
   operation, expected result, and the validation rules it maps to.
4. Constraints — turn each security, logging, and monitoring constraint into a negative
   or audit test where feasible.
5. Error handling — turn each documented failure expectation into a negative test case.

## Mapping to validation rules

Each interaction's `validation_refs` link the design to concrete validation rules
(for example `VR-SIP-001`, `VR-DIA-001`). The coverage planner uses these links to ensure
every critical rule has at least one functional and one negative case.

## Example

A fixed-to-mobile voice path traverses access, call-control, application, policy,
subscriber-data, and accounting placeholders. The originating INVITE hop maps to SIP
header rules; the subscriber lookup hop maps to Diameter session-id and result-code
rules; the accounting hop maps to start/stop record presence.

## Pitfalls

- Do not invent interactions the LLD does not describe.
- Treat optional packets and flexible ordering as warnings, not failures, when the design
  permits them.
- Keep all extracted artifacts free of real topology and identities.
