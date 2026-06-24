from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from backend.config.settings import settings
from backend.llm.ollama_profiles import chat_model_for_role


RecommendationMode = Literal["external", "local", "deterministic"]


@dataclass(frozen=True)
class AgentModelProfile:
    agent_name: str
    label: str
    purpose: str
    uses_llm: bool
    prompt_names: tuple[str, ...] = ()
    local_role: str | None = None
    recommended_mode: RecommendationMode = "deterministic"
    rationale: str = ""

    def as_dict(self) -> dict[str, object]:
        local_model = (
            chat_model_for_role(self.local_role)
            if self.uses_llm and self.local_role
            else None
        )
        recommended_provider = None
        recommended_model = None
        if self.recommended_mode == "external":
            recommended_provider = "openai_compatible"
            recommended_model = settings.openai_compatible_chat_model
        elif self.recommended_mode == "local":
            recommended_provider = "ollama"
            recommended_model = local_model
        return {
            **asdict(self),
            "prompt_names": list(self.prompt_names),
            "local_provider": "ollama" if self.uses_llm else None,
            "local_model": local_model,
            "external_provider": "openai_compatible" if self.uses_llm else None,
            "external_model": (
                settings.openai_compatible_chat_model if self.uses_llm else None
            ),
            "recommended_provider": recommended_provider,
            "recommended_model": recommended_model,
        }


AGENT_MODEL_PROFILES = (
    AgentModelProfile(
        agent_name="RequirementAgent",
        label="Requirement analysis",
        purpose="Interpret ticket intent, ambiguity, constraints, and expected behavior.",
        uses_llm=True,
        prompt_names=("requirement_analysis_v1",),
        local_role="main_rag",
        recommended_mode="external",
        rationale=(
            "External is recommended for nuanced requirement reasoning. Local Qwen remains "
            "the private/offline option."
        ),
    ),
    AgentModelProfile(
        agent_name="CoveragePlannerAgent",
        label="Coverage planning",
        purpose="Reason about business risk, edge cases, regression scope, and priority.",
        uses_llm=True,
        prompt_names=("coverage_planning_v1",),
        local_role="reasoning",
        recommended_mode="external",
        rationale=(
            "External is recommended because deeper reasoning generally improves risk and "
            "coverage decisions."
        ),
    ),
    AgentModelProfile(
        agent_name="TestCaseGeneratorAgent",
        label="Test generation",
        purpose="Generate complete positive, negative, boundary, and regression test cases.",
        uses_llm=True,
        prompt_names=("test_case_generation_v1",),
        local_role="stable_baseline",
        recommended_mode="external",
        rationale=(
            "External is recommended for broader scenario generation and more consistent "
            "long-form test output."
        ),
    ),
    AgentModelProfile(
        agent_name="ReportGeneratorAgent",
        label="Report generation",
        purpose="Summarize workflow evidence, outcomes, and next actions.",
        uses_llm=True,
        prompt_names=("report_generation_v1",),
        local_role="main_rag",
        recommended_mode="local",
        rationale=(
            "Local is usually sufficient for grounded summarization and keeps workflow "
            "evidence private."
        ),
    ),
    AgentModelProfile(
        agent_name="AutomationGeneratorAgent",
        label="Automation generation",
        purpose="Generate deterministic Robot Framework artifacts.",
        uses_llm=False,
        rationale="Currently implemented as a deterministic tool; no model call is made.",
    ),
    AgentModelProfile(
        agent_name="TestDataResolverAgent",
        label="Test data resolution",
        purpose="Resolve local fixtures and generated test-data values.",
        uses_llm=False,
        rationale="Currently implemented as a deterministic tool; no model call is made.",
    ),
    AgentModelProfile(
        agent_name="ValidatorAgent",
        label="Automation validation",
        purpose="Validate Robot artifacts, references, and dry-run behavior.",
        uses_llm=False,
        rationale="Validation is deterministic so pass/fail decisions remain reproducible.",
    ),
    AgentModelProfile(
        agent_name="HumanApprovalAgent",
        label="Human approval",
        purpose="Enforce review policy before handoff and execution.",
        uses_llm=False,
        rationale="Approval remains policy-driven and human-controlled.",
    ),
)

_PROFILE_BY_AGENT = {
    profile.agent_name: profile for profile in AGENT_MODEL_PROFILES
}
_AGENT_BY_PROMPT = {
    prompt_name: profile.agent_name
    for profile in AGENT_MODEL_PROFILES
    for prompt_name in profile.prompt_names
}


def list_agent_model_profiles() -> list[dict[str, object]]:
    return [profile.as_dict() for profile in AGENT_MODEL_PROFILES]


def list_agent_names() -> set[str]:
    return set(_PROFILE_BY_AGENT)


def list_llm_agent_names() -> set[str]:
    return {
        profile.agent_name
        for profile in AGENT_MODEL_PROFILES
        if profile.uses_llm
    }


def agent_name_for_prompt(prompt_name: str) -> str | None:
    return _AGENT_BY_PROMPT.get(prompt_name)


def embedding_recommendation() -> dict[str, object]:
    return {
        "recommended_mode": "local",
        "recommended_provider": "ollama_nomic_embed_text",
        "recommended_model": "nomic-embed-text",
        "fallback_provider": "local_hash_embeddings",
        "rationale": (
            "Embeddings can stay local safely: Nomic keeps source text on the machine and "
            "is sufficient for the current RAG and episodic-memory workload."
        ),
    }
