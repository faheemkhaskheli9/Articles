from pathlib import Path

import pytest

from legal_rag.corpus import load_corpus, parse_document
from legal_rag.retrieval import Retriever, expand_query, tokenize


def test_one_chunk_per_provision_with_stable_ids():
    chunks = load_corpus()
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids)) == 12
    assert "sample_tenancy_act#s4" in ids and "sample_consumer_rules#r1" in ids
    s4 = next(c for c in chunks if c.chunk_id == "sample_tenancy_act#s4")
    assert s4.citation == "Sample Tenancy Act (Illustrative), Section 4 (Notice to Vacate)"
    assert "90 days" in s4.text and "Section 5" not in s4.text


def test_parser_rejects_duplicate_and_empty_provisions(tmp_path: Path):
    dup = tmp_path / "dup.txt"
    dup.write_text("Section 1. A\ntext\nSection 1. B\nmore\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        parse_document(dup)
    empty = tmp_path / "empty.txt"
    empty.write_text("Section 1. A\n\nSection 2. B\ntext\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no text"):
        parse_document(empty)
    none = tmp_path / "none.txt"
    none.write_text("just prose\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no Section"):
        parse_document(none)


def test_glossary_prefers_longest_phrase():
    glossary = {"کرایہ": "rent", "کرایہ دار": "tenant"}
    assert tokenize(expand_query("کرایہ دار", glossary)) == ["tenant"]


def test_explicit_missing_provision_abstains_even_with_matching_words(rag):
    decision = rag.retriever.retrieve("What does Section 12 say about the security deposit?")
    assert decision.abstain and decision.reason == "referenced_provision_not_in_corpus"


def test_explicit_existing_provision_is_grounded(rag):
    decision = rag.retriever.retrieve("Explain section 7")
    assert not decision.abstain
    assert decision.results[0].chunk.chunk_id == "sample_tenancy_act#s7"


@pytest.mark.parametrize("query", ["What is the capital gains tax rate?", "the of and", ""])
def test_off_topic_and_empty_queries_abstain(rag, query):
    assert rag.retriever.retrieve(query).abstain


def test_near_miss_blocked_by_coverage_not_by_score(rag):
    decision = rag.retriever.retrieve("How much notice must my employer give before firing me?")
    assert decision.abstain and decision.reason == "query_not_covered"
    assert decision.results[0].score >= rag.retriever.min_score


def test_invalid_retriever_settings():
    chunks = load_corpus()
    with pytest.raises(ValueError):
        Retriever(chunks, top_k=0)
    with pytest.raises(ValueError):
        Retriever(chunks, min_coverage=1.5)
