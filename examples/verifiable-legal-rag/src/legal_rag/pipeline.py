"""Retrieve, gate, generate, verify — and fall back or abstain instead of guessing."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .corpus import DEFAULT_CORPUS_DIR, Chunk, load_corpus
from .generation import Claim, ExtractiveGenerator, Generator
from .retrieval import DEFAULT_GLOSSARY, RetrievalDecision, Retriever, load_glossary
from .verify import Issue, verify

DISCLAIMER = "Legal information from a fictional sample corpus, not legal advice."
ABSTAIN_MESSAGE = "No sufficiently relevant provision was found in the available corpus."


@dataclass(frozen=True)
class Answer:
    status: str  # answered | answered_with_fallback | abstained
    reason: str
    generator: str | None
    claims: tuple[Claim, ...]
    citations: tuple[str, ...]
    retrieval: RetrievalDecision
    rejected_issues: tuple[Issue, ...] = field(default_factory=tuple)
    disclaimer: str = DISCLAIMER

    def render(self, corpus: dict[str, Chunk]) -> str:
        if self.status == "abstained":
            return f"{ABSTAIN_MESSAGE} ({self.reason})\n{self.disclaimer}"
        lines = []
        for claim in self.claims:
            refs = "; ".join(corpus[c].citation for c in claim.citations)
            lines.append(f"- {claim.text} [{refs}]")
        if self.status == "answered_with_fallback":
            lines.append("(Model answer failed verification; showing a verified extractive answer.)")
        lines.append(self.disclaimer)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "reason": self.reason,
            "generator": self.generator,
            "claims": [
                {"text": c.text, "citations": list(c.citations), "quote": c.quote} for c in self.claims
            ],
            "citations": list(self.citations),
            "retrieval": {
                "query_terms": list(self.retrieval.query_terms),
                "abstain": self.retrieval.abstain,
                "reason": self.retrieval.reason,
                "results": [
                    {
                        "chunk_id": r.chunk.chunk_id,
                        "score": round(r.score, 3),
                        "coverage": round(r.coverage, 3),
                        "matched_terms": list(r.matched_terms),
                    }
                    for r in self.retrieval.results
                ],
            },
            "rejected_issues": [vars(i) for i in self.rejected_issues],
            "disclaimer": self.disclaimer,
        }


class LegalRAG:
    def __init__(self, chunks: list[Chunk], retriever: Retriever, generator: Generator | None = None):
        self.corpus = {chunk.chunk_id: chunk for chunk in chunks}
        self.retriever = retriever
        self.generator = generator or ExtractiveGenerator()
        self.fallback = ExtractiveGenerator()

    @classmethod
    def from_files(
        cls,
        corpus_dir: Path = DEFAULT_CORPUS_DIR,
        glossary_path: Path = DEFAULT_GLOSSARY,
        generator: Generator | None = None,
        **retriever_options: float,
    ) -> "LegalRAG":
        chunks = load_corpus(corpus_dir)
        return cls(chunks, Retriever(chunks, load_glossary(glossary_path), **retriever_options), generator)

    def ask(self, question: str) -> Answer:
        decision = self.retriever.retrieve(question)
        if decision.abstain:
            return Answer("abstained", decision.reason, None, (), (), decision)
        sources = list(decision.results)
        evidence = [s.chunk for s in sources]

        rejected: tuple[Issue, ...] = ()
        try:
            draft = self.generator.generate(question, sources)
            report = verify(draft, evidence, self.corpus)
        except ValueError as exc:  # malformed model output is a verification failure
            draft, report = None, None
            rejected = (Issue(-1, "invalid_output", str(exc)),)
        if report is not None and report.verified:
            return self._answered("answered", decision, self.generator.name, draft.claims)
        if report is not None:
            rejected = report.issues
        if self.generator.name == self.fallback.name:
            return Answer("abstained", "verification_failed", None, (), (), decision, rejected)
        fallback = self.fallback.generate(question, sources)
        if verify(fallback, evidence, self.corpus).verified:
            answer = self._answered("answered_with_fallback", decision, self.fallback.name, fallback.claims)
            return Answer(**{**answer.__dict__, "rejected_issues": rejected})
        return Answer("abstained", "verification_failed", None, (), (), decision, rejected)

    @staticmethod
    def _answered(status: str, decision: RetrievalDecision, generator: str, claims: tuple[Claim, ...]) -> Answer:
        citations = tuple(dict.fromkeys(c for claim in claims for c in claim.citations))
        return Answer(status, decision.reason, generator, claims, citations, decision)
