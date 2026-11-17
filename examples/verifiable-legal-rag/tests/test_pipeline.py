import json

import pytest

from legal_rag.cli import load_dotenv, main
from legal_rag.evaluate import classify, evaluate_questions
from legal_rag.generation import OpenAICompatibleGenerator
from legal_rag.pipeline import LegalRAG


def fake_transport(content: str, calls: list | None = None):
    def transport(url, headers, body):
        if calls is not None:
            calls.append((url, headers, body))
        return {"choices": [{"message": {"content": content}}]}
    return transport


def rag_with(content: str, calls: list | None = None) -> LegalRAG:
    gen = OpenAICompatibleGenerator(base_url="http://local/v1", api_key="k", model="m",
                                    transport=fake_transport(content, calls))
    return LegalRAG.from_files(generator=gen)


QUESTION = "How long is the notice to vacate a landlord must serve?"


def test_verified_model_answer_is_returned():
    calls: list = []
    content = json.dumps({"claims": [{
        "text": "The landlord must serve written notice to vacate of not less than 90 days.",
        "citations": ["sample_tenancy_act#s4"],
        "quote": "written notice to vacate of not less than 90 days"}]})
    answer = rag_with(content, calls).ask(QUESTION)
    assert answer.status == "answered" and answer.generator == "openai"
    url, headers, body = calls[0]
    assert url == "http://local/v1/chat/completions"
    assert headers["Authorization"] == "Bearer k"
    assert body["temperature"] == 0 and "[sample_tenancy_act#s4]" in body["messages"][1]["content"]


@pytest.mark.parametrize("content", [
    "not json at all",
    json.dumps({"claims": [{"text": "Landlords may evict without notice.",
                            "citations": ["sample_tenancy_act#s4"],
                            "quote": "landlords may evict without notice at any time"}]}),
])
def test_unverified_model_answer_falls_back_to_extractive(content):
    answer = rag_with(content).ask(QUESTION)
    assert answer.status == "answered_with_fallback"
    assert answer.generator == "extractive"
    assert answer.rejected_issues
    assert answer.citations == ("sample_tenancy_act#s4",)


def test_model_is_not_called_when_retrieval_abstains():
    calls: list = []
    answer = rag_with("{}", calls).ask("Biryani ki recipe batao")
    assert answer.status == "abstained" and calls == []


def test_openai_generator_requires_model(monkeypatch):
    monkeypatch.delenv("LLM_MODEL", raising=False)
    with pytest.raises(ValueError, match="LLM_MODEL"):
        OpenAICompatibleGenerator(model=None)


def test_evaluation_set_has_no_unsafe_answers_at_default_threshold(rag):
    report = evaluate_questions(rag)
    assert report["unsafe_answers"] == 0
    assert report["totals"]["correct_answer"] >= 10
    assert set(report["by_language"]) == {"en", "ur", "ur-Latn"}


def test_classify_rejects_mixed_citations():
    case = {"expected_status": "answered", "expected_sources": ["a"]}
    assert classify(case, "answered", ("a",)) == "correct_answer"
    assert classify(case, "answered", ("a", "b")) == "wrong_source"
    assert classify(case, "abstained", ()) == "missed_answer"


def test_cli_ask_json_and_verify_fixtures(capsys):
    assert main(["ask", "--json", "Can a tenant sublet part of the premises?"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "answered" and out["citations"] == ["sample_tenancy_act#s6"]
    assert main(["verify-fixtures"]) == 0


def test_dotenv_does_not_override_existing_env(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("# comment\nLLM_MODEL='from-file'\nNEW_VAR=1\n", encoding="utf-8")
    monkeypatch.setenv("LLM_MODEL", "from-shell")
    monkeypatch.delenv("NEW_VAR", raising=False)
    load_dotenv(env)
    import os
    assert os.environ["LLM_MODEL"] == "from-shell" and os.environ["NEW_VAR"] == "1"
