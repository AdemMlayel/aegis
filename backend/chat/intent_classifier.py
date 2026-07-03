from __future__ import annotations

import re
import unicodedata
from typing import Literal, cast, get_args

from pydantic import Field

from backend.chat.schemas import ChatIntent
from backend.graph.state import StrictModel


DetectedLanguage = Literal["en", "fr", "de", "es", "pt", "unknown"]

_VALID_INTENT_SET: frozenset[str] = frozenset(get_args(ChatIntent))

# Intents that map to a state-changing chat action (ChatActionKind). The LLM
# adjudication layer must never *override into* one of these (W9): they stay
# rule-driven so a prompt-injected message cannot surface a destructive action
# card. Kept in lockstep with ChatActionKind in chat/schemas.py.
_MUTATING_INTENTS: frozenset[str] = frozenset(
    {
        "workflow_start",
        "workflow_step",
        "approval_request",
        "execution_request",
    }
)


class ClassifiedIntent(StrictModel):
    intent: ChatIntent
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    ticket_id: str | None = None
    context_id: str | None = None
    normalized_message: str
    detected_language: DetectedLanguage = "unknown"


INTENT_PATTERNS: dict[ChatIntent, list[str]] = {
    "help": [
        "help",
        "what can you do",
        "how can you help",
        "aide",
        "que peux tu faire",
        "comment peux tu aider",
        "hilfe",
        "was kannst du",
        "ayuda",
        "que puedes hacer",
        "ajuda",
        "o que podes fazer",
    ],
    "system_question": [
        "mocked",
        "mock",
        "real",
        "provider",
        "providers",
        "configured",
        "system status",
        "active mode",
        "mode actif",
        "simule",
        "mocke",
        "reel",
        "fournisseur",
        "fournisseurs",
        "statut systeme",
        "systemstatus",
        "anbieter",
        "configurado",
        "proveedor",
        "real y simulado",
        "provedor",
        "modo ativo",
    ],
    "workflow_start": [
        "analyze",
        "analyse",
        "start analysis",
        "begin workflow",
        "create workflow",
        "analyser",
        "demarrer analyse",
        "commencer workflow",
        "lancer analyse",
        "analysiere",
        "workflow starten",
        "analizar",
        "iniciar analisis",
        "analise",
        "iniciar analise",
    ],
    "workflow_step": [
        "next step",
        "continue",
        "resume",
        "run next",
        "run next stage",
        "prochaine etape",
        "continuer",
        "reprendre",
        "lancer prochaine etape",
        "nachster schritt",
        "fortsetzen",
        "siguiente paso",
        "continuar",
        "proxima etapa",
        "continuar fluxo",
    ],
    "show_stage_output": [
        "show output",
        "show the output",
        "show stage output",
        "stage output",
        "show me the requirements",
        "show requirements",
        "show the requirements",
        "show coverage",
        "show the coverage",
        "show the test cases",
        "show test cases",
        "let me see",
        "display the",
        "view the output",
        "see the requirements",
        "see the coverage",
        "what did the stage produce",
        "what did it produce",
        "stage result",
        "stage results",
        "montre les exigences",
        "montrer la sortie",
        "voir les exigences",
        "zeige die anforderungen",
        "mostrar requisitos",
        "mostrar la salida",
        "mostrar requisitos",
        "ver os requisitos",
    ],
    "workflow_status": [
        "where are we",
        "workflow status",
        "current status",
        "progress",
        "next stage",
        "completed stages",
        "ou en sommes nous",
        "statut du workflow",
        "progression",
        "etape suivante",
        "etapes terminees",
        "wo stehen wir",
        "status des workflows",
        "progreso",
        "estado del workflow",
        "donde estamos",
        "estado do workflow",
        "onde estamos",
    ],
    "approval_request": [
        "approve",
        "approval",
        "approuver",
        "approbation",
        "validation humaine",
        "genehmigen",
        "freigabe",
        "aprobar",
        "aprobacion",
        "aprovar",
        "aprovacao",
    ],
    "execution_request": [
        "execute",
        "run tests",
        "run the tests",
        "execution",
        "executer",
        "lancer les tests",
        "execution des tests",
        "ausfuhren",
        "tests ausfuhren",
        "ejecutar",
        "ejecutar pruebas",
        "executar",
        "executar testes",
    ],
    "test_case_suggestion": [
        "suggest test",
        "suggest test case",
        "suggest test cases",
        "propose test",
        "generate test case",
        "test case ideas",
        "what test cases",
        "recommend test",
        "draft test cases",
        "suggerer des tests",
        "proposer des cas de test",
        "cas de test",
        "testfalle vorschlagen",
        "testfall",
        "sugerir casos de prueba",
        "casos de prueba",
        "sugerir casos de teste",
        "casos de teste",
    ],
    "artifact_question": [
        "robot",
        "artifact",
        "artifacts",
        "generated file",
        "automation file",
        "keyword",
        "keywords",
        "artefact",
        "artefacts",
        "fichier robot",
        "mot cle",
        "mots cles",
        "datei robot",
        "schlusselwort",
        "artefacto",
        "archivo robot",
        "palabra clave",
        "artefato",
        "arquivo robot",
        "palavra chave",
    ],
    "validation_question": [
        "validation",
        "validate",
        "dry run",
        "why did validation",
        "valider",
        "pourquoi la validation",
        "trockenlauf",
        "validacion",
        "validar",
        "validacao",
    ],
    "investigation_question": [
        "why did it fail",
        "failure",
        "failed",
        "investigate",
        "root cause",
        "evidence",
        "pourquoi ca a echoue",
        "echec",
        "echoue",
        "investiguer",
        "cause racine",
        "preuve",
        "fehler",
        "fehlgeschlagen",
        "ursache",
        "evidenz",
        "fallo",
        "fallo la prueba",
        "causa raiz",
        "evidencia",
        "falha",
        "falhou",
        "causa raiz",
        "evidencia",
    ],
    "self_healing_question": [
        "self heal",
        "self healing",
        "broken locator",
        "broken locators",
        "broken keyword",
        "unknown keyword",
        "locator repair",
        "repair locator",
        "fix the locator",
        "fix locators",
        "needs healing",
        "what needs fixing",
        "auto repair",
        "auto fix",
        "suggest fixes",
        "suggest a fix",
        "auto reparation",
        "localisateur casse",
        "selbstheilung",
        "autorreparacion",
        "autocorrecao",
    ],
    "report_request": [
        "report",
        "summary",
        "pm summary",
        "executive summary",
        "rapport",
        "resume",
        "synthese",
        "resume pm",
        "bericht",
        "zusammenfassung",
        "informe",
        "resumen",
        "relatorio",
        "resumo",
    ],
    "ticket_question": [
        "ticket",
        "requirement",
        "requirements",
        "missing",
        "acceptance",
        "criteria",
        "risk",
        "exigence",
        "exigences",
        "manquant",
        "critere",
        "criteres",
        "risque",
        "anforderung",
        "akzeptanzkriterien",
        "risiko",
        "requisito",
        "faltante",
        "criterio",
        "riesgo",
        "criterios de aceptacion",
        "requisito",
        "criterios de aceitacao",
        "risco",
    ],
    "knowledge_question": [
        "knowledge",
        "rag",
        "memory",
        "corpus",
        "sanitized",
        "connaissance",
        "memoire",
        "sanitise",
        "sanitisee",
        "wissen",
        "speicher",
        "bereinigt",
        "conocimiento",
        "memoria",
        "sanitizado",
        "conhecimento",
        "memoria",
        "sanitizado",
    ],
    "action_history": [
        "action history",
        "actions history",
        "pending actions",
        "confirmed actions",
        "cancelled actions",
        "historique des actions",
        "actions en attente",
        "actions confirmees",
        "actions annulees",
        "aktionsverlauf",
        "pendiente acciones",
        "historial de acciones",
        "historico de acoes",
        "acoes pendentes",
    ],
    "system_knowledge": [
        "architecture",
        "how does the system",
        "how does aegis",
        "how it works",
        "how does it work",
        "explain the system",
        "explain the workflow",
        "explain the architecture",
        "system elements",
        "system components",
        "what agents",
        "which agents",
        "list agents",
        "agent roster",
        "workflow stages",
        "how many stages",
        "what stages",
        "governance model",
        "how does governance",
        "tell me about the system",
        "what is aegis",
        "explain demo mode",
        "what is demo mode",
        "explain providers",
        "explain the providers",
        "explain the knowledge layer",
        "explain rag",
        "how is the system structured",
        "system design",
        "comment fonctionne",
        "expliquer le systeme",
        "expliquer l architecture",
        "quels agents",
        "etapes du workflow",
        "modele de gouvernance",
        "wie funktioniert das system",
        "welche agenten",
        "como funciona el sistema",
        "que agentes",
        "como funciona o sistema",
        "quais agentes",
    ],
    "unknown": [],
}

