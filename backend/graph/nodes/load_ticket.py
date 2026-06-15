from backend.graph.state import TestContext, TicketData


def default_ticket() -> TicketData:
    return TicketData(
        id="FAKE-001",
        title="Money Transfer Feature",
        description="As a customer, I want to transfer money to another account.",
        acceptance_criteria=[
            "Transfer completes within 3 seconds",
            "Balance updates immediately",
            "Confirmation notification is sent",
        ],
        priority="high",
        labels=["banking", "payments"],
    )


def load_ticket(context: TestContext) -> TestContext:
    if context.ticket is None:
        context.ticket = default_ticket()

    context.mark("ticket_loaded")
    return context
