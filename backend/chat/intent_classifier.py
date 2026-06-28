from __future__ import annotations

import re
import unicodedata
from typing import Literal

from pydantic import Field

from backend.chat.schemas import ChatIntent
from backend.graph.state import StrictModel


DetectedLanguage = Literal["en", "fr", "de", "es", "pt", "unknown"]


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
    "unknown": [],
}

CONFIDENCE_BY_INTENT: dict[ChatIntent, float] = {
    "help": 0.95,
    "system_question": 0.84,
    "workflow_start": 0.88,
    "workflow_step": 0.84,
    "workflow_status": 0.87,
    "approval_request": 0.83,
    "execution_request": 0.87,
    "artifact_question": 0.80,
    "validation_question": 0.84,
    "investigation_question": 0.82,
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

    intent = _match_intent(normalized)
    return ClassifiedIntent(
        intent=intent,
        confidence=CONFIDENCE_BY_INTENT[intent],
        ticket_id=ticket_id,
        context_id=context_id,
        normalized_message=normalized,
        detected_language=_detect_language(normalized),
    )


def _match_intent(normalized: str) -> ChatIntent:
    for intent, patterns in INTENT_PATTERNS.items():
        if intent == "unknown":
            continue
        if _contains_any(normalized, patterns):
            return intent
    return "unknown"


def _contains_any(value: str, needles: list[str]) -> bool:
    tokens = set(re.findall(r"[a-z0-9]+", value))
    for needle in needles:
        if " " in needle:
            if needle in value:
                return True
        elif needle in tokens:
            return True
    return False


def _normalize_text(value: str) -> str:
    collapsed = " ".join(value.strip().lower().split())
    without_accents = "".join(
        char
        for char in unicodedata.normalize("NFKD", collapsed)
        if not unicodedata.combining(char)
    )
    return without_accents.replace("’", "'")


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