CONFIDENCE_BY_INTENT: dict[ChatIntent, float] = {
    "help": 0.95,
    "system_question": 0.84,
    "system_knowledge": 0.82,
    "workflow_start": 0.88,
    "workflow_step": 0.84,
    "workflow_status": 0.87,
    "show_stage_output": 0.85,
    "approval_request": 0.83,
    "execution_request": 0.87,
    "artifact_question": 0.80,
    "test_case_suggestion": 0.83,
    "validation_question": 0.84,
    "investigation_question": 0.82,
    "self_healing_question": 0.83,
    "report_request": 0.83,
    "ticket_question": 0.78,
    "knowledge_question": 0.76,
    "action_history": 0.82,
    "unknown": 0.40,
}

LANGUAGE_HINTS: dict[DetectedLanguage, list[str]] = {
    "fr": ["que", "pourquoi", "statut", "rapport", "resume", "prochaine", "etape", "ticket", "ou", "sommes", "nous", "dans"],
    "de": ["was", "bericht", "nachster", "schritt", "fehler", "stehen", "wir"],
    "es": ["que", "estado", "informe", "resumen", "siguiente", "paso", "pruebas"],
    "pt": ["que", "estado", "relatorio", "resumo", "proxima", "etapa", "testes"],
    "en": ["what", "why", "status", "report", "summary", "next", "ticket", "where", "are", "we", "run", "stage", "resume"],
    "unknown": [],
}


