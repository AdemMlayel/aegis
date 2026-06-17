from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from backend.config.settings import settings
from backend.llm.http_json import LLMHTTPError, get_json, post_json
from backend.llm.ollama import _extract_ollama_text


ProfileKind = Literal["chat", "embedding"]


@dataclass(frozen=True)
class OllamaModelProfile:
    role: str
    model: str
    kind: ProfileKind
    purpose: str
    env_key: str
    fallback_model: str | None = None

    @property
    def pull_command(self) -> str:
        return f"ollama pull {self.model}"

    @property
    def fallback_pull_command(self) -> str | None:
        if not self.fallback_model:
            return None
        return f"ollama pull {self.fallback_model}"


@dataclass(frozen=True)
class OllamaSmokeTestResult:
    role: str
    model: str
    kind: ProfileKind
    available: bool
    ok: bool
    response_excerpt: str = ""
    error: str | None = None


def list_ollama_profiles() -> list[OllamaModelProfile]:
    return [
        OllamaModelProfile(
            role="main_rag",
            model=settings.ollama_rag_model,
            kind="chat",
            purpose="Main assistant and RAG reasoning for requirement/report prompts.",
            env_key="AEGISQA_OLLAMA_RAG_MODEL",
        ),
        OllamaModelProfile(
            role="stable_baseline",
            model=settings.ollama_baseline_model,
            kind="chat",
            purpose="Stable baseline model for general QA decisions.",
            env_key="AEGISQA_OLLAMA_BASELINE_MODEL",
        ),
        OllamaModelProfile(
            role="coding_repo_analysis",
            model=settings.ollama_coding_model,
            kind="chat",
            purpose="Coding, repository analysis, and generated automation review.",
            env_key="AEGISQA_OLLAMA_CODING_MODEL",
        ),
        OllamaModelProfile(
            role="fast_testing",
            model=settings.ollama_fast_model,
            kind="chat",
            purpose="Lightweight quick checks and smoke testing.",
            env_key="AEGISQA_OLLAMA_FAST_MODEL",
            fallback_model=settings.ollama_fast_fallback_model,
        ),
        OllamaModelProfile(
            role="reasoning",
            model=settings.ollama_reasoning_model,
            kind="chat",
            purpose="Deeper reasoning for coverage and risk analysis.",
            env_key="AEGISQA_OLLAMA_REASONING_MODEL",
            fallback_model=settings.ollama_reasoning_fallback_model,
        ),
        OllamaModelProfile(
            role="rag_embedding",
            model=settings.ollama_embedding_model,
            kind="embedding",
            purpose="Embedding model for RAG and episodic-memory retrieval.",
            env_key="AEGISQA_OLLAMA_EMBEDDING_MODEL",
            fallback_model=settings.ollama_embedding_fallback_model,
        ),
    ]


def list_installed_ollama_models() -> tuple[bool, list[str], str | None]:
    try:
        payload = get_json(
            url=f"{settings.ollama_base_url.rstrip('/')}/api/tags",
            timeout_seconds=settings.ollama_discovery_timeout_seconds,
        )
    except LLMHTTPError as exc:
        return False, [], str(exc)
    models = payload.get("models", [])
    if not isinstance(models, list):
        return False, [], "Ollama /api/tags returned an invalid models payload."
    names: list[str] = []
    for model in models:
        if isinstance(model, dict) and isinstance(model.get("name"), str):
            names.append(model["name"])
    return True, sorted(names), None


def model_profile_status() -> dict[str, object]:
    service_available, installed_models, error = list_installed_ollama_models()
    installed = set(installed_models)
    profiles = []
    for profile in list_ollama_profiles():
        profile_dict = asdict(profile)
        profile_dict["installed"] = profile.model in installed
        profile_dict["fallback_installed"] = (
            profile.fallback_model in installed if profile.fallback_model else False
        )
        profile_dict["pull_command"] = profile.pull_command
        profile_dict["fallback_pull_command"] = profile.fallback_pull_command
        profiles.append(profile_dict)
    return {
        "base_url": settings.ollama_base_url,
        "service_available": service_available,
        "service_error": error,
        "installed_models": installed_models,
        "profiles": profiles,
    }


def smoke_test_profiles(
    *,
    roles: list[str] | None = None,
    prompt: str = "Return only OK if this model is ready for AegisQA.",
) -> list[OllamaSmokeTestResult]:
    selected_roles = set(roles or [profile.role for profile in list_ollama_profiles()])
    _, installed_models, _ = list_installed_ollama_models()
    installed = set(installed_models)
    results: list[OllamaSmokeTestResult] = []
    for profile in list_ollama_profiles():
        if profile.role not in selected_roles:
            continue
        if profile.model not in installed:
            results.append(
                OllamaSmokeTestResult(
                    role=profile.role,
                    model=profile.model,
                    kind=profile.kind,
                    available=False,
                    ok=False,
                    error=f"Model is not installed. Run: {profile.pull_command}",
                )
            )
            continue
        try:
            if profile.kind == "embedding":
                embedding = embed_with_ollama(model=profile.model, text=prompt)
                excerpt = f"embedding_dimensions={len(embedding)}"
            else:
                excerpt = chat_with_ollama(model=profile.model, prompt=prompt)
        except Exception as exc:  # noqa: BLE001 - smoke tests should report provider failures.
            results.append(
                OllamaSmokeTestResult(
                    role=profile.role,
                    model=profile.model,
                    kind=profile.kind,
                    available=True,
                    ok=False,
                    error=str(exc),
                )
            )
            continue
        results.append(
            OllamaSmokeTestResult(
                role=profile.role,
                model=profile.model,
                kind=profile.kind,
                available=True,
                ok=True,
                response_excerpt=excerpt[:240],
            )
        )
    return results


def chat_with_ollama(*, model: str, prompt: str) -> str:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": settings.ollama_temperature},
    }
    response = post_json(
        url=f"{settings.ollama_base_url.rstrip('/')}/api/chat",
        payload=payload,
        timeout_seconds=settings.llm_http_timeout_seconds,
    )
    return _extract_ollama_text(response)


def embed_with_ollama(*, model: str, text: str) -> tuple[float, ...]:
    try:
        response = post_json(
            url=f"{settings.ollama_base_url.rstrip('/')}/api/embed",
            payload={"model": model, "input": text},
            timeout_seconds=settings.llm_http_timeout_seconds,
        )
        embeddings = response.get("embeddings")
        if isinstance(embeddings, list) and embeddings and isinstance(embeddings[0], list):
            return tuple(float(value) for value in embeddings[0])
    except LLMHTTPError:
        pass

    response = post_json(
        url=f"{settings.ollama_base_url.rstrip('/')}/api/embeddings",
        payload={"model": model, "prompt": text},
        timeout_seconds=settings.llm_http_timeout_seconds,
    )
    embedding = response.get("embedding")
    if isinstance(embedding, list):
        return tuple(float(value) for value in embedding)
    raise RuntimeError("Ollama embedding response did not include an embedding vector.")
