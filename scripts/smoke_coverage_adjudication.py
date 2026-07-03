"""Smoke: run real plan_coverage and show adjudication landed in the plan."""
from backend.graph.state import TicketData
from backend.tools.requirement_heuristics import analyze_ticket
from backend.tools.coverage_heuristics import plan_coverage

ticket = TicketData(
    id="AI-777",
    title="Transfer funds with insufficient balance",
    description=(
        "As a customer I transfer funds between accounts. If the balance is "
        "insufficient the system must return an error and no money moves. "
        "Minimum transfer is 1 USD, maximum 50000 USD."
    ),
    acceptance_criteria=["Transfer completes within 2 seconds for valid input."],
    priority="high",
    labels=["banking", "transfer", "authorization"],
)
analysis = analyze_ticket(ticket)
plan = plan_coverage(ticket=ticket, analysis=analysis)

print("=== confidence ===")
print(plan.confidence)
print("=== regressions (prioritization tail) ===")
print(plan.regression_tests_to_rerun)
print("=== risk_rationale (adjudication-relevant lines) ===")
for line in plan.risk_rationale:
    if any(k in line for k in ("confidence:", "LLM", "regressions", "risk notes")):
        print(" -", line)
print("=== provider used ===")
print("OK")