def classify_chat_intent(message: str) -> ClassifiedIntent:
    normalized = _normalize_text(message)
    ticket_id = _extract_ticket_id(message)
    context_id = _extract_context_id(message)

    if not normalized:
        return ClassifiedIntent(
            intent="unknown",
            confidence=0.0,
            normalized_message=normalized,
            detected_language="unknown",
        )

    intent, score = _score_intents(normalized)
    if intent == "unknown":
        confidence = CONFIDENCE_BY_INTENT["unknown"]
    else:
        # Blend the intent's base confidence with how strongly it matched, so a
        # weak single-token hit reads as lower confidence than a strong phrase.
        base = CONFIDENCE_BY_INTENT[intent]
        confidence = round(min(0.99, base * 0.6 + min(score, 6) / 6 * base * 0.4), 2)

    # LLM adjudication layer: only consult the model when the deterministic
    # result is unknown or weak, and only when a real LLM is configured (no-op
    # in demo mode / with the mock provider). This keeps the fast path free and
    # uses the LLM purely to rescue ambiguous natural phrasings.
    if intent == "unknown" or score < _LLM_ESCALATION_SCORE:
        llm_result = _maybe_classify_with_llm(message)
        if llm_result is not None:
            llm_intent, llm_confidence = llm_result
            # Trust the LLM when it is reasonably confident and it actually
            # picked a concrete intent (don't let it downgrade a rule hit to
            # unknown unless the rules were already unknown). W9: never let the
            # LLM *override into a mutating intent* -- a prompt-injected message
            # could otherwise surface a destructive action card (start/step/
            # approve/execute). Mutating intents stay rule-driven only; the LLM
            # may only rescue read-only (question/suggestion) intents.
            if (
                llm_intent != "unknown"
                and llm_confidence >= 0.5
                and llm_intent in _VALID_INTENT_SET
                and llm_intent not in _MUTATING_INTENTS
            ):
                intent = cast(ChatIntent, llm_intent)
                confidence = round(max(confidence, llm_confidence), 2)

    return ClassifiedIntent(
        intent=intent,
        confidence=confidence,
        ticket_id=ticket_id,
        context_id=context_id,
        normalized_message=normalized,
        detected_language=_detect_language(normalized),
    )


