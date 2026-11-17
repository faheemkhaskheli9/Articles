import json

from llm_cascade.backends import FunctionBackend
from llm_cascade.cli import main
from llm_cascade.evaluate import cascade_report, load, rules_report


def test_datasets_are_labelled_with_allowed_values():
    from llm_cascade.schema import FIELDS
    for name in ("postings", "holdout"):
        for row in load(name):
            assert set(row["labels"]) == set(FIELDS)
            for f, v in row["labels"].items():
                assert v in FIELDS[f]


def test_reported_numbers():
    """The figures quoted in the article. Update both together."""
    dev = rules_report(load("postings"), trust_absence=True)
    assert (dev["rules_answered"], dev["rules_wrong"], dev["postings_needing_a_model"]) == (80, 0, 14)
    hold = rules_report(load("holdout"), trust_absence=True)
    assert (hold["rules_answered"], hold["rules_wrong"]) == (30, 4)
    strict = rules_report(load("holdout"), trust_absence=False)
    assert (strict["rules_answered"], strict["rules_wrong"]) == (16, 0)
    assert dev["tokens_escalated_compact"] < dev["tokens_escalated_full_text"] < dev["tokens_send_everything"]


def test_cascade_report_with_an_oracle_backend():
    rows = load("holdout")
    labels = {r["text"]: r["labels"] for r in rows}

    def oracle(messages):
        # answers with the label and no evidence: accepted only for default values
        text = messages[-1]["content"].split("Posting:\n", 1)[1]
        match = next((lab for t, lab in labels.items() if text in t), {})
        return json.dumps({f: {"value": v, "evidence": ""} for f, v in match.items()})

    r = cascade_report(rows, [FunctionBackend("local", oracle)], trust_absence=False)
    assert r["answered"] + len(r["needs_review"]) == 48
    assert r["rejected_answers_by_tier"]["local"] == len(r["needs_review"])


def test_cli_demo_and_evaluate(capsys):
    main(["demo"])
    assert "Blue Card" in capsys.readouterr().out
    main(["evaluate", "--json"])
    report = json.loads(capsys.readouterr().out)
    assert report["holdout"]["trust_absence=True"]["rules_wrong"] == 4


def test_cli_extract_offline(capsys):
    main(["extract", "--text", "Fully remote. We do not sponsor visas."])
    out = json.loads(capsys.readouterr().out)
    assert out["results"]["visa_sponsorship"]["value"] == "no"
    assert out["calls"] == []
