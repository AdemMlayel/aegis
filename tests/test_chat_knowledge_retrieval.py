"""Tests for the knowledge_question chat response doing REAL RAG retrieval.

Before this, knowledge_question returned a static corpus census regardless of
what the user asked. Now a substantive query retrieves and surfaces actual
chunks (leveraging the fixed semantic embedding), a bare inventory question
returns the census, and an unrelated query honestly reports no match.
"""
from __future__ import annotations

from backend.chat.response_builder import _knowledge_response, _knowledge_query_terms


def test_substantive_query_retrieves_relevant_chunk() -> None:
    out = _knowledge_response("what does the corpus say about banking risk")
    assert "KB-BANK-001" in out
    assert "relevance" in out


def test_robot_query_retrieves_robot_chunk() -> None:
    out = _knowledge_response("knowledge about robot validation keywords")
    assert "KB-ROBOT-001" in out


def test_bare_inventory_question_returns_census() -> None:
    out = _knowledge_response("what is in the knowledge base")
    assert "Knowledge chunks" in out
    assert "Robot keywords" in out
    # Census, not a retrieval listing.
    assert "relevance" not in out


def test_unrelated_query_reports_no_match_honestly() -> None:
    out = _knowledge_response("knowledge about quantum cryptography blockchain")
    assert "Nothing in the sanitized knowledge corpus matched" in out
    # Must NOT surface low-relevance noise as if it were an answer.
    assert "relevance" not in out


def test_query_terms_strip_rag_metawords() -> None:
    # The meta-words that trigger the intent must not themselves drive retrieval.
    assert _knowledge_query_terms("what does the knowledge corpus say") == []
    assert _knowledge_query_terms("knowledge about banking risk") == ["banking", "risk"]


def test_empty_message_falls_back_to_inventory() -> None:
    out = _knowledge_response("")
    assert "Knowledge chunks" in out