# Below this deterministic score, escalate to the optional LLM classifier.
_LLM_ESCALATION_SCORE = 2.0


def _maybe_classify_with_llm(message: str) -> tuple[str, float] | None:
    """Best-effort LLM classification; isolated so it never breaks chat."""
    try:
        from backend.chat.llm_intent import classify_intent_with_llm

        return classify_intent_with_llm(message)
    except Exception:  # noqa: BLE001 - classification must never hard-fail chat.
        return None


# Strong, high-weight signals that should win even when a generic keyword from
# another intent also appears. Phrases are matched as substrings of the
# normalized message; each match adds the given weight. These resolve the
# real-world collisions (e.g. "test scenarios" must beat the bare "test"/"ticket"
# tokens, "broken / dig in" must mean investigation rather than help).
STRONG_SIGNALS: dict[ChatIntent, list[tuple[str, float]]] = {
    "test_case_suggestion": [
        ("test case", 4.0), ("test cases", 4.0), ("test scenario", 4.0),
        ("test scenarios", 4.0), ("scenarios for", 3.0), ("suggest test", 4.0),
        ("propose test", 4.0), ("generate test", 3.5), ("draft test", 3.5),
        ("what should i test", 4.0), ("what to test", 4.0),
        ("what should i be testing", 4.0), ("cases should i write", 4.0),
        ("recommend test", 3.5), ("cas de test", 4.0), ("casos de prueba", 4.0),
        ("casos de teste", 4.0), ("testfalle", 4.0),
    ],
    "investigation_question": [
        ("dig in", 3.5), ("dig into", 3.5), ("is broken", 3.0), ("seems broken", 3.0),
        ("looks broken", 3.0), ("root cause", 4.0), ("why did it fail", 4.0),
        ("why is it failing", 4.0), ("what went wrong", 4.0), ("whats wrong", 3.0),
        ("investigate", 4.0), ("troubleshoot", 4.0), ("debug", 3.0),
    ],
    "self_healing_question": [
        ("self heal", 4.5), ("self healing", 4.5), ("broken locator", 4.5),
        ("broken locators", 4.5), ("broken keyword", 4.5), ("unknown keyword", 4.0),
        ("locator repair", 4.5), ("repair the locator", 4.5), ("fix the locator", 4.5),
        ("fix the locators", 4.5), ("fix the keyword", 4.0), ("needs healing", 4.5),
        ("what needs fixing", 4.0), ("what needs healing", 4.5), ("suggest fixes", 3.5),
        ("suggest a fix", 3.5), ("self repair", 4.0), ("heal the test", 4.5),
        ("auto repair", 4.0), ("auto fix", 3.5),
    ],
    "workflow_start": [
        ("kick off", 3.5), ("kickoff", 3.5), ("start the analysis", 4.0),
        ("start analysis", 4.0), ("begin the workflow", 4.0), ("start the workflow", 4.0),
        ("run the analysis", 3.5), ("analyze this", 3.5), ("analyse this", 3.5),
        ("get started", 3.0), ("lets start", 3.0),
    ],
    "workflow_step": [
        ("keep going", 4.0), ("carry on", 3.5), ("next step", 4.0), ("run next", 4.0),
        ("continue the workflow", 4.0), ("resume the workflow", 4.0), ("proceed", 3.0),
        ("go ahead", 2.5), ("move on", 2.5), ("next stage", 3.5),
        ("do the coverage", 4.5), ("do coverage", 4.0), ("run coverage", 4.5),
        ("run the coverage", 4.5), ("do the requirements", 4.5),
        ("run requirements", 4.5), ("run the requirements", 4.5),
        ("do the tests", 4.5), ("run the tests stage", 4.5), ("do the automation", 4.5),
        ("run automation", 4.5), ("run the automation", 4.5),
        ("do the validation", 4.5), ("run validation", 4.5), ("run the validation", 4.5),
        ("do the report", 4.5), ("run the report", 4.5), ("generate the report stage", 4.0),
        ("run the stage", 4.0), ("run that stage", 4.0), ("run this stage", 4.0),
    ],
    "show_stage_output": [
        ("show me the requirement", 6.0), ("show the requirement", 6.0),
        ("show requirement", 5.5), ("see the requirement", 5.5),
        ("view the requirement", 5.5), ("show me the requirements", 6.0),
        ("show the requirements", 6.0), ("show requirements", 5.5),
        ("see the requirements", 5.5), ("show me the coverage", 6.0),
        ("show the coverage", 6.0), ("show coverage", 5.5), ("see the coverage", 5.5),
        ("view the coverage", 5.5), ("view the requirements", 5.5),
        ("view the test case", 5.5),
        ("show me the test case", 6.0), ("show the test case", 6.0),
        ("show test case", 5.5), ("see the test case", 5.5),
        ("show me the test cases", 9.0), ("show the test cases", 9.0),
        ("show test cases", 8.5), ("see the test cases", 8.5),
        ("show me the generated test", 9.0),
        ("show me the output", 5.0), ("show the output", 5.0), ("show stage output", 6.0),
        ("show me the stage output", 6.0), ("stage output", 3.5),
        ("what did the stage produce", 5.0), ("what did it produce", 4.0),
        ("let me see the", 4.0), ("display the requirement", 5.5),
        ("display the coverage", 5.5), ("display the test case", 5.5),
        ("so i can approve", 3.5), ("show me what", 3.0), ("show me so i can", 4.5),
    ],
    "workflow_status": [
        ("where are we", 4.0), ("whats the status", 4.0), ("what is the status",
         4.0), ("current status", 3.5), ("how far along", 3.5),
        ("what stage", 3.0), ("hows it going", 2.5), ("progress so far", 3.0),
    ],
    "ticket_question": [
        ("missing anything", 3.5), ("anything missing", 3.5), ("whats missing", 3.5),
        ("ticket gaps", 3.0), ("acceptance criteria", 3.5), ("about this ticket", 3.0),
    ],
    "report_request": [
        ("wrap it up", 3.5), ("wrap up", 3.0), ("executive summary", 4.0),
        ("pm summary", 4.0), ("final report", 4.0), ("give me a summary", 3.5),
        ("summarize", 3.5), ("summarise", 3.5),
    ],
    "execution_request": [
        ("run the tests", 4.0), ("execute the tests", 4.0), ("run them", 2.5),
        ("execute the workflow", 4.0),
    ],
    "approval_request": [
        ("approve it", 4.0), ("approve the", 3.5), ("sign off", 3.5),
        ("looks good approve", 4.0),
    ],
    "validation_question": [
        ("validation failing", 4.0), ("validation complaining", 4.0),
        ("why did validation", 4.0), ("dry run", 3.5), ("dry-run", 3.5),
    ],
    "artifact_question": [
        ("robot file", 4.0), ("the robot", 2.5), ("generated file", 3.5),
        ("show me the robot", 4.0), ("automation file", 3.5),
    ],
    "system_knowledge": [
        ("how does the system", 4.0), ("how does aegis", 4.0), ("explain the system", 4.0),
        ("explain the architecture", 4.0), ("what agents", 3.5), ("which agents", 3.5),
        ("workflow stages", 3.5), ("how does governance", 4.0), ("what is aegis", 3.5),
        ("how does it work", 3.0), ("how it works", 3.0),
    ],
    "system_question": [
        ("what is mocked", 4.0), ("mocked and what is real", 4.0), ("what is real",
         3.0), ("which providers", 3.5), ("system status", 3.0), ("active mode", 3.0),
    ],
    "knowledge_question": [
        ("rag corpus", 3.5), ("knowledge base", 3.5), ("sanitized corpus", 3.5),
        ("vector", 2.5),
    ],
    "action_history": [
        ("action history", 4.0), ("pending actions", 4.0), ("what actions", 3.0),
        ("confirmed actions", 3.5),
    ],
    "help": [
        ("what can you do", 4.0), ("how can you help", 4.0), ("what can you help",
         4.0), ("how do i use", 3.0), ("what do you do", 3.5),
    ],
}

