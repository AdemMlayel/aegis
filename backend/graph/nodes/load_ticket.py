from backend.config.settings import settings
from backend.embeddings import embedding_provider_registry
from backend.graph.state import IntegrationProviderRef, TestContext, TicketData
from backend.integrations.profile import build_integration_profile
from backend.llm import llm_provider_registry


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
    if context.integration_profile is None:
        context.integration_profile = build_integration_profile()
    _sync_intelligence_profile(context)

    context.mark("ticket_loaded")
    return context


def _sync_intelligence_profile(context: TestContext) -> None:
    context.sync_intelligence_trace_config()
    if context.integration_profile is None:
        return

    if llm_provider_registry.has(context.intelligence_config.llm_provider):
        spec = llm_provider_registry.get(context.intelligence_config.llm_provider).spec
        context.integration_profile.llm_provider = IntegrationProviderRef(
            kind="llm_provider",
            name=spec.name,
            mode=spec.mode,
            requires_external_api=spec.requires_external_api,
            status=(
                "ready"
                if not spec.requires_external_api or settings.external_connectors_enabled
                else "disabled"
            ),
            notes=["Selected for this workflow intelligence run."],
        )

    if embedding_provider_registry.has(context.intelligence_config.embedding_provider):
        spec = embedding_provider_registry.get(context.intelligence_config.embedding_provider).spec
        context.integration_profile.embedding_provider = IntegrationProviderRef(
            kind="embedding_provider",
            name=spec.name,
            mode=spec.mode,
            requires_external_api=spec.requires_external_api,
            status=(
                "ready"
                if not spec.requires_external_api or settings.external_connectors_enabled
                else "disabled"
            ),
            notes=["Selected for this workflow intelligence run."],
        )
