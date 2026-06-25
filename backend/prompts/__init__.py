from __future__ import annotations

import backend.prompts.templates  # noqa: F401 - registers built-in prompt templates
from backend.prompts.base import PromptRegistry, PromptTemplateSpec, prompt_registry

__all__ = ["PromptRegistry", "PromptTemplateSpec", "prompt_registry"]