# Short conversational openers map to help so the copilot greets instead of
# falling through to the unknown fallback.
GREETINGS: frozenset[str] = frozenset(
    {
        "hi", "hey", "hello", "yo", "hiya", "greetings", "sup",
        "bonjour", "salut", "hallo", "hola", "ola", "oi",
    }
)
COURTESIES: frozenset[str] = frozenset(
    {"thanks", "thank you", "thx", "ty", "merci", "danke", "gracias", "obrigado", "cheers"}
)

# Minimum score required to claim a non-unknown intent. Below this we defer to
# the (optional) LLM layer / unknown fallback rather than guess wrong.
_MIN_SCORE = 1.0


def _score_intents(normalized: str) -> tuple[ChatIntent, float]:
    tokens = set(re.findall(r"[a-z0-9]+", normalized))

    # Pure greeting / courtesy shortcuts (only when the whole message is short).
    word_count = len(normalized.split())
    if word_count <= 3:
        if tokens & GREETINGS or normalized in GREETINGS:
            return "help", 5.0
        if normalized in COURTESIES or tokens & {t for c in COURTESIES for t in c.split()}:
            return "help", 4.0

    scores: dict[ChatIntent, float] = {}

    # 1) Strong phrase signals (high weight, resolve collisions).
    for intent, signals in STRONG_SIGNALS.items():
        for phrase, weight in signals:
            if phrase in normalized:
                scores[intent] = scores.get(intent, 0.0) + weight

    # 2) Base keyword patterns (lower weight; multi-word phrases worth more).
    for intent, patterns in INTENT_PATTERNS.items():
        if intent == "unknown":
            continue
        for needle in patterns:
            if " " in needle:
                if needle in normalized:
                    scores[intent] = scores.get(intent, 0.0) + 1.5
            elif needle in tokens:
                scores[intent] = scores.get(intent, 0.0) + 1.0

    if not scores:
        return "unknown", 0.0

    best_intent = max(scores, key=lambda key: (scores[key], -_TIE_ORDER.index(key)))
    best_score = scores[best_intent]
    if best_score < _MIN_SCORE:
        return "unknown", best_score
    return best_intent, best_score


