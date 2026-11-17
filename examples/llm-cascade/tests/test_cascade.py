import json

from llm_cascade.backends import Cache, FunctionBackend, OpenAICompatible
from llm_cascade.cascade import Cascade
from llm_cascade.validate import check_answer

POSTING = (
    "Speech AI Engineer, Berlin. Office-first culture with optional remote Fridays. "
    "We sponsor visas. Our team speaks German day to day, so you will pick it up quickly."
)


def answer(**fields):
    return lambda messages: json.dumps(fields)


def requested(messages):
    user = messages[-1]["content"]
    return json.loads(user.split("\n", 1)[0].split(": ", 1)[1])


def test_rules_answer_without_any_model_call():
    local = FunctionBackend("local", answer())
    out = Cascade([local]).run("Fully remote. We do not sponsor visas. German is not required.")
    assert local.calls == 0
    assert {f: r.tier for f, r in out.results.items()} == dict.fromkeys(out.results, "rules")


def test_only_unresolved_fields_reach_the_model():
    seen = {}

    def fn(messages):
        seen.update(requested(messages))
        return json.dumps({
            "work_mode": {"value": "hybrid", "evidence": "Office-first culture with optional remote Fridays."},
            "german": {"value": "not_required", "evidence": "so you will pick it up quickly"},
        })

    out = Cascade([FunctionBackend("local", fn)]).run(POSTING)
    assert set(seen) == {"work_mode", "german"}  # visa was answered by rules
    assert out.results["visa_sponsorship"].tier == "rules"
    assert out.results["work_mode"].tier == "local"
    assert out.results["german"].value == "not_required"


def test_invented_evidence_escalates_to_the_next_tier():
    local = FunctionBackend("local", answer(
        work_mode={"value": "remote", "evidence": "This role is fully remote."},  # not in the text
        german={"value": "not_required", "evidence": ""},
    ))
    remote = FunctionBackend("remote", answer(
        work_mode={"value": "hybrid", "evidence": "optional remote Fridays"},
    ))
    out = Cascade([local, remote]).run(POSTING)
    assert out.results["german"].tier == "local"
    assert out.results["work_mode"].tier == "remote"
    assert "not a quote" in out.calls[0].rejected["work_mode"]
    assert out.calls[1].fields == ["work_mode"]


def test_evidence_that_rules_contradict_is_rejected():
    ok, reason = check_answer("visa_sponsorship",
                              {"value": "yes", "evidence": "We do not sponsor visas."},
                              "We do not sponsor visas.")
    assert not ok and "rules read" in reason


def test_bad_values_and_missing_evidence_are_rejected():
    assert not check_answer("work_mode", {"value": "sometimes", "evidence": ""}, "x")[0]
    assert not check_answer("work_mode", {"value": "remote", "evidence": ""}, "x")[0]
    assert check_answer("work_mode", {"value": "unknown", "evidence": ""}, "x")[0]
    assert not check_answer("german", "required", "x")[0]


def test_broken_json_and_errors_fall_through_to_review():
    broken = FunctionBackend("local", lambda m: "Sure! Here is the JSON:")

    def boom(messages):
        raise OSError("connection refused")

    out = Cascade([broken, FunctionBackend("remote", boom)]).run(POSTING)
    assert out.needs_review == ["work_mode", "german"]
    assert all("call failed" in r for c in out.calls for r in c.rejected.values())


def test_compaction_drops_boilerplate():
    sizes = []

    def fn(messages):
        sizes.append(len(messages[-1]["content"]))
        return "{}"

    blurb = " ".join(["We value curiosity, ownership and kindness."] * 30)
    text = POSTING + " " + blurb
    Cascade([FunctionBackend("a", fn)]).run(text)
    Cascade([FunctionBackend("b", fn)], compact=False).run(text)
    assert sizes[0] < sizes[1] / 3


def test_cache_returns_stored_answer_without_network(tmp_path):
    cache = Cache(tmp_path / "c.sqlite")
    backend = OpenAICompatible("local", "http://127.0.0.1:9", "m", cache=cache, timeout=0.1)
    messages = [{"role": "user", "content": "hi"}]
    cache.put(Cache.key("m", "http://127.0.0.1:9", messages), '{"ok": 1}')
    assert backend.complete(messages) == '{"ok": 1}'
    assert backend.cache_hits == 1


def test_openai_compatible_backend_over_http(tmp_path):
    """Run the real HTTP client against a local fake server shaped like Ollama/OpenAI."""
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    received = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            received.append(body)
            content = json.dumps({"work_mode": {"value": "hybrid", "evidence": "optional remote Fridays"},
                                  "german": {"value": "not_required", "evidence": ""}})
            data = json.dumps({"choices": [{"message": {"content": content}}]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/v1"
        backend = OpenAICompatible("local", url, "qwen2.5:7b", cache=Cache(tmp_path / "c.sqlite"))
        first = Cascade([backend]).run(POSTING)
        second = Cascade([backend]).run(POSTING)
    finally:
        server.shutdown()
    assert first.results["work_mode"].tier == "local"
    assert len(received) == 1 and backend.cache_hits == 1  # second run served from cache
    assert received[0]["temperature"] == 0 and received[0]["seed"] == 7
    assert second.results == first.results
