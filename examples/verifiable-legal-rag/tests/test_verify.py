import pytest

from legal_rag.evaluate import evaluate_verifier
from legal_rag.generation import Claim, DraftAnswer, parse_draft
from legal_rag.verify import negations_in, numbers_in, verify


def test_every_adversarial_fixture_produces_exact_issue_codes(rag):
    report = evaluate_verifier(rag)
    failures = [r for r in report["results"] if not r["passed"]]
    assert report["cases"] >= 10
    assert failures == []


def test_quote_matching_ignores_whitespace_and_case_but_not_words(rag):
    s4 = rag.corpus["sample_tenancy_act#s4"]
    ok = DraftAnswer((Claim("Notice of not less than 90 days.", (s4.chunk_id,),
                            "WRITTEN   notice to vacate of not less than 90 days"),))
    assert verify(ok, [s4], rag.corpus).verified
    bad = DraftAnswer((Claim("Notice of not less than 90 days.", (s4.chunk_id,),
                             "written notice to vacate of not more than 90 days"),))
    assert "quote_not_found" in verify(bad, [s4], rag.corpus).codes


def test_number_words_are_compared_with_digits():
    assert numbers_in("three months and 1,500 rupees") == {"3", "1500"}
    assert numbers_in("twelve months") == {"12"}


def test_negation_words_are_whole_words_only():
    assert negations_in("Nothing notable") == set()
    assert negations_in("shall not sublet") == {"not", "shall not"}


@pytest.mark.parametrize(
    "payload",
    ["not json", "[]", '{"claims": "x"}', '{"claims": [1]}',
     '{"claims": [{"text": "a", "quote": "b", "citations": "id"}]}',
     '{"claims": [{"text": 1, "quote": "b", "citations": []}]}'],
)
def test_parse_draft_rejects_malformed_output(payload):
    with pytest.raises(ValueError):
        parse_draft(payload)