# Tie-break order: when two intents score equally, prefer the more specific /
# actionable one. Earlier in the list wins.
_TIE_ORDER: list[ChatIntent] = [
    "test_case_suggestion",
    "investigation_question",
    "self_healing_question",
    "workflow_step",
    "show_stage_output",
    "execution_request",
    "approval_request",
    "workflow_start",
    "validation_question",
    "artifact_question",
    "report_request",
    "workflow_status",
    "system_knowledge",
    "system_question",
    "knowledge_question",
    "ticket_question",
    "action_history",
    "help",
    "unknown",
]


def _normalize_text(value: str) -> str:
    lowered = value.strip().lower()
    without_accents = "".join(
        char
        for char in unicodedata.normalize("NFKD", lowered)
        if not unicodedata.combining(char)
    )
    # Drop apostrophes so contractions collapse ("what's" -> "whats",
    # "how's" -> "hows"), then replace any remaining punctuation with spaces so
    # phrase matching is not blocked by trailing "?" / "!" / commas.
    without_apostrophes = re.sub(r"['’`]", "", without_accents)
    spaced = re.sub(r"[^a-z0-9]+", " ", without_apostrophes)
    return " ".join(spaced.split())


def _detect_language(normalized: str) -> DetectedLanguage:
    tokens = set(re.findall(r"[a-z0-9]+", normalized))
    best_language: DetectedLanguage = "unknown"
    best_score = 0
    for language, hints in LANGUAGE_HINTS.items():
        if language == "unknown":
            continue
        score = 0
        for hint in hints:
            if " " in hint:
                score += int(hint in normalized)
            else:
                score += int(hint in tokens)
        if score > best_score:
            best_language = language
            best_score = score
    return best_language


def _extract_ticket_id(message: str) -> str | None:
    match = re.search(r"\b[A-Z][A-Z0-9]+-[A-Z0-9-]+-\d+\b|\b[A-Z]{2,}-\d+\b", message)
    return match.group(0) if match else None


def _extract_context_id(message: str) -> str | None:
    match = re.search(
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
        message,
        flags=re.IGNORECASE,
    )
    return match.group(0) if match else None
